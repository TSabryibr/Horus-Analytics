from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import timedelta, timezone
from pathlib import Path

import pandas as pd

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None

from functools import lru_cache

from core.settings import settings


_SYMBOL_TABLE_RE = re.compile(r"^_[A-Za-z][A-Za-z0-9_]*$")
_SOURCE_CACHE_VERSION = 1
_SOURCE_CACHE_DIR = Path(settings.DATA_ROOT) / "_source_cache"




@dataclass(frozen=True)
class MubasherPaths:
    root: Path
    user_id: str
    history_db: Path
    intraday_db: Path
    historical_trade_dir: Path


def build_paths(root: Path | str, user_id: str | None = None) -> MubasherPaths:
    root_path = Path(root)
    user_data_root = root_path / "UserData"

    if not user_id or not str(user_id).strip():
        user_dirs = sorted([d for d in user_data_root.iterdir() if d.is_dir()], key=lambda p: p.name)
        if not user_dirs:
            raise FileNotFoundError(f"No user folders found under {user_data_root}")
        user_id = user_dirs[0].name

    base_user = user_data_root / str(user_id).strip()
    return MubasherPaths(
        root=root_path,
        user_id=user_id,
        history_db=base_user / "History" / "CASE" / "history.db",
        intraday_db=base_user / "Intraday" / "CASE" / "INTRADAY_MASTER.db",
        historical_trade_dir=base_user / "HistoricalTrade" / "CASE",
    )


