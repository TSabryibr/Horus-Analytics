"""
REPLAY CAMPAIGN
===============
Multi-day replay campaign orchestration, availability checks, and multi-day aggregation.
"""

import datetime
import time
import traceback
from typing import Any

from core.settings import settings
from utils.logger import setup_logger
from .state import (
    _REPLAY_STATE,
    _REPLAY_STOP_EVENT,
    REPLAY_PREFIX,
    _realm_for_replay_market,
    _parse_market_times,
    _resolve_replay_scanner_profile,
    _format_duration,
    _resolve_dispatch,
    _get_timeutils,
    _get_logger,
)
from .trades import (
    _clear_simulation_portfolio,
    _load_open_replay_positions,
    _summarize_replay_trades,
    _close_open_replay_positions_at_end,
    _replay_telegram_config,
)
from .runner import _run_one_tick, _generate_replay_report

logger = setup_logger("horus.replay.campaign")


def _iter_campaign_dates(
    start_date: datetime.date,
    end_date: datetime.date,
    include_weekends: bool = False,
) -> list[datetime.date]:
    dates = []
    current = start_date
    while current <= end_date:
        if include_weekends or current.weekday() not in {4, 5}:
            dates.append(current)
        current += datetime.timedelta(days=1)
    return dates


def _get_replay_campaign_intraday_availability(
    start_date: datetime.date,
    end_date: datetime.date,
    replay_market: str = "EGX30",
    include_weekends: bool = False,
    max_days: int = 31,
    allow_missing_intraday_as_holidays: bool = False,
) -> dict:
    """Return campaign-level intraday availability for every requested trading day."""
    target = _resolve_dispatch("_get_replay_campaign_intraday_availability", None)
    if target is not None and target is not _get_replay_campaign_intraday_availability:
        return target(
            start_date,
            end_date,
            replay_market=replay_market,
            include_weekends=include_weekends,
            max_days=max_days,
            allow_missing_intraday_as_holidays=allow_missing_intraday_as_holidays,
        )

    from data_engine import intraday_store

    realm = _realm_for_replay_market(replay_market)
    date_counts = intraday_store.get_intraday_date_counts(realm=realm)
    counts_by_date = {str(row["date"]): row for row in date_counts if row.get("date")}
    available_dates = sorted(counts_by_date)
    requested_dates = _iter_campaign_dates(start_date, end_date, include_weekends=include_weekends)
    requested_iso = [d.isoformat() for d in requested_dates]
    replay_dates = [
        date_text
        for date_text in requested_iso
        if int(counts_by_date.get(date_text, {}).get("records") or 0) > 0
    ]
    missing_dates = [date_text for date_text in requested_iso if date_text not in replay_dates]
    skipped_holiday_dates = list(missing_dates) if allow_missing_intraday_as_holidays else []
    available = bool(replay_dates) and (not missing_dates or allow_missing_intraday_as_holidays)

    if len(replay_dates) > max_days:
        return {
            "available": False,
            "code": "intraday_campaign_range_too_large",
            "realm": realm,
            "market": replay_market,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days_total": len(replay_dates),
            "max_days": max_days,
            "replay_dates": replay_dates,
            "missing_dates": missing_dates,
            "skipped_holiday_dates": skipped_holiday_dates,
            "allow_missing_intraday_as_holidays": allow_missing_intraday_as_holidays,
            "available_start_date": available_dates[0] if available_dates else None,
            "available_end_date": available_dates[-1] if available_dates else None,
        }

    return {
        "available": available,
        "code": "ok" if available else "intraday_campaign_data_unavailable",
        "realm": realm,
        "market": replay_market,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days_total": len(replay_dates),
        "requested_days_total": len(requested_iso),
        "replay_dates": replay_dates,
        "missing_dates": missing_dates,
        "skipped_holiday_dates": skipped_holiday_dates,
        "allow_missing_intraday_as_holidays": allow_missing_intraday_as_holidays,
        "available_start_date": available_dates[0] if available_dates else None,
        "available_end_date": available_dates[-1] if available_dates else None,
    }


