from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from data_engine.data_quality import validate_ohlcv_and_quarantine


from core.settings import settings

def _db_path(realm: str = "EGX") -> Path:
    root = Path(settings.DATA_ROOT) / realm
    root.mkdir(parents=True, exist_ok=True)
    return root / "intraday_store.sqlite"




def _connect(realm: str = "EGX") -> sqlite3.Connection:
    # Increased timeout to 60s to handle long-running batch ingests in dedicated workers
    conn = sqlite3.connect(_db_path(realm), timeout=60)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=MEMORY")
    conn.execute("PRAGMA cache_size=-65536")
    conn.execute("PRAGMA busy_timeout=60000")
    # Enable memory-mapped I/O for faster reading
    conn.execute("PRAGMA mmap_size=268435456") 
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS intraday_bars (
            ticker TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            PRIMARY KEY (ticker, timestamp)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_intraday_bars_ticker_ts "
        "ON intraday_bars(ticker, timestamp)"
    )


def _normalize_intraday_frame(df: pd.DataFrame, ticker: str, realm: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    work = df.copy()
    work.columns = [str(c).lower() for c in work.columns]

    if "timestamp" in work.columns:
        work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    elif isinstance(work.index, pd.DatetimeIndex):
        work = work.reset_index().rename(columns={"index": "timestamp"})
        work["timestamp"] = pd.to_datetime(work["timestamp"], errors="coerce")
    else:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    validated, _ = validate_ohlcv_and_quarantine(
        ticker=ticker,
        df=work,
        realm=realm,
        stream="intraday_store",
    )
    if validated.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    return validated


def get_last_timestamp(ticker: str, realm: str = "EGX"):
    ticker = ticker.strip().upper()
    if not ticker:
        return None
    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT MAX(timestamp) FROM intraday_bars WHERE ticker = ?",
            (ticker,),
        ).fetchone()
    value = row[0] if row else None
    if not value:
        return None
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts


def get_latest_timestamps(realm: str = "EGX") -> dict[str, pd.Timestamp]:
    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT ticker, MAX(timestamp) AS latest_timestamp
            FROM intraday_bars
            GROUP BY ticker
            """
        ).fetchall()

    out: dict[str, pd.Timestamp] = {}
    for ticker, raw_ts in rows:
        if not ticker or not raw_ts:
            continue
        ts = pd.to_datetime(raw_ts, errors="coerce")
        if pd.isna(ts):
            continue
        out[str(ticker).upper()] = ts
    return out


def get_latest_bars(tickers: list[str] | None = None, realm: str = "EGX") -> pd.DataFrame:
    columns = ["ticker", "timestamp", "open", "high", "low", "close", "volume"]
    normalized_tickers: list[str] | None = None
    if tickers is not None:
        normalized_tickers = list(
            dict.fromkeys(str(ticker).strip().upper() for ticker in tickers if str(ticker).strip())
        )
        if not normalized_tickers:
            return pd.DataFrame(columns=columns)

    rows = []
    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        if normalized_tickers is None:
            rows = conn.execute(
                """
                SELECT b.ticker, b.timestamp, b.open, b.high, b.low, b.close, b.volume
                FROM intraday_bars b
                JOIN (
                    SELECT ticker, MAX(timestamp) AS latest_timestamp
                    FROM intraday_bars
                    GROUP BY ticker
                ) latest
                  ON b.ticker = latest.ticker
                 AND b.timestamp = latest.latest_timestamp
                ORDER BY b.ticker ASC
                """
            ).fetchall()
        else:
            for ticker in normalized_tickers:
                row = conn.execute(
                    """
                    SELECT ticker, timestamp, open, high, low, close, volume
                    FROM intraday_bars
                    WHERE ticker = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    (ticker,),
                ).fetchone()
                if row is not None:
                    rows.append(row)

    if not rows:
        return pd.DataFrame(columns=columns)

    out = pd.DataFrame(rows, columns=columns)
    out["ticker"] = out["ticker"].astype(str).str.upper()
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    return out.dropna(subset=["timestamp"]).reset_index(drop=True)


