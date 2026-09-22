"""
SESSION MODE MANAGER
====================
Automatic detection and runtime transitions between LIVE and ANALYSIS modes.

LIVE mode:   Connects to intraday live feed, continuously syncs data.
ANALYSIS mode: Loads history data once at startup, then idles.

Auto-boot rules:
    - LIVE   if app starts 30 min before market open → market close, on trading days
    - ANALYSIS otherwise (after hours, weekends)

Runtime transitions are driven by APScheduler cron jobs registered in api.py.
"""

import datetime
import logging

logger = logging.getLogger("horus.session_mode")


settings = None
LiveFeedManager = None


def _get_settings():
    if settings is not None:
        return settings
    from core.settings import settings as _settings
    return _settings


def _get_live_feed_manager():
    if LiveFeedManager is not None:
        return LiveFeedManager
    from core.market.LiveFeedManager import LiveFeedManager as _lfm
    return _lfm




# ---------------------------------------------------------------------------
# Pure compute — no side effects, fully testable
# ---------------------------------------------------------------------------


def compute_session_mode(
    now: datetime.datetime,
    market_start_hhmm: str,
    market_end_hhmm: str,
    weekend_days: list[int],
    pre_market_minutes: int = 30,
    holiday_dates: set[datetime.date] | None = None,
) -> str:
    """Determine the session mode from the current time and market schedule.

    Returns ``"LIVE"`` when *now* falls within the live window on a trading
    day, ``"ANALYSIS"`` otherwise.

    Parameters
    ----------
    now : datetime.datetime
        Current local datetime.
    market_start_hhmm : str
        Market open time in ``"HHMM"`` format (e.g. ``"1000"``).
    market_end_hhmm : str
        Market close time in ``"HHMM"`` format (e.g. ``"1430"``).
    weekend_days : list[int]
        ``datetime.weekday()`` values that are non-trading days.
    pre_market_minutes : int
        Minutes before market open to enter LIVE mode.
    """
    # Weekend → always ANALYSIS
    if now.weekday() in weekend_days:
        return "ANALYSIS"
    if holiday_dates and now.date() in holiday_dates:
        return "ANALYSIS"

    # Parse market times
    start_hhmm = str(market_start_hhmm).strip().zfill(4)
    end_hhmm = str(market_end_hhmm).strip().zfill(4)

    market_open = now.replace(
        hour=int(start_hhmm[:2]),
        minute=int(start_hhmm[2:]),
        second=0,
        microsecond=0,
    )
    market_close = now.replace(
        hour=int(end_hhmm[:2]),
        minute=int(end_hhmm[2:]),
        second=0,
        microsecond=0,
    )

    live_window_start = market_open - datetime.timedelta(minutes=pre_market_minutes)

    if live_window_start <= now <= market_close:
        return "LIVE"

    return "ANALYSIS"


def resolve_startup_session_mode(
    configured_mode: str | None,
    *,
    is_frozen: bool,
    force_session_mode: bool,
    now: datetime.datetime,
    market_start_hhmm: str,
    market_end_hhmm: str,
    weekend_days: list[int],
    pre_market_minutes: int = 30,
    holiday_dates: set[datetime.date] | None = None,
) -> dict:
    """Resolve configured and effective startup session modes.

    Packaged runs default to market-time auto-detection unless an explicit
    force flag is present. Source/dev runs keep the configured mode when it is
    valid, preserving existing testing workflows.
    """

    normalized_configured = str(configured_mode or "").strip().upper()
    configured_valid = normalized_configured in {"LIVE", "ANALYSIS"}

    auto_mode = compute_session_mode(
        now,
        market_start_hhmm,
        market_end_hhmm,
        weekend_days,
        pre_market_minutes=pre_market_minutes,
        holiday_dates=holiday_dates,
    )

    if configured_valid:
        resolved_configured = normalized_configured
    else:
        resolved_configured = auto_mode

    if force_session_mode:
        effective_mode = resolved_configured
        reason = "forced_configured_mode"
    elif is_frozen:
        effective_mode = auto_mode
        reason = "live_window" if auto_mode == "LIVE" else "market_closed"
    elif configured_valid:
        effective_mode = resolved_configured
        reason = "configured_mode"
    else:
        effective_mode = auto_mode
        reason = "auto_detected_invalid_configured_mode"

    return {
        "configured_session_mode": resolved_configured,
        "effective_session_mode": effective_mode,
        "forced_mode": bool(force_session_mode),
        "reason": reason,
        "is_frozen": bool(is_frozen),
        "auto_session_mode": auto_mode,
    }


