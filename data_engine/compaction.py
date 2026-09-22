from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_engine.history_watermarks import (
    load_index as load_history_watermark_index,
    save_index as save_history_watermark_index,
    update_flat_date as update_history_flat_date,
)

from core.settings import settings
DATA_ROOT = Path(settings.DATA_ROOT)


def _partition_root(realm: str, folder: str) -> Path:
    return DATA_ROOT / realm / folder / "by_date"


def _legacy_file(realm: str, folder: str, ticker: str) -> Path:
    return DATA_ROOT / realm / folder / f"{ticker}.parquet"


def _read_all_partitions(realm: str, folder: str, ticker: str) -> pd.DataFrame:
    root = _partition_root(realm, folder)
    paths: list[Path] = []
    legacy_path = _legacy_file(realm, folder, ticker)
    if legacy_path.exists():
        paths.append(legacy_path)
    if root.exists():
        paths.extend(sorted(root.glob(f"*/{ticker}.parquet")))
    if not paths:
        return pd.DataFrame()
    frames = []
    for path in paths:
        try:
            frames.append(pd.read_parquet(path))
        except Exception:
            continue
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames)
    if not isinstance(out.index, pd.DatetimeIndex):
        if "timestamp" in out.columns:
            out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce")
            out = out.dropna(subset=["timestamp"]).set_index("timestamp")
        else:
            return pd.DataFrame()
    out = out[~out.index.duplicated(keep="last")]
    return out.sort_index()


def compact_symbol(realm: str, folder: str, ticker: str) -> bool:
    df = _read_all_partitions(realm, folder, ticker)
    if df is None or df.empty:
        return False
    path = _legacy_file(realm, folder, ticker)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, compression="snappy")
    if folder == "history" and isinstance(df.index, pd.DatetimeIndex):
        try:
            watermark_index = load_history_watermark_index(path.parent)
            changed = update_history_flat_date(
                watermark_index,
                ticker,
                path,
                pd.to_datetime(df.index.max()).date(),
            )
            if changed:
                save_history_watermark_index(path.parent, watermark_index)
        except Exception:
            pass
    return True


def compact_folder(realm: str, folder: str, max_tickers: int = 500) -> dict:
    root = _partition_root(realm, folder)
    legacy_root = DATA_ROOT / realm / folder
    if not root.exists() and not legacy_root.exists():
        return {"folder": folder, "compacted": 0, "scanned": 0}

    tickers = set()
    if legacy_root.exists():
        for p in legacy_root.glob("*.parquet"):
            tickers.add(p.stem.upper())
    if root.exists():
        for p in root.glob("*/*.parquet"):
            tickers.add(p.stem.upper())
    ordered = sorted(tickers)[: max(1, int(max_tickers))]

    compacted = 0
    for ticker in ordered:
        if compact_symbol(realm, folder, ticker):
            compacted += 1

    return {
        "folder": folder,
        "compacted": compacted,
        "scanned": len(ordered),
    }
