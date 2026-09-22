from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import json
import os
from pathlib import Path
import sys
from threading import Lock
from time import perf_counter
from typing import Any
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, Request

from core import TimeUtils
from core.settings import settings
from routes.analytics.cache import _cache_ttl_seconds, _current_data_version
from routes.shared import limiter

public_router = APIRouter(tags=["analytics"])
router = APIRouter(tags=["analytics"])

ANALYTICS_CACHE_FILE = Path(settings.DATA_ROOT) / "cache" / "analytics_cache.json"
ANALYTICS_LOCK = Lock()
ANALYTICS_CACHE_STATE: dict[str, Any] = {
    "data": [],
    "rows": 0,
    "last_updated": None,
    "status": "IDLE",
    "scan_id": None,
    "started_at": None,
    "completed_at": None,
    "duration_sec": None,
    "error": None,
    "cache_source": "memory",
    "processed": 0,
    "total": 0,
    "progress_pct": 0,
    "workers": 1,
    "version": -1,
}


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return fallback


def _safe_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _resolve_analytics_workers(total_tickers: int) -> int:
    if total_tickers <= 1:
        return 1
    cpu = os.cpu_count() or 4
    suggested = max(4, min(16, cpu * 2))
    configured = _safe_int(os.getenv("ANALYTICS_SCAN_WORKERS"), suggested)
    bounded = max(1, min(32, configured))
    return min(total_tickers, bounded)


def _analytics_state_snapshot(include_data: bool = True) -> dict:
    lock = _resolve_symbol("ANALYTICS_LOCK", ANALYTICS_LOCK)
    cache_state = _resolve_symbol("ANALYTICS_CACHE_STATE", ANALYTICS_CACHE_STATE)
    with lock:
        snapshot = dict(cache_state)
        if include_data:
            data_val = cache_state.get("data")
            snapshot["data"] = list(data_val) if isinstance(data_val, list) else []
        else:
            snapshot.pop("data", None)
    return snapshot


def _analytics_rows_from_state(*, allow_stale: bool = False) -> list[dict[str, Any]]:
    state = _analytics_state_snapshot(include_data=True)
    rows = state.get("data")
    if not isinstance(rows, list) or not rows:
        return []

    cache_version = int(state.get("version", -1) or -1)
    current_version_fn = _resolve_symbol("_current_data_version", _current_data_version)
    current_version = current_version_fn()
    if cache_version == current_version or allow_stale:
        return list(rows)
    return []


def _resolve_analytics_cache_file() -> Path:
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, "ANALYTICS_CACHE_FILE"):
        val = getattr(mod, "ANALYTICS_CACHE_FILE")
        if val is not None:
            return Path(val)
    return ANALYTICS_CACHE_FILE


def _load_analytics_cache_from_disk() -> None:
    loader_fn = _resolve_symbol("_load_analytics_cache_from_disk", None)
    if loader_fn and loader_fn is not _load_analytics_cache_from_disk:
        return loader_fn()

    cache_file = _resolve_analytics_cache_file()
    if not cache_file.exists():
        return
    try:
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
        data = payload.get("data")
        if not isinstance(data, list):
            return
        lock = _resolve_symbol("ANALYTICS_LOCK", ANALYTICS_LOCK)
        cache_state = _resolve_symbol("ANALYTICS_CACHE_STATE", ANALYTICS_CACHE_STATE)
        with lock:
            cache_state["data"] = data
            cache_state["rows"] = len(data)
            cache_state["last_updated"] = payload.get("last_updated")
            cache_state["completed_at"] = payload.get("completed_at")
            cache_state["duration_sec"] = payload.get("duration_sec")
            cache_state["status"] = "IDLE"
            cache_state["error"] = None
            cache_state["cache_source"] = "disk"
            cache_state["version"] = payload.get("version", -1)
    except Exception:
        return


def _persist_analytics_cache_to_disk() -> None:
    snapshot = _analytics_state_snapshot(include_data=True)
    payload = {
        "data": snapshot.get("data", []),
        "rows": snapshot.get("rows", 0),
        "last_updated": snapshot.get("last_updated"),
        "completed_at": snapshot.get("completed_at"),
        "duration_sec": snapshot.get("duration_sec"),
        "version": snapshot.get("version", -1),
    }
    cache_file = _resolve_analytics_cache_file()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = cache_file.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps(payload), encoding="utf-8")
    tmp_path.replace(cache_file)


def get_cached_analytics_rows(*, allow_stale: bool = False) -> list[dict[str, Any]]:
    rows = _analytics_rows_from_state(allow_stale=allow_stale)
    if rows:
        return rows
    _load_analytics_cache_from_disk()
    return _analytics_rows_from_state(allow_stale=allow_stale)