def _open_sqlite_ro(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(path)
    uri = f"file:///{path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=20)


def _db_signature(path: Path) -> dict[str, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return {
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _source_cache_path(db_path: Path, name: str) -> Path:
    digest = hashlib.sha1(db_path.resolve().as_posix().encode("utf-8")).hexdigest()[:16]
    return _SOURCE_CACHE_DIR / f"{name}_{digest}.json"


def _load_source_cache(db_path: Path, name: str):
    signature = _db_signature(db_path)
    if signature is None:
        return None
    path = _source_cache_path(db_path, name)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(raw, dict):
        return None
    if raw.get("version") != _SOURCE_CACHE_VERSION or raw.get("signature") != signature:
        return None
    payload = raw.get("payload")
    return payload if isinstance(payload, dict) else None


def _save_source_cache(db_path: Path, name: str, payload: dict) -> None:
    signature = _db_signature(db_path)
    if signature is None:
        return
    try:
        _SOURCE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _source_cache_path(db_path, name)
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps(
                {
                    "version": _SOURCE_CACHE_VERSION,
                    "signature": signature,
                    "payload": payload,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        tmp_path.replace(path)
    except Exception:
        pass


def open_history_connection(paths: MubasherPaths) -> sqlite3.Connection:
    return _open_sqlite_ro(paths.history_db)


def _quoted_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _cairo_tz() -> timezone | ZoneInfo:
    if ZoneInfo is None:
        return timezone(timedelta(hours=2), name="UTC+02")
    try:
        return ZoneInfo("Africa/Cairo")
    except Exception:
        return timezone(timedelta(hours=2), name="UTC+02")


def _normalize_yyyymmdd(value) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if re.fullmatch(r"\d{8}", text):
        return text
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    return ts.strftime("%Y%m%d")


@lru_cache(maxsize=4)
def _cached_list_symbol_tables(db_path: str) -> list[tuple[str, str]]:
    """Cache the schema table list mapped by the string path of the db."""
    with closing(_open_sqlite_ro(Path(db_path))) as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables: list[tuple[str, str]] = []
        for (name,) in cur.fetchall():
            if not _SYMBOL_TABLE_RE.fullmatch(name):
                continue
            tables.append((name, name[1:].upper()))
        return tables

def list_history_symbols(paths: MubasherPaths) -> list[str]:
    return [symbol for _, symbol in _cached_list_symbol_tables(paths.history_db.as_posix())]


def list_intraday_symbols(paths: MubasherPaths) -> list[str]:
    return [symbol for _, symbol in _cached_list_symbol_tables(paths.intraday_db.as_posix())]


def _find_table_for_symbol(db_path: str, symbol: str) -> str | None:
    target = symbol.strip().upper()
    return _symbol_table_map(db_path).get(target)


@lru_cache(maxsize=4)
def _symbol_table_map(db_path: str) -> dict[str, str]:
    return {symbol: table_name for table_name, symbol in _cached_list_symbol_tables(db_path)}


def _empty_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])


def _normalize_history_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return _empty_ohlcv_frame()

    df = df.rename(
        columns={
            "DATE": "timestamp",
            "OP": "open",
            "HIG": "high",
            "LOW": "low",
            "CLS": "close",
            "VOL": "volume",
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(str), format="%Y%m%d", errors="coerce")
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = df["volume"].fillna(0)

    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    df = df.sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    return df[["timestamp", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def _load_history_dataframe_from_table(
    conn: sqlite3.Connection,
    table_name: str,
    min_date=None,
) -> pd.DataFrame:
    normalized_min = _normalize_yyyymmdd(min_date)
    if normalized_min:
        q = (
            f"SELECT DATE, OP, HIG, LOW, CLS, VOL "
            f"FROM {_quoted_identifier(table_name)} "
            f"WHERE DATE > ? ORDER BY DATE"
        )
        df = pd.read_sql_query(q, conn, params=[normalized_min])
    else:
        q = (
            f"SELECT DATE, OP, HIG, LOW, CLS, VOL "
            f"FROM {_quoted_identifier(table_name)} ORDER BY DATE"
        )
        df = pd.read_sql_query(q, conn)
    return _normalize_history_dataframe(df)


def load_history_dataframe(
    paths: MubasherPaths,
    symbol: str,
    min_date=None,
    conn: sqlite3.Connection | None = None,
) -> pd.DataFrame:
    table_name = _find_table_for_symbol(paths.history_db.as_posix(), symbol)
    if not table_name:
        return _empty_ohlcv_frame()

    if conn is not None:
        return _load_history_dataframe_from_table(conn, table_name, min_date=min_date)

    with closing(open_history_connection(paths)) as owned_conn:
        return _load_history_dataframe_from_table(owned_conn, table_name, min_date=min_date)


def epoch_minute_to_local_naive(minute_series: pd.Series | int | float) -> pd.Series | pd.Timestamp:
    is_scalar = not isinstance(minute_series, (pd.Series, pd.Index, list))
    series = pd.Series([minute_series]) if is_scalar else minute_series
    utc_dt = pd.to_datetime(series, unit="m", origin="unix", utc=True, errors="coerce")
    local_dt = utc_dt.dt.tz_convert(_cairo_tz())
    res = local_dt.dt.tz_localize(None)
    return res.iloc[0] if is_scalar else res


def local_naive_to_epoch_minute(value) -> int | None:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return None
    try:
        if getattr(ts, "tzinfo", None) is None:
            local_ts = ts.tz_localize(_cairo_tz(), nonexistent="shift_forward", ambiguous="NaT")
        else:
            local_ts = ts.tz_convert(_cairo_tz())
    except Exception:
        return None
    if pd.isna(local_ts):
        return None
    return int(local_ts.tz_convert("UTC").timestamp() // 60)


def load_intraday_dataframe(paths: MubasherPaths, symbol: str, min_tmin: int | None = None) -> pd.DataFrame:
    table_name = _find_table_for_symbol(paths.intraday_db.as_posix(), symbol)
    if not table_name:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    with closing(_open_sqlite_ro(paths.intraday_db)) as conn:

        if min_tmin is None:
            q = (
                f"SELECT TMIN, OP, HIG, LOW, CLS, VOL "
                f"FROM {_quoted_identifier(table_name)} ORDER BY TMIN"
            )
            df = pd.read_sql_query(q, conn)
        else:
            q = (
                f"SELECT TMIN, OP, HIG, LOW, CLS, VOL "
                f"FROM {_quoted_identifier(table_name)} "
                f"WHERE TMIN > ? ORDER BY TMIN"
            )
            df = pd.read_sql_query(q, conn, params=[int(min_tmin)])

    if df.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    df = df.rename(
        columns={
            "TMIN": "tmin",
            "OP": "open",
            "HIG": "high",
            "LOW": "low",
            "CLS": "close",
            "VOL": "volume",
        }
    )

    df["tmin"] = pd.to_numeric(df["tmin"], errors="coerce")
    df["timestamp"] = epoch_minute_to_local_naive(df["tmin"])

    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = df["volume"].fillna(0)

    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    df = df.sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    return df[["timestamp", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def get_intraday_latest_bars(paths: MubasherPaths) -> dict[str, dict[str, object]]:
    cached = _load_source_cache(paths.intraday_db, "intraday_latest_bars")
    if cached is not None:
        out: dict[str, dict[str, object]] = {}
        for raw_ticker, raw_bar in cached.items():
            if not isinstance(raw_bar, dict):
                continue
            ticker = str(raw_ticker).strip().upper()
            if not ticker:
                continue
            try:
                out[ticker] = {
                    "tmin": int(raw_bar["tmin"]),
                    "timestamp": pd.Timestamp(raw_bar["timestamp"]),
                    "open": float(raw_bar["open"]),
                    "high": float(raw_bar["high"]),
                    "low": float(raw_bar["low"]),
                    "close": float(raw_bar["close"]),
                    "volume": float(raw_bar["volume"]),
                }
            except (KeyError, TypeError, ValueError):
                continue
        return out

    rows: list[tuple[object, object, object, object, object, object, object]] = []
    with closing(_open_sqlite_ro(paths.intraday_db)) as conn:
        for table_name, symbol in _cached_list_symbol_tables(paths.intraday_db.as_posix()):
            table_ident = _quoted_identifier(table_name)
            q = (
                f"SELECT TMIN, OP, HIG, LOW, CLS, VOL "
                f"FROM {table_ident} "
                f"WHERE TMIN = (SELECT MAX(TMIN) FROM {table_ident}) "
                f"LIMIT 1"
            )
            try:
                row = conn.execute(q).fetchone()
            except sqlite3.DatabaseError:
                continue
            if row is None or row[0] is None:
                continue
            rows.append((symbol, *row))

    if not rows:
        return {}

    df = pd.DataFrame(
        rows,
        columns=["ticker", "tmin", "open", "high", "low", "close", "volume"],
    )
    df["ticker"] = df["ticker"].astype(str).str.upper()
    df["tmin"] = pd.to_numeric(df["tmin"], errors="coerce")
    df["timestamp"] = epoch_minute_to_local_naive(df["tmin"])

    for col in ("open", "high", "low", "close", "volume"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["volume"] = df["volume"].fillna(0)

    df = df.dropna(subset=["ticker", "tmin", "timestamp", "open", "high", "low", "close"])
    if df.empty:
        return {}

    df["tmin"] = df["tmin"].astype("int64")
    df = df.sort_values(["ticker", "tmin"]).drop_duplicates(subset=["ticker"], keep="last")

    out: dict[str, dict[str, object]] = {}
    for row in df.itertuples(index=False):
        ticker = str(row.ticker).strip().upper()
        if not ticker:
            continue
        out[ticker] = {
            "tmin": int(row.tmin),
            "timestamp": row.timestamp,
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": float(row.volume),
        }
    _save_source_cache(
        paths.intraday_db,
        "intraday_latest_bars",
        {
            ticker: {
                **{k: v for k, v in bar.items() if k != "timestamp"},
                "timestamp": pd.Timestamp(bar["timestamp"]).isoformat(),
            }
            for ticker, bar in out.items()
        },
    )
    return out


def get_history_last_dates(
    paths: MubasherPaths,
    conn: sqlite3.Connection | None = None,
) -> dict[str, str]:
    cached = _load_source_cache(paths.history_db, "history_last_dates")
    if cached is not None:
        return {
            str(symbol).upper(): str(last_date)
            for symbol, last_date in cached.items()
            if re.fullmatch(r"\d{8}", str(last_date))
        }

    out: dict[str, str] = {}
    owns_conn = conn is None
    active_conn = conn or open_history_connection(paths)
    try:
        for table_name, symbol in _cached_list_symbol_tables(paths.history_db.as_posix()):
            q = f"SELECT MAX(DATE) FROM {_quoted_identifier(table_name)}"
            max_date = active_conn.execute(q).fetchone()[0]
            text = str(max_date).strip() if max_date is not None else ""
            if re.fullmatch(r"\d{8}", text):
                out[symbol] = text
    finally:
        if owns_conn:
            active_conn.close()
    _save_source_cache(paths.history_db, "history_last_dates", out)
    return out


def get_intraday_last_minutes(paths: MubasherPaths) -> dict[str, int]:
    out: dict[str, int] = {}
    with closing(_open_sqlite_ro(paths.intraday_db)) as conn:
        for table_name, symbol in _cached_list_symbol_tables(paths.intraday_db.as_posix()):
            q = f"SELECT MAX(TMIN) FROM {_quoted_identifier(table_name)}"
            max_tmin = conn.execute(q).fetchone()[0]
            if max_tmin is None:
                continue
            try:
                out[symbol] = int(max_tmin)
            except (TypeError, ValueError):
                continue
    return out


def get_trade_db_file(paths: MubasherPaths, trade_date: str) -> Path:
    return paths.historical_trade_dir / f"{trade_date}.db"


def list_trade_dates(paths: MubasherPaths) -> list[str]:
    if not paths.historical_trade_dir.exists():
        return []
    out: list[str] = []
    for db_file in sorted(paths.historical_trade_dir.glob("*.db")):
        d = db_file.stem
        if re.fullmatch(r"\d{8}", d):
            out.append(d)
    return out


def load_trade_ticks_dataframe(paths: MubasherPaths, trade_date: str, symbol: str | None = None) -> pd.DataFrame:
    db_file = get_trade_db_file(paths, trade_date)
    if not db_file.exists():
        return pd.DataFrame(
            columns=[
                "timestamp",
                "timestamp_utc",
                "trade_date",
                "sequence",
                "symbol",
                "price",
                "quantity",
                "vwap",
                "net_change",
                "pct_change",
                "market_id",
                "transaction_type",
                "instrument_type",
                "is_odd_lot",
            ]
        )

    with closing(_open_sqlite_ro(db_file)) as conn:
        q = (
            "SELECT SEQUENCE, SYMBOL, TRADETIME, TRADEPRICE, TRADEQUANTITY, "
            "VWAP, NETCHANGE, PERCENTCHANGE, MARKETID, TRANSACTIONTYPE, INSTRUMENTTYPE, ISODDLOTTRADE "
            "FROM TRADES ORDER BY SEQUENCE"
        )
        df = pd.read_sql_query(q, conn)

    if df.empty:
        return pd.DataFrame()

    df = df.rename(
        columns={
            "SEQUENCE": "sequence",
            "SYMBOL": "symbol",
            "TRADETIME": "trade_time",
            "TRADEPRICE": "price",
            "TRADEQUANTITY": "quantity",
            "VWAP": "vwap",
            "NETCHANGE": "net_change",
            "PERCENTCHANGE": "pct_change",
            "MARKETID": "market_id",
            "TRANSACTIONTYPE": "transaction_type",
            "INSTRUMENTTYPE": "instrument_type",
            "ISODDLOTTRADE": "is_odd_lot",
        }
    )

    df["symbol"] = df["symbol"].astype(str).str.upper().str.strip()
    if symbol:
        target = symbol.upper().strip()
        df = df[df["symbol"] == target]
        if df.empty:
            return pd.DataFrame()

    time_text = df["trade_time"].astype(str).str.zfill(6)
    ts_utc = pd.to_datetime(trade_date + time_text, format="%Y%m%d%H%M%S", errors="coerce", utc=True)
    ts_local = ts_utc.dt.tz_convert(_cairo_tz()).dt.tz_localize(None)
    df["timestamp_utc"] = ts_utc
    df["timestamp"] = ts_local
    df["trade_date"] = trade_date

    for col in ("sequence", "quantity", "market_id"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ("price", "vwap", "net_change", "pct_change"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["timestamp", "sequence", "symbol", "price", "quantity"])
    df = df.sort_values(["symbol", "sequence"])
    df = df.drop_duplicates(subset=["symbol", "sequence"], keep="last")
    return df[
        [
            "timestamp",
            "timestamp_utc",
            "trade_date",
            "sequence",
            "symbol",
            "price",
            "quantity",
            "vwap",
            "net_change",
            "pct_change",
            "market_id",
            "transaction_type",
            "instrument_type",
            "is_odd_lot",
        ]
    ].reset_index(drop=True)
