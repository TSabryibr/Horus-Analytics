"""
REPLAY STATE & AVAILABILITY
===========================
Thread-safe singleton state and availability inspection for Market Replay.
"""

import bisect
import datetime
import sys
import threading
from typing import Any

from core.settings import settings
from core.simulation_profiles import resolve_simulation_scanner_profile, run_selected_simulation_profile_scan
from utils.logger import setup_logger

logger = setup_logger("horus.replay")

REPLAY_PREFIX = "[🔄 REPLAY]"

_REPLAY_STATE: dict[str, Any] = {
    "status": "IDLE",       # IDLE | STARTING | RUNNING | STOPPING | COMPLETED | ERROR
    "date": None,
    "speed": 1,
    "notify": False,
    "report": False,
    "live_channel_routing": False,
    "started_at": None,
    "completed_at": None,
    "current_time": None,
    "market_open": None,
    "market_close": None,
    "ticks_completed": 0,
    "total_ticks": 0,
    "progress_pct": 0.0,
    "signals_found": 0,
    "unique_signals": set(),
    "scan_results": [],
    "active_trades": [],
    "pending_entries": [],
    "pre_close_previews": {},
    "pre_close_reconciliation": [],
    "profile_id": None,
    "profile_name": None,
    "profile_source_type": None,
    "profile_scope": "HORUS_CORE",
    "market": "EGX30",
    "intraday_availability": None,
    "mode": "SINGLE_DAY",
    "start_date": None,
    "end_date": None,
    "current_date": None,
    "days_total": 0,
    "days_completed": 0,
    "current_day_index": 0,
    "replay_dates": [],
    "day_results": [],
    "campaign_summary": None,
    "campaign_progress_pct": 0.0,
    "reset_portfolio": True,
    "close_open_positions_end": False,
    "allow_missing_intraday_as_holidays": False,
    "skipped_holiday_dates": [],
    "error": None,
}
_REPLAY_LOCK = threading.Lock()
_REPLAY_THREAD: threading.Thread | None = None
_REPLAY_STOP_EVENT = threading.Event()


def _resolve_dispatch(name: str, fallback_fn, self_fn=None):
    """Dynamic dispatcher to support monkeypatched test harnesses on core.replay_engine."""
    mod = sys.modules.get("core.replay_engine")
    if mod is not None and hasattr(mod, name):
        val = getattr(mod, name)
        if val is not None and val is not fallback_fn and (self_fn is None or val is not self_fn):
            return val
    return fallback_fn


def _get_thread_class():
    mod = sys.modules.get("core.replay_engine")
    if mod is not None and hasattr(mod, "threading"):
        th = getattr(mod, "threading")
        if hasattr(th, "Thread"):
            return th.Thread
    return threading.Thread


def _get_timeutils():
    mod = sys.modules.get("core.replay_engine")
    if mod is not None and hasattr(mod, "TimeUtils"):
        return getattr(mod, "TimeUtils")
    from core import TimeUtils
    return TimeUtils


def _get_logger():
    mod = sys.modules.get("core.replay_engine")
    if mod is not None and hasattr(mod, "logger"):
        return getattr(mod, "logger")
    return logger


def _reset_state():
    """Reset replay state to defaults."""
    _REPLAY_STATE.update({
        "status": "IDLE",
        "date": None,
        "speed": 1,
        "notify": False,
        "report": False,
        "live_channel_routing": False,
        "started_at": None,
        "completed_at": None,
        "current_time": None,
        "market_open": None,
        "market_close": None,
        "ticks_completed": 0,
        "total_ticks": 0,
        "progress_pct": 0.0,
        "signals_found": 0,
        "unique_signals": set(),
        "scan_results": [],
        "active_trades": [],
        "pending_entries": [],
        "pre_close_previews": {},
        "pre_close_reconciliation": [],
        "profile_id": None,
        "profile_name": None,
        "profile_source_type": None,
        "profile_scope": "HORUS_CORE",
        "market": "EGX30",
        "intraday_availability": None,
        "mode": "SINGLE_DAY",
        "start_date": None,
        "end_date": None,
        "current_date": None,
        "days_total": 0,
        "days_completed": 0,
        "current_day_index": 0,
        "replay_dates": [],
        "day_results": [],
        "campaign_summary": None,
        "campaign_progress_pct": 0.0,
        "reset_portfolio": True,
        "close_open_positions_end": False,
        "allow_missing_intraday_as_holidays": False,
        "skipped_holiday_dates": [],
        "error": None,
    })


