import os
import time
from pathlib import Path
from threading import Lock

import duckdb
import pandas as pd

from data_engine import intraday_store

from core.settings import settings
DATA_ROOT = Path(settings.DATA_ROOT)

_DB = duckdb.connect(database=':memory:')
_CACHE_LOCK = Lock()
_DB_LOCK = Lock() # Protects duckdb connection from concurrent thread access
_QUERY_CACHE: dict[str, tuple[tuple, pd.DataFrame]] = {}
_LIST_CACHE: dict[str, tuple[float, list[str]]] = {}


def clear_data_cache() -> None:
    with _CACHE_LOCK:
        _QUERY_CACHE.clear()
        _LIST_CACHE.clear()


def _duckdb_execute(query: str):
    """Preserve the injectable _DB seam while keeping cursor-based isolation for real DuckDB connections."""
    connection_type = getattr(duckdb, "DuckDBPyConnection", None)
    if connection_type is not None and isinstance(_DB, connection_type):
        return _DB.cursor().execute(query)
    return _DB.execute(query)


def _normalize_df_index(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if not isinstance(df.index, pd.DatetimeIndex):
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"]).set_index("timestamp")
        else:
            return pd.DataFrame()
    return df[~df.index.duplicated(keep="last")].sort_index()


def _get_history_stamp(realm: str, timeframe: str, ticker: str) -> tuple:
    """Builds a fast cache stamp based on mtime of the flat file & latest partition."""
    flat_path = DATA_ROOT / realm / timeframe / f"{ticker}.parquet"
    part_root = DATA_ROOT / realm / timeframe / "by_date"
    
    flat_stamp = None
    if flat_path.exists():
        stat = flat_path.stat()
        flat_stamp = (int(stat.st_mtime_ns), int(stat.st_size))
        
    part_stamp = None
    if part_root.exists():
        # Get latest day dir to check newest partition changes rapidly
        try:
            day_dirs = sorted([d.name for d in part_root.iterdir() if d.is_dir()], reverse=True)
            for d in day_dirs:
                p_file = part_root / d / f"{ticker}.parquet"
                if p_file.exists():
                    stat = p_file.stat()
                    part_stamp = (d, int(stat.st_mtime_ns), int(stat.st_size))
                    break
        except Exception:
            pass
            
    return (flat_stamp, part_stamp)


def _query_history_with_duckdb(realm: str, timeframe: str, ticker: str, limit: int | None = None) -> pd.DataFrame:
    """Executes a DuckDB query over Parquet files, wrapped in an mtime stat cache."""
    cache_key = f"{realm}:{timeframe}:{ticker}"
    
    # 1. Fast Cache Check (only for unlimited reads to keep it simple & memory bound)
    stamp = _get_history_stamp(realm, timeframe, ticker)
    if not stamp[0] and not stamp[1]: # No files exist
        return pd.DataFrame()
        
    if limit is None:
        with _CACHE_LOCK:
            cached = _QUERY_CACHE.get(cache_key)
            if cached and cached[0] == stamp:
                return cached[1]
                
    # 2. Build DuckDB Query
    flat_path = DATA_ROOT / realm / timeframe / f"{ticker}.parquet"
    part_path = DATA_ROOT / realm / timeframe / "by_date" / "*" / f"{ticker}.parquet"
    
    query_parts = []
    if stamp[0]:
        query_parts.append(f"SELECT *, 0 AS __horus_source_rank FROM read_parquet('{flat_path.as_posix()}')")
    if stamp[1]:
        query_parts.append(f"SELECT *, 1 AS __horus_source_rank FROM read_parquet('{part_path.as_posix()}', union_by_name=true)")
        
    union_query = "\n".join(query_parts) if len(query_parts) == 1 else "\nUNION ALL BY NAME\n".join(query_parts)
    
    # 2.1 Wait/Retry loop to handle Windows "File in use" during sync
    df_schema = None
    max_retries = 3
    for attempt in range(max_retries):
        try:
            df_schema = _duckdb_execute(f"SELECT * FROM ({union_query}) LIMIT 0").df()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1) # Wait for sync to release file
                continue
            print(f"[Error: DuckDB] Schema read failed for {ticker}: {e}")
            return pd.DataFrame()
        
    time_cols = [c for c in df_schema.columns if c.lower() in ['timestamp', 'time', 'date', '__index_level_0__']]
    if not time_cols:
        return pd.DataFrame()

    time_cols_sql = ", ".join(f'"{c}"' for c in time_cols)
    unified_time_expr = f"COALESCE({time_cols_sql})" if len(time_cols) > 1 else f'"{time_cols[0]}"'
    
    data_cols = [c for c in df_schema.columns if c not in time_cols and c != "__horus_source_rank"]
    select_expr = ", ".join(f'"{c}"' for c in data_cols)
    if select_expr:
        select_expr += f", {unified_time_expr} AS timestamp"
    else:
        select_expr = f"{unified_time_expr} AS timestamp"
    source_rank_expr = '"__horus_source_rank"' if "__horus_source_rank" in df_schema.columns else "0"

    limit_clause = f" LIMIT {limit}" if limit and limit > 0 else ""
    
    sql = f"""
        SELECT * FROM (
            SELECT {select_expr}, {source_rank_expr} AS __horus_source_rank FROM (
                {union_query}
            )
        )
        QUALIFY ROW_NUMBER() OVER (PARTITION BY "timestamp" ORDER BY "__horus_source_rank" DESC, "timestamp" DESC) = 1
        ORDER BY "timestamp" DESC
        {limit_clause}
    """
    
    try:
        df = None
        for attempt in range(max_retries):
            try:
                # Preserve cursor isolation for the real connection, but respect wrapped test seams.
                df = _duckdb_execute(sql).df()
                break
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                raise

        if df is None or df.empty:
            return pd.DataFrame()
            
        # Normalize column names for downstream Pandas logic
        rename_map = {c: c.lower() for c in df.columns}
        df.rename(columns=rename_map, inplace=True)
        if "__horus_source_rank" in df.columns:
            df.drop(columns=["__horus_source_rank"], inplace=True)
        
        # Limit pushdown required DESC order, so reverse to ASC for final Pandas return
        df.sort_values("timestamp", ascending=True, inplace=True)
        out = _normalize_df_index(df)
        
        # 3. Cache the normalized unlimited read
        if limit is None:
            with _CACHE_LOCK:
                _QUERY_CACHE[cache_key] = (stamp, out)
        return out
        
    except Exception as e:
        print(f"[Error: DuckDB] Failed to load {ticker}: {e}")
        return pd.DataFrame()

