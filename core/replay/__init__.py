"""
REPLAY PACKAGE
==============
Modular simulation and backtesting subsystem for Horus Analytics II.
"""

import datetime
import threading

from .state import (
    _REPLAY_STATE,
    _REPLAY_LOCK,
    _REPLAY_STOP_EVENT,
    _REPLAY_THREAD,
    REPLAY_PREFIX,
    _reset_state,
    _parse_market_times,
    _resolve_replay_scanner_profile,
    _run_selected_replay_profile_scan,
    _realm_for_replay_market,
    _get_replay_intraday_availability,
    _format_intraday_availability_error,
    _safe_float,
    _format_duration,
)
from .trades import (
    _get_simulation_portfolio,
    _clear_simulation_portfolio,
    _load_open_replay_positions,
    _summarize_replay_trades,
    _build_risk_sized_replay_trade,
    _create_mock_replay_position,
    _update_mock_position_state,
    _latest_replay_exit_price,
    _close_open_replay_positions_at_end,
    _replay_telegram_config,
    _build_replay_followup_message,
    _broadcast_replay_followup,
    _mock_trade_monitor,
)
from .runner import (
    _empty_pending_replay_result,
    _is_daily_replay_scan,
    _is_pre_close_replay_scan,
    _replay_signal_tickers,
    _record_replay_pre_close_previews,
    _reconcile_replay_pre_close_previews,
    _has_open_replay_trade,
    _has_pending_replay_entry,
    _queue_daily_replay_entry,
    _resolve_pending_replay_gap_pct,
    _latest_replay_open_price,
    _execute_pending_replay_entries,
    _persist_replay_signals,
    _notify_replay_entry,
    _safe_broadcast,
    _safe_broadcast_image,
    _broadcast_replay_signals,
    _generate_replay_report,
    _run_one_tick,
    _replay_worker,
)
from .campaign import (
    _iter_campaign_dates,
    _get_replay_campaign_intraday_availability,
    _format_campaign_availability_error,
    _record_campaign_tick_result,
    _update_campaign_progress,
    _run_replay_campaign_day,
    _replay_campaign_worker,
)


def start_replay(
    replay_date: str,
    speed: int = 10,
    notify: bool = False,
    report: bool = False,
    profile_id: int | None = None,
    use_active_profile: bool = False,
    close_open_positions_end: bool = False,
    live_channel_routing: bool = False,
) -> dict:
    """Start a market replay session."""
    global _REPLAY_THREAD

    if not _REPLAY_LOCK.acquire(blocking=False):
        return {"status": "error", "message": "A replay session is already running."}

    try:
        if _REPLAY_STATE["status"] == "RUNNING":
            return {"status": "error", "message": "Replay already in progress."}

        try:
            parsed_date = datetime.datetime.strptime(replay_date, "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": f"Invalid date format: {replay_date}. Use YYYY-MM-DD."}

        speed = max(1, min(speed, 200))
        try:
            resolved_profile = _resolve_replay_scanner_profile(profile_id=profile_id, use_active_profile=use_active_profile)
        except (LookupError, ValueError) as exc:
            return {"status": "error", "message": str(exc)}

        replay_market = str(getattr(resolved_profile, "market", "EGX30") or "EGX30")
        intraday_availability = _get_replay_intraday_availability(parsed_date, replay_market=replay_market)
        if not intraday_availability.get("available"):
            message = _format_intraday_availability_error(intraday_availability)
            _reset_state()
            _REPLAY_STATE.update({
                "status": "ERROR",
                "date": replay_date,
                "market": replay_market,
                "intraday_availability": intraday_availability,
                "error": message,
            })
            return {
                "status": "error",
                "code": "intraday_data_unavailable",
                "message": message,
                **intraday_availability,
            }

        _reset_state()
        _REPLAY_STATE.update({
            "status": "STARTING",
            "date": replay_date,
            "speed": speed,
            "notify": notify,
            "report": report,
            "close_open_positions_end": close_open_positions_end,
            "live_channel_routing": live_channel_routing,
            "profile_id": getattr(resolved_profile, "id", None),
            "profile_name": getattr(resolved_profile, "profile_name", None),
            "profile_source_type": getattr(resolved_profile, "source_type", None),
            "profile_scope": "DAILY_PHASES_ONLY" if resolved_profile is not None else "HORUS_CORE",
            "market": replay_market,
            "intraday_availability": intraday_availability,
            "use_active_profile": use_active_profile,
            "started_at": datetime.datetime.now().isoformat(),
        })
        _REPLAY_STOP_EVENT.clear()

        _REPLAY_THREAD = threading.Thread(
            target=_replay_worker,
            args=(
                parsed_date,
                speed,
                notify,
                report,
                close_open_positions_end,
                live_channel_routing,
            ),
            daemon=True,
            name="ReplayEngine",
        )
        _REPLAY_THREAD.start()

        return {
            "status": "started",
            "date": replay_date,
            "speed": speed,
            "notify": notify,
            "report": report,
            "close_open_positions_end": close_open_positions_end,
            "live_channel_routing": live_channel_routing,
            "profile_id": getattr(resolved_profile, "id", None),
            "profile_name": getattr(resolved_profile, "profile_name", None),
            "profile_source_type": getattr(resolved_profile, "source_type", None),
            "intraday_availability": intraday_availability,
        }
    finally:
        _REPLAY_LOCK.release()