def get_intraday_date_counts(realm: str = "EGX") -> list[dict[str, int | str]]:
    """Return available intraday dates with record and ticker counts."""
    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT
                substr(timestamp, 1, 10) AS session_date,
                COUNT(*) AS records,
                COUNT(DISTINCT ticker) AS tickers
            FROM intraday_bars
            WHERE timestamp IS NOT NULL AND length(timestamp) >= 10
            GROUP BY session_date
            ORDER BY session_date ASC
            """
        ).fetchall()

    return [
        {"date": str(session_date), "records": int(records or 0), "tickers": int(tickers or 0)}
        for session_date, records, tickers in rows
        if session_date
    ]


def upsert_intraday(
    ticker: str,
    df: pd.DataFrame,
    realm: str = "EGX",
    accumulate_volume: bool = True,
) -> int:
    ticker = ticker.strip().upper()
    if not ticker:
        return 0

    work = _normalize_intraday_frame(df, ticker=ticker, realm=realm)
    if work.empty:
        return 0

    rows = [
        (
            ticker,
            row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            float(row.volume),
        )
        for row in work.itertuples(index=False)
    ]

    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        if accumulate_volume:
            conflict_update = """
                ON CONFLICT(ticker, timestamp) DO UPDATE SET
                    open=intraday_bars.open,
                    high=MAX(intraday_bars.high, excluded.high),
                    low=MIN(intraday_bars.low, excluded.low),
                    close=excluded.close,
                    volume=intraday_bars.volume + excluded.volume
            """
        else:
            conflict_update = """
                ON CONFLICT(ticker, timestamp) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume
            """
        conn.executemany(
            f"""
            INSERT INTO intraday_bars(ticker, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            {conflict_update}
            """,
            rows,
        )
    return len(rows)


def replace_intraday(ticker: str, df: pd.DataFrame, realm: str = "EGX") -> int:
    ticker = ticker.strip().upper()
    if not ticker:
        return 0

    work = _normalize_intraday_frame(df, ticker=ticker, realm=realm)
    if work.empty:
        return 0

    rows = [
        (
            ticker,
            row.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            float(row.open),
            float(row.high),
            float(row.low),
            float(row.close),
            float(row.volume),
        )
        for row in work.itertuples(index=False)
    ]

    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        conn.execute("DELETE FROM intraday_bars WHERE ticker = ?", (ticker,))
        conn.executemany(
            """
            INSERT INTO intraday_bars(ticker, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker, timestamp) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                volume=excluded.volume
            """,
            rows,
        )
    return len(rows)


def get_intraday_data(ticker: str, realm: str = "EGX", limit: int | None = None) -> pd.DataFrame:
    ticker = ticker.strip().upper()
    if not ticker:
        return pd.DataFrame()

    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        if limit is not None and int(limit) > 0:
            rows = conn.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM intraday_bars
                WHERE ticker = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (ticker, int(limit)),
            ).fetchall()
            rows = list(reversed(rows))
        else:
            rows = conn.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM intraday_bars
                WHERE ticker = ?
                ORDER BY timestamp ASC
                """,
                (ticker,),
            ).fetchall()

    if not rows:
        return pd.DataFrame()

    out = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out = out.dropna(subset=["timestamp"])
    if out.empty:
        return pd.DataFrame()
    out = out.set_index("timestamp")
    out.index.name = "timestamp"
    return out


def get_bulk_intraday_data(
    tickers: list[str],
    realm: str = "EGX",
    since_timestamp: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """
    Fetch intraday bars for multiple tickers.
    If since_timestamp is provided, bounds query to timestamp >= since_timestamp
    to avoid unbounded historical table scans across all days.
    """
    if not tickers:
        return pd.DataFrame(columns=["ticker", "timestamp", "open", "high", "low", "close", "volume"])

    # SQLite parameter limit is typically 999. If more, we'd need to chunk.
    # Egx universe is ~250-400 tickers, so one shot is fine.
    placeholders = ",".join(["?"] * len(tickers))
    params: list[object] = [str(t).strip().upper() for t in tickers]
    time_clause = ""
    if since_timestamp is not None:
        if hasattr(since_timestamp, "strftime"):
            ts_str = since_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            ts_str = str(since_timestamp).strip()
        time_clause = " AND timestamp >= ?"
        params.append(ts_str)

    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        sql = f"""
            SELECT ticker, timestamp, open, high, low, close, volume
            FROM intraday_bars
            WHERE ticker IN ({placeholders}){time_clause}
            ORDER BY timestamp ASC
        """
        rows = conn.execute(sql, params).fetchall()

    if not rows:
        return pd.DataFrame(columns=["ticker", "timestamp", "open", "high", "low", "close", "volume"])

    out = pd.DataFrame(rows, columns=["ticker", "timestamp", "open", "high", "low", "close", "volume"])
    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
    out = out.dropna(subset=["timestamp"])
    return out


def list_tickers(realm: str = "EGX") -> list[str]:
    with closing(_connect(realm)) as conn, conn:
        _ensure_schema(conn)
        rows = conn.execute(
            "SELECT DISTINCT ticker FROM intraday_bars ORDER BY ticker ASC"
        ).fetchall()
    return [str(r[0]).upper() for r in rows if r and r[0]]
