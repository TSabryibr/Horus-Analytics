from core.settings import settings
import os
import time
import threading
import datetime
from typing import Optional, Dict, Any, Tuple

from core import TimeUtils
from core import Heimdall
from data_engine.freshness import evaluate_freshness
from data_engine.pipeline_worker import (
    AdaptiveSyncWorker,
    read_worker_state,
    worker_state_is_recovering,
    worker_retry_reason,
    _write_worker_state,
)
from data_engine.sync import sync_all
from core.pipeline_alerts import maybe_play_pipeline_stale_sound
from utils.logger import setup_logger

from routes.shared import (
    get_system_state_snapshot,
    set_pipeline_state,
    set_freshness_state,
    SYSTEM_STATE,
    SYSTEM_STATE_LOCK
)

logger = setup_logger("horus.pipeline")

def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")

def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default

def _sync_all_with_timeout(timeout_seconds: int) -> None:
    if timeout_seconds <= 0:
        sync_all()
        return

    sync_error = {}
    completed = threading.Event()

    def _runner():
        try:
            sync_all()
        except Exception as e:
            sync_error["error"] = e
        finally:
            completed.set()

    threading.Thread(target=_runner, daemon=True).start()

    if not completed.wait(timeout_seconds):
        raise TimeoutError(f"sync_all exceeded timeout ({timeout_seconds}s)")

    if "error" in sync_error:
        raise sync_error["error"]


def _evaluate_freshness_with_timeout(timeout_seconds: int) -> dict | None:
    if timeout_seconds <= 0:
        return evaluate_freshness(
            realm=getattr(Heimdall, "CURRENT_REALM", "EGX"),
            run_date=TimeUtils.today(),
            scan_type="INTRADAY",
        )

    done = threading.Event()
    result: dict[str, dict] = {}
    err: dict[str, BaseException] = {}

    def _runner():
        try:
            result["freshness"] = evaluate_freshness(
                realm=getattr(Heimdall, "CURRENT_REALM", "EGX"),
                run_date=TimeUtils.today(),
                scan_type="INTRADAY",
            )
        except Exception as e:
            err["error"] = e
        finally:
            done.set()

    threading.Thread(target=_runner, daemon=True).start()
    if not done.wait(timeout_seconds):
        return None
    if "error" in err:
        raise err["error"]
    
    val = result.get("freshness")
    if not isinstance(val, dict):
        return None
    return val


_PIPELINE_STATE_CACHE_LOCK = threading.Lock()
_PIPELINE_STATE_CACHE = {"ts": 0.0, "snapshot": None}
_SYNC_WORKER: AdaptiveSyncWorker | None = None


class _ReconciliationLogDedup:
    """Rate-limit identical reconciliation log messages to reduce noise."""

    _lock = threading.Lock()
    _interval_sec = 300  # configurable via PIPELINE_RECONCILIATION_LOG_INTERVAL_SEC
    _state: dict[str, dict] = {}  # key -> {"ts": float, "count": int}

    @classmethod
    def _interval(cls) -> int:
        return max(30, _env_int("PIPELINE_RECONCILIATION_LOG_INTERVAL_SEC", 300))

    @classmethod
    def should_log(cls, key: str) -> tuple[bool, int]:
        """Return (should_emit, suppressed_count) for the given message key."""
        now = time.time()
        with cls._lock:
            entry = cls._state.get(key)
            if entry is None:
                cls._state[key] = {"ts": now, "count": 0}
                return True, 0
            elapsed = now - entry["ts"]
            if elapsed >= cls._interval():
                suppressed = entry["count"]
                cls._state[key] = {"ts": now, "count": 0}
                return True, suppressed
            entry["count"] += 1
            return False, entry["count"]

    @classmethod
    def log_warning(cls, key: str, message: str) -> None:
        should_emit, suppressed = cls.should_log(key)
        if should_emit:
            suffix = f" (suppressed {suppressed}x in last {cls._interval()}s)" if suppressed else ""
            logger.warning(f"{message}{suffix}")

    @classmethod
    def log_error(cls, key: str, message: str) -> None:
        should_emit, suppressed = cls.should_log(key)
        if should_emit:
            suffix = f" (suppressed {suppressed}x in last {cls._interval()}s)" if suppressed else ""
            logger.error(f"{message}{suffix}")


