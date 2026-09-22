from core.settings import settings
from core.exclusions import get_all_exclusions

from pathlib import Path

import pandas as pd

from core import Heimdall
from core import TimeUtils
from data_engine.mubasher_sqlite_source import build_paths, list_trade_dates, load_trade_ticks_dataframe
from data_engine.ticker_filters import is_supported_ticker


def _today_yyyymmdd() -> str:
    return TimeUtils.today().strftime("%Y%m%d")


def _target_dir(trade_date: str) -> Path:
    realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
    from core.settings import settings
    out = Path(settings.DATA_ROOT) / realm / "ticks" / trade_date
    out.mkdir(parents=True, exist_ok=True)
    return out


def _get_existing_max_sequence(path: Path) -> int:
    if not path.exists():
        return -1
    try:
        df = pd.read_parquet(path)
    except Exception:
        return -1
    if df is None or df.empty or "sequence" not in df.columns:
        return -1
    try:
        return int(pd.to_numeric(df["sequence"], errors="coerce").max())
    except Exception:
        return -1


def _save_symbol_ticks(path: Path, df_new: pd.DataFrame) -> tuple[int, int]:
    """
    Returns (rows_before, rows_after).
    """
    existing_rows = 0
    if path.exists():
        try:
            existing = pd.read_parquet(path)
            existing_rows = len(existing)
        except Exception:
            existing = pd.DataFrame(columns=df_new.columns)
        combined = pd.concat([existing, df_new], ignore_index=True)
    else:
        combined = df_new.copy()

    combined = combined.drop_duplicates(subset=["sequence"], keep="last")
    combined = combined.sort_values("sequence")
    rows_before = existing_rows
    rows_after = len(combined)
    combined.to_parquet(path, compression="snappy", index=False)
    return rows_before, rows_after


def ingest_ticks(trade_date: str | None = None) -> dict:
    """
    Ingests tick-by-tick trades from Mubasher HistoricalTrade YYYYMMDD.db into parquet.
    Stores per symbol in: data/{realm}/ticks/{trade_date}/{ticker}.parquet
    """
    requested_trade_date = trade_date
    trade_date = trade_date or _today_yyyymmdd()
    try:
        paths = build_paths(
            Path(settings.MUBASHER_ROOT_DIR),
            user_id=(settings.MUBASHER_USER_ID or None),
        )
    except Exception as e:
        return {
            "status": "error",
            "trade_date": trade_date,
            "message": f"Mubasher source unavailable: {e}",
            "symbols_touched": 0,
            "rows_added": 0,
        }

    available_dates = list_trade_dates(paths)
    fallback_used = False
    if trade_date not in available_dates:
        if requested_trade_date:
            return {
                "status": "empty",
                "trade_date": trade_date,
                "message": f"No tick DB found for requested date {trade_date}.",
                "symbols_touched": 0,
                "rows_added": 0,
            }
        older_or_equal = [d for d in available_dates if d <= trade_date]
        if older_or_equal:
            trade_date = older_or_equal[-1]
            fallback_used = True

    ticks_df = load_trade_ticks_dataframe(paths, trade_date=trade_date)
    if ticks_df is None or ticks_df.empty:
        return {
            "status": "empty",
            "trade_date": trade_date,
            "message": "No ticks found for trade date.",
            "symbols_touched": 0,
            "rows_added": 0,
        }

    excluded = get_all_exclusions()
    if excluded:
        ticks_df = ticks_df[~ticks_df["symbol"].isin(excluded)]
    ticks_df = ticks_df[ticks_df["symbol"].map(is_supported_ticker)]
    if ticks_df.empty:
        return {
            "status": "empty",
            "trade_date": trade_date,
            "message": "All ticks filtered by exclusions.",
            "symbols_touched": 0,
            "rows_added": 0,
        }

    out_dir = _target_dir(trade_date)
    symbols_touched = 0
    rows_added = 0

    for symbol, group in ticks_df.groupby("symbol", sort=True):
        out_file = out_dir / f"{symbol}.parquet"
        max_seq = _get_existing_max_sequence(out_file)
        delta = group[group["sequence"] > max_seq] if max_seq >= 0 else group
        if delta.empty:
            continue

        before_rows, after_rows = _save_symbol_ticks(out_file, delta)
        symbols_touched += 1
        rows_added += max(0, after_rows - before_rows)

    return {
        "status": "ok",
        "trade_date": trade_date,
        "fallback_used": fallback_used,
        "symbols_touched": symbols_touched,
        "rows_added": int(rows_added),
        "output_dir": str(out_dir),
    }


if __name__ == "__main__":
    print(ingest_ticks())
