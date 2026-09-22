"""
SCHEDULER CATCHUP & CONFIGURATION
=================================
Startup/wake-up recovery routines, cron reschedule calculators, and missed job triggers.
"""

import datetime
from core.settings import settings
from core import TimeUtils
from utils.logger import setup_logger

from .state import (
    _pre_close_was_completed,
    _mark_pre_close_completed,
    _daily_signal_was_completed,
    _mark_daily_signal_completed,
    _daily_signal_is_pending,
    _mark_daily_signal_pending,
    _ai_daily_report_was_sent,
    _morning_daily_was_completed,
    _daily_signal_run_date,
    _resolve_scheduling_dispatch,
)
from .scans import (
    _background_ops_paused_for_time_travel,
    _run_is_durable_completed,
    _ensure_scheduler_data_ready,
    scheduled_scan_logic,
    scheduled_morning_daily_signal_scan,
)
from .reports import (
    scheduled_daily_ai_report_dispatch,
    scheduled_weekly_analysis_report_dispatch,
    scheduled_monthly_analysis_report_dispatch,
)

logger = setup_logger("horus.scheduling.catchup")

_ORIGINAL_SCHEDULED_SCAN_LOGIC = scheduled_scan_logic
_ORIGINAL_ENSURE_SCHEDULER_DATA_READY = _ensure_scheduler_data_ready


def _get_catchup_dep(name: str):
    import sys
    orig = _ORIGINAL_SCHEDULED_SCAN_LOGIC if name == "scheduled_scan_logic" else _ORIGINAL_ENSURE_SCHEDULER_DATA_READY
    catchup_mod = sys.modules.get("core.scheduling.catchup")
    if catchup_mod is not None and hasattr(catchup_mod, name):
        val = getattr(catchup_mod, name)
        if val is not orig:
            return val
    root_mod = sys.modules.get("core.scheduling")
    if root_mod is not None and hasattr(root_mod, name):
        val = getattr(root_mod, name)
        if val is not orig:
            return val
    return orig


def _scheduler_int_setting(name: str, default: int, *, minimum: int | None = None) -> int:
    try:
        value = int(getattr(settings, name, default))
    except (TypeError, ValueError):
        value = default
    if minimum is not None:
        value = max(minimum, value)
    return value


def get_market_signal_schedule() -> dict:
    close_h, close_m = settings.get_market_close_hour_minute()
    close_dt = datetime.datetime(2000, 1, 1, close_h, close_m)
    pc_offset = _scheduler_int_setting("PRE_CLOSE_OFFSET_MINS", 20, minimum=0)
    ds_offset = _scheduler_int_setting("DAILY_SIGNAL_OFFSET_MINS", 30, minimum=0)
    intraday_interval = _scheduler_int_setting("INTRADAY_INTERVAL_MINS", 5, minimum=1)

    morning_h = _scheduler_int_setting("MORNING_DAILY_SIGNAL_HOUR", 9, minimum=0)
    morning_m = _scheduler_int_setting("MORNING_DAILY_SIGNAL_MINUTE", 30, minimum=0)
    morning_dt = datetime.datetime(2000, 1, 1, morning_h, morning_m)

    return {
        "close_dt": close_dt,
        "close_hour": close_h,
        "close_minute": close_m,
        "pre_close_dt": close_dt - datetime.timedelta(minutes=pc_offset),
        "daily_signal_dt": close_dt + datetime.timedelta(minutes=ds_offset),
        "morning_daily_signal_dt": morning_dt,
        "morning_daily_signal_hour": morning_h,
        "morning_daily_signal_minute": morning_m,
        "pre_close_offset_mins": pc_offset,
        "daily_signal_offset_mins": ds_offset,
        "intraday_interval_mins": intraday_interval,
    }