def _pipeline_worker_mode() -> str:
    raw = os.getenv("PIPELINE_SYNC_WORKER_MODE", "internal").strip().lower()
    if raw in {"internal", "external", "off"}:
        return raw
    return "internal"


def _derive_pipeline_state_from_freshness(freshness: dict) -> tuple[str, str, dict]:
    history_ratio = float((((freshness or {}).get("history") or {}).get("kpis") or {}).get("fresh_ratio", 0.0))
    intraday_ratio = float((((freshness or {}).get("intraday") or {}).get("kpis") or {}).get("live_ratio", 0.0))
    market_open = bool(settings.is_market_open())

    history_ok = bool(((freshness or {}).get("history") or {}).get("ok", False))
    intraday_signal_ok = bool(((freshness or {}).get("intraday") or {}).get("ok", False))
    intraday_ok = intraday_signal_ok if market_open else True

    degradation_reason = None
    if not market_open and not history_ok:
        history_last = ((freshness or {}).get("history") or {}).get("last_updated")
        if history_last:
            try:
                from datetime import date as dt_date
                last_d = dt_date.fromisoformat(str(history_last)[:10])
                if settings.is_recent_trading_day(last_d, max_trading_days=1):
                    history_ok = True
            except Exception:
                pass

    if market_open and intraday_ratio == 0.0:
        pipeline_state = "DEGRADED"
        message = "History is fresh, but intraday provider is unreachable. Read-only stale mode is active."
        degradation_reason = "intraday_provider_unreachable"
    elif history_ok and intraday_ok:
        pipeline_state = "FRESH"
        message = "Data pipeline is fresh." if market_open else "Market closed. Historical book aligned."
    elif history_ok:
        pipeline_state = "STALE"
        message = "History is fresh, intraday feed is stale. Read-only stale mode is active."
    else:
        pipeline_state = "DEGRADED"
        message = "History freshness is below threshold. Read-only stale mode is active."

    freshness_metrics = {
        "history_fresh_ratio": float(int(float(history_ratio or 0.0) * 10000)) / 10000.0,
        "intraday_live_ratio": float(int(float(intraday_ratio or 0.0) * 10000)) / 10000.0,
        "history_ok": bool(history_ok),
        "intraday_ok": bool(intraday_ok),
        "market_open": market_open,
        "overall_ok": pipeline_state == "FRESH",
        "checked_at": TimeUtils.now().isoformat(),
        "session_mode": settings.SESSION_MODE,
    }
    if degradation_reason:
        freshness_metrics["degradation_reason"] = degradation_reason
    return pipeline_state, message, freshness_metrics


def _worker_pipeline_state_message(pipeline_state: str) -> str:
    normalized = str(pipeline_state or "").upper()
    if normalized == "FRESH":
        return "Data pipeline is fresh." if settings.is_market_open() else "Market closed. Historical book aligned."
    if normalized == "SYNCING":
        return "Sync worker is refreshing data. Read-only stale mode is active."
    if normalized in {"STALE", "DEGRADED"}:
        return "Read-only stale mode is active."
    return "Pipeline state unavailable."


def _freshness_checked_age_seconds(freshness_metrics: dict | None) -> float | None:
    checked_at = (freshness_metrics or {}).get("checked_at")
    if not checked_at:
        return None
    try:
        checked_dt = datetime.datetime.fromisoformat(str(checked_at).replace("Z", "+00:00"))
    except Exception:
        return None
    if checked_dt.tzinfo is not None:
        checked_dt = checked_dt.replace(tzinfo=None)
    return max(0.0, (TimeUtils.now().replace(tzinfo=None) - checked_dt).total_seconds())


def _worker_freshness_expired(worker_state: dict | None, worker_pipeline_state: str) -> bool:
    if str(worker_pipeline_state or "").upper() != "FRESH":
        return False
    freshness_metrics = dict((worker_state or {}).get("freshness") or {})
    age_seconds = _freshness_checked_age_seconds(freshness_metrics)
    if age_seconds is None:
        return False
    max_age_seconds = max(30, _env_int("PIPELINE_FRESH_WORKER_MAX_AGE_SEC", 900))
    return age_seconds > max_age_seconds


def _should_reconcile_worker_freshness(worker_state: dict | None, worker_pipeline_state: str) -> bool:
    if not _env_bool("PIPELINE_RECONCILE_STALE_WORKER_STATE", True):
        return False
    if not worker_state:
        return False
    if bool(worker_state.get("syncing", False)):
        return False
    if worker_state_is_recovering(worker_state):
        return False
    if worker_pipeline_state in {"STALE", "DEGRADED"}:
        return True
    if _worker_freshness_expired(worker_state, worker_pipeline_state):
        return True
    return False


