from core.settings import settings
import os
import sys
import webbrowser
import logging
import datetime

from core import TimeUtils
from core.session_mode import resolve_startup_session_mode
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
from core import scheduling

logger = logging.getLogger("horus.api")


def _has_interactive_console() -> bool:
    stdin = getattr(sys, "stdin", None)
    stdout = getattr(sys, "stdout", None)
    try:
        return bool(stdin and stdout and stdin.isatty() and stdout.isatty())
    except Exception:
        return False


def _startup_prompt(message: str) -> str:
    return input(message)


def _maybe_prompt_to_open_browser(port: int) -> bool:
    frontend_port = int(os.getenv("FRONTEND_PORT", str(port)))
    url = f"http://localhost:{frontend_port}"
    raw = os.getenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        logger.info("[Startup] Browser auto-open skipped (HORUS_DISABLE_BROWSER_AUTO_OPEN).")
        return False

    # For packaged app, always auto-open and never prompt/block on stdin
    if getattr(sys, "frozen", False):
        webbrowser.open(url)
        logger.info(f"[Startup] Browser auto-opened for packaged app at {url}")
        return True

    if not _has_interactive_console():
        logger.info(f"[Startup] Browser launch prompt skipped (no interactive console). Frontend is ready at {url}")
        return False

    response = _startup_prompt(f"Horus is ready at {url}\nOpen frontend in your browser now? [y/N] ").strip().lower()
    if response in ("y", "yes"):
        webbrowser.open(url)
        return True

    logger.info("[Startup] Browser launch declined by user.")
    return False


def _complete_startup_interaction(port: int, start_services) -> bool:
    did_open = _maybe_prompt_to_open_browser(port)
    start_services()
    return did_open


def _resolve_api_port() -> int:
    return _env_int("PORT", 8200)


def _resolve_startup_session_mode() -> dict:
    holiday_dates = set()
    try:
        from database import Holiday
        today = TimeUtils.today()
        if Holiday.select().where(Holiday.date == today).exists():
            holiday_dates.add(today)
    except Exception:
        holiday_dates = set()

    resolution = resolve_startup_session_mode(
        configured_mode=getattr(settings, "SESSION_MODE", ""),
        is_frozen=bool(getattr(sys, "frozen", False)),
        force_session_mode=_env_bool("SESSION_MODE_FORCE", False),
        now=TimeUtils.now(),
        market_start_hhmm=settings._active_market_start(),
        market_end_hhmm=settings._active_market_end(),
        weekend_days=list(getattr(settings, "MARKET_WEEKEND", [4, 5])),
        pre_market_minutes=30,
        holiday_dates=holiday_dates,
    )
    settings.SESSION_MODE = resolution["effective_session_mode"]
    return resolution


def _register_market_watchdog_jobs(scheduler, callback, *, market_open_time):
    scheduler.add_job(
        callback,
        'interval',
        minutes=5,
        id='market_watchdog',
        coalesce=True,
        max_instances=1,
        misfire_grace_time=60,
    )
    scheduler.add_job(
        callback,
        'cron',
        hour=market_open_time.hour,
        minute=market_open_time.minute,
        id='market_watchdog_open',
        misfire_grace_time=300,
        coalesce=True,
        max_instances=1,
    )


def _register_signal_scan_jobs(scheduler):
    try:
        from utils.currency_fetcher import get_parallel_usd_egp_rate
        logger.info("[Startup] Warming parallel market USD/EGP rate cache...")
        rate = get_parallel_usd_egp_rate()
        logger.info(f"[Startup] Parallel market USD/EGP rate cache warmed. Current rate: {rate:.2f}")
    except Exception as e:
        logger.warning(f"[Startup] Failed to warm parallel market rate cache: {e}")

    signal_schedule = scheduling.get_market_signal_schedule()
    scheduler.add_job(
        scheduling.scheduled_intraday_scan,
        'interval',
        minutes=signal_schedule["intraday_interval_mins"],
        id='intraday_scan',
    )
    scheduler.add_job(
        scheduling.scheduled_pre_close_scan,
        'cron',
        hour=signal_schedule["pre_close_dt"].hour,
        minute=signal_schedule["pre_close_dt"].minute,
        id='pre_close_scan',
    )
    scheduler.add_job(
        scheduling.scheduled_daily_signal_scan,
        'cron',
        hour=signal_schedule["daily_signal_dt"].hour,
        minute=signal_schedule["daily_signal_dt"].minute,
        id='daily_signal_scan',
    )
    scheduler.add_job(
        scheduling.scheduled_morning_daily_signal_scan,
        'cron',
        hour=signal_schedule["morning_daily_signal_hour"],
        minute=signal_schedule["morning_daily_signal_minute"],
        id='morning_daily_signal_scan',
    )
    logger.info(
        "[Startup] Signal scan jobs registered: "
        f"intraday every {signal_schedule['intraday_interval_mins']}m, "
        f"pre-close at {signal_schedule['pre_close_dt'].strftime('%H:%M')} "
        f"({signal_schedule['pre_close_offset_mins']}m before close), "
        f"daily preview signal at {signal_schedule['daily_signal_dt'].strftime('%H:%M')} "
        f"({signal_schedule['daily_signal_offset_mins']}m after close), "
        f"morning confirmed daily signal at {signal_schedule['morning_daily_signal_dt'].strftime('%H:%M')}."
    )

    try:
        scheduling.catchup_morning_daily_signal()
    except Exception as catchup_e:
        logger.warning(f"[Startup] Failed to execute morning daily signal catchup: {catchup_e}")

    return signal_schedule


def purge_excluded_tickers():
    try:
        from core.exclusions import get_excluded_tickers_upper, purge_blacklisted_data
        exclusions = get_excluded_tickers_upper()
        if not exclusions:
            return
        logger.info(f"[Startup] Purging {len(exclusions)} excluded tickers from DB...")
        counts = purge_blacklisted_data(exclusions)
        logger.info(f"[Startup] Exclusion purge counts: {counts}")
    except Exception as e:
        logger.error(f"[Startup] Failed to purge excluded tickers: {e}")