# ---------------------------------------------------------------------------
# Transition handler — applies mode change with side effects
# ---------------------------------------------------------------------------


def apply_mode_transition(target_mode: str) -> dict:
    """Switch ``SESSION_MODE`` to *target_mode* and start/stop the live feed.

    Returns a dict summarising what happened.
    """
    settings = _get_settings()
    LiveFeedManager = _get_live_feed_manager()

    target_mode = target_mode.strip().upper()
    if target_mode not in {"LIVE", "ANALYSIS"}:
        raise ValueError(f"Invalid session mode: {target_mode!r}")

    current_mode = settings.SESSION_MODE

    if current_mode == target_mode:
        logger.info(
            "[SessionMode] Already in %s mode — no transition needed.", target_mode
        )
        return {
            "status": "noop",
            "mode": target_mode,
            "message": f"Already in {target_mode} mode.",
        }

    logger.info(
        "[SessionMode] Transitioning %s → %s", current_mode, target_mode
    )
    settings.SESSION_MODE = target_mode

    if target_mode == "LIVE":
        try:
            from utils.power import set_market_keepalive
            set_market_keepalive(True)
        except Exception as p_err:
            logger.warning("[SessionMode] Failed to engage keep-alive: %s", p_err)
        # Start the live ZMQ feed if market is open
        if settings.is_market_open() and not LiveFeedManager.is_running():
            try:
                LiveFeedManager.start_monitoring()
                logger.info("[SessionMode] LiveFeedManager started.")
            except Exception as e:
                logger.error("[SessionMode] Failed to start LiveFeedManager: %s", e)
    elif target_mode == "ANALYSIS":
        try:
            from utils.power import set_market_keepalive
            set_market_keepalive(False)
        except Exception as p_err:
            logger.warning("[SessionMode] Failed to release keep-alive: %s", p_err)
        # Stop the live feed if running
        if LiveFeedManager.is_running():
            try:
                LiveFeedManager.stop_monitoring()
                logger.info("[SessionMode] LiveFeedManager stopped.")
            except Exception as e:
                logger.error("[SessionMode] Failed to stop LiveFeedManager: %s", e)

    message = f"Session mode transitioned from {current_mode} to {target_mode}."
    logger.info("[SessionMode] %s", message)
    return {"status": "transitioned", "from": current_mode, "to": target_mode, "message": message}


# ---------------------------------------------------------------------------
# Scheduler callbacks — invoked by APScheduler cron jobs
# ---------------------------------------------------------------------------


def scheduled_enter_live_mode() -> None:
    """Cron callback: switch to LIVE mode at pre-market time on trading days."""
    from core import TimeUtils
    settings = _get_settings()

    now = TimeUtils.now()

    # Safety: skip if today is a weekend day
    if now.weekday() in settings.MARKET_WEEKEND:
        logger.info("[SessionMode] Skipping LIVE transition - weekend day.")
        return
    if settings._is_db_holiday(now.date()):
        logger.info("[SessionMode] Skipping LIVE transition - registered holiday.")
        return

    result = apply_mode_transition("LIVE")
    logger.info("[SessionMode] scheduled_enter_live_mode result: %s", result)


def scheduled_enter_analysis_mode() -> None:
    """Cron callback: switch to ANALYSIS mode at market close."""
    settings = _get_settings()
    result = apply_mode_transition("ANALYSIS")
    logger.info("[SessionMode] scheduled_enter_analysis_mode result: %s", result)
    try:
        from core.scheduling import catchup_missed_post_market_jobs
        catchup_missed_post_market_jobs()
    except Exception as catchup_e:
        logger.error(f"[SessionMode] Post-market catchup error on ANALYSIS mode enter: {catchup_e}")