def _normalize_bootstrapped_pipeline_state(
    pipeline_state: str,
    message: str,
) -> tuple[str, str]:
    normalized = str(pipeline_state or "DEGRADED").upper()
    if normalized != "STARTING":
        return normalized, message
    return "DEGRADED", "Pipeline health is still being evaluated. Read-only stale mode is active."


def _can_preserve_known_fresh_state(pipeline_state: str, freshness_metrics: dict) -> bool:
    return (
        str(pipeline_state or "").upper() == "FRESH"
        and bool((freshness_metrics or {}).get("overall_ok", False))
    )


def _persist_reconciled_worker_state(
    worker_state: dict | None,
    *,
    pipeline_state: str,
    freshness_metrics: dict,
) -> dict | None:
    if not worker_state:
        return worker_state

    normalized = str(pipeline_state or "").upper()
    payload = dict(worker_state)
    payload["pipeline_state"] = normalized
    payload["freshness"] = freshness_metrics
    payload["syncing"] = False

    if normalized == "FRESH":
        payload["last_success_at"] = TimeUtils.now().isoformat()
        payload["last_failure_at"] = None
        payload["last_error"] = None
        payload["fail_count"] = 0
        payload["next_retry_seconds"] = 0
        payload["backoff_seconds"] = 0
        payload["retry_reason"] = None

    try:
        _write_worker_state(payload)
    except Exception as exc:
        logger.error(f"[Pipeline] Failed to persist reconciled worker state: {exc}")
    return payload


def _sync_worker_payload(worker_state: dict | None) -> dict:
    if not worker_state:
        return {
            "enabled": _pipeline_worker_mode() != "off",
            "running": False,
            "syncing": False,
            "pipeline_state": None,
            "last_heartbeat_at": None,
            "last_attempt_at": None,
            "last_success_at": None,
            "last_failure_at": None,
            "last_error": None,
            "fail_count": 0,
            "next_retry_seconds": 0,
            "backoff_seconds": 0,
            "retry_reason": None,
            "recovering": False,
        }
    retry_reason = (
        str(worker_state.get("retry_reason"))
        if worker_state.get("retry_reason")
        else worker_retry_reason(worker_state)
    )
    recovering = (
        bool(worker_state.get("recovering"))
        if "recovering" in worker_state
        else worker_state_is_recovering(worker_state)
    )
    return {
        "enabled": bool(worker_state.get("enabled", True)),
        "running": bool(worker_state.get("running", False)),
        "syncing": bool(worker_state.get("syncing", False)),
        "pipeline_state": worker_state.get("pipeline_state"),
        "last_heartbeat_at": worker_state.get("last_heartbeat_at"),
        "last_attempt_at": worker_state.get("last_attempt_at"),
        "last_success_at": worker_state.get("last_success_at"),
        "last_failure_at": worker_state.get("last_failure_at"),
        "last_error": worker_state.get("last_error"),
        "fail_count": int(worker_state.get("fail_count", 0) or 0),
        "next_retry_seconds": int(worker_state.get("next_retry_seconds", 0) or 0),
        "backoff_seconds": int(worker_state.get("backoff_seconds", 0) or 0),
        "retry_reason": retry_reason,
        "recovering": recovering,
    }


