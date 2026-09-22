"""
SCHEDULING SCANS DAILY
======================
Daily post-market confirmation scan, morning daily scan, and daily signal pipeline.
"""

from __future__ import annotations

import datetime
import os
from fastapi import HTTPException

from core import TimeUtils
from core import pipeline as _pipeline
from core.pipeline import _env_bool, _env_int
from core.settings import settings
from database import SignalDelivery
from routes import signals
from utils.logger import setup_logger

from ..state import (
    _daily_signal_was_completed,
    _mark_daily_signal_completed,
    _mark_morning_daily_completed,
    _morning_daily_was_completed,
    _resolve_scheduling_dispatch,
)
from .deliveries import (
    _background_ops_paused_for_time_travel,
    _completed_daily_signal_run_has_results,
    _ensure_scheduler_data_ready,
    _run_is_durable_completed,
    _scheduler_run_key,
)
from .runner import scheduled_scan_logic

logger = setup_logger("horus.scheduling.scans.daily")


def _get_logger():
    return _resolve_scheduling_dispatch("logger", logger)


def scheduled_daily_signal_scan(market_date: datetime.date | None = None):
    if _background_ops_paused_for_time_travel():
        _get_logger().info("[Scheduler] DAILY SIGNAL scan skipped: time travel/backfill is active.")
        return
    pipeline_obj = _resolve_scheduling_dispatch("_pipeline", _pipeline)
    if pipeline_obj.pipeline_allows_active_ops("scheduled_daily_signal_scan"):
        now_dt = TimeUtils.now()
        market_date_val = market_date or settings.get_last_completed_market_day(now_dt)
        run_date_str = market_date_val.isoformat()
        preview_run_key = _scheduler_run_key("DAILY SIGNAL", is_intraday=False, market_date=market_date_val, preview_only=True)
        confirmed_run_key = _scheduler_run_key("DAILY SIGNAL", is_intraday=False, market_date=market_date_val, preview_only=False)

        if (
            _completed_daily_signal_run_has_results(preview_run_key)
            or _completed_daily_signal_run_has_results(confirmed_run_key)
            or _run_is_durable_completed(preview_run_key)
            or _run_is_durable_completed(confirmed_run_key)
            or _daily_signal_was_completed(run_date_str)
        ):
            _get_logger().info(
                f"[Scheduler] DAILY SIGNAL scan skipped: completed run already exists for date {run_date_str}."
            )
            _mark_daily_signal_completed(run_date_str)
            from ..reports import maybe_dispatch_pending_ai_daily_report_after_data_update
            maybe_dispatch_pending_ai_daily_report_after_data_update()
            return
        ensure_ready_fn = _resolve_scheduling_dispatch("_ensure_scheduler_data_ready", _ensure_scheduler_data_ready)
        if not ensure_ready_fn("DAILY SIGNAL"):
            _get_logger().info("[Scheduler] DAILY SIGNAL scan skipped: data not ready; report marked pending.")
            return
        scan_logic = _resolve_scheduling_dispatch("scheduled_scan_logic", scheduled_scan_logic)
        if scan_logic(is_intraday=False, scan_label="DAILY SIGNAL", market_date=market_date_val, preview_only=True):
            _mark_daily_signal_completed(run_date_str)
            from ..reports import maybe_dispatch_pending_ai_daily_report_after_data_update
            maybe_dispatch_pending_ai_daily_report_after_data_update()
    else:
        _get_logger().info("[Scheduler] DAILY SIGNAL scan skipped: pipeline gate blocked.")