def reschedule_market_jobs(scheduler=None):
    if scheduler is None:
        logger.debug("[Scheduler] No scheduler instance provided to reschedule_market_jobs; skipping.")
        return
    schedule = get_market_signal_schedule()
    pc_offset = schedule["pre_close_offset_mins"]
    pre_close_dt = schedule["pre_close_dt"]
    ds_offset = schedule["daily_signal_offset_mins"]
    daily_signal_dt = schedule["daily_signal_dt"]
    morning_dt = schedule["morning_daily_signal_dt"]

    try:
        scheduler.reschedule_job('pre_close_scan', trigger='cron', hour=pre_close_dt.hour, minute=pre_close_dt.minute)
        logger.info(f"[Scheduler] Pre-Close scan ({pc_offset}m before) rescheduled to {pre_close_dt.strftime('%H:%M')}")
    except Exception as e:
        logger.warning(f"[Scheduler] Could not reschedule pre_close_scan: {e}")

    try:
        scheduler.reschedule_job('daily_signal_scan', trigger='cron', hour=daily_signal_dt.hour, minute=daily_signal_dt.minute)
        logger.info(f"[Scheduler] Daily Signal scan ({ds_offset}m after) rescheduled to {daily_signal_dt.strftime('%H:%M')}")
    except Exception as e:
        logger.warning(f"[Scheduler] Could not reschedule daily_signal_scan: {e}")

    try:
        scheduler.reschedule_job('morning_daily_signal_scan', trigger='cron', hour=morning_dt.hour, minute=morning_dt.minute)
        logger.info(f"[Scheduler] Morning Daily Signal scan rescheduled to {morning_dt.strftime('%H:%M')}")
    except Exception as e:
        logger.warning(f"[Scheduler] Could not reschedule morning_daily_signal_scan: {e}")

    try:
        intraday_interval = schedule["intraday_interval_mins"]
        scheduler.reschedule_job('intraday_scan', trigger='interval', minutes=intraday_interval)
        logger.info(f"[Scheduler] Intraday scan rescheduled to every {intraday_interval} minutes.")
    except Exception as e:
        logger.warning(f"[Scheduler] Could not reschedule intraday_scan: {e}")


def catchup_morning_daily_signal() -> bool:
    """Startup catch-up for morning daily signal scan if app started before market open."""
    now_dt = TimeUtils.now()
    today_date = TimeUtils.today()

    if today_date.weekday() in settings.MARKET_WEEKEND or settings._is_db_holiday(today_date):
        return False

    current_time_str = now_dt.strftime("%H:%M")
    if current_time_str >= settings.MARKET_START_TIME and not TimeUtils.is_simulating():
        logger.info("[Scheduler] [CATCH-UP] Morning daily signal catchup skipped: market is already open.")
        return False

    target_market_date = settings.get_last_completed_market_day(now_dt)
    run_date_str = target_market_date.isoformat()
    durable_run_key = f"{run_date_str}:DAILY:CONFIRMED"

    if _morning_daily_was_completed(run_date_str) or _run_is_durable_completed(durable_run_key):
        return False

    logger.info(f"[Scheduler] [CATCH-UP] Running morning daily signal catchup for market_date {run_date_str}...")
    return scheduled_morning_daily_signal_scan(market_date=target_market_date)