def start_replay_campaign(
    start_date: str,
    end_date: str,
    speed: int = 10,
    notify: bool = False,
    report: bool = False,
    profile_id: int | None = None,
    use_active_profile: bool = False,
    reset_portfolio: bool = True,
    close_open_positions_end: bool = False,
    include_weekends: bool = False,
    max_days: int = 31,
    allow_missing_intraday_as_holidays: bool = False,
    live_channel_routing: bool = False,
) -> dict:
    """Start a multi-day replay campaign over loaded intraday records."""
    global _REPLAY_THREAD

    if not _REPLAY_LOCK.acquire(blocking=False):
        return {"status": "error", "message": "A replay session is already running."}

    try:
        if _REPLAY_STATE["status"] in {"STARTING", "RUNNING", "STOPPING"}:
            return {"status": "error", "message": "Replay already in progress."}

        try:
            parsed_start = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
            parsed_end = datetime.datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            return {"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."}

        if parsed_end < parsed_start:
            return {"status": "error", "message": "Campaign end_date must be on or after start_date."}

        speed = max(1, min(speed, 200))
        try:
            resolved_profile = _resolve_replay_scanner_profile(profile_id=profile_id, use_active_profile=use_active_profile)
        except (LookupError, ValueError) as exc:
            return {"status": "error", "message": str(exc)}

        replay_market = str(getattr(resolved_profile, "market", "EGX30") or "EGX30")
        intraday_availability = _get_replay_campaign_intraday_availability(
            parsed_start,
            parsed_end,
            replay_market=replay_market,
            include_weekends=include_weekends,
            max_days=max_days,
            allow_missing_intraday_as_holidays=allow_missing_intraday_as_holidays,
        )
        if not intraday_availability.get("available"):
            message = _format_campaign_availability_error(intraday_availability)
            _reset_state()
            _REPLAY_STATE.update({
                "status": "ERROR",
                "mode": "CAMPAIGN",
                "date": start_date,
                "start_date": start_date,
                "end_date": end_date,
                "market": replay_market,
                "intraday_availability": intraday_availability,
                "error": message,
            })
            return {
                "status": "error",
                "code": intraday_availability.get("code", "intraday_campaign_data_unavailable"),
                "message": message,
                **intraday_availability,
            }

        replay_dates = [
            datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
            for date_text in intraday_availability.get("replay_dates", [])
        ]
        _reset_state()
        _REPLAY_STATE.update({
            "status": "STARTING",
            "mode": "CAMPAIGN",
            "date": start_date,
            "start_date": start_date,
            "end_date": end_date,
            "current_date": start_date,
            "speed": speed,
            "notify": notify,
            "report": report,
            "profile_id": getattr(resolved_profile, "id", None),
            "profile_name": getattr(resolved_profile, "profile_name", None),
            "profile_source_type": getattr(resolved_profile, "source_type", None),
            "profile_scope": "DAILY_PHASES_ONLY" if resolved_profile is not None else "HORUS_CORE",
            "market": replay_market,
            "intraday_availability": intraday_availability,
            "use_active_profile": use_active_profile,
            "started_at": datetime.datetime.now().isoformat(),
            "days_total": len(replay_dates),
            "days_completed": 0,
            "current_day_index": 0,
            "replay_dates": [d.isoformat() for d in replay_dates],
            "reset_portfolio": reset_portfolio,
            "close_open_positions_end": close_open_positions_end,
            "allow_missing_intraday_as_holidays": allow_missing_intraday_as_holidays,
            "skipped_holiday_dates": list(intraday_availability.get("skipped_holiday_dates") or []),
            "live_channel_routing": live_channel_routing,
        })
        _REPLAY_STOP_EVENT.clear()

        _REPLAY_THREAD = threading.Thread(
            target=_replay_campaign_worker,
            args=(
                replay_dates,
                speed,
                notify,
                report,
                reset_portfolio,
                close_open_positions_end,
                allow_missing_intraday_as_holidays,
                live_channel_routing,
            ),
            daemon=True,
            name="ReplayCampaignEngine",
        )
        _REPLAY_THREAD.start()

        return {
            "status": "started",
            "mode": "CAMPAIGN",
            "start_date": start_date,
            "end_date": end_date,
            "speed": speed,
            "notify": notify,
            "report": report,
            "reset_portfolio": reset_portfolio,
            "close_open_positions_end": close_open_positions_end,
            "allow_missing_intraday_as_holidays": allow_missing_intraday_as_holidays,
            "live_channel_routing": live_channel_routing,
            "skipped_holiday_dates": list(intraday_availability.get("skipped_holiday_dates") or []),
            "days_total": len(replay_dates),
            "replay_dates": [d.isoformat() for d in replay_dates],
            "profile_id": getattr(resolved_profile, "id", None),
            "profile_name": getattr(resolved_profile, "profile_name", None),
            "profile_source_type": getattr(resolved_profile, "source_type", None),
            "intraday_availability": intraday_availability,
        }
    finally:
        _REPLAY_LOCK.release()


