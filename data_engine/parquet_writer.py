import pandas as pd
from pathlib import Path

from data_engine.data_quality import validate_ohlcv_and_quarantine
from data_engine.history_watermarks import (
    load_index as load_history_watermark_index,
    save_index as save_history_watermark_index,
    update_flat_date as update_history_flat_date,
)

from core.settings import settings
DATA_ROOT = Path(settings.DATA_ROOT)


def _has_existing_partitions(partition_root: Path, ticker: str) -> bool:
    if not partition_root.exists():
        return False
    try:
        return any(partition_root.glob(f"*/{ticker}.parquet"))
    except Exception:
        return False


def _enforce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].astype("float64")
    return df


def _drop_future_rows(df: pd.DataFrame) -> pd.DataFrame:
    now_ts = pd.Timestamp.now().tz_localize(None)
    cutoff_ts = now_ts.replace(hour=23, minute=59, second=59) + pd.Timedelta(days=2)
    return df[df.index <= cutoff_ts]


def _ensure_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.index, pd.DatetimeIndex):
        return df
    if "timestamp" not in df.columns:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    return df.set_index("timestamp")


def _merge_and_write(file_path: Path, df: pd.DataFrame) -> tuple[int, pd.Timestamp | None]:
    current = _ensure_datetime_index(df.copy())
    if file_path.exists():
        try:
            existing_df = _ensure_datetime_index(pd.read_parquet(file_path))
            current = pd.concat([existing_df, current])
        except Exception as e:
            print(f"Warning: Could not read existing file {file_path}. Overwriting. Error: {e}")

    if not isinstance(current.index, pd.DatetimeIndex):
        raise ValueError("DataFrame must have a DatetimeIndex or a 'timestamp' column.")

    current = current[~current.index.duplicated(keep="last")]
    current.sort_index(inplace=True)
    current = _drop_future_rows(current)
    current = _enforce_numeric_columns(current)

    file_path.parent.mkdir(parents=True, exist_ok=True)
    current.to_parquet(file_path, compression="snappy")
    max_ts = current.index.max() if not current.empty else None
    return len(current), max_ts


def _write_history_partitions(ticker: str, df: pd.DataFrame, partition_root: Path) -> tuple[int, int]:
    rows_written = 0
    partitions_written = 0
    for day, day_df in df.groupby(df.index.normalize(), sort=True):
        if day_df.empty:
            continue
        day_text = pd.Timestamp(day).date().isoformat()
        file_path = partition_root / day_text / f"{ticker}.parquet"
        partition_rows, _ = _merge_and_write(file_path, day_df)
        rows_written += partition_rows
        partitions_written += 1
    return rows_written, partitions_written


def _record_history_flat_watermark(ticker: str, file_path: Path, max_ts) -> None:
    if max_ts is None or pd.isna(max_ts):
        return
    try:
        watermark_index = load_history_watermark_index(file_path.parent)
        changed = update_history_flat_date(
            watermark_index,
            ticker,
            file_path,
            pd.to_datetime(max_ts).date(),
        )
        if changed:
            save_history_watermark_index(file_path.parent, watermark_index)
    except Exception:
        pass


def save_stream(ticker: str, df: pd.DataFrame, folder: str = "intraday", realm: str = "EGX"):
    """
    Saves a dataframe to a Partitioned Parquet file in the Data Lake.
    
    Args:
        ticker: The stock ticker (e.g., "COMI").
        df: The pandas DataFrame containing the data. 
            MUST have a 'timestamp' column or index.
        folder: Subfolder in the data lake (e.g., "intraday" or "history").
        realm: The market realm subfolder (e.g., "EGX", "SAUDI").
    """
    # 1. Ensure Directory Exists (data/{realm}/{folder}/)
    target_dir = DATA_ROOT / realm / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # New layout: data/{realm}/{folder}/by_date/YYYY-MM-DD/{ticker}.parquet
    partition_root = target_dir / "by_date"
    
    # 2. Standardize Columns
    # Force column names to be lowercase
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure timestamp is datetime and set as index
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    
    if not isinstance(df.index, pd.DatetimeIndex):
         raise ValueError("DataFrame must have a DatetimeIndex or a 'timestamp' column.")

    # 2.1 Validate row-level data quality and quarantine bad rows to DLQ
    validated_df, dq = validate_ohlcv_and_quarantine(
        ticker=ticker,
        df=df.reset_index(),
        realm=realm,
        stream=folder,
    )
    if validated_df.empty:
        print(f"[Warn] No valid rows for {ticker} in {folder}; rejected={dq.get('rejected_rows', 0)}")
        return
    df = validated_df.set_index("timestamp")

    ticker = str(ticker).upper().strip()

    # 3. Initial full history loads stay flat. Incremental history updates use
    # small date partitions so daily sync avoids rewriting years of data.
    file_path = target_dir / f"{ticker}.parquet"
    use_partitions = (
        folder == "history"
        and (file_path.exists() or _has_existing_partitions(partition_root, ticker))
    )

    if use_partitions:
        rows_written, partitions_written = _write_history_partitions(ticker, df, partition_root)
        print(
            f"[Success] Saved {rows_written} total rows for {ticker} "
            f"across {partitions_written} {folder} partition(s)"
        )
        return

    rows_written, max_ts = _merge_and_write(file_path, df)
    if folder == "history":
        _record_history_flat_watermark(ticker, file_path, max_ts)
    print(
        f"[Success] Saved {rows_written} total rows for {ticker} "
        f"to {file_path}"
    )