def _format_campaign_availability_error(availability: dict) -> str:
    if availability.get("code") == "intraday_campaign_range_too_large":
        return (
            f"Replay Campaign has {availability.get('days_total', 0)} loaded intraday days. "
            f"The V1 limit is {availability.get('max_days', 31)} days; choose a shorter range."
        )

    missing_dates = availability.get("missing_dates") or []
    start_date = availability.get("start_date")
    end_date = availability.get("end_date")
    available_start = availability.get("available_start_date")
    available_end = availability.get("available_end_date")

    if not available_start:
        return (
            f"No intraday records are loaded for the Replay Campaign range "
            f"{start_date} to {end_date}. Load intraday data first, then start the campaign."
        )

    if not missing_dates:
        return (
            f"Replay Campaign cannot start because the selected range {start_date} to {end_date} "
            "does not contain any EGX trading weekdays. Choose a range that includes Sunday through Thursday."
        )

    preview = ", ".join(missing_dates[:8])
    suffix = f" and {len(missing_dates) - 8} more" if len(missing_dates) > 8 else ""
    return (
        f"Replay Campaign cannot start because these trading days have no intraday records: "
        f"{preview}{suffix}. Loaded replay data is available from {available_start} to {available_end}. "
        "Enable Missing Days = Holidays to skip those dates and continue the campaign."
    )


def _record_campaign_tick_result(tick_result: dict, day_signals: set[str]):
    for signal in tick_result.get("signals", []):
        ticker = signal.get("ticker")
        if ticker:
            _REPLAY_STATE["unique_signals"].add(ticker)
            day_signals.add(ticker)
    _REPLAY_STATE["signals_found"] = len(_REPLAY_STATE["unique_signals"])
    _REPLAY_STATE["scan_results"].append(tick_result)


def _update_campaign_progress(ticks_completed: int, total_ticks: int, day_index: int, days_total: int):
    day_progress = (ticks_completed / total_ticks) if total_ticks else 1
    _REPLAY_STATE["ticks_completed"] = ticks_completed
    _REPLAY_STATE["progress_pct"] = round(day_progress * 100, 1)
    _REPLAY_STATE["campaign_progress_pct"] = round((((day_index - 1) + day_progress) / max(days_total, 1)) * 100, 1)


