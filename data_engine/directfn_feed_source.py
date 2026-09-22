from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

import pandas as pd


@dataclass
class DirectFNLayout:
    history_root: Path
    intraday_root: Path
    symbol_map: Path


def detect_layout(history_dir: Path, intraday_dir: Path) -> Optional[DirectFNLayout]:
    """
    Best-effort layout discovery for DirectFN Pro 10+ feed.
    Expects:
    - history_dir: .../metafiles/marketdata_h2/history/case
    - intraday_dir: .../metafiles/marketdata_h2/ohlc/case
    - symbol_map: .../metafiles/marketdata_h2/symbolmapping.csv
    """
    history_dir = history_dir.expanduser()
    intraday_dir = intraday_dir.expanduser()
    if not history_dir.exists() or not intraday_dir.exists():
        return None

    # symbolmapping.csv can live at multiple levels depending on installer
    candidates = [
        history_dir.parent.parent / "symbolmapping.csv",  # .../marketdata_h2/symbolmapping.csv
        history_dir.parent / "symbolmapping.csv",         # .../history/symbolmapping.csv
        history_dir / "symbolmapping.csv",                # .../history/case/symbolmapping.csv
        intraday_dir / "symbolmapping.csv",               # .../ohlc/case/symbolmapping.csv
    ]
    symbol_map = next((p for p in candidates if p.exists()), None)
    if symbol_map is None:
        return None

    return DirectFNLayout(history_root=history_dir, intraday_root=intraday_dir, symbol_map=symbol_map)


def load_symbol_map(symbol_map_path: Path) -> Dict[str, str]:
    """
    Returns mapping of feed file base name -> ticker symbol (upper).
    File format: FILE_NAME|SYMBOL
    """
    mapping: Dict[str, str] = {}
    candidates = [symbol_map_path]
    if symbol_map_path.parent.name.lower() == "case" and symbol_map_path.parent.parent.name.lower() in {"history", "ohlc"}:
        root = symbol_map_path.parent.parent.parent
        for folder in ("history", "ohlc"):
            candidate = root / folder / "case" / "symbolmapping.csv"
            if candidate.exists() and candidate not in candidates:
                candidates.append(candidate)

    for path in candidates:
        try:
            df = pd.read_csv(path, sep="|")
            if "FILE_NAME" in df.columns and "SYMBOL" in df.columns:
                for _, row in df.iterrows():
                    fname = str(row["FILE_NAME"]).strip()
                    sym = str(row["SYMBOL"]).strip().upper()
                    if fname and sym and fname not in mapping:
                        mapping[fname] = sym
        except Exception:
            continue
    return mapping


def iter_history_files(layout: DirectFNLayout, symbol_map: Dict[str, str]) -> Iterator[Tuple[str, Path]]:
    for csv_path in layout.history_root.rglob("*.csv"):
        stem = csv_path.stem
        symbol = symbol_map.get(stem)
        if symbol:
            yield symbol, csv_path


def read_history_file(path: Path) -> pd.DataFrame:
    """
    DirectFN history format: DATE|OP|HIG|LOW|CLS|VOL
    DATE is YYYYMMDD
    """
    df = pd.read_csv(path, sep="|")
    required = {"DATE", "OP", "HIG", "LOW", "CLS"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()
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
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d", errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    return df[["timestamp", "open", "high", "low", "close", "volume"]].sort_values("timestamp")


def iter_intraday_files(
    layout: DirectFNLayout, symbol_map: Dict[str, str], lookback_days: int = 5
) -> Iterator[Tuple[str, Path]]:
    """
    DirectFN intraday path layout: ohlc/case/YYYYMMDD/<file>.csv
    """
    cutoff = datetime.now().date() - timedelta(days=max(0, lookback_days))
    for day_dir in sorted(layout.intraday_root.iterdir()):
        if not day_dir.is_dir():
            continue
        try:
            day = datetime.strptime(day_dir.name, "%Y%m%d").date()
        except ValueError:
            continue
        if day < cutoff:
            continue
        for csv_path in day_dir.glob("*.csv"):
            stem = csv_path.stem
            symbol = symbol_map.get(stem)
            if symbol:
                yield symbol, csv_path


def read_intraday_file(path: Path, tz: str = "Africa/Cairo") -> pd.DataFrame:
    """
    DirectFN intraday format: TMIN|OP|HIG|LOW|CLS|VOL
    TMIN is Unix epoch minutes.
    """
    df = pd.read_csv(path, sep="|")
    required = {"TMIN", "OP", "HIG", "LOW", "CLS"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()
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
    tmin_numeric = pd.to_numeric(df["tmin"], errors="coerce")
    non_na = tmin_numeric.dropna()
    # DirectFN can encode epoch in seconds, while other local stores may use minutes.
    # Infer by magnitude to avoid empty intraday datasets.
    if non_na.empty:
        ts = pd.to_datetime(df["tmin"], errors="coerce")
    else:
        sample = float(non_na.iloc[-1])
        if sample > 1.0e11:
            unit = "ms"
        elif sample > 1.0e9:
            unit = "s"
        else:
            unit = "m"
        try:
            ts = pd.to_datetime(tmin_numeric, unit=unit, utc=True, errors="coerce")
            ts = ts.dt.tz_convert(tz).dt.tz_localize(None)
        except Exception:
            ts = pd.to_datetime(tmin_numeric, unit=unit, errors="coerce")
    df["timestamp"] = ts
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close"])
    return df[["timestamp", "open", "high", "low", "close", "volume"]].sort_values("timestamp")


def latest_history_snapshot(layout: DirectFNLayout, symbol_map: Dict[str, str]) -> Tuple[int, Optional[str]]:
    count = 0
    latest: Optional[str] = None
    for _, path in iter_history_files(layout, symbol_map):
        try:
            df = pd.read_csv(path, sep="|", usecols=["DATE"])
            if df.empty:
                continue
            last_date = str(int(df["DATE"].iloc[-1])).zfill(8)
            count += 1
            if latest is None or last_date > latest:
                latest = last_date
        except Exception:
            continue
    return count, latest


def latest_intraday_snapshot(layout: DirectFNLayout, symbol_map: Dict[str, str]) -> Tuple[int, Optional[str]]:
    count = 0
    latest: Optional[str] = None
    for _, path in iter_intraday_files(layout, symbol_map, lookback_days=2):
        try:
            df = pd.read_csv(path, sep="|", usecols=["TMIN"])
            if df.empty:
                continue
            last_tmin = float(pd.to_numeric(df["TMIN"], errors="coerce").dropna().iloc[-1])
            if last_tmin > 1.0e11:
                ts_obj = datetime.fromtimestamp(last_tmin / 1000.0, tz=timezone.utc)
            elif last_tmin > 1.0e9:
                ts_obj = datetime.fromtimestamp(last_tmin, tz=timezone.utc)
            else:
                ts_obj = datetime.fromtimestamp(last_tmin * 60.0, tz=timezone.utc)
            ts = ts_obj.astimezone().strftime("%Y%m%d%H%M%S")
            count += 1
            if latest is None or ts > latest:
                latest = ts
        except Exception:
            continue
    return count, latest