def ensure_analytics_rows(*, scan_id: str, allow_stale: bool = False) -> list[dict[str, Any]]:
    get_rows_fn = _resolve_symbol("get_cached_analytics_rows", get_cached_analytics_rows)
    rows = get_rows_fn(allow_stale=False)
    if rows:
        return rows

    stale_rows = get_rows_fn(allow_stale=True) if allow_stale else []
    if stale_rows:
        return stale_rows

    state = _analytics_state_snapshot(include_data=False)
    if state.get("status") != "RUNNING":
        task_runner = _resolve_symbol("run_analytics_task_logic", run_analytics_task_logic)
        task_runner(scan_id)
        rows = get_rows_fn(allow_stale=False)
        if rows:
            return rows

    return stale_rows


def _parse_date_prefix(value: str | None):
    if not value:
        return None
    try:
        return datetime.datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _history_last_data_day():
    try:
        from core.DataManager import DataManager

        status = DataManager.get_data_status()
        return _parse_date_prefix(status.get("last_updated"))
    except Exception:
        return None


def _resolve_history_last_data_day():
    mod = sys.modules.get("routes.analytics")
    if mod and hasattr(mod, "_history_last_data_day"):
        fn = getattr(mod, "_history_last_data_day")
        if fn is not _history_last_data_day:
            return fn()
    return _history_last_data_day()


def _parse_analytics_timestamp(value: str | None):
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        ts = datetime.datetime.fromisoformat(text)
        if ts.tzinfo is not None:
            ts = ts.astimezone().replace(tzinfo=None)
        return ts
    except Exception:
        return None


def _analytics_cache_age_seconds(state: dict) -> float | None:
    ts = _parse_analytics_timestamp(state.get("last_updated") or state.get("completed_at"))
    if ts is None:
        return None
    try:
        time_utils = _resolve_symbol("TimeUtils", TimeUtils)
        return max(0.0, float((time_utils.now().replace(tzinfo=None) - ts).total_seconds()))
    except Exception:
        return None


def _analytics_cache_needs_refresh(state: dict, current_version: int) -> bool:
    if state.get("status") == "RUNNING":
        return False
    if not state.get("rows"):
        return True
    if current_version > 0 and state.get("version", -1) != current_version:
        return True

    cache_day = _parse_date_prefix(state.get("last_updated") or state.get("completed_at"))
    history_day = _resolve_history_last_data_day()
    if history_day is not None and (cache_day is None or cache_day < history_day):
        return True

    if settings.is_market_open():
        time_utils = _resolve_symbol("TimeUtils", TimeUtils)
        live_day = time_utils.today()
        if cache_day is None or cache_day < live_day:
            return True
        live_ttl = _cache_ttl_seconds("ANALYTICS_LIVE_CACHE_TTL_SEC", 300)
        age_seconds = _analytics_cache_age_seconds(state)
        if age_seconds is None or age_seconds > live_ttl:
            return True

    return False


def _analytics_refresh_should_block_response(state: dict) -> bool:
    return bool(settings.is_market_open())


def _begin_analytics_scan(scan_id: str, total: int = 0, workers: int = 1) -> None:
    time_utils = _resolve_symbol("TimeUtils", TimeUtils)
    now_text = time_utils.now().strftime("%Y-%m-%d %H:%M:%S")
    lock = _resolve_symbol("ANALYTICS_LOCK", ANALYTICS_LOCK)
    cache_state = _resolve_symbol("ANALYTICS_CACHE_STATE", ANALYTICS_CACHE_STATE)
    with lock:
        cache_state["status"] = "RUNNING"
        cache_state["scan_id"] = scan_id
        cache_state["started_at"] = now_text
        cache_state["completed_at"] = None
        cache_state["duration_sec"] = None
        cache_state["error"] = None
        cache_state["processed"] = 0
        cache_state["total"] = int(total)
        cache_state["progress_pct"] = 0
        cache_state["workers"] = int(max(1, workers))


def _update_scan_progress(processed: int, total: int) -> None:
    pct = int((processed / total) * 100) if total > 0 else 0
    lock = _resolve_symbol("ANALYTICS_LOCK", ANALYTICS_LOCK)
    cache_state = _resolve_symbol("ANALYTICS_CACHE_STATE", ANALYTICS_CACHE_STATE)
    with lock:
        cache_state["processed"] = int(processed)
        cache_state["total"] = int(total)
        cache_state["progress_pct"] = pct


