"""
SCHEDULING STATE & LOCKS
========================
Concurrency locks, retry trackers, deduplication keys, and run completion trackers.
"""

import sys
import threading
from core.pipeline import _env_bool
from utils.logger import setup_logger

logger = setup_logger("horus.scheduling.state")


def _resolve_scheduling_dispatch(name: str, fallback_fn):
    """Dynamic dispatcher to support monkeypatched test harnesses on core.scheduling."""
    mod = sys.modules.get("core.scheduling")
    if mod is not None and hasattr(mod, name):
        val = getattr(mod, name)
        if val is not None and val is not fallback_fn:
            return val
    return fallback_fn

_TRADE_MONITOR_LOCK = threading.Lock()
_USE_LEGACY_EXECUTOR = _env_bool("HORUS_USE_LEGACY_EXECUTOR", False)
_NO_SIGNAL_NOTICE_LOCK = threading.Lock()
_NO_SIGNAL_NOTICE_KEYS: set[str] = set()
_AI_DAILY_REPORT_LOCK = threading.Lock()
_AI_DAILY_REPORT_PENDING_DATES: set[str] = set()
_AI_DAILY_REPORT_SENT_DATES: set[str] = set()
_DAILY_SIGNAL_LOCK = threading.Lock()
_DAILY_SIGNAL_PENDING_DATES: set[str] = set()
_DAILY_SIGNAL_COMPLETED_DATES: set[str] = set()
_DAILY_SIGNAL_RETRY_COUNTS: dict[str, int] = {}

# Pre-close scan retry state
_PRE_CLOSE_LOCK = threading.Lock()
_PRE_CLOSE_RETRY_COUNTS: dict[str, int] = {}
_PRE_CLOSE_COMPLETED_DATES: set[str] = set()

_DATA_WAITING_NOTICE_LOCK = threading.Lock()
_DATA_WAITING_NOTICE_SENT_DATES: set[str] = set()

_PENDING_ENTRIES_LOCK = threading.Lock()
_PENDING_ENTRIES_EXECUTED_DATES: set[str] = set()

_MORNING_DAILY_SIGNAL_LOCK = threading.Lock()
_MORNING_DAILY_SIGNAL_COMPLETED_DATES: set[str] = set()


def _maybe_broadcast_data_waiting_subscriber_notice(run_date: str) -> bool:
    from core import AlertManager
    with _DATA_WAITING_NOTICE_LOCK:
        if run_date in _DATA_WAITING_NOTICE_SENT_DATES:
            return False
        _DATA_WAITING_NOTICE_SENT_DATES.add(run_date)

    msg = (
        "📢 [HORUS ANALYTICS] Notice: The daily signal will be sent once the market data is updated.\n"
        "إشعار هورس أناليتكس: سيتم إرسال الإشارة اليومية فور تحديث بيانات السوق."
    )
    try:
        AlertManager.broadcast_alert(msg)
        logger.info(f"[Scheduler] Broadcasted data-waiting subscriber notice for date {run_date}")
        return True
    except Exception as exc:
        logger.error(f"[Scheduler] Failed to broadcast data-waiting subscriber notice: {exc}")
        return False


def _get_daily_signal_retry_count(run_date: str) -> int:
    with _DAILY_SIGNAL_LOCK:
        return _DAILY_SIGNAL_RETRY_COUNTS.get(run_date, 0)


def _increment_daily_signal_retry_count(run_date: str) -> int:
    with _DAILY_SIGNAL_LOCK:
        _DAILY_SIGNAL_RETRY_COUNTS[run_date] = _DAILY_SIGNAL_RETRY_COUNTS.get(run_date, 0) + 1
        return _DAILY_SIGNAL_RETRY_COUNTS[run_date]


def _get_pre_close_retry_count(run_date: str) -> int:
    with _PRE_CLOSE_LOCK:
        return _PRE_CLOSE_RETRY_COUNTS.get(run_date, 0)


def _increment_pre_close_retry_count(run_date: str) -> int:
    with _PRE_CLOSE_LOCK:
        _PRE_CLOSE_RETRY_COUNTS[run_date] = _PRE_CLOSE_RETRY_COUNTS.get(run_date, 0) + 1
        return _PRE_CLOSE_RETRY_COUNTS[run_date]


def _mark_pre_close_completed(run_date: str) -> None:
    with _PRE_CLOSE_LOCK:
        _PRE_CLOSE_COMPLETED_DATES.add(run_date)


def _pre_close_was_completed(run_date: str) -> bool:
    with _PRE_CLOSE_LOCK:
        return run_date in _PRE_CLOSE_COMPLETED_DATES


def _mark_morning_daily_completed(run_date: str) -> None:
    with _MORNING_DAILY_SIGNAL_LOCK:
        _MORNING_DAILY_SIGNAL_COMPLETED_DATES.add(run_date)


def _morning_daily_was_completed(run_date: str) -> bool:
    with _MORNING_DAILY_SIGNAL_LOCK:
        return run_date in _MORNING_DAILY_SIGNAL_COMPLETED_DATES


def _mark_daily_signal_pending(run_date: str) -> None:
    with _DAILY_SIGNAL_LOCK:
        if run_date not in _DAILY_SIGNAL_COMPLETED_DATES:
            _DAILY_SIGNAL_PENDING_DATES.add(run_date)


def _mark_daily_signal_completed(run_date: str) -> None:
    with _DAILY_SIGNAL_LOCK:
        _DAILY_SIGNAL_COMPLETED_DATES.add(run_date)
        _DAILY_SIGNAL_PENDING_DATES.discard(run_date)


def _daily_signal_is_pending(run_date: str) -> bool:
    with _DAILY_SIGNAL_LOCK:
        return run_date in _DAILY_SIGNAL_PENDING_DATES


def _daily_signal_was_completed(run_date: str) -> bool:
    with _DAILY_SIGNAL_LOCK:
        return run_date in _DAILY_SIGNAL_COMPLETED_DATES


def _mark_ai_daily_report_pending(report_date: str) -> None:
    with _AI_DAILY_REPORT_LOCK:
        if report_date not in _AI_DAILY_REPORT_SENT_DATES:
            _AI_DAILY_REPORT_PENDING_DATES.add(report_date)


def _mark_ai_daily_report_sent(report_date: str) -> None:
    with _AI_DAILY_REPORT_LOCK:
        _AI_DAILY_REPORT_SENT_DATES.add(report_date)
        _AI_DAILY_REPORT_PENDING_DATES.discard(report_date)


def _ai_daily_report_was_sent(report_date: str) -> bool:
    with _AI_DAILY_REPORT_LOCK:
        return report_date in _AI_DAILY_REPORT_SENT_DATES


def _ai_daily_report_is_pending(report_date: str) -> bool:
    with _AI_DAILY_REPORT_LOCK:
        return report_date in _AI_DAILY_REPORT_PENDING_DATES


def _daily_signal_run_date() -> str:
    from core import TimeUtils
    return TimeUtils.today().isoformat()
