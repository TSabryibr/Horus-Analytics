from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple
import re

import pandas as pd


_FILE_RE = re.compile(r"^F(?P<id>\d+)\.(?P<ext>DAT|MWD)$", re.IGNORECASE)


@dataclass
class MetaStockDatLayout:
    history_root: Path
    intraday_root: Path


def detect_layout(history_dir: Path, intraday_dir: Path) -> Optional[MetaStockDatLayout]:
    history_dir = history_dir.expanduser()
    intraday_dir = intraday_dir.expanduser()
    if not history_dir.exists() or not intraday_dir.exists():
        return None

    # Avoid hard-failing on transient MASTER/XMASTER rotation windows.
    # Layout is considered valid if folders exist and contain expected feed files.
    history_ok = any(history_dir.glob("F*.DAT")) or any(history_dir.glob("F*.MWD"))
    intraday_ok = any(intraday_dir.glob("F*.DAT")) or any(intraday_dir.glob("F*.MWD"))
    if not history_ok or not intraday_ok:
        return None

    return MetaStockDatLayout(history_root=history_dir, intraday_root=intraday_dir)


def load_symbol_map(layout: MetaStockDatLayout) -> Dict[int, str]:
    symbol_map: Dict[int, str] = {}
    symbol_map.update(_parse_master(layout.history_root / "MASTER"))
    symbol_map.update(_parse_xmaster(layout.history_root / "XMASTER"))

    # Intraday may contain a newer or different subset; keep any missing ids.
    for fid, sym in _parse_master(layout.intraday_root / "MASTER").items():
        symbol_map.setdefault(fid, sym)
    for fid, sym in _parse_xmaster(layout.intraday_root / "XMASTER").items():
        symbol_map.setdefault(fid, sym)

    return symbol_map


def iter_history_files(layout: MetaStockDatLayout, symbol_map: Dict[int, str]) -> Iterator[Tuple[str, Path]]:
    for path in sorted(layout.history_root.glob("F*.*")):
        fid = _extract_file_id(path)
        if fid is None:
            continue
        sym = symbol_map.get(fid)
        if sym:
            yield sym, path


def iter_intraday_files(
    layout: MetaStockDatLayout, symbol_map: Dict[int, str], lookback_days: int = 5
) -> Iterator[Tuple[str, Path]]:
    cutoff = datetime.now() - timedelta(days=max(0, lookback_days))
    for path in sorted(layout.intraday_root.glob("F*.*")):
        fid = _extract_file_id(path)
        if fid is None:
            continue
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) < cutoff:
                continue
        except OSError:
            continue
        sym = symbol_map.get(fid)
        if sym:
            yield sym, path


def read_history_file(path: Path) -> pd.DataFrame:
    data = _read_bytes(path)
    if not data:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    candidates = [
        _decode_series(data, header=28, record_len=28, with_time=False),
        _decode_series(data, header=32, record_len=28, with_time=False),
        _decode_series(data, header=0, record_len=28, with_time=False),
    ]
    return _best_non_empty(candidates)


def read_intraday_file(path: Path, tz: str = "Africa/Cairo") -> pd.DataFrame:
    data = _read_bytes(path)
    if not data:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    # Main format observed in DFN MetaStock intraday files: 32-byte bars.
    candidates = [
        _decode_series(data, header=32, record_len=32, with_time=True),
        _decode_series(data, header=28, record_len=32, with_time=True),
        _decode_series(data, header=28, record_len=28, with_time=False),
    ]
    df = _best_non_empty(candidates)
    if df.empty:
        return df

    # Data already encodes market-local date/time; keep naive local timestamps.
    _ = tz
    return df


def latest_history_snapshot(layout: MetaStockDatLayout, symbol_map: Dict[int, str]) -> Tuple[int, Optional[str]]:
    count = 0
    latest: Optional[str] = None
    for _, path in iter_history_files(layout, symbol_map):
        ts = _latest_timestamp(path, intraday=False)
        if ts is None:
            continue
        count += 1
        stamp = ts.strftime("%Y%m%d")
        if latest is None or stamp > latest:
            latest = stamp
    return count, latest


def latest_intraday_snapshot(layout: MetaStockDatLayout, symbol_map: Dict[int, str]) -> Tuple[int, Optional[str]]:
    count = 0
    latest: Optional[str] = None
    for _, path in iter_intraday_files(layout, symbol_map, lookback_days=3):
        ts = _latest_timestamp(path, intraday=True)
        if ts is None:
            continue
        count += 1
        stamp = ts.strftime("%Y%m%d%H%M%S")
        if latest is None or stamp > latest:
            latest = stamp
    return count, latest


def _parse_master(path: Path) -> Dict[int, str]:
    out: Dict[int, str] = {}
    data = _read_bytes(path)
    rec_len = 53
    if len(data) < rec_len:
        return out

    for i in range(0, len(data) - rec_len + 1, rec_len):
        rec = data[i : i + rec_len]
        fid = rec[0]
        if fid <= 0:
            continue
        symbol = _decode_ascii(rec[36:50]).upper()
        if _looks_like_symbol(symbol):
            out[fid] = symbol
    return out


def _parse_xmaster(path: Path) -> Dict[int, str]:
    out: Dict[int, str] = {}
    data = _read_bytes(path)
    rec_len = 150
    if len(data) < rec_len:
        return out

    # Record 0 is an XMASTER header. Symbols are from record 1 onward and
    # map to F256.. sequentially in this feed variant.
    max_records = len(data) // rec_len
    for idx in range(1, max_records):
        rec = data[idx * rec_len : (idx + 1) * rec_len]
        symbol = _decode_ascii(rec[1:15]).upper()
        if not _looks_like_symbol(symbol):
            continue
        fid = 255 + idx
        out[fid] = symbol
    return out