def run_analytics_task_logic(scan_id: str):
    started = perf_counter()
    time_utils = _resolve_symbol("TimeUtils", TimeUtils)
    lock = _resolve_symbol("ANALYTICS_LOCK", ANALYTICS_LOCK)
    cache_state = _resolve_symbol("ANALYTICS_CACHE_STATE", ANALYTICS_CACHE_STATE)
    try:
        from core.analyzers import MomentumBreakoutScanner
        from core.DataManager import DataManager
        from routes.scanner import sanitize_floats

        if settings.is_market_open():
            try:
                DataManager.refresh_intraday_cache_if_due()
            except Exception:
                pass

        tickers = DataManager.list_tickers()
        total = len(tickers)
        workers = _resolve_analytics_workers(total)
        _begin_analytics_scan(scan_id, total=total, workers=workers)

        if total == 0:
            finished_at = time_utils.now().strftime("%Y-%m-%d %H:%M:%S")
            with lock:
                cache_state["data"] = []
                cache_state["rows"] = 0
                cache_state["last_updated"] = finished_at
                cache_state["status"] = "IDLE"
                cache_state["scan_id"] = scan_id
                cache_state["completed_at"] = finished_at
                raw_dur_zero = perf_counter() - started
                cache_state["duration_sec"] = float(int(float(raw_dur_zero) * 100)) / 100.0
                cache_state["error"] = None
                cache_state["cache_source"] = "memory"
                cache_state["processed"] = 0
                cache_state["total"] = 0
                cache_state["progress_pct"] = 100
            _persist_analytics_cache_to_disk()
            return

        results = []
        processed = 0
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="analytics-scan") as pool:
            future_to_ticker = {pool.submit(MomentumBreakoutScanner.analyze_stock, ticker): ticker for ticker in tickers}
            for future in as_completed(future_to_ticker):
                processed += 1
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                except Exception:
                    pass
                if processed == total or processed % 10 == 0:
                    _update_scan_progress(processed=processed, total=total)

        finished_at = time_utils.now().strftime("%Y-%m-%d %H:%M:%S")
        results.sort(key=lambda item: str(item.get("Ticker", "")))
        sanitized = sanitize_floats(results)
        with lock:
            cache_state["data"] = sanitized
            cache_state["rows"] = len(sanitized)
            cache_state["last_updated"] = finished_at
            cache_state["status"] = "IDLE"
            cache_state["scan_id"] = scan_id
            cache_state["completed_at"] = finished_at
            raw_dur_ok = perf_counter() - started
            cache_state["duration_sec"] = float(int(float(raw_dur_ok) * 100)) / 100.0
            cache_state["error"] = None
            cache_state["cache_source"] = "memory"
            cache_state["processed"] = total
            cache_state["total"] = total
            cache_state["progress_pct"] = 100
            from routes.shared import SYSTEM_STATE

            cache_state["version"] = SYSTEM_STATE.get("data_version", 0)
        _persist_analytics_cache_to_disk()
    except Exception as e:
        with lock:
            cache_state["status"] = "ERROR"
            cache_state["scan_id"] = scan_id
            cache_state["completed_at"] = time_utils.now().strftime("%Y-%m-%d %H:%M:%S")
            raw_dur_fail = perf_counter() - started
            cache_state["duration_sec"] = float(int(float(raw_dur_fail) * 100)) / 100.0
            cache_state["error"] = str(e)

            total_val = cache_state.get("total")
            proc_val = cache_state.get("processed")
            if total_val is not None and proc_val is not None and float(total_val) > 0:
                cache_state["progress_pct"] = int((float(proc_val) / float(total_val)) * 100)


_load_analytics_cache_from_disk()


@public_router.get("/api/v1/analytics", summary="Full Analytics Data", description="Retrieves the full cached analytics dataset.")
@limiter.limit("30/minute")
def get_analytics_data(request: Request, background_tasks: BackgroundTasks):
    state = _analytics_state_snapshot(include_data=False)
    version_getter = _resolve_symbol("_current_data_version", _current_data_version)
    current_version = version_getter()
    should_refresh = _analytics_cache_needs_refresh(state, current_version)

    if should_refresh:
        scan_id = uuid4().hex[:12]
        _begin_analytics_scan(scan_id, total=0, workers=1)
        task_runner = _resolve_symbol("run_analytics_task_logic", run_analytics_task_logic)
        if _analytics_refresh_should_block_response(state):
            task_runner(scan_id)
        else:
            background_tasks.add_task(task_runner, scan_id)
        return _analytics_state_snapshot(include_data=True)

    return _analytics_state_snapshot(include_data=True)


@public_router.get("/api/v1/analytics/status", summary="Analytics Scan Status", description="Lightweight status endpoint for analytics scan progress.")
@limiter.limit("120/minute")
def get_analytics_status(request: Request):
    return _analytics_state_snapshot(include_data=False)


@router.post("/api/v1/analytics/refresh", summary="Trigger Analytics Refresh", description="Manually triggers a background refresh of the analytics cache.")
@limiter.limit("10/minute")
def refresh_analytics(background_tasks: BackgroundTasks, request: Request):
    state = _analytics_state_snapshot(include_data=False)
    if state.get("status") == "RUNNING":
        return {
            "message": "Scan already in progress",
            "status": "RUNNING",
            "scan_id": state.get("scan_id"),
            "rows": state.get("rows", 0),
            "last_updated": state.get("last_updated"),
        }

    scan_id = uuid4().hex[:12]
    _begin_analytics_scan(scan_id, total=0, workers=1)
    task_runner = _resolve_symbol("run_analytics_task_logic", run_analytics_task_logic)
    background_tasks.add_task(task_runner, scan_id)
    return {
        "message": "Scan started",
        "status": "RUNNING",
        "scan_id": scan_id,
    }