def scheduled_morning_daily_signal_scan(market_date: datetime.date | None = None) -> bool:
    bg_paused_fn = _resolve_scheduling_dispatch("_background_ops_paused_for_time_travel", _background_ops_paused_for_time_travel)
    if bg_paused_fn():
        logger.info("[Scheduler] MORNING DAILY SIGNAL scan skipped: time travel/backfill is active.")
        return False
    pipeline_obj = _resolve_scheduling_dispatch("_pipeline", _pipeline)
    if not pipeline_obj.pipeline_allows_active_ops("scheduled_morning_daily_signal_scan"):
        logger.info("[Scheduler] MORNING DAILY SIGNAL scan skipped: pipeline gate blocked.")
        return False

    time_utils = _resolve_scheduling_dispatch("TimeUtils", TimeUtils)
    current_settings = _resolve_scheduling_dispatch("settings", settings)
    now_dt = time_utils.now()
    today_date = time_utils.today()

    if today_date.weekday() in current_settings.MARKET_WEEKEND or current_settings._is_db_holiday(today_date):
        logger.info("[Scheduler] MORNING DAILY SIGNAL scan skipped: non-trading day (weekend/holiday).")
        return False

    current_time_str = now_dt.strftime("%H:%M")
    if current_time_str >= current_settings.MARKET_START_TIME and not time_utils.is_simulating():
        logger.info(
            f"[Scheduler] MORNING DAILY SIGNAL scan skipped: market is already open ({current_time_str} >= {current_settings.MARKET_START_TIME})."
        )
        return False

    target_market_date = market_date or current_settings.get_last_completed_market_day(now_dt)
    run_date_str = target_market_date.isoformat()
    durable_run_key = f"{run_date_str}:DAILY:CONFIRMED"

    run_durable_fn = _resolve_scheduling_dispatch("_run_is_durable_completed", _run_is_durable_completed)
    if _morning_daily_was_completed(run_date_str) or run_durable_fn(durable_run_key):
        logger.info(f"[Scheduler] MORNING DAILY SIGNAL scan skipped: already completed for {run_date_str} ({durable_run_key}).")
        _mark_morning_daily_completed(run_date_str)
        return False

    logger.info(f"[Scheduler] Running MORNING DAILY SIGNAL scan for market_date: {run_date_str}")
    scan_logic = _resolve_scheduling_dispatch("scheduled_scan_logic", scheduled_scan_logic)
    completed = scan_logic(
        scan_type="DAILY_SIGNAL",
        scan_label="DAILY SIGNAL",
        is_intraday=False,
        is_pre_close=False,
        market_date=target_market_date,
        is_retry=False,
        preview_only=False,
        run_key=durable_run_key,
    )
    if completed:
        _mark_morning_daily_completed(run_date_str)
        logger.info(f"[Scheduler] MORNING DAILY SIGNAL scan completed successfully for market_date: {run_date_str}")
        return True
    return False


def scheduled_daily_signal_pipeline():
    if not _env_bool("SIGNAL_AUTO_DAILY_ENABLED", True):
        return
    if not _pipeline.pipeline_allows_active_ops("scheduled_daily_signal_pipeline"):
        return
    try:
        run_date = TimeUtils.today().strftime("%Y-%m-%d")
        run_req = signals.DailyRunRequest(
            run_date=run_date,
            scan_type="DAILY",
            force=False,
            notify=_env_bool("SIGNAL_AUTO_NOTIFY", False),
            index=os.getenv("SIGNAL_AUTO_INDEX", "EGX30"),
            model_version=os.getenv("SIGNAL_MODEL_VERSION", "v1"),
        )
        run_result = signals.run_daily_signals_logic(run_req)
        run = run_result.get("run") or {}
        run_id = run.get("id")
        status = run_result.get("status")
        logger.info(f"[Signals] Daily run status={status} run_id={run_id} date={run_date}")

        if not run_id or status == "blocked":
            return

        desk = signals._get_signal_desk_state()
        if str(desk.operating_mode or "MANUAL").upper() == "AUTOPILOT" and desk.autopilot_armed:
            autopilot_result = signals.trigger_signal_desk_autopilot_logic(
                signals.SignalDeskAutopilotRequest(
                    run_id=run_id,
                    dry_run=_env_bool("SIGNAL_AUTO_PUBLISH_DRY_RUN", False),
                    max_retries=_env_int("SIGNAL_PUBLISH_RETRIES", 2),
                    backoff_ms=_env_int("SIGNAL_PUBLISH_BACKOFF_MS", 500),
                    enforce_window=True,
                    ignore_guard=False,
                )
            )
            logger.info(f"[Signals] Desk autopilot status={autopilot_result.get('status')} run_id={run_id}")
            return

        if not _env_bool("SIGNAL_AUTO_PUBLISH_ENABLED", True):
            return

        already_sent = SignalDelivery.select().where(
            (SignalDelivery.run == run_id) & (SignalDelivery.status == "SENT")
        ).count()
        if already_sent > 0 and status == "existing":
            logger.info(f"[Signals] Skipping republish for existing run {run_id}; sent deliveries={already_sent}")
            return

        publish_req = signals.PublishSignalsRequest(
            run_id=run_id,
            channel="TELEGRAM",
            dry_run=_env_bool("SIGNAL_AUTO_PUBLISH_DRY_RUN", False),
            max_retries=_env_int("SIGNAL_PUBLISH_RETRIES", 2),
            backoff_ms=_env_int("SIGNAL_PUBLISH_BACKOFF_MS", 500),
            enforce_window=True,
        )
        publish_result = signals.publish_signal_run_logic(publish_req)
        logger.info(f"[Signals] Publish summary: {publish_result.get('summary')}")
        from ..reports import scheduled_managed_advisory_dispatch
        scheduled_managed_advisory_dispatch()
    except HTTPException as he:
        logger.warning(f"[Signals] Pipeline blocked/failed: {he.detail}")
    except Exception as e:
        logger.error(f"[Signals] Pipeline error: {e}")