def _decode_series(data: bytes, header: int, record_len: int, with_time: bool) -> pd.DataFrame:
    if header < 0 or record_len <= 0 or len(data) <= header:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    rows = []
    for pos in range(header, len(data) - record_len + 1, record_len):
        rec = data[pos : pos + record_len]
        if with_time:
            date_value = _mbf_to_float(rec[0:4])
            time_value = _mbf_to_float(rec[4:8])
            ts = _decode_timestamp(date_value, time_value)
            base = 8
        else:
            date_value = _mbf_to_float(rec[0:4])
            ts = _decode_timestamp(date_value, None)
            base = 4

        if ts is None:
            continue

        o = _mbf_to_float(rec[base : base + 4])
        h = _mbf_to_float(rec[base + 4 : base + 8])
        l = _mbf_to_float(rec[base + 8 : base + 12])
        c = _mbf_to_float(rec[base + 12 : base + 16])
        v = _mbf_to_float(rec[base + 16 : base + 20])

        if min(o, h, l, c) <= 0:
            continue
        if not (l <= max(o, c, h) and h >= min(o, c, l)):
            continue

        rows.append((ts, float(o), float(h), float(l), float(c), float(v)))

    if not rows:
        return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df = df.drop_duplicates(subset=["timestamp"], keep="last").sort_values("timestamp")
    return df.reset_index(drop=True)


def _best_non_empty(candidates: list[pd.DataFrame]) -> pd.DataFrame:
    best = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
    for df in candidates:
        if not df.empty and len(df) > len(best):
            best = df
    return best


def _latest_timestamp(path: Path, intraday: bool) -> Optional[datetime]:
    data = _read_bytes(path)
    if not data:
        return None

    if intraday:
        attempts = [(32, 32, True), (28, 32, True), (28, 28, False)]
    else:
        attempts = [(28, 28, False), (32, 28, False), (0, 28, False)]

    best: Optional[datetime] = None
    for header, rec_len, with_time in attempts:
        if len(data) <= header or (len(data) - header) < rec_len:
            continue
        n = (len(data) - header) // rec_len
        pos = header + (n - 1) * rec_len
        rec = data[pos : pos + rec_len]
        if with_time:
            ts = _decode_timestamp(_mbf_to_float(rec[0:4]), _mbf_to_float(rec[4:8]))
        else:
            ts = _decode_timestamp(_mbf_to_float(rec[0:4]), None)
        if ts is not None and (best is None or ts > best):
            best = ts
    return best


def _decode_timestamp(date_value: float, time_value: Optional[float]) -> Optional[datetime]:
    date_int = int(round(date_value))
    ymd = _decode_date_int(date_int)
    if ymd is None:
        return None
    year, month, day = ymd

    hour = 0
    minute = 0
    second = 0
    if time_value is not None:
        hms = _decode_time_int(int(round(time_value)))
        if hms is None:
            return None
        hour, minute, second = hms

    try:
        ts = datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None

    if ts.year < 1990 or ts.year > 2100:
        return None
    return ts


def _decode_date_int(value: int) -> Optional[Tuple[int, int, int]]:
    if value <= 0:
        return None

    s = str(value)
    if len(s) == 8 and s[:2] in {"19", "20"}:
        year = int(s[0:4])
        month = int(s[4:6])
        day = int(s[6:8])
        return year, month, day

    # MetaStock variant observed in DFN files:
    # 1YYMMDD => 20YYMMDD, 0YYMMDD => 19YYMMDD
    if len(s) == 7 and s[0] in {"0", "1"}:
        century = 1900 if s[0] == "0" else 2000
        year = century + int(s[1:3])
        month = int(s[3:5])
        day = int(s[5:7])
        return year, month, day

    # Fallback for compact YYMMDD values.
    if len(s) == 6:
        yy = int(s[0:2])
        year = 2000 + yy if yy <= 70 else 1900 + yy
        month = int(s[2:4])
        day = int(s[4:6])
        return year, month, day

    return None


def _decode_time_int(value: int) -> Optional[Tuple[int, int, int]]:
    if value < 0:
        return None

    # Commonly HHMMSS in DFN intraday files.
    s = f"{value:06d}"
    hh = int(s[0:2])
    mm = int(s[2:4])
    ss = int(s[4:6])
    if 0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 59:
        return hh, mm, ss

    # Fallback HHMM.
    s4 = f"{value:04d}"
    hh = int(s4[0:2])
    mm = int(s4[2:4])
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return hh, mm, 0

    return None


def _mbf_to_float(raw: bytes) -> float:
    if len(raw) != 4:
        return 0.0
    b0, b1, b2, b3 = raw
    if b0 == 0 and b1 == 0 and b2 == 0 and b3 == 0:
        return 0.0
    sign = -1.0 if (b2 & 0x80) else 1.0
    mantissa = ((b2 & 0x7F) << 16) | (b1 << 8) | b0
    return sign * (1.0 + mantissa / (1 << 23)) * (2.0 ** (b3 - 129))


def _extract_file_id(path: Path) -> Optional[int]:
    m = _FILE_RE.match(path.name)
    if not m:
        return None
    try:
        return int(m.group("id"))
    except ValueError:
        return None


def _decode_ascii(raw: bytes) -> str:
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="ignore").strip()


def _looks_like_symbol(symbol: str) -> bool:
    if not symbol:
        return False
    if not any("A" <= ch <= "Z" for ch in symbol):
        return False
    for ch in symbol:
        if not (("A" <= ch <= "Z") or ("0" <= ch <= "9") or ch in {".", "-", "_"}):
            return False
    return True


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        return b""
