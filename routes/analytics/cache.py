import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any, Optional
from fastapi import HTTPException

from core import TimeUtils
from core.settings import settings as core_settings
from routes.shared import ARBITRAGE_CACHE, NEWS_CACHE, get_system_state_snapshot

NEWS_CACHE_FILE = Path(core_settings.DATA_ROOT) / "cache" / "news_cache.json"


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return fallback


def _resolve_news_cache_file() -> Path:
    val = _resolve_symbol("NEWS_CACHE_FILE", NEWS_CACHE_FILE)
    return Path(val) if val is not None else NEWS_CACHE_FILE


def _cache_ttl_seconds(env_key: str, default_sec: int) -> int:
    raw = os.getenv(env_key)
    if raw is None:
        return default_sec
    try:
        return max(0, int(raw))
    except (TypeError, ValueError):
        return default_sec


def _current_data_version() -> int:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, "_current_data_version"):
        fn = getattr(mod, "_current_data_version")
        if fn is not _current_data_version:
            return fn()

    snapshot_fn = _resolve_symbol("get_system_state_snapshot", get_system_state_snapshot)
    snapshot = snapshot_fn() or {}
    version = int(snapshot.get("data_version", 0) or 0)
    if version > 0:
        return version
    try:
        from core.pipeline import refresh_pipeline_state

        refreshed = refresh_pipeline_state()
        return int((refreshed or {}).get("data_version", version) or 0)
    except Exception:
        return version


def _cache_is_fresh(cache_bucket: dict, ttl_sec: int) -> bool:
    current_version = _current_data_version()
    cache_version = cache_bucket.get("version", -1)

    # Version mismatch always means stale
    if cache_version != current_version:
        return False

    # In Analysis mode, we trust the cache once it's populated for this version
    if core_settings.SESSION_MODE == "ANALYSIS":
        return cache_version == current_version and cache_bucket.get("data") is not None

    time_utils = _resolve_symbol("TimeUtils", TimeUtils)
    ts = cache_bucket.get("timestamp")
    if not ts:
        return False
    try:
        age = (time_utils.now() - ts).total_seconds()
        return age <= ttl_sec
    except Exception:
        return False


def _mark_cache_timestamp(cache_bucket: dict) -> None:
    time_utils = _resolve_symbol("TimeUtils", TimeUtils)
    cache_bucket["timestamp"] = time_utils.now()
    cache_bucket["version"] = _current_data_version()
    cache_bucket["cache_source"] = "memory"


def _cache_age_seconds(cache_bucket: dict) -> Optional[float]:
    time_utils = _resolve_symbol("TimeUtils", TimeUtils)
    ts = cache_bucket.get("timestamp")
    if not ts:
        return None
    try:
        return max(0.0, float((time_utils.now() - ts).total_seconds()))
    except Exception:
        return None


def _normalize_arbitrage_universe(universe: Optional[str]) -> str:
    normalized = str(universe or "default").strip().lower()
    aliases = {
        "default": "default",
        "egx100": "default",
        "100": "default",
        "core": "default",
        "extended": "extended",
        "all": "extended",
        "market": "extended",
    }
    resolved = aliases.get(normalized)
    if not resolved:
        raise HTTPException(status_code=400, detail="Invalid arbitrage universe. Use 'default' or 'extended'.")
    return resolved


def _arbitrage_cache_bucket(universe_mode: str) -> dict:
    if universe_mode == "default":
        return ARBITRAGE_CACHE
    variants = ARBITRAGE_CACHE.setdefault("variants", {})
    bucket = variants.get(universe_mode)
    if bucket is None:
        bucket = {"data": [], "timestamp": None, "version": -1}
        variants[universe_mode] = bucket
    return bucket


def _disk_grace_ttl_seconds(env_key: str, default_sec: int) -> int:
    return _cache_ttl_seconds(env_key, default_sec)


def _persist_news_cache_to_disk(payload: dict[str, Any], timestamp: datetime.datetime, version: int) -> None:
    disk_payload = {
        "data": payload,
        "timestamp": timestamp.isoformat() if timestamp else None,
        "version": int(version),
    }
    cache_file = _resolve_news_cache_file()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_file.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(disk_payload), encoding="utf-8")
    tmp_path.replace(cache_file)


def _load_news_cache_from_disk() -> None:
    cache_file = _resolve_news_cache_file()
    if not cache_file.exists():
        return
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        cached_data = payload.get("data")
        timestamp_raw = payload.get("timestamp")
        cached_version = int(payload.get("version", -1))
        if not isinstance(cached_data, dict) or not timestamp_raw:
            return
        timestamp = datetime.datetime.fromisoformat(timestamp_raw)
        NEWS_CACHE["data"] = cached_data
        NEWS_CACHE["timestamp"] = timestamp
        NEWS_CACHE["version"] = cached_version
        NEWS_CACHE["cache_source"] = "disk"
    except Exception:
        return


_load_news_cache_from_disk()