def maybe_run_pending_daily_signal_after_data_update():
    run_date = _daily_signal_run_date()
    if _daily_signal_was_completed(run_date):
        logger.info(f"[Scheduler] Daily signal data-update hook skipped: already completed for {run_date}.")
        return {"status": "already_completed", "run_date": run_date}
    is_post_market = (
        TimeUtils.now().strftime("%H:%M") >= settings.MARKET_END_TIME
        or not settings.is_market_open()
        or TimeUtils.is_simulating()
    )
    if not _daily_signal_is_pending(run_date) and not is_post_market:
        logger.info(f"[Scheduler] Daily signal data-update hook skipped: no pending report for {run_date}.")
        return {"status": "not_pending", "run_date": run_date}
    if _background_ops_paused_for_time_travel():
        logger.info("[Scheduler] Daily signal data-update hook skipped: time travel/backfill is active.")
        return {"status": "paused", "run_date": run_date}
    ensure_ready_fn = _get_catchup_dep("_ensure_scheduler_data_ready")
    if not ensure_ready_fn("DAILY SIGNAL"):
        _mark_daily_signal_pending(run_date)
        return {"status": "pending", "run_date": run_date}

    scan_logic_fn = _get_catchup_dep("scheduled_scan_logic")
    completed = scan_logic_fn(is_intraday=False, scan_label="DAILY SIGNAL", preview_only=True)
    if completed:
        _mark_daily_signal_completed(run_date)
        from .reports import maybe_dispatch_pending_ai_daily_report_after_data_update
        maybe_dispatch_pending_ai_daily_report_after_data_update()
        return {"status": "completed", "run_date": run_date}
    return {"status": "failed", "run_date": run_date}


def maybe_run_pending_pre_close_signal_after_data_update():
    run_date = TimeUtils.today().isoformat()
    if _pre_close_was_completed(run_date):
        logger.info(f"[Scheduler] Pre-close signal data-update hook skipped: already completed for {run_date}.")
        return {"status": "already_completed", "run_date": run_date}
    if _background_ops_paused_for_time_travel():
        logger.info("[Scheduler] Pre-close signal data-update hook skipped: time travel/backfill is active.")
        return {"status": "paused", "run_date": run_date}
    ensure_ready_fn = _get_catchup_dep("_ensure_scheduler_data_ready")
    if not ensure_ready_fn("PRE-CLOSE"):
        return {"status": "pending", "run_date": run_date}

    scan_logic_fn = _get_catchup_dep("scheduled_scan_logic")
    completed = scan_logic_fn(is_intraday=False, scan_label="PRE-CLOSE")
    if completed:
        _mark_pre_close_completed(run_date)
        return {"status": "completed", "run_date": run_date}
    return {"status": "failed", "run_date": run_date}