def _run_replay_campaign_day(
    replay_date: datetime.date,
    speed: int,
    notify: bool,
    replay_profile=None,
    replay_market: str = "EGX30",
    day_index: int = 1,
    days_total: int = 1,
    live_channel_routing: bool = False,
) -> dict:
    """Run one replay day for campaign mode without clearing carried positions."""
    target = _resolve_dispatch("_run_replay_campaign_day", None)
    if target is not None and target is not _run_replay_campaign_day:
        return target(
            replay_date,
            speed,
            notify,
            replay_profile=replay_profile,
            replay_market=replay_market,
            day_index=day_index,
            days_total=days_total,
            live_channel_routing=live_channel_routing,
        )

    TimeUtils = _get_timeutils()
    market_open, market_close = _parse_market_times(replay_date)
    intraday_interval = getattr(settings, "INTRADAY_INTERVAL_MINS", 5)
    market_duration_mins = int((market_close - market_open).total_seconds() / 60)
    total_ticks = max(1, market_duration_mins // intraday_interval)
    real_interval_sec = max(2.0, (intraday_interval * 60) / speed)
    day_signals: set[str] = set()

    _REPLAY_STATE.update({
        "date": replay_date.isoformat(),
        "current_date": replay_date.isoformat(),
        "current_day_index": day_index,
        "days_total": days_total,
        "market_open": market_open.strftime("%H:%M"),
        "market_close": market_close.strftime("%H:%M"),
        "total_ticks": total_ticks,
        "ticks_completed": 0,
        "progress_pct": 0.0,
    })

    TimeUtils.set_replay(
        market_open,
        market_override=True,
        live_channel_routing=live_channel_routing,
    )
    _REPLAY_STATE["status"] = "RUNNING"
    _REPLAY_STATE["current_time"] = market_open.strftime("%H:%M")
    logger.info(
        f"[Replay] Campaign day {day_index}/{days_total}: {replay_date} | "
        f"Speed: {speed}x | Total ticks: {total_ticks}"
    )

    for tick in range(total_ticks):
        if _REPLAY_STOP_EVENT.is_set():
            logger.info("[Replay] Campaign stop requested - aborting.")
            _REPLAY_STATE["status"] = "STOPPING"
            break

        current_sim = TimeUtils.now()
        _REPLAY_STATE["current_time"] = current_sim.strftime("%H:%M")
        tick_result = _run_one_tick(
            tick + 1,
            is_intraday=True,
            scan_label="INTRADAY",
            notify=notify,
            replay_profile=replay_profile,
            replay_market=replay_market,
        )
        _record_campaign_tick_result(tick_result, day_signals)
        _update_campaign_progress(tick + 1, total_ticks, day_index, days_total)

        TimeUtils.advance_simulation(intraday_interval)
        if tick < total_ticks - 1 and not _REPLAY_STOP_EVENT.is_set():
            time.sleep(real_interval_sec)

    if not _REPLAY_STOP_EVENT.is_set():
        pre_close_offset = getattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)
        pre_close_time = market_close - datetime.timedelta(minutes=pre_close_offset)
        TimeUtils.set_simulation(pre_close_time)
        pc_result = _run_one_tick(
            total_ticks + 1,
            is_intraday=False,
            scan_label="PRE-CLOSE",
            notify=notify,
            replay_profile=replay_profile,
            replay_market=replay_market,
        )
        _record_campaign_tick_result(pc_result, day_signals)

        daily_offset = getattr(settings, "DAILY_SIGNAL_OFFSET_MINS", 30)
        daily_time = market_close + datetime.timedelta(minutes=daily_offset)
        TimeUtils.set_simulation(daily_time)
        daily_result = _run_one_tick(
            total_ticks + 2,
            is_intraday=False,
            scan_label="DAILY SIGNAL",
            notify=notify,
            replay_profile=replay_profile,
            replay_market=replay_market,
        )
        _record_campaign_tick_result(daily_result, day_signals)

    trade_summary = _summarize_replay_trades(_REPLAY_STATE["active_trades"])
    return {
        "date": replay_date.isoformat(),
        "ticks_completed": _REPLAY_STATE["ticks_completed"],
        "total_ticks": total_ticks,
        "signals_found": len(day_signals),
        **trade_summary,
        "stopped": _REPLAY_STOP_EVENT.is_set(),
    }


