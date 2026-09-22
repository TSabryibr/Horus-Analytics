from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any


INDEX_FILENAME = "_watermarks.json"
INDEX_VERSION = 1


def index_path(history_dir: Path) -> Path:
    return history_dir / INDEX_FILENAME


def _file_signature(path: Path) -> dict[str, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return {
        "size": int(stat.st_size),
        "mtime_ns": int(stat.st_mtime_ns),
    }


def _empty_index() -> dict[str, Any]:
    return {
        "version": INDEX_VERSION,
        "symbols": {},
    }


def load_index(history_dir: Path) -> dict[str, Any]:
    path = index_path(history_dir)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return _empty_index()
    if not isinstance(raw, dict) or raw.get("version") != INDEX_VERSION:
        return _empty_index()
    symbols = raw.get("symbols")
    if not isinstance(symbols, dict):
        return _empty_index()
    return raw


def save_index(history_dir: Path, index: dict[str, Any]) -> None:
    history_dir.mkdir(parents=True, exist_ok=True)
    index["version"] = INDEX_VERSION
    index.setdefault("symbols", {})
    path = index_path(history_dir)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(
        json.dumps(index, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _parse_date(value: object) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def cached_flat_date(index: dict[str, Any], ticker: str, flat_path: Path) -> date | None:
    ticker = str(ticker).strip().upper()
    entry = index.get("symbols", {}).get(ticker)
    if not isinstance(entry, dict):
        return None
    signature = _file_signature(flat_path)
    if signature is None or entry.get("flat_signature") != signature:
        return None
    return _parse_date(entry.get("flat_date"))


def update_flat_date(index: dict[str, Any], ticker: str, flat_path: Path, last_date: date | None) -> bool:
    ticker = str(ticker).strip().upper()
    signature = _file_signature(flat_path)
    if not ticker or signature is None or last_date is None:
        return False

    symbols = index.setdefault("symbols", {})
    entry = symbols.setdefault(ticker, {})
    next_entry = {
        **entry,
        "flat_date": last_date.isoformat(),
        "flat_signature": signature,
    }
    if entry == next_entry:
        return False
    symbols[ticker] = next_entry
    return True