def refresh_pipeline_state(force: bool = False) -> dict:
    cache_ttl_sec = max(1, _env_int("PIPELINE_STATE_CACHE_TTL_SEC", 15))
    now_ts = time.time()
    with _PIPELINE_STATE_CACHE_LOCK:
        cached = _PIPELINE_STATE_CACHE.get("snapshot")
        cached_ts = float(_PIPELINE_STATE_CACHE.get("ts", 0.0) or 0.0)
        if not force and cached and (now_ts - cached_ts) < cache_ttl_sec:
            return cached

    system_state = get_system_state_snapshot()
    if _env_bool("HORUS_DISABLE_READINESS_GATE", False):
        test_state = dict(system_state)
        test_state["pipeline_state"] = "FRESH"
        test_state["overall_ok"] = True
        test_state["sync_worker"] = {
            "enabled": False,
            "pipeline_state": None,
            "recovering": False,
            "retry_reason": None,
        }
        with _PIPELINE_STATE_CACHE_LOCK:
            _PIPELINE_STATE_CACHE["snapshot"] = test_state
            _PIPELINE_STATE_CACHE["ts"] = now_ts
        return test_state

    if not bool(system_state.get("bootstrap_complete", False)):
        with _PIPELINE_STATE_CACHE_LOCK:
            _PIPELINE_STATE_CACHE["snapshot"] = system_state
            _PIPELINE_STATE_CACHE["ts"] = now_ts
        return system_state

    pipeline_state = str(system_state.get("pipeline_state", "DEGRADED")).upper()
    message = str(system_state.get("message") or "Pipeline state unavailable.")
    pipeline_state, message = _normalize_bootstrapped_pipeline_state(pipeline_state, message)
    freshness_metrics = dict(system_state.get("freshness") or {})
    if not freshness_metrics:
        freshness_metrics = {
            "history_fresh_ratio": 0.0,
            "intraday_live_ratio": 0.0,
            "history_ok": False,
            "intraday_ok": False,
            "market_open": bool(settings.is_market_open()),
            "overall_ok": False,
            "checked_at": TimeUtils.now().isoformat(),
        }
    prior_pipeline_state = pipeline_state
    prior_message = message
    prior_freshness_metrics = dict(freshness_metrics)

    worker_state = read_worker_state()
    worker_payload = _sync_worker_payload(worker_state)

    worker_pipeline_state = str(worker_state.get("pipeline_state", "")).upper() if worker_state else ""
    if worker_pipeline_state == "SYNCING":
        pipeline_state = "SYNCING"
        message = _worker_pipeline_state_message(worker_pipeline_state)
        if worker_state.get("freshness"):
            freshness_metrics = dict(worker_state.get("freshness"))
    elif worker_pipeline_state in {"FRESH", "STALE", "DEGRADED"}:
        pipeline_state = worker_pipeline_state
        message = _worker_pipeline_state_message(worker_pipeline_state)
        if worker_state.get("freshness"):
            freshness_metrics = dict(worker_state.get("freshness"))
        worker_freshness_expired = _worker_freshness_expired(worker_state, worker_pipeline_state)
        if _should_reconcile_worker_freshness(worker_state, worker_pipeline_state):
            timeout_sec = 0 if worker_freshness_expired else max(1, _env_int("PIPELINE_INLINE_FRESHNESS_TIMEOUT_SEC", 2))
            try:
                freshness = _evaluate_freshness_with_timeout(timeout_sec)
                if freshness:
                    reconciled_state, reconciled_message, reconciled_metrics = _derive_pipeline_state_from_freshness(freshness)
                    if reconciled_state != worker_pipeline_state or worker_freshness_expired:
                        logger.info(
                            "[Pipeline] Reconciled worker state %s -> %s using inline freshness check.",
                            worker_pipeline_state,
                            reconciled_state,
                        )
                        worker_state = _persist_reconciled_worker_state(
                            worker_state,
                            pipeline_state=reconciled_state,
                            freshness_metrics=reconciled_metrics,
                        )
                        worker_payload = _sync_worker_payload(worker_state)
                    pipeline_state = reconciled_state
                    message = reconciled_message
                    freshness_metrics = reconciled_metrics
                else:
                    if _can_preserve_known_fresh_state(prior_pipeline_state, prior_freshness_metrics):
                        _ReconciliationLogDedup.log_warning(
                            "timeout_preserve",
                            "[Pipeline] Stale worker reconciliation timed out; preserving known fresh system state.",
                        )
                        pipeline_state = prior_pipeline_state
                        message = prior_message
                        freshness_metrics = prior_freshness_metrics
                    else:
                        _ReconciliationLogDedup.log_warning(
                            "timeout_keep",
                            "[Pipeline] Stale worker reconciliation timed out; keeping worker state.",
                        )
            except Exception as e:
                _ReconciliationLogDedup.log_error(
                    "reconcile_error",
                    f"[Pipeline] Stale worker reconciliation failed: {e}",
                )
                if _can_preserve_known_fresh_state(prior_pipeline_state, prior_freshness_metrics):
                    pipeline_state = prior_pipeline_state
                    message = prior_message
                    freshness_metrics = prior_freshness_metrics
    elif _env_bool("PIPELINE_INLINE_FRESHNESS_EVAL", False):
        timeout_sec = max(1, _env_int("PIPELINE_INLINE_FRESHNESS_TIMEOUT_SEC", 2))
        try:
            freshness = _evaluate_freshness_with_timeout(timeout_sec)
            if freshness:
                pipeline_state, message, freshness_metrics = _derive_pipeline_state_from_freshness(freshness)
            else:
                message = "Freshness evaluation timed out; using cached pipeline state."
        except Exception as e:
            logger.error(f"[Pipeline] Freshness evaluation failed: {e}")
            message = f"Freshness evaluation failed: {e}"

    worker_success_ts = worker_state.get("last_success_at") if worker_state else None
    with _PIPELINE_STATE_CACHE_LOCK:
        last_seen_success = _PIPELINE_STATE_CACHE.get("last_seen_success")
        if worker_success_ts and worker_success_ts != last_seen_success:
            with SYSTEM_STATE_LOCK:
                SYSTEM_STATE["data_version"] += 1
                logger.info(f"[Pipeline] Data change detected ({worker_success_ts}). Version incremented to {SYSTEM_STATE['data_version']}.")
            _PIPELINE_STATE_CACHE["last_seen_success"] = worker_success_ts

    set_freshness_state(
        history_fresh_ratio=float(freshness_metrics.get("history_fresh_ratio", 0.0) or 0.0),
        intraday_live_ratio=float(freshness_metrics.get("intraday_live_ratio", 0.0) or 0.0),
        history_ok=bool(freshness_metrics.get("history_ok", False)),
        intraday_ok=bool(freshness_metrics.get("intraday_ok", False)),
        market_open=bool(freshness_metrics.get("market_open", False)),
        overall_ok=bool(freshness_metrics.get("overall_ok", False)),
        checked_at=freshness_metrics.get("checked_at"),
        session_mode=freshness_metrics.get("session_mode"),
    )
    set_pipeline_state(
        pipeline_state,
        message=message,
        sync_worker=worker_payload,
        data_version=get_system_state_snapshot().get("data_version", 0),
    )
    maybe_play_pipeline_stale_sound(pipeline_state)
    snapshot = get_system_state_snapshot()
    with _PIPELINE_STATE_CACHE_LOCK:
        _PIPELINE_STATE_CACHE["snapshot"] = snapshot
        _PIPELINE_STATE_CACHE["ts"] = now_ts
    return snapshot