def catchup_missed_post_market_jobs() -> dict:
    """Executes any missed post-market jobs (pre-close, daily signal, AI report, weekly/monthly report)."""
    now_dt = TimeUtils.now()
    current_time_str = now_dt.strftime("%H:%M")

    if current_time_str < settings.MARKET_END_TIME and not TimeUtils.is_simulating():
        logger.info("[Scheduler] [CATCH-UP] Skipping post-market catchup before market close.")
        return {
            "status": "skipped",
            "reason": "before_market_close",
            "executed_jobs": [],
        }

    target_market_date = TimeUtils.today()
    run_date = target_market_date.isoformat()

    logger.info(f"[Scheduler] [CATCH-UP] Checking missed post-market jobs for date: {run_date}")
    executed_jobs = []
    schedule = get_market_signal_schedule()
    is_sim = TimeUtils.is_simulating()
    scan_logic_fn = _get_catchup_dep("scheduled_scan_logic")
    ensure_ready_fn = _get_catchup_dep("_ensure_scheduler_data_ready")

    # 1. Pre-close signal scan catch-up (scheduled before market close)
    pre_close_key = f"{run_date}:PRE_CLOSE"
    if not _pre_close_was_completed(run_date) and not _run_is_durable_completed(pre_close_key):
        logger.info("[Scheduler] [CATCH-UP] Running catch-up for PRE-CLOSE signal scan...")
        try:
            completed = scan_logic_fn(is_intraday=False, scan_label="PRE-CLOSE", market_date=target_market_date)
            if completed:
                _mark_pre_close_completed(run_date)
                executed_jobs.append("pre_close_scan")
        except Exception as e:
            logger.error(f"[Scheduler] [CATCH-UP] Pre-close scan catch-up failed: {e}")

    # 2. Daily signal scan (preview) catch-up
    # Only catch up if current time is at or after scheduled time OR in simulation
    daily_signal_time = schedule["daily_signal_dt"].strftime("%H:%M")
    preview_key = f"{run_date}:DAILY:PREVIEW"
    if not _daily_signal_was_completed(run_date) and not _run_is_durable_completed(preview_key):
        if not is_sim and current_time_str < daily_signal_time:
            logger.info(
                f"[Scheduler] [CATCH-UP] DAILY SIGNAL scan is scheduled for {daily_signal_time}; "
                f"skipping premature catch-up at {current_time_str}. Marking as pending."
            )
            _mark_daily_signal_pending(run_date)
        else:
            # Check if today's EOD data is actually ready before running
            if not ensure_ready_fn("DAILY SIGNAL"):
                logger.info(
                    f"[Scheduler] [CATCH-UP] DAILY SIGNAL scan deferred: today's EOD data not ready for {run_date}; "
                    f"marked pending."
                )
                _mark_daily_signal_pending(run_date)
            else:
                logger.info("[Scheduler] [CATCH-UP] Running catch-up for DAILY SIGNAL preview scan...")
                try:
                    completed = scan_logic_fn(is_intraday=False, scan_label="DAILY SIGNAL", market_date=target_market_date, preview_only=True)
                    if completed:
                        _mark_daily_signal_completed(run_date)
                        executed_jobs.append("daily_signal_scan")
                except Exception as e:
                    logger.error(f"[Scheduler] [CATCH-UP] Daily signal scan catch-up failed: {e}")

    # 3. Daily AI report dispatch catch-up
    ai_report_hour = _scheduler_int_setting("AI_REPORT_DISPATCH_HOUR", 15)
    ai_report_minute = _scheduler_int_setting("AI_REPORT_DISPATCH_MINUTE", 0)
    ai_report_time = f"{ai_report_hour:02d}:{ai_report_minute:02d}"
    if not _ai_daily_report_was_sent(run_date):
        if not is_sim and current_time_str < ai_report_time:
            logger.info(
                f"[Scheduler] [CATCH-UP] DAILY AI REPORT is scheduled for {ai_report_time}; "
                f"skipping premature catch-up at {current_time_str}."
            )
        else:
            logger.info("[Scheduler] [CATCH-UP] Running catch-up for DAILY AI REPORT dispatch...")
            try:
                scheduled_daily_ai_report_dispatch(dispatch_source="catchup")
                if _ai_daily_report_was_sent(run_date):
                    executed_jobs.append("daily_ai_report_dispatch")
            except Exception as e:
                logger.error(f"[Scheduler] [CATCH-UP] Daily AI report catch-up failed: {e}")

    # 4. Weekly / Monthly analysis report catch-up
    weekly_hour = _scheduler_int_setting("WEEKLY_REPORT_DISPATCH_HOUR", 15)
    weekly_minute = _scheduler_int_setting("WEEKLY_REPORT_DISPATCH_MINUTE", 10)
    weekly_time = f"{weekly_hour:02d}:{weekly_minute:02d}"
    monthly_hour = _scheduler_int_setting("MONTHLY_REPORT_DISPATCH_HOUR", 15)
    monthly_minute = _scheduler_int_setting("MONTHLY_REPORT_DISPATCH_MINUTE", 20)
    monthly_time = f"{monthly_hour:02d}:{monthly_minute:02d}"
    if is_sim or current_time_str >= weekly_time:
        try:
            scheduled_weekly_analysis_report_dispatch()
        except Exception as e:
            logger.error(f"[Scheduler] [CATCH-UP] Weekly report dispatch catch-up failed: {e}")
    if is_sim or current_time_str >= monthly_time:
        try:
            scheduled_monthly_analysis_report_dispatch()
        except Exception as e:
            logger.error(f"[Scheduler] [CATCH-UP] Monthly report dispatch catch-up failed: {e}")

    summary = {
        "status": "completed",
        "run_date": run_date,
        "executed_jobs": executed_jobs,
    }
    logger.info(f"[Scheduler] [CATCH-UP] Finished post-market catch-up: {summary}")
    return summary
