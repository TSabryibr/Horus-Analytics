"""
SCHEDULING SCANS PRE-CLOSE
==========================
Pre-close preview scan logic, retries, and deadline enforcement.
"""

from __future__ import annotations

import datetime
from core import AlertManager, TimeUtils
from core import pipeline as _pipeline
from core.pipeline import _env_int
from core.settings import settings
from utils.logger import setup_logger

from ..state import (
    _increment_pre_close_retry_count,
    _mark_pre_close_completed,
    _pre_close_was_completed,
    _resolve_scheduling_dispatch,
)
from .deliveries import (
    _background_ops_paused_for_time_travel,
    _ensure_scheduler_data_ready,
)
from .runner import scheduled_scan_logic

logger = setup_logger("horus.scheduling.scans.pre_close")


def _get_logger():
    return _resolve_scheduling_dispatch("logger", logger)


def _pre_close_is_past_hard_deadline() -> bool:
    hard_deadline_mins = max(1, _env_int("PRE_CLOSE_HARD_DEADLINE_MINS", 5))
    close_h, close_m = settings.get_market_close_hour_minute()
    close_dt = TimeUtils.now().replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    deadline_dt = close_dt - datetime.timedelta(minutes=hard_deadline_mins)
    return TimeUtils.now() >= deadline_dt


def _schedule_pre_close_retry(run_date: str, *, reason: str) -> None:
    retry_delay_mins = max(1, _env_int("PRE_CLOSE_RETRY_DELAY_MINS", 2))
    next_run = TimeUtils.now() + datetime.timedelta(minutes=retry_delay_mins)

    close_h, close_m = settings.get_market_close_hour_minute()
    close_dt = TimeUtils.now().replace(hour=close_h, minute=close_m, second=0, microsecond=0)
    if next_run >= close_dt:
        logger.info(
            f"[Scheduler] PRE-CLOSE retry ({reason}) skipped: next run would be past market close."
        )
        return

    try:
        from routes.shared import scheduler as _aps_scheduler
        _aps_scheduler.modify_job(
            'pre_close_scan',
            next_run_time=next_run,
        )
        logger.info(
            f"[Scheduler] PRE-CLOSE retry scheduled in {retry_delay_mins}m "
            f"(reason={reason}, next_run={next_run.strftime('%H:%M:%S')})."
        )
    except Exception as exc:
        logger.warning(
            f"[Scheduler] PRE-CLOSE retry scheduling failed ({reason}): {exc}"
        )


def scheduled_pre_close_scan():
    if _background_ops_paused_for_time_travel():
        _get_logger().info("[Scheduler] PRE-CLOSE scan skipped: time travel/backfill is active.")
        return

    run_date = TimeUtils.today().isoformat()

    if _pre_close_was_completed(run_date):
        _get_logger().info("[Scheduler] PRE-CLOSE scan skipped: already completed today.")
        return

    pipeline_obj = _resolve_scheduling_dispatch("_pipeline", _pipeline)
    if not pipeline_obj.pipeline_allows_active_ops("scheduled_pre_close_scan"):
        _get_logger().info("[Scheduler] PRE-CLOSE scan skipped: pipeline gate blocked.")
        _schedule_pre_close_retry(run_date, reason="pipeline_gate_blocked")
        return

    past_deadline = _pre_close_is_past_hard_deadline()
    if past_deadline:
        _get_logger().warning(
            "[Scheduler] PRE-CLOSE scan: hard deadline reached — firing with available data "
            "(data freshness requirements relaxed)."
        )

    ensure_ready_fn = _resolve_scheduling_dispatch("_ensure_scheduler_data_ready", _ensure_scheduler_data_ready)
    if past_deadline or ensure_ready_fn("PRE-CLOSE"):
        settings.ENABLE_INTRADAY_ALERTS = settings.TELEGRAM_AUTO_BROADCAST_DAILY
        scan_logic = _resolve_scheduling_dispatch("scheduled_scan_logic", scheduled_scan_logic)
        if scan_logic(is_intraday=False, scan_label="PRE-CLOSE"):
            _mark_pre_close_completed(run_date)
    else:
        current_retries = _increment_pre_close_retry_count(run_date)
        max_retries = max(1, _env_int("PRE_CLOSE_MAX_RETRIES", 3))
        if current_retries < max_retries:
            _get_logger().info(
                f"[Scheduler] PRE-CLOSE data not ready (attempt {current_retries}/{max_retries}) — scheduling retry."
            )
            _schedule_pre_close_retry(run_date, reason="data_not_ready")
        else:
            _get_logger().warning(
                f"[Scheduler] PRE-CLOSE scan: all {current_retries} retries exhausted — "
                "data still not ready. Broadcasting admin alert."
            )
            try:
                alert_mgr = _resolve_scheduling_dispatch("AlertManager", AlertManager)
                alert_mgr.broadcast_alert(
                    f"⚠️ Pre-close signal scan failed after {current_retries} retries — "
                    "intraday data still not ready. No pre-close signal was sent today."
                )
            except Exception as alert_exc:
                logger.error(f"[Scheduler] PRE-CLOSE admin alert failed: {alert_exc}")
            return
