from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from data_engine.observability import emit_event, incr_counter

from core.settings import settings
DATA_ROOT = Path(settings.DATA_ROOT)


def _safe_to_datetime(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    return pd.to_datetime(series, errors="coerce")


def _safe_to_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series
    return pd.to_numeric(series, errors="coerce")


def _append_dlq(rejected: pd.DataFrame, ticker: str, realm: str, stream: str) -> Path | None:
    if rejected is None or rejected.empty:
        return None

    target_dir = DATA_ROOT / realm / "dlq" / stream
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{ticker}.parquet"

    if file_path.exists():
        try:
            existing = pd.read_parquet(file_path)
            rejected = pd.concat([existing, rejected], ignore_index=True)
        except Exception:
            pass

    rejected = rejected.drop_duplicates(keep="last")
    rejected.to_parquet(file_path, compression="snappy", index=False)
    return file_path


def _rejection_reason_counts(rejected: pd.DataFrame) -> dict[str, int]:
    if rejected is None or rejected.empty or "_dlq_reason" not in rejected.columns:
        return {}

    counts: dict[str, int] = {}
    for raw in rejected["_dlq_reason"].dropna().astype(str):
        for reason in [part.strip() for part in raw.split("|") if part.strip()]:
            counts[reason] = counts.get(reason, 0) + 1
    return counts


def _legacy_zero_price_source_note(
    rejected: pd.DataFrame,
    *,
    stream: str,
    rejection_reason_counts: dict[str, int],
) -> str | None:
    if stream != "history" or rejected is None or rejected.empty:
        return None

    if set(rejection_reason_counts) != {"invalid_price"}:
        return None

    price_cols = [col for col in ("open", "high", "low", "close") if col in rejected.columns]
    if not price_cols:
        return None

    numeric_prices = rejected[price_cols].apply(pd.to_numeric, errors="coerce")
    if not numeric_prices.eq(0).any(axis=None):
        return None

    return "Legacy vendor source contains zero-price OHLC rows; quarantined as expected."


def validate_ohlcv_and_quarantine(
    ticker: str,
    df: pd.DataFrame,
    *,
    realm: str = "EGX",
    stream: str = "intraday",
) -> tuple[pd.DataFrame, dict]:
    """
    Validate OHLCV rows, return cleaned rows, and quarantine rejected rows to DLQ parquet.
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]), {
            "input_rows": 0,
            "valid_rows": 0,
            "rejected_rows": 0,
            "dlq_path": None,
            "rejection_reason_counts": {},
        }

    work = df.copy()
    # Normalize columns carefully: lowercase AND strip whitespace.
    work.columns = [str(c).lower().strip().replace("<", "").replace(">", "") for c in work.columns]

    if "timestamp" not in work.columns and isinstance(work.index, pd.DatetimeIndex):
        work = work.reset_index().rename(columns={"index": "timestamp"})
    if "timestamp" not in work.columns:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"]), {
            "input_rows": int(len(df)),
            "valid_rows": 0,
            "rejected_rows": int(len(df)),
            "dlq_path": None,
            "rejection_reason_counts": {"missing_timestamp_column": int(len(df))},
        }

    price_cols = ["open", "high", "low", "close"]
    value_cols = [*price_cols, "volume"]

    for col in value_cols:
        if col not in work.columns:
            work[col] = pd.NA

    work["timestamp"] = _safe_to_datetime(work["timestamp"])
    for col in value_cols:
        work[col] = _safe_to_numeric(work[col])

    # Repair OHLC violations by Expanding High/Low range.
    # We do this BEFORE validation to save rows with minor floating point or feed errors.
    high_components = work[["high", "open", "close"]]
    low_components = work[["low", "open", "close"]]
    work["high"] = high_components.max(axis=1, skipna=True)
    work["low"] = low_components.min(axis=1, skipna=True)
    work["volume"] = work["volume"].fillna(0.0)

    valid_ts = work["timestamp"].notna()
    price_frame = work[price_cols]
    # Check that all core prices are valid numbers
    is_numeric_price = price_frame.notna().all(axis=1)
    # Check for unrealistic prices (e.g. 0 or negative)
    positive_prices = (price_frame > 0).all(axis=1)
    
    valid_prices = is_numeric_price & positive_prices
    
    # Check bounds with a tiny epsilon to handle float precision jitter
    eps = 1e-7
    valid_hilo = work["high"] >= (work["low"] - eps)
    open_close = work[["open", "close"]]
    open_close_max = open_close.max(axis=1)
    open_close_min = open_close.min(axis=1)
    valid_bounds = (work["high"] >= (open_close_max - eps)) & (work["low"] <= (open_close_min + eps))
    valid_volume = work["volume"] >= 0

    # Reject bars in the future (> now + 2 days for timezone/buffer)
    now_ts = pd.Timestamp.now()
    cutoff_ts = now_ts.replace(hour=23, minute=59, second=59) + pd.Timedelta(days=2)
    # Ensure timestamps are naive for comparison if now_ts is naive.
    try:
        timestamp_for_future = work["timestamp"]
        if getattr(timestamp_for_future.dt, "tz", None) is not None:
            timestamp_for_future = timestamp_for_future.dt.tz_localize(None)
    except Exception:
        timestamp_for_future = pd.to_datetime(work["timestamp"], errors="coerce").dt.tz_localize(None)
    valid_future = timestamp_for_future <= cutoff_ts.tz_localize(None)

    valid_mask = valid_ts & valid_prices & valid_hilo & valid_bounds & valid_volume & valid_future

    if valid_mask.all():
        rejected = pd.DataFrame()
        cleaned = work[["timestamp", "open", "high", "low", "close", "volume"]].copy()
    else:
        reasons = pd.Series("", index=work.index, dtype="object")
        reasons = reasons.mask(~valid_ts, reasons + "|invalid_timestamp")
        reasons = reasons.mask(~valid_future, reasons + "|future_timestamp")
        reasons = reasons.mask(~valid_prices, reasons + "|invalid_price")
        reasons = reasons.mask(~valid_hilo, reasons + "|high_lt_low")
        reasons = reasons.mask(~valid_bounds, reasons + "|ohlc_out_of_bounds")
        reasons = reasons.mask(~valid_volume, reasons + "|negative_volume")

        rejected = work.loc[~valid_mask].copy()
        if not rejected.empty:
            rejected["_dlq_reason"] = reasons.loc[~valid_mask].str.lstrip("|")
            rejected["_rejected_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            rejected["_ticker"] = str(ticker).upper().strip()
            rejected["_stream"] = stream

        cleaned = work.loc[valid_mask, ["timestamp", "open", "high", "low", "close", "volume"]].copy()

    cleaned = cleaned.sort_values("timestamp")
    cleaned = cleaned.drop_duplicates(subset=["timestamp"], keep="last")

    input_rows = int(len(work))
    valid_rows = int(len(cleaned))
    rejected_rows = int(len(rejected))
    rejection_reason_counts = _rejection_reason_counts(rejected)
    incr_counter("dq.input_rows.total", input_rows)
    incr_counter(f"dq.input_rows.{stream}", input_rows)
    incr_counter("dq.valid_rows.total", valid_rows)
    incr_counter(f"dq.valid_rows.{stream}", valid_rows)
    if rejected_rows > 0:
        incr_counter("dq.rejected_rows.total", rejected_rows)
        incr_counter(f"dq.rejected_rows.{stream}", rejected_rows)

    dlq_path = _append_dlq(rejected, ticker=str(ticker).upper().strip(), realm=realm, stream=stream) if rejected_rows > 0 else None
    
    # Noise reduction: only log if rejections are significant (e.g. > 5 rows or > 1% of batch)
    input_rows = len(df)
    rejected_ratio = rejected_rows / input_rows if input_rows > 0 else 0
    source_note = _legacy_zero_price_source_note(
        rejected,
        stream=stream,
        rejection_reason_counts=rejection_reason_counts,
    )
    
    if rejected_rows > 5 or (rejected_rows > 0 and rejected_ratio > 0.01):
        emit_event(
            "pipeline.data_quality.rejected_rows",
            level="info",
            ticker=str(ticker).upper().strip(),
            stream=stream,
            realm=realm,
            rejected_rows=rejected_rows,
            input_rows=input_rows,
            dlq_path=str(dlq_path) if dlq_path else None,
            rejection_reason_counts=rejection_reason_counts,
            source_note=source_note,
        )
    return cleaned.reset_index(drop=True), {
        "input_rows": input_rows,
        "valid_rows": valid_rows,
        "rejected_rows": rejected_rows,
        "dlq_path": str(dlq_path) if dlq_path else None,
        "rejection_reason_counts": rejection_reason_counts,
    }