def pipeline_allows_active_ops(action_name: str) -> bool:
    if getattr(settings, "MAINTENANCE_MODE", False):
        logger.warning(f"[Gate] Blocking {action_name} while MAINTENANCE_MODE is ACTIVE.")
        return False
    state = refresh_pipeline_state()
    pipeline_state = str(state.get("pipeline_state", "DEGRADED")).upper()
    
    # Allow FRESH always.
    if pipeline_state == "FRESH":
        return True
        
    read_only_actions = {"get_settings", "get_data_status"}
    if action_name in read_only_actions:
        return True

    daily_history_readiness_actions = {
        "scheduled_daily_signal_scan",
        "scheduled_morning_daily_signal_scan",
        "scheduled_daily_signal_pipeline",
    }
    if action_name in daily_history_readiness_actions and pipeline_state in {"STARTING", "STALE", "DEGRADED"}:
        logger.info(
            f"[Gate] Allowing {action_name} while pipeline_state={pipeline_state}; "
            "daily history readiness will decide whether the scan can run."
        )
        return True

    # Position monitoring may continue with stale history only when live
    # intraday data is actually fresh. Never manage exits from old prices.
    live_price_actions = {"scheduled_trade_monitor", "manual_trade_monitor"}
    if action_name in live_price_actions:
        freshness = state.get("freshness") or {}
        intraday_ok = bool(freshness.get("intraday_ok", False))
        intraday_ratio = float(freshness.get("intraday_live_ratio", 0.0) or 0.0)
        market_open = bool(freshness.get("market_open", settings.is_market_open()))
        min_intraday_ratio = float(getattr(settings, "FRESHNESS_MIN_INTRADAY_RATIO", 0.65) or 0.65)
        if market_open and (intraday_ok or intraday_ratio >= min_intraday_ratio):
            return True
        logger.warning(
            f"[Gate] Blocking {action_name} while pipeline_state={pipeline_state}; "
            f"intraday_ok={intraday_ok} intraday_live_ratio={intraday_ratio:.2f}"
        )
        return False

    logger.warning(f"[Gate] Blocking {action_name} while pipeline_state={pipeline_state}")
    return False