def stop_replay() -> dict:
    """Force-stop the current replay session."""
    if _REPLAY_STATE["status"] not in {"RUNNING", "STARTING"}:
        return {"status": "noop", "message": "No active replay to stop."}

    _REPLAY_STOP_EVENT.set()
    _REPLAY_STATE["status"] = "STOPPING"

    return {"status": "stopping", "message": "Replay stop requested."}


def get_replay_status() -> dict:
    """Get the current replay session status."""
    state_copy = dict(_REPLAY_STATE)
    if "unique_signals" in state_copy and isinstance(state_copy["unique_signals"], set):
        state_copy["unique_signals"] = list(state_copy["unique_signals"])
    state_copy["pending_entries_count"] = len(state_copy.get("pending_entries") or [])
    return state_copy


__all__ = [
    "REPLAY_PREFIX",
    "_REPLAY_STATE",
    "_REPLAY_LOCK",
    "_REPLAY_THREAD",
    "_REPLAY_STOP_EVENT",
    "_reset_state",
    "_parse_market_times",
    "_resolve_replay_scanner_profile",
    "_run_selected_replay_profile_scan",
    "_realm_for_replay_market",
    "_get_replay_intraday_availability",
    "_format_intraday_availability_error",
    "_safe_float",
    "_format_duration",
    "_get_simulation_portfolio",
    "_clear_simulation_portfolio",
    "_load_open_replay_positions",
    "_summarize_replay_trades",
    "_build_risk_sized_replay_trade",
    "_create_mock_replay_position",
    "_update_mock_position_state",
    "_latest_replay_exit_price",
    "_close_open_replay_positions_at_end",
    "_replay_telegram_config",
    "_build_replay_followup_message",
    "_broadcast_replay_followup",
    "_mock_trade_monitor",
    "_empty_pending_replay_result",
    "_is_daily_replay_scan",
    "_is_pre_close_replay_scan",
    "_replay_signal_tickers",
    "_record_replay_pre_close_previews",
    "_reconcile_replay_pre_close_previews",
    "_has_open_replay_trade",
    "_has_pending_replay_entry",
    "_queue_daily_replay_entry",
    "_resolve_pending_replay_gap_pct",
    "_latest_replay_open_price",
    "_execute_pending_replay_entries",
    "_persist_replay_signals",
    "_notify_replay_entry",
    "_safe_broadcast",
    "_safe_broadcast_image",
    "_broadcast_replay_signals",
    "_generate_replay_report",
    "_run_one_tick",
    "_replay_worker",
    "_iter_campaign_dates",
    "_get_replay_campaign_intraday_availability",
    "_format_campaign_availability_error",
    "_record_campaign_tick_result",
    "_update_campaign_progress",
    "_run_replay_campaign_day",
    "_replay_campaign_worker",
    "start_replay",
    "start_replay_campaign",
    "stop_replay",
    "get_replay_status",
]
