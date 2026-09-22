import os
import sys
import datetime as _dt
import logging
import threading
from apscheduler.jobstores.base import JobLookupError

from core.settings import settings as core_settings
from core import scheduling
from core.pipeline import _env_bool, _env_int
from database import db

logger = logging.getLogger("horus.api")


def _wal_checkpoint():
    """Periodic SQLite WAL checkpoint to compact the WAL file."""
    try:
        logger.info("[WAL] Executing passive WAL checkpoint")
        db.execute_sql("PRAGMA wal_checkpoint(PASSIVE)")
        logger.info("[WAL] Passive WAL checkpoint completed successfully")
    except Exception as e:
        logger.warning(f"[WAL] Passive WAL checkpoint failed: {e}")


def register_scheduled_jobs(scheduler) -> None:
    if scheduler.running:
        return

    import api

    last_watchdog_state: bool | None = None

    def scheduled_market_watchdog():
        nonlocal last_watchdog_state

        market_is_open = core_settings.is_market_open()

        if market_is_open:
            try:
                from core.market.feed_watchdog import MarketFeedWatchdog
                MarketFeedWatchdog.check_and_heal()
            except Exception as w_exc:
                logger.error(f"[Watchdog] Feed watchdog check_and_heal failed: {w_exc}")

        if market_is_open == last_watchdog_state:
            return

        last_watchdog_state = market_is_open
        market_jobs = ['intraday_scan', 'trade_monitor', 'signal_delivery_retry']

        for job_id in market_jobs:
            try:
                if market_is_open:
                    scheduler.resume_job(job_id)
                else:
                    scheduler.pause_job(job_id)
            except JobLookupError:
                pass

        if market_is_open:
            logger.info("[Watchdog] Market opened. Heavy background tasks resumed.")
        else:
            logger.info("[Watchdog] Market closed. Heavy background tasks paused.")
            try:
                scheduling.catchup_missed_post_market_jobs()
            except Exception as catchup_e:
                logger.error(f"[Watchdog] Post-market catchup failed: {catchup_e}")

    _start_h_str = core_settings._active_market_start().zfill(4)
    _market_open_time = _dt.time(int(_start_h_str[:2]), int(_start_h_str[2:]))
    api._register_market_watchdog_jobs(
        scheduler,
        scheduled_market_watchdog,
        market_open_time=_market_open_time,
    )
    _signal_schedule = api._register_signal_scan_jobs(scheduler)
    _close_dt = _signal_schedule["close_dt"]
    _close_h = _signal_schedule["close_hour"]
    _close_m = _signal_schedule["close_minute"]
    _trade_monitor_interval_sec = _env_int("TRADE_MONITOR_INTERVAL_SEC", 30)
    _trade_monitor_max_instances = max(1, _env_int("TRADE_MONITOR_MAX_INSTANCES", 2))

    scheduler.add_job(
        scheduling.scheduled_trade_monitor,
        'interval',
        seconds=_trade_monitor_interval_sec,
        id='trade_monitor',
        misfire_grace_time=_env_int("TRADE_MONITOR_MISFIRE_GRACE_SEC", 30),
        coalesce=True,
        max_instances=_trade_monitor_max_instances,
    )
    scheduler.add_job(
        scheduling.scheduled_followup_processing,
        'interval',
        seconds=30,
        id='followup_processing',
        misfire_grace_time=30,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_daily_signal_pipeline,
        'cron',
        hour=_env_int("SIGNAL_DAILY_RUN_HOUR", 14),
        minute=_env_int("SIGNAL_DAILY_RUN_MINUTE", 45),
        id='signal_daily_pipeline',
        misfire_grace_time=_env_int("SIGNAL_DAILY_MISFIRE_GRACE_SEC", 300),
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_failed_delivery_retry,
        'interval',
        minutes=_env_int("SIGNAL_RETRY_INTERVAL_MINUTES", 10),
        id='signal_delivery_retry',
        misfire_grace_time=_env_int("SIGNAL_RETRY_MISFIRE_GRACE_SEC", 30),
        coalesce=True,
        max_instances=1,
    )
    if _env_bool("HORUS_MANAGED_ADVISORY_ENABLED", False):
        scheduler.add_job(
            scheduling.scheduled_managed_advisory_dispatch,
            'cron',
            hour=_env_int("HORUS_MANAGED_ADVISORY_HOUR", 15),
            minute=_env_int("HORUS_MANAGED_ADVISORY_MINUTE", 30),
            id='managed_advisory_dispatch',
            misfire_grace_time=300,
            coalesce=True,
            max_instances=1,
        )
    scheduler.add_job(
        scheduling.scheduled_weekly_walkforward_validation,
        'cron',
        day_of_week=os.getenv("SIGNAL_WALKFORWARD_DAY_OF_WEEK", "sun"),
        hour=_env_int("SIGNAL_WALKFORWARD_HOUR", 16),
        minute=_env_int("SIGNAL_WALKFORWARD_MINUTE", 30),
        id='signal_walkforward_validation',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_wfa_metrics_update,
        'cron',
        day_of_week='sat',
        hour=1,
        minute=0,
        id='wfa_metrics_update',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_system_audit,
        'cron',
        hour=1,
        minute=15,
        id='system_audit',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_daily_database_backup,
        'cron',
        hour=_env_int("DATABASE_BACKUP_HOUR", 15),
        minute=_env_int("DATABASE_BACKUP_MINUTE", 45),
        id='database_daily_backup',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_daily_ai_report_dispatch,
        'cron',
        hour=_env_int("AI_REPORT_DISPATCH_HOUR", 15),
        minute=_env_int("AI_REPORT_DISPATCH_MINUTE", 0),
        id='ai_daily_report_dispatch',
        misfire_grace_time=_env_int("AI_REPORT_DISPATCH_MISFIRE_GRACE_SEC", 120),
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_weekly_analysis_report_dispatch,
        'cron',
        hour=_env_int("WEEKLY_REPORT_DISPATCH_HOUR", 15),
        minute=_env_int("WEEKLY_REPORT_DISPATCH_MINUTE", 10),
        id='analysis_weekly_dispatch',
        misfire_grace_time=_env_int("WEEKLY_REPORT_DISPATCH_MISFIRE_GRACE_SEC", 120),
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduling.scheduled_monthly_analysis_report_dispatch,
        'cron',
        hour=_env_int("MONTHLY_REPORT_DISPATCH_HOUR", 15),
        minute=_env_int("MONTHLY_REPORT_DISPATCH_MINUTE", 20),
        id='analysis_monthly_dispatch',
        misfire_grace_time=_env_int("MONTHLY_REPORT_DISPATCH_MISFIRE_GRACE_SEC", 120),
        coalesce=True,
        max_instances=1,
    )

    from core.session_mode import scheduled_enter_live_mode, scheduled_enter_analysis_mode
    _start_dt = _dt.datetime(2000, 1, 1, int(_start_h_str[:2]), int(_start_h_str[2:]))
    _pre_market_dt = _start_dt - _dt.timedelta(minutes=30)
    _trading_dow = 'sun,mon,tue,wed,thu'
    scheduler.add_job(
        scheduled_enter_live_mode,
        'cron',
        day_of_week=_trading_dow,
        hour=_pre_market_dt.hour,
        minute=_pre_market_dt.minute,
        id='session_enter_live',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        scheduled_enter_analysis_mode,
        'cron',
        hour=_close_h,
        minute=_close_m,
        id='session_enter_analysis',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        _wal_checkpoint,
        'interval',
        minutes=30,
        id='wal_checkpoint',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
        replace_existing=True,
    )

    if (
        os.getenv("ENABLE_EMBEDDED_MUBASHER_HARVESTER", "false").lower() == "true"
        and "pytest" not in sys.modules
        and "PYTEST_CURRENT_TEST" not in os.environ
        and (core_settings.LOCAL_INTRADAY_PROVIDER == "MUBASHER_DB" or core_settings.LOCAL_HISTORY_PROVIDER == "MUBASHER_DB")
    ):
        try:
            from data_engine.mubasher_extractor import perform_extraction
            threading.Thread(target=perform_extraction, daemon=True, name="MubasherInitialExtraction").start()
            scheduler.add_job(
                perform_extraction,
                'interval',
                minutes=5,
                id='mubasher_extractor',
                misfire_grace_time=300,
                coalesce=True,
                max_instances=1,
                replace_existing=True,
            )
            logger.info("[Startup] Registered Mubasher shadow-copy extraction job (every 5m).")
        except Exception as e:
            logger.error(f"[Startup] Failed to register Mubasher extraction job: {e}")

    logger.info(
        "[Startup] Session mode jobs registered: "
        f"LIVE at {_pre_market_dt.strftime('%H:%M')} (trading days), "
        f"ANALYSIS at {_close_dt.strftime('%H:%M')}."
    )
    scheduler.start()
    logger.info("[Startup] Scheduler Started. Periodic WAL checkpoints registered.")
    scheduling.start_edge_pipeline_watcher()