def get_data(
    ticker: str,
    timeframe: str = "intraday",
    realm: str = "EGX",
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Loads market data for a ticker from the Partitioned Parquet Data Lake.
    
    Args:
        ticker: The stock ticker (e.g., "COMI").
        timeframe: "intraday" (1min) or "history" (daily).
        realm: The market realm (e.g., "EGX", "SAUDI").
        
    Returns:
        pd.DataFrame: DataFrame with DatetimeIndex and columns [open, high, low, close, volume].
    """
    try:
        tf = str(timeframe or "intraday").lower()

        if tf == "intraday":
            df_store = intraday_store.get_intraday_data(ticker, realm=realm, limit=limit)
            if df_store is not None and not df_store.empty:
                return df_store

        df = _query_history_with_duckdb(realm=realm, timeframe=tf, ticker=ticker, limit=limit)

        # Warm intraday store from parquet when store is empty.
        if tf == "intraday" and df is not None and not df.empty:
            intraday_store.upsert_intraday(ticker, df, realm=realm)

        return df
        
    except Exception as e:
        print(f"[Error] Failed to load {ticker}: {e}")
        return pd.DataFrame()

def get_bulk_data(
    tickers: list[str],
    timeframe: str = "history",
    realm: str = "EGX",
    limit: int | None = None
) -> pd.DataFrame:
    """
    Loads multiple tickers efficiently in a single DuckDB query.
    Returns a unified DataFrame with a 'ticker' column.
    """
    if not tickers:
        return pd.DataFrame()
    
    tf = str(timeframe or "history").lower()
    requested_tickers = sorted({str(t).upper() for t in tickers if str(t or "").strip()})
    if not requested_tickers:
        return pd.DataFrame()

    # History Flat Paths + by_date partitions (M4)
    valid_paths = []
    # 1. Flat files
    for t in requested_tickers:
        p = DATA_ROOT / realm / tf / f"{t}.parquet"
        if p.exists():
            valid_paths.append(str(p.as_posix()))
            
    # 2. Partitioned files, scoped to the requested tickers.
    # The previous broad by_date/*/*.parquet glob made small bulk requests scan
    # the entire market partition set.
    by_date_dir = DATA_ROOT / realm / tf / "by_date"
    if by_date_dir.exists():
        partition_globs: set[str] = set()
        day_dirs = [d for d in by_date_dir.iterdir() if d.is_dir()]
        for ticker in requested_tickers:
            filename = f"{ticker}.parquet"
            if any((day_dir / filename).exists() for day_dir in day_dirs):
                partition_globs.add(str((by_date_dir / "*" / filename).as_posix()))
        valid_paths.extend(sorted(partition_globs))

    if not valid_paths:
        return pd.DataFrame()
        
    # We use 'filename=true' to distinguish tickers in the unified DF
    # Note: tickers like 'COMI' will have filename '.../COMI.parquet'
    sql = rf"""
        SELECT 
            *,
            UPPER(regexp_extract(filename, '([^/\\]+)\.parquet$', 1)) as ticker,
            CASE
                WHEN regexp_matches(filename, '(^|[/\\])by_date([/\\])') THEN 1
                ELSE 0
            END AS __horus_source_rank
        FROM read_parquet({valid_paths}, filename=true)
    """
    
    if limit:
        # If limit is requested, we need a window function per ticker to be accurate
        sql = f"""
            SELECT * FROM (
                SELECT *, 
                ROW_NUMBER() OVER (PARTITION BY ticker ORDER BY timestamp DESC, __horus_source_rank DESC) as row_num
                FROM ({sql})
            ) WHERE row_num <= {limit}
        """

    sql = f"""
        SELECT * EXCLUDE (__horus_source_rank) FROM (
            SELECT *,
            ROW_NUMBER() OVER (
                PARTITION BY ticker, timestamp
                ORDER BY __horus_source_rank DESC
            ) AS __horus_dedupe_rank
            FROM ({sql})
        )
        WHERE __horus_dedupe_rank = 1
    """

    try:
        with _DB_LOCK:
            df = _DB.execute(sql).df()
        if df is None or df.empty:
            return pd.DataFrame()
            
        # Standardize columns
        df.rename(columns={c: c.lower() for c in df.columns}, inplace=True)
        if "__horus_dedupe_rank" in df.columns:
            df.drop(columns=["__horus_dedupe_rank"], inplace=True)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    except Exception as e:
        print(f"[Error: DuckDB Bulk] {e}")
        return pd.DataFrame()

def list_tickers(timeframe: str = "intraday", realm: str = "EGX") -> list:
    """Returns a list of available tickers in the partitioned data lake."""
    tf = str(timeframe or "intraday").lower()
    cache_key = f"{realm}:{tf}"
    cache_ttl_sec = max(1, int(os.getenv("LIST_TICKERS_CACHE_TTL_SEC", "60")))
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _LIST_CACHE.get(cache_key)
        if cached and (now - cached[0]) <= cache_ttl_sec:
            return list(cached[1])

    items: set[str] = set()

    if tf == "intraday":
        try:
            items.update(intraday_store.list_tickers(realm=realm))
        except Exception:
            pass

    path = DATA_ROOT / realm / tf
    if path.exists():
        items.update([f.stem for f in path.glob("*.parquet")])
    partition_root = path / "by_date"
    if partition_root.exists():
        lookback = max(1, int(os.getenv("LIST_TICKERS_PARTITION_LOOKBACK", "14")))
        day_dirs = sorted(
            [d for d in partition_root.iterdir() if d.is_dir()],
            key=lambda p: p.name,
            reverse=True,
        )
        scan_dirs = day_dirs[:lookback]
        for day_dir in scan_dirs:
            items.update([f.stem for f in day_dir.glob("*.parquet")])
        if not items and day_dirs:
            # Cold fallback when recent windows are empty/corrupted.
            items.update([f.stem for f in partition_root.glob("*/*.parquet")])

    out = sorted(items)
    if out:
        with _CACHE_LOCK:
            _LIST_CACHE[cache_key] = (now, out)
    return out
