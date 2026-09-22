"""
SCHEDULING SCANS INTRADAY
=========================
Intraday live scanning loop and pending entry execution.
"""

from __future__ import annotations

import datetime
from core import TimeUtils
from core import pipeline as _pipeline
from core.settings import settings
from utils.logger import setup_logger

from ..state import (
    _PENDING_ENTRIES_EXECUTED_DATES,
    _PENDING_ENTRIES_LOCK,
    _pre_close_was_completed,
    _resolve_scheduling_dispatch,
)
from .deliveries import _background_ops_paused_for_time_travel
from .execution import _signal_auto_execution_enabled, execute_pending_daily_entries_for_horus
from .runner import scheduled_scan_logic

logger = setup_logger("horus.scheduling.scans.intraday")


def _get_logger():
    return _resolve_scheduling_dispatch("logger", logger)


def scheduled_intraday_scan():
    if _background_ops_paused_for_time_travel():
        _get_logger().info("[Scheduler] INTRADAY scan skipped: time travel/backfill is active.")
        return
    if not settings.is_market_open():
        _get_logger().info("[Scheduler] INTRADAY scan skipped: market is closed.")
        return
    pipeline_obj = _resolve_scheduling_dispatch("_pipeline", _pipeline)
    if not pipeline_obj.pipeline_allows_active_ops("scheduled_intraday_scan"):
        _get_logger().info("[Scheduler] INTRADAY scan skipped: pipeline gate blocked.")
        return
    _close_h, _close_m = settings.get_market_close_hour_minute()
    _offset = getattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)
    _cutoff = TimeUtils.now().replace(hour=_close_h, minute=_close_m, second=0) - datetime.timedelta(minutes=_offset)
    if TimeUtils.now() >= _cutoff:
        run_date = TimeUtils.today().isoformat()
        if _pre_close_was_completed(run_date):
            logger.info("[Scheduler] Intraday scan skipped: pre-close scan has already completed for today.")
            return
        else:
            logger.info(
                f"[Scheduler] Intraday scan past cutoff ({_offset}m) but PRE-CLOSE scan not completed yet. "
                "Running intraday scan to maintain continuous data coverage."
            )

    if _signal_auto_execution_enabled():
        today_key = str(TimeUtils.today())
        with _PENDING_ENTRIES_LOCK:
            do_pending = today_key not in _PENDING_ENTRIES_EXECUTED_DATES
            if do_pending:
                _PENDING_ENTRIES_EXECUTED_DATES.add(today_key)
        if do_pending:
            try:
                logger.info("[Scheduler] INTRADAY: executing pending daily entries (once today).")
                pending_fn = _resolve_scheduling_dispatch("execute_pending_daily_entries_for_horus", execute_pending_daily_entries_for_horus)
                pending_fn()
            except Exception as pending_exc:
                logger.error(f"[Scheduler] INTRADAY pending execution error: {pending_exc}")
        else:
            logger.info("[Scheduler] INTRADAY: pending daily entries already executed today, skipping.")

    settings.ENABLE_INTRADAY_ALERTS = settings.TELEGRAM_AUTO_BROADCAST_INTRADAY
    scan_logic = _resolve_scheduling_dispatch("scheduled_scan_logic", scheduled_scan_logic)
    scan_logic(is_intraday=True, scan_label="INTRADAY")
