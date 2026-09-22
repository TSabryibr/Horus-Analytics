import os
import json
import copy
import threading
import time
from pathlib import Path
from typing import Any, Dict
from core.settings import settings as core_settings
from routes import shared

STRATEGY_HEALTH_CACHE_LOCK = threading.Lock()
STRATEGY_HEALTH_CACHE: Dict[str, Any] = {"key": None, "payload": None, "ts": 0.0, "source": None}
STRATEGY_HEALTH_CACHE_FILE = Path(core_settings.DATA_ROOT) / "cache" / "strategy_health_cache.json"

# Lock for stale-while-revalidate: prevents overlapping background recomputations
_RECOMPUTE_LOCK = threading.Lock()


def is_recompute_in_progress() -> bool:
    """Check if a background recomputation is already running."""
    locked = _RECOMPUTE_LOCK.acquire(blocking=False)
    if locked:
        _RECOMPUTE_LOCK.release()
        return False
    return True

def _strategy_health_cache_ttl_sec() -> int:
    raw = os.getenv("STRATEGY_HEALTH_CACHE_TTL_SEC")
    if raw is None:
        return 300
    try:
        return max(0, int(raw))
    except ValueError:
        return 300

def _strategy_health_disk_grace_ttl_sec() -> int:
    raw = os.getenv("STRATEGY_HEALTH_DISK_GRACE_TTL_SEC")
    if raw is None:
        return 300
    try:
        return max(0, int(raw))
    except ValueError:
        return 300

def _current_data_version() -> int:
    snapshot = shared.get_system_state_snapshot() or {}
    version = int(snapshot.get("data_version", 0) or 0)
    if version > 0:
        return version
    try:
        from core.pipeline import refresh_pipeline_state
        refreshed = refresh_pipeline_state()
        return int((refreshed or {}).get("data_version", version) or 0)
    except Exception:
        return version

def reset_strategy_health_cache() -> None:
    with STRATEGY_HEALTH_CACHE_LOCK:
        STRATEGY_HEALTH_CACHE["key"] = None
        STRATEGY_HEALTH_CACHE["payload"] = None
        STRATEGY_HEALTH_CACHE["ts"] = 0.0
        STRATEGY_HEALTH_CACHE["source"] = None

def _serialize_strategy_health_cache_key(key: tuple[int, int, str] | None) -> list | None:
    if key is None:
        return None
    return [int(key[0]), int(key[1]), str(key[2])]

def _deserialize_strategy_health_cache_key(value: Any) -> tuple[int, int, str] | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    try:
        return int(value[0]), int(value[1]), str(value[2])
    except (TypeError, ValueError):
        return None

def _persist_strategy_health_cache_to_disk(*, key: tuple[int, int, str], payload: dict[str, Any], timestamp: float) -> None:
    disk_payload = {
        "key": _serialize_strategy_health_cache_key(key),
        "payload": payload,
        "timestamp": float(timestamp),
    }
    STRATEGY_HEALTH_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = STRATEGY_HEALTH_CACHE_FILE.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(disk_payload), encoding="utf-8")
    tmp_path.replace(STRATEGY_HEALTH_CACHE_FILE)

def _load_strategy_health_cache_from_disk() -> None:
    if not STRATEGY_HEALTH_CACHE_FILE.exists():
        return
    try:
        payload = json.loads(STRATEGY_HEALTH_CACHE_FILE.read_text(encoding="utf-8"))
        key = _deserialize_strategy_health_cache_key(payload.get("key"))
        cached_payload = payload.get("payload")
        cached_ts = float(payload.get("timestamp", 0.0) or 0.0)
        if key is None or not isinstance(cached_payload, dict) or cached_ts <= 0:
            return
        with STRATEGY_HEALTH_CACHE_LOCK:
            STRATEGY_HEALTH_CACHE["key"] = key
            STRATEGY_HEALTH_CACHE["payload"] = copy.deepcopy(cached_payload)
            STRATEGY_HEALTH_CACHE["ts"] = cached_ts
            STRATEGY_HEALTH_CACHE["source"] = "disk"
    except Exception:
        return

_load_strategy_health_cache_from_disk()