def _parse_market_times(replay_date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """Parse market open/close for the replay date using settings."""
    s = settings

    start_hhmm = s._active_market_start().zfill(4)
    end_hhmm = s._active_market_end().zfill(4)

    market_open = datetime.datetime.combine(
        replay_date,
        datetime.time(int(start_hhmm[:2]), int(start_hhmm[2:])),
    )
    market_close = datetime.datetime.combine(
        replay_date,
        datetime.time(int(end_hhmm[:2]), int(end_hhmm[2:])),
    )
    return market_open, market_close


def _resolve_replay_scanner_profile(profile_id: int | None = None, use_active_profile: bool = False):
    """Resolve the simulation scanner profile, falling back to the active profile.

    Direct call instead of _resolve_dispatch to avoid a circular reference:
    _resolve_replay_scanner_profile → _resolve_dispatch → core.replay_engine._resolve_replay_scanner_profile → recursion.
    """
    return resolve_simulation_scanner_profile(profile_id=profile_id, use_active_profile=use_active_profile)


def _run_selected_replay_profile_scan(profile):
    """Resolve and run the selected replay profile scan.

    Direct call instead of _resolve_dispatch to avoid a circular reference:
    _run_selected_replay_profile_scan → _resolve_dispatch → core.replay_engine._run_selected_replay_profile_scan → recursion.
    """
    return run_selected_simulation_profile_scan(profile=profile)


def _realm_for_replay_market(replay_market: str | None) -> str:
    market = (replay_market or "").upper()
    if market.startswith("EGX"):
        return "EGX"
    return "EGX"


def _get_replay_intraday_availability(
    replay_date: datetime.date,
    replay_market: str = "EGX30",
) -> dict:
    """Return whether replay_date has intraday records and nearby usable dates."""
    target = _resolve_dispatch("_get_replay_intraday_availability", None)
    if target is not None and target is not _get_replay_intraday_availability:
        return target(replay_date, replay_market=replay_market)

    from data_engine import intraday_store

    realm = _realm_for_replay_market(replay_market)
    target_date = replay_date.isoformat()

    date_counts = intraday_store.get_intraday_date_counts(realm=realm)
    counts_by_date = {str(row["date"]): row for row in date_counts if row.get("date")}
    available_dates = sorted(counts_by_date)
    target_row = counts_by_date.get(target_date)

    if not available_dates:
        return {
            "available": False,
            "date": target_date,
            "realm": realm,
            "market": replay_market,
            "intraday_records": 0,
            "intraday_tickers": 0,
            "available_start_date": None,
            "available_end_date": None,
            "nearest_previous_date": None,
            "nearest_next_date": None,
            "available_dates_sample": [],
        }

    insert_at = bisect.bisect_left(available_dates, target_date)
    nearest_previous = available_dates[insert_at - 1] if insert_at > 0 else None
    nearest_next = available_dates[insert_at] if insert_at < len(available_dates) else None
    sample_start = max(0, min(insert_at, max(0, len(available_dates) - 10)))
    sample = available_dates[sample_start:sample_start + 10]

    return {
        "available": target_row is not None and int(target_row.get("records") or 0) > 0,
        "date": target_date,
        "realm": realm,
        "market": replay_market,
        "intraday_records": int(target_row.get("records") or 0) if target_row else 0,
        "intraday_tickers": int(target_row.get("tickers") or 0) if target_row else 0,
        "available_start_date": available_dates[0],
        "available_end_date": available_dates[-1],
        "nearest_previous_date": nearest_previous,
        "nearest_next_date": nearest_next,
        "available_dates_sample": sample,
    }


def _format_intraday_availability_error(availability: dict) -> str:
    target_date = availability.get("date")
    start_date = availability.get("available_start_date")
    end_date = availability.get("available_end_date")
    previous_date = availability.get("nearest_previous_date")
    next_date = availability.get("nearest_next_date")

    if not start_date:
        return (
            f"No intraday records are loaded for {target_date}. "
            "Load intraday data first, then start Market Replay."
        )
    if next_date:
        return (
            f"No intraday records found for {target_date}. "
            f"The first replay day with intraday data is {start_date}; "
            f"the next usable date from your selection is {next_date}."
        )
    if previous_date:
        return (
            f"No intraday records found for {target_date}. "
            f"The latest replay day with intraday data is {end_date}; "
            f"try {previous_date} or another loaded intraday date."
        )
    return (
        f"No intraday records found for {target_date}. "
        f"Replay data is available from {start_date} to {end_date}."
    )


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _format_duration(started_at_iso: str | None) -> str:
    """Format the elapsed wall-clock duration."""
    if not started_at_iso:
        return "N/A"
    try:
        started = datetime.datetime.fromisoformat(started_at_iso)
        elapsed = datetime.datetime.now() - started
        minutes = int(elapsed.total_seconds() / 60)
        seconds = int(elapsed.total_seconds() % 60)
        return f"{minutes}m {seconds}s"
    except Exception:
        return "N/A"