def _replay_campaign_worker(
    replay_dates: list[datetime.date],
    speed: int,
    notify: bool,
    report: bool,
    reset_portfolio: bool,
    close_open_positions_end: bool = False,
    allow_missing_intraday_as_holidays: bool = False,
    live_channel_routing: bool = False,
):
    """Replay multiple loaded intraday days while carrying open simulation positions."""
    TimeUtils = _get_timeutils()
    logger = _get_logger()
    try:
        if reset_portfolio:
            clear_fn = _resolve_dispatch("_clear_simulation_portfolio", _clear_simulation_portfolio)
            clear_fn()
            _REPLAY_STATE["active_trades"] = []
        else:
            _REPLAY_STATE["active_trades"] = _load_open_replay_positions()
        _REPLAY_STATE["pending_entries"] = []

        replay_profile = _resolve_replay_scanner_profile(
            profile_id=_REPLAY_STATE.get("profile_id"),
            use_active_profile=bool(_REPLAY_STATE.get("use_active_profile", False)),
        )
        replay_market = str(_REPLAY_STATE.get("market") or "EGX30")

        if notify:
            from core import AlertManager
            token, chat_id = _replay_telegram_config()
            AlertManager.broadcast_alert(
                f"{REPLAY_PREFIX} REPLAY CAMPAIGN STARTED\n"
                f"Range: {replay_dates[0]} to {replay_dates[-1]}\n"
                f"Days: {len(replay_dates)}\n"
                f"Speed: {speed}x",
                token=token,
                chat_id=chat_id,
            )

        from core import AlertManager
        day_results = []
        for index, replay_date in enumerate(replay_dates, start=1):
            if _REPLAY_STOP_EVENT.is_set():
                _REPLAY_STATE["status"] = "STOPPING"
                break

            AlertManager.clear_deduplication_state(replay_date.strftime("%Y-%m-%d"))
            run_day_fn = _resolve_dispatch("_run_replay_campaign_day", _run_replay_campaign_day)
            result = run_day_fn(
                replay_date,
                speed,
                notify,
                replay_profile=replay_profile,
                replay_market=replay_market,
                day_index=index,
                days_total=len(replay_dates),
                live_channel_routing=live_channel_routing,
            )
            day_results.append(result)
            _REPLAY_STATE["day_results"] = list(day_results)
            _REPLAY_STATE["days_completed"] = len([item for item in day_results if not item.get("stopped")])
            if result.get("stopped"):
                break

        if close_open_positions_end and not _REPLAY_STOP_EVENT.is_set():
            _close_open_replay_positions_at_end()

        if report and not _REPLAY_STOP_EVENT.is_set():
            _generate_replay_report(notify)

        trade_summary = _summarize_replay_trades(_REPLAY_STATE["active_trades"])
        _REPLAY_STATE["campaign_summary"] = {
            "days_completed": _REPLAY_STATE["days_completed"],
            "days_total": len(replay_dates),
            "signals_found": _REPLAY_STATE["signals_found"],
            **trade_summary,
        }

        if not _REPLAY_STOP_EVENT.is_set():
            _REPLAY_STATE["status"] = "COMPLETED"
            _REPLAY_STATE["campaign_progress_pct"] = 100.0
        _REPLAY_STATE["completed_at"] = datetime.datetime.now().isoformat()

        if notify and not _REPLAY_STOP_EVENT.is_set():
            from core import AlertManager
            token, chat_id = _replay_telegram_config()
            AlertManager.broadcast_alert(
                f"{REPLAY_PREFIX} REPLAY CAMPAIGN COMPLETE\n"
                f"Days: {_REPLAY_STATE['days_completed']}/{len(replay_dates)}\n"
                f"Signals Found: {_REPLAY_STATE['signals_found']}\n"
                f"Open Positions: {trade_summary['open_positions']}\n"
                f"Closed Positions: {trade_summary['closed_positions']}\n"
                f"TP1 Hits: {trade_summary['tp1_hits']}\n"
                f"TP2 Exits: {trade_summary['tp2_exits']}\n"
                f"SL Exits: {trade_summary['stop_loss_exits']}\n"
                f"BE Stops: {trade_summary['breakeven_stop_exits']}\n"
                f"Duration: {_format_duration(_REPLAY_STATE['started_at'])}",
                token=token,
                chat_id=chat_id,
            )

        logger.info(
            f"[Replay] Campaign completed: {_REPLAY_STATE['signals_found']} signals "
            f"across {_REPLAY_STATE['days_completed']}/{len(replay_dates)} days | "
            f"open={trade_summary['open_positions']} closed={trade_summary['closed_positions']} "
            f"tp1={trade_summary['tp1_hits']} tp2={trade_summary['tp2_exits']} "
            f"sl={trade_summary['stop_loss_exits']} be={trade_summary['breakeven_stop_exits']}"
        )

    except Exception as e:
        _REPLAY_STATE["status"] = "ERROR"
        _REPLAY_STATE["error"] = str(e)
        logger.error(f"[Replay] Campaign fatal error: {e}\n{traceback.format_exc()}")
    finally:
        TimeUtils.clear_replay()
