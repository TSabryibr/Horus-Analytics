"""
REPLAY RUNNER
=============
Single-day tick loop, execution, scan dispatch, notifications, and signal persistence.
"""

import datetime
import time
import traceback
from typing import Any

import sys
from core.settings import settings
from utils.logger import setup_logger
from .state import (
    _REPLAY_STATE,
    _REPLAY_STOP_EVENT,
    REPLAY_PREFIX,
    _parse_market_times,
    _resolve_replay_scanner_profile,
    _run_selected_replay_profile_scan,
    _safe_float,
    _format_duration,
    _resolve_dispatch,
    _get_timeutils,
)


def _get_daily_scanner():
    mod = sys.modules.get("core.replay_engine")
    if mod is not None and hasattr(mod, "DailyScanner"):
        return getattr(mod, "DailyScanner")
    from core import DailyScanner
    return DailyScanner
from .trades import (
    _build_risk_sized_replay_trade,
    _create_mock_replay_position,
    _mock_trade_monitor,
    _clear_simulation_portfolio,
    _close_open_replay_positions_at_end,
    _replay_telegram_config,
    _broadcast_replay_followup,
)

logger = setup_logger("horus.replay.runner")


def _empty_pending_replay_result() -> dict:
    return {
        "queued": 0,
        "opened": 0,
        "skipped": 0,
        "failed": 0,
        "remaining": len(_REPLAY_STATE.get("pending_entries") or []),
        "items": [],
    }


def _is_daily_replay_scan(scan_label: str | None) -> bool:
    return (scan_label or "").strip().upper() == "DAILY SIGNAL"


def _is_pre_close_replay_scan(scan_label: str | None) -> bool:
    return (scan_label or "").strip().upper() == "PRE-CLOSE"


def _replay_signal_tickers(signals: list[dict]) -> set[str]:
    return {
        str((signal or {}).get("Ticker") or "").strip().upper()
        for signal in (signals or [])
        if str((signal or {}).get("Ticker") or "").strip()
    }


def _record_replay_pre_close_previews(signals: list[dict]) -> dict:
    previews = {
        str((signal or {}).get("Ticker") or "").strip().upper(): dict(signal or {})
        for signal in (signals or [])
        if str((signal or {}).get("Ticker") or "").strip()
    }
    _REPLAY_STATE["pre_close_previews"] = previews
    return {"recorded": len(previews), "tickers": sorted(previews)}


def _reconcile_replay_pre_close_previews(daily_signals: list[dict], *, notify: bool) -> dict:
    previews = dict(_REPLAY_STATE.get("pre_close_previews") or {})
    confirmed = _replay_signal_tickers(daily_signals)
    preview_tickers = set(previews)
    confirmed_previews = sorted(preview_tickers & confirmed)
    cancelled_previews = sorted(preview_tickers - confirmed)

    remaining_pending = []
    cancelled_pending = 0
    for pending in _REPLAY_STATE.get("pending_entries") or []:
        ticker = str(pending.get("ticker") or "").strip().upper()
        trigger_source = str(pending.get("trigger_source") or "").strip().upper()
        if trigger_source == "PRE_CLOSE" and ticker in cancelled_previews:
            cancelled_pending += 1
            continue
        remaining_pending.append(pending)
    _REPLAY_STATE["pending_entries"] = remaining_pending

    if notify:
        broadcast_followup_fn = _resolve_dispatch("_broadcast_replay_followup", _broadcast_replay_followup)
        for ticker in cancelled_previews:
            preview = previews.get(ticker) or {}
            broadcast_followup_fn(
                {
                    "ticker": ticker,
                    "side": str(preview.get("Signal_Type") or "BUY").upper(),
                    "stop_loss": preview.get("Stop_Loss"),
                    "tp2": preview.get("Target_Price_2"),
                },
                trigger_state="CANCELLED",
                close_reason="PRE_CLOSE_NOT_CONFIRMED",
            )

    result = {
        "status": "completed",
        "confirmed": len(confirmed_previews),
        "cancelled": len(cancelled_previews),
        "cancelled_pending_entries": cancelled_pending,
        "confirmed_tickers": confirmed_previews,
        "cancelled_tickers": cancelled_previews,
    }
    _REPLAY_STATE.setdefault("pre_close_reconciliation", []).append(result)
    return result


def _has_open_replay_trade(ticker: str) -> bool:
    clean_ticker = (ticker or "").strip().upper()
    return bool(
        clean_ticker
        and any(
            str(trade.get("ticker") or "").strip().upper() == clean_ticker
            and trade.get("state") in {"OPEN", "TP1_HIT"}
            for trade in _REPLAY_STATE.get("active_trades") or []
        )
    )


def _has_pending_replay_entry(ticker: str) -> bool:
    clean_ticker = (ticker or "").strip().upper()
    return bool(
        clean_ticker
        and any(
            str(entry.get("ticker") or "").strip().upper() == clean_ticker
            and entry.get("state") == "PENDING_OPEN"
            for entry in _REPLAY_STATE.get("pending_entries") or []
        )
    )


def _queue_daily_replay_entry(signal: dict, scan_label: str, regime: str | None) -> dict:
    TimeUtils = _get_timeutils()
    ticker = str(signal.get("Ticker") or "").strip().upper()
    planned_entry_price = _safe_float(signal.get("Entry_Price"))
    item = {
        "ticker": ticker,
        "action": "queued",
        "reason": None,
        "planned_entry_price": planned_entry_price,
    }

    if not ticker:
        item.update({"action": "failed", "reason": "missing_ticker"})
        return item
    if planned_entry_price <= 0:
        item.update({"action": "failed", "reason": "invalid_planned_entry_price"})
        return item
    if _has_open_replay_trade(ticker):
        item.update({"action": "skipped", "reason": "already_open"})
        return item
    if _has_pending_replay_entry(ticker):
        item.update({"action": "skipped", "reason": "already_pending"})
        return item

    pending_entry = {
        "ticker": ticker,
        "state": "PENDING_OPEN",
        "trigger_source": "DAILY_NEXT_OPEN",
        "scan_label": scan_label,
        "regime": regime,
        "planned_entry_price": planned_entry_price,
        "queued_at": TimeUtils.now().isoformat(),
        "signal": dict(signal),
    }
    _REPLAY_STATE.setdefault("pending_entries", []).append(pending_entry)
    return item


def _resolve_pending_replay_gap_pct(max_gap_pct: float | None = None) -> float:
    if max_gap_pct is None:
        try:
            max_gap_pct = getattr(settings, "PENDING_ENTRY_MAX_GAP_PCT", 1.5)
        except Exception:
            max_gap_pct = 1.5
    try:
        resolved = float(max_gap_pct)
    except (TypeError, ValueError):
        resolved = 1.5
    return resolved if resolved > 0 else 1.5


def _latest_replay_open_price(ticker: str) -> tuple[float | None, str | None]:
    try:
        from core.DataManager import DataManager

        frame = DataManager.get_intraday_data(ticker, limit=1, refresh_if_stale=False)
        if frame is None or frame.empty or "Open" not in frame.columns:
            return None, None
        last_bar = frame.iloc[-1]
        open_price = _safe_float(last_bar.get("Open"))
        if open_price <= 0:
            return None, None
        try:
            open_ts = frame.index[-1].isoformat()
        except Exception:
            open_ts = None
        return open_price, open_ts
    except Exception as exc:
        logger.debug(f"[Replay] Unable to read replay open price for {ticker}: {exc}")
        return None, None


def _execute_pending_replay_entries(notify: bool = True, max_gap_pct: float | None = None) -> dict:
    """Execute replay daily signals at the next visible intraday open."""
    TimeUtils = _get_timeutils()
    result = _empty_pending_replay_result()
    pending_entries = list(_REPLAY_STATE.get("pending_entries") or [])
    if not pending_entries:
        return result

    max_gap_pct = _resolve_pending_replay_gap_pct(max_gap_pct)
    remaining_entries: list[dict] = []

    for pending in pending_entries:
        signal = dict(pending.get("signal") or {})
        ticker = str(pending.get("ticker") or signal.get("Ticker") or "").strip().upper()
        planned_entry_price = _safe_float(pending.get("planned_entry_price") or signal.get("Entry_Price"))
        item: dict[str, Any] = {
            "ticker": ticker,
            "trigger_source": pending.get("trigger_source") or "DAILY_NEXT_OPEN",
            "planned_entry_price": planned_entry_price,
            "actual_entry_price": None,
            "gap_pct": None,
            "reason": None,
        }

        if not ticker:
            item["reason"] = "missing_ticker"
            result["failed"] += 1
            result["items"].append(item)
            continue
        if planned_entry_price <= 0:
            item["reason"] = "invalid_planned_entry_price"
            result["failed"] += 1
            result["items"].append(item)
            continue
        if _has_open_replay_trade(ticker):
            item["reason"] = "already_open"
            result["skipped"] += 1
            result["items"].append(item)
            continue

        open_price, open_ts = _latest_replay_open_price(ticker)
        if open_price is None:
            remaining_entries.append(pending)
            item["reason"] = "open_price_unavailable"
            result["items"].append(item)
            continue

        gap_pct = abs(open_price - planned_entry_price) / planned_entry_price * 100.0
        item["actual_entry_price"] = open_price
        item["gap_pct"] = round(gap_pct, 4)
        item["open_ts"] = open_ts
        if gap_pct > max_gap_pct:
            item["reason"] = "gap_threshold_exceeded"
            result["skipped"] += 1
            result["items"].append(item)
            logger.info(
                "[Replay] Pending daily entry skipped: ticker=%s gap_pct=%.4f planned=%.4f actual=%.4f max_gap_pct=%.4f",
                ticker,
                gap_pct,
                planned_entry_price,
                open_price,
                max_gap_pct,
            )
            continue

        signal["Ticker"] = ticker
        signal["Entry_Price"] = open_price
        signal["Planned_Entry_Price"] = planned_entry_price
        signal["Gap_Pct"] = gap_pct
        signal["Open_Timestamp"] = open_ts
        entry_at = TimeUtils.now().isoformat()
        trade, skip_reason = _build_risk_sized_replay_trade(signal, entry_at=entry_at)
        if trade is None:
            item["reason"] = skip_reason or "trade_build_failed"
            result["skipped"] += 1
            result["items"].append(item)
            continue

        trade["planned_entry_price"] = planned_entry_price
        trade["actual_entry_price"] = open_price
        trade["gap_pct"] = round(gap_pct, 4)
        trade["open_ts"] = open_ts
        trade["trigger_source"] = pending.get("trigger_source") or "DAILY_NEXT_OPEN"
        create_fn = _resolve_dispatch("_create_mock_replay_position", _create_mock_replay_position)
        if create_fn(trade):
            _REPLAY_STATE.setdefault("active_trades", []).append(trade)
            result["opened"] += 1
            item["reason"] = "opened"
            result["items"].append(item)
            if notify:
                notify_fn = _resolve_dispatch("_notify_replay_entry", _notify_replay_entry)
                notify_fn(signal)
        else:
            item["reason"] = "position could not be persisted"
            result["failed"] += 1
            result["items"].append(item)

    _REPLAY_STATE["pending_entries"] = remaining_entries
    result["remaining"] = len(remaining_entries)
    return result


def _persist_replay_signals(signals: list):
    """Save replay signals to the Signal table with source='REPLAY'."""
    target = _resolve_dispatch("_persist_replay_signals", None)
    if target is not None and target is not _persist_replay_signals:
        return target(signals)

    TimeUtils = _get_timeutils()
    from database import Signal
    from peewee import fn
    from core.exclusions import normalize_ticker

    for s in signals:
        ticker_clean = normalize_ticker(s.get("Ticker"))
        if not ticker_clean:
            continue
        try:
            existing = Signal.get_or_none(
                (fn.Upper(Signal.ticker) == ticker_clean)
                & (Signal.signal_type == s["Signal_Type"])
                & (Signal.date == TimeUtils.today())
            )
            if existing:
                if float(s.get("Score", 0)) > existing.score:
                    existing.score = float(s.get("Score", 0))
                    existing.price = float(s.get("Entry_Price", 0))
                    existing.source = "REPLAY"
                    existing.rationale = " | ".join(s.get("Alpha_Rationale", []))
                    existing.save()
            else:
                Signal.create(
                    ticker=s["Ticker"],
                    date=TimeUtils.today(),
                    signal_type=s["Signal_Type"],
                    price=float(s.get("Entry_Price", 0)),
                    score=float(s.get("Score", 0)),
                    source="REPLAY",
                    rationale=" | ".join(s.get("Alpha_Rationale", [])),
                )
        except Exception as e:
            logger.error(f"[Replay] Error saving signal {ticker_clean}: {e}")


def _notify_replay_entry(sig: dict):
    """Sends an ENTRY alert for the replay session."""
    target = _resolve_dispatch("_notify_replay_entry", None)
    if target is not None and target is not _notify_replay_entry:
        return target(sig)

    from core import AlertManager, ReportGenerator
    token, chat_id = _replay_telegram_config()
    ticker = sig.get("Ticker")
    price = float(sig.get("Entry_Price", 0))
    sl = float(sig.get("Stop_Loss", 0))
    tp = float(sig.get("Target_Price", 0))

    try:
        card = ReportGenerator.create_horus_signal_card(
            ticker=ticker,
            entry=price,
            stop_loss=sl,
            tp1=tp,
            tp2=float(sig.get("Target_Price_2", tp*1.04)),
            score=sig.get("Score", 0),
            signal_label=f"{REPLAY_PREFIX} ENTRY"
        )
        AlertManager.broadcast_image(card, caption=f"{REPLAY_PREFIX} Entry: {ticker}", token=token, chat_id=chat_id)
        return
    except Exception as e:
        logger.error(f"[Replay] Entry card error for {ticker}: {e}")

    msg = (
        f"{REPLAY_PREFIX} AUTO-ENTRY EXECUTED\n"
        f"Ticker: {ticker}\n"
        f"Price: {price:.2f}\n"
        f"Target: {tp:.2f}\n"
        f"Stop: {sl:.2f}"
    )
    AlertManager.broadcast_alert(msg, token=token, chat_id=chat_id)


def _safe_broadcast(message: str, token: str | None = None, chat_id: str | None = None):
    from core import AlertManager
    max_retries = 3
    for attempt in range(max_retries):
        try:
            AlertManager.broadcast_alert(message, token=token, chat_id=chat_id)
            time.sleep(0.3)
            return
        except Exception as e:
            if "Connection aborted" in str(e) or "timeout" in str(e).lower():
                logger.warning(f"[Replay] Telegram timeout (attempt {attempt+1}/{max_retries}), retrying...")
                time.sleep(2)
                continue
            logger.error(f"[Replay] Broadcast failed: {e}")
            break


def _safe_broadcast_image(img_buf, caption: str, token: str | None = None, chat_id: str | None = None):
    from core import AlertManager
    max_retries = 2
    for attempt in range(max_retries):
        try:
            AlertManager.broadcast_image(img_buf, caption, token=token, chat_id=chat_id)
            time.sleep(0.5)
            return
        except Exception as e:
            logger.warning(f"[Replay] Telegram image timeout (attempt {attempt+1}/{max_retries}), retrying...")
            time.sleep(3)
            continue


def _broadcast_replay_signals(signals: list, filtered_signals: list, regime: str, scan_label: str, is_intraday: bool):
    """Send replay-tagged Telegram alerts."""
    target = _resolve_dispatch("_broadcast_replay_signals", None)
    if target is not None and target is not _broadcast_replay_signals:
        return target(signals, filtered_signals, regime, scan_label, is_intraday)

    from core import ReportGenerator, TelegramBot_Alerts

    if not filtered_signals:
        return

    mode_label = "INTRADAY" if is_intraday else "DAILY"
    token, chat_id = _replay_telegram_config()
    _safe_broadcast(
        f"{REPLAY_PREFIX} [{mode_label} SCAN]\n"
        f"[MARKET REGIME: {regime}]\n"
        f"Signals Found: {len(filtered_signals)}",
        token=token,
        chat_id=chat_id
    )

    for i, s in enumerate(filtered_signals[:3]):
        try:
            img_buf = ReportGenerator.create_horus_signal_card(
                ticker=s.get("Ticker"),
                entry=float(s.get("Entry_Price", 0)),
                stop_loss=float(s.get("Stop_Loss", 0)),
                tp1=float(s.get("Target_Price", 0)),
                tp2=float(s.get("Target_Price_2", 0)) if s.get("Target_Price_2") is not None else None,
                score=s.get("Score", 0),
                rsi=s.get("RSI"),
                volume_x=s.get("Volume_x"),
                signal_label=f"{REPLAY_PREFIX} {scan_label}",
            )
            rsi_text = f"{float(s.get('RSI')):.1f}" if s.get("RSI") is not None else "N/A"
            vol_text = f"{float(s.get('Volume_x')):.1f}x" if s.get("Volume_x") is not None else "N/A"
            caption = (
                f"{REPLAY_PREFIX} [TOP {i+1}] {s.get('Ticker')} | Score: {s.get('Score', 0)}/10\n"
                f"RSI: {rsi_text} | Vol Spike: {vol_text}"
            )
            _safe_broadcast_image(img_buf, caption, token=token, chat_id=chat_id)
        except Exception as e:
            logger.error(f"[Replay] Card error for {s.get('Ticker')}: {e}")

    full_msg = TelegramBot_Alerts.format_signal_alert(filtered_signals)
    if full_msg:
        _safe_broadcast(f"{REPLAY_PREFIX} [FULL SUMMARY]\n{full_msg}", token=token, chat_id=chat_id)


def _generate_replay_report(notify: bool):
    """Generate the AI daily report as part of the replay session."""
    try:
        from routes import ai_report
        payload = ai_report.get_ai_daily_report(force_refresh=True, use_llm=True)
        if isinstance(payload, dict) and payload.get("status") == "success" and notify:
            from core import AlertManager
            from core.scheduling import _build_ai_report_telegram_message
            token, chat_id = _replay_telegram_config()
            message = _build_ai_report_telegram_message(payload)
            AlertManager.broadcast_alert(f"{REPLAY_PREFIX} [AI DAILY REPORT]\n{message}", token=token, chat_id=chat_id)
        logger.info("[Replay] AI report generated successfully.")
    except Exception as e:
        logger.error(f"[Replay] AI report generation failed: {e}")


def _run_one_tick(
    tick_index: int,
    is_intraday: bool,
    scan_label: str,
    notify: bool,
    replay_profile=None,
    replay_market: str = "EGX30",
) -> dict:
    """Execute one scan cycle for the current simulated time."""
    TimeUtils = _get_timeutils()
    from core import AlertManager

    current_time = TimeUtils.now()
    tick_result: dict[str, Any] = {
        "tick": tick_index,
        "simulated_time": current_time.strftime("%Y-%m-%d %H:%M"),
        "scan_label": scan_label,
        "signals_count": 0,
        "signals": [],
        "skipped_entries": 0,
        "pending_entries": _empty_pending_replay_result(),
        "error": None,
    }

    try:
        if is_intraday:
            tick_result["pending_entries"] = _execute_pending_replay_entries(notify=notify)

        if replay_profile is not None and not is_intraday:
            run_profile_fn = _resolve_dispatch("_run_selected_replay_profile_scan", _run_selected_replay_profile_scan)
            signals, monitored, breadth, regime, strategy_profile = run_profile_fn(replay_profile)
        else:
            DailyScanner = _get_daily_scanner()
            is_pc = _is_pre_close_replay_scan(scan_label)
            signals, monitored, breadth, regime = DailyScanner.get_market_signals(
                index_choice=replay_market,
                is_intraday=is_intraday,
                is_pre_close=is_pc,
            )
            strategy_profile = {
                "source_type": "HORUS",
                "profile_name": "Horus Core",
                "market": replay_market,
                "timeframe": "INTRADAY" if is_intraday else "1D",
            }
        signals = list(signals or [])
        tick_result["signals_count"] = len(signals)
        tick_result["regime"] = regime
        tick_result["breadth"] = breadth
        tick_result["strategy_profile"] = strategy_profile

        current_hhmm = current_time.strftime("%H:%M")
        is_swing_scan = (
            not is_intraday
            or _is_pre_close_replay_scan(scan_label)
            or _is_daily_replay_scan(scan_label)
            or current_hhmm >= "14:00"
        )
        signal_lane = "SWING" if is_swing_scan else "INTRADAY"

        for s in signals:
            s["source"] = "REPLAY"
            s["signal_lane"] = signal_lane
            s["is_swing"] = is_swing_scan
            s["is_intraday"] = not is_swing_scan

        if not is_intraday and _is_pre_close_replay_scan(scan_label):
            tick_result["pre_close_preview"] = _record_replay_pre_close_previews(signals)
        elif not is_intraday and _is_daily_replay_scan(scan_label):
            tick_result["pre_close_reconciliation"] = _reconcile_replay_pre_close_previews(
                signals,
                notify=notify,
            )

        persist_fn = _resolve_dispatch("_persist_replay_signals", _persist_replay_signals)
        persist_fn(signals)

        filtered_signals = AlertManager.filter_new_signals(signals, scan_label)
        filtered_signals.sort(key=lambda s: _safe_float(s.get("Score"), 0.0), reverse=True)

        if notify and signals and not is_intraday:
            broadcast_fn = _resolve_dispatch("_broadcast_replay_signals", _broadcast_replay_signals)
            broadcast_fn(signals, filtered_signals, regime, scan_label, is_intraday)

        tick_result["signals"] = []
        cutoff_hhmm = getattr(settings, "REPLAY_ENTRY_CUTOFF_HHMM", "12:30") or "12:30"
        max_positions = int(getattr(settings, "REPLAY_MAX_CONCURRENT_POSITIONS", 5) or 5)

        for s in filtered_signals:
            ticker = s.get("Ticker")
            signal_row: dict[str, Any] = {
                "ticker": ticker,
                "score": s.get("Score"),
                "type": s.get("Signal_Type"),
                "skip_reason": None,
            }
            tick_result["signals"].append(signal_row)

            if _is_daily_replay_scan(scan_label) and not is_intraday:
                queue_result = _queue_daily_replay_entry(s, scan_label, regime)
                signal_row["pending_action"] = queue_result["action"]
                if queue_result["action"] == "queued":
                    tick_result["pending_entries"]["queued"] += 1
                elif queue_result["action"] == "skipped":
                    signal_row["skip_reason"] = queue_result["reason"]
                    tick_result["pending_entries"]["skipped"] += 1
                    tick_result["skipped_entries"] += 1
                else:
                    signal_row["skip_reason"] = queue_result["reason"]
                    tick_result["pending_entries"]["failed"] += 1
                    tick_result["skipped_entries"] += 1
                tick_result["pending_entries"]["items"].append(queue_result)
                continue
            
            if signal_lane == "INTRADAY" and current_hhmm >= cutoff_hhmm:
                signal_row["skip_reason"] = f"intraday_entry_cutoff_exceeded (after {cutoff_hhmm})"
                tick_result["skipped_entries"] += 1
                continue

            active_open_count = len([
                t for t in _REPLAY_STATE.get("active_trades") or []
                if t.get("state") in {"OPEN", "TP1_HIT"}
            ])
            if active_open_count >= max_positions:
                signal_row["skip_reason"] = f"max_concurrent_positions_reached ({active_open_count}/{max_positions})"
                tick_result["skipped_entries"] += 1
                continue

            if ticker and not any(
                t["ticker"] == ticker and t.get("state") in {"OPEN", "TP1_HIT"}
                for t in _REPLAY_STATE["active_trades"]
            ):
                entry_at = TimeUtils.now().isoformat()
                trade, skip_reason = _build_risk_sized_replay_trade(s, entry_at=entry_at)
                if trade is None:
                    signal_row["skip_reason"] = skip_reason
                    tick_result["skipped_entries"] += 1
                    continue
                
                if is_intraday:
                    create_fn = _resolve_dispatch("_create_mock_replay_position", _create_mock_replay_position)
                    if create_fn(trade):
                        _REPLAY_STATE["active_trades"].append(trade)
                    else:
                        signal_row["skip_reason"] = "position could not be persisted"
                        tick_result["skipped_entries"] += 1
                    if notify and any(t["ticker"] == ticker for t in _REPLAY_STATE["active_trades"]):
                        notify_fn = _resolve_dispatch("_notify_replay_entry", _notify_replay_entry)
                        notify_fn(s)

        if is_intraday:
            monitor_fn = _resolve_dispatch("_mock_trade_monitor", _mock_trade_monitor)
            monitor_fn(notify=notify)

        tick_result["pending_entries"]["remaining"] = len(_REPLAY_STATE.get("pending_entries") or [])

    except Exception as e:
        tick_result["error"] = str(e)
        logger.error(f"[Replay] Tick {tick_index} error: {e}")

    return tick_result


def _replay_worker(
    replay_date: datetime.date,
    speed: int,
    notify: bool,
    report: bool,
    close_open_positions_end: bool = False,
    live_channel_routing: bool = False,
):
    """Main replay thread — advances the clock and triggers scans."""
    TimeUtils = _get_timeutils()
    try:
        clear_fn = _resolve_dispatch("_clear_simulation_portfolio", _clear_simulation_portfolio)
        clear_fn()
        _REPLAY_STATE["pending_entries"] = []

        from core import AlertManager
        AlertManager.clear_deduplication_state(replay_date.strftime("%Y-%m-%d"))

        market_open, market_close = _parse_market_times(replay_date)
        intraday_interval = getattr(settings, "INTRADAY_INTERVAL_MINS", 5)
        replay_profile = _resolve_replay_scanner_profile(
            profile_id=_REPLAY_STATE.get("profile_id"),
            use_active_profile=bool(_REPLAY_STATE.get("use_active_profile", False)),
        )
        replay_market = str(_REPLAY_STATE.get("market") or "EGX30")

        market_duration_mins = int((market_close - market_open).total_seconds() / 60)
        total_ticks = market_duration_mins // intraday_interval

        _REPLAY_STATE.update({
            "market_open": market_open.strftime("%H:%M"),
            "market_close": market_close.strftime("%H:%M"),
            "total_ticks": total_ticks,
            "ticks_completed": 0,
            "progress_pct": 0.0,
        })

        real_interval_sec = (intraday_interval * 60) / speed
        real_interval_sec = max(2.0, real_interval_sec)

        TimeUtils.set_replay(
            market_open,
            market_override=True,
            live_channel_routing=live_channel_routing,
        )
        _REPLAY_STATE["status"] = "RUNNING"
        _REPLAY_STATE["current_time"] = market_open.strftime("%H:%M")
        logger.info(
            f"[Replay] Started: {replay_date} | Speed: {speed}x | "
            f"Interval: {real_interval_sec:.1f}s real / {intraday_interval}m sim | "
            f"Total ticks: {total_ticks}"
        )

        if notify:
            token, chat_id = _replay_telegram_config()
            AlertManager.broadcast_alert(
                f"{REPLAY_PREFIX} 🎬 REPLAY SESSION STARTED\n"
                f"Date: {replay_date}\n"
                f"Speed: {speed}x\n"
                f"Market: {_REPLAY_STATE['market_open']} → {_REPLAY_STATE['market_close']}\n"
                f"Estimated duration: {int(total_ticks * real_interval_sec / 60)} min",
                token=token,
                chat_id=chat_id
            )

        for tick in range(total_ticks):
            if _REPLAY_STOP_EVENT.is_set():
                logger.info("[Replay] Stop requested — aborting.")
                _REPLAY_STATE["status"] = "STOPPING"
                break

            current_sim = TimeUtils.now()
            _REPLAY_STATE["current_time"] = current_sim.strftime("%H:%M")

            logger.info(f"[Replay] Tick {tick+1}/{total_ticks} @ {current_sim.strftime('%H:%M')}")
            tick_result = _run_one_tick(
                tick + 1,
                is_intraday=True,
                scan_label="INTRADAY",
                notify=notify,
                replay_profile=replay_profile,
                replay_market=replay_market,
            )
            _REPLAY_STATE["ticks_completed"] = tick + 1
            _REPLAY_STATE["progress_pct"] = round(((tick + 1) / total_ticks) * 100, 1)
            
            for s in tick_result.get("signals", []):
                if s.get("ticker"):
                    _REPLAY_STATE["unique_signals"].add(s["ticker"])
            _REPLAY_STATE["signals_found"] = len(_REPLAY_STATE["unique_signals"])
            _REPLAY_STATE["scan_results"].append(tick_result)

            TimeUtils.advance_simulation(intraday_interval)
            if tick < total_ticks - 1 and not _REPLAY_STOP_EVENT.is_set():
                time.sleep(real_interval_sec)

        if not _REPLAY_STOP_EVENT.is_set():
            pre_close_offset = getattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)
            pre_close_time = market_close - datetime.timedelta(minutes=pre_close_offset)
            TimeUtils.set_simulation(pre_close_time)

            logger.info(f"[Replay] Running PRE-CLOSE scan @ {pre_close_time.strftime('%H:%M')}")
            pc_result = _run_one_tick(
                total_ticks + 1,
                is_intraday=False,
                scan_label="PRE-CLOSE",
                notify=notify,
                replay_profile=replay_profile,
                replay_market=replay_market,
            )
            for s in pc_result.get("signals", []):
                if s.get("ticker"):
                    _REPLAY_STATE["unique_signals"].add(s["ticker"])
            _REPLAY_STATE["signals_found"] = len(_REPLAY_STATE["unique_signals"])
            _REPLAY_STATE["scan_results"].append(pc_result)

            daily_offset = getattr(settings, "DAILY_SIGNAL_OFFSET_MINS", 30)
            daily_time = market_close + datetime.timedelta(minutes=daily_offset)
            TimeUtils.set_simulation(daily_time)

            logger.info(f"[Replay] Running DAILY SIGNAL scan @ {daily_time.strftime('%H:%M')}")
            daily_result = _run_one_tick(
                total_ticks + 2,
                is_intraday=False,
                scan_label="DAILY SIGNAL",
                notify=notify,
                replay_profile=replay_profile,
                replay_market=replay_market,
            )
            for s in daily_result.get("signals", []):
                if s.get("ticker"):
                    _REPLAY_STATE["unique_signals"].add(s["ticker"])
            _REPLAY_STATE["signals_found"] = len(_REPLAY_STATE["unique_signals"])
            _REPLAY_STATE["scan_results"].append(daily_result)

            if close_open_positions_end:
                _close_open_replay_positions_at_end()

            if report:
                _generate_replay_report(notify)

        _REPLAY_STATE["status"] = "COMPLETED"
        _REPLAY_STATE["completed_at"] = datetime.datetime.now().isoformat()

        if notify:
            from core import AlertManager
            token, chat_id = _replay_telegram_config()
            AlertManager.broadcast_alert(
                f"{REPLAY_PREFIX} ✅ REPLAY SESSION COMPLETE\n"
                f"Date: {replay_date}\n"
                f"Ticks: {_REPLAY_STATE['ticks_completed']}/{total_ticks}\n"
                f"Signals Found: {_REPLAY_STATE['signals_found']}\n"
                f"Duration: {_format_duration(_REPLAY_STATE['started_at'])}",
                token=token,
                chat_id=chat_id
            )

        logger.info(
            f"[Replay] Completed: {_REPLAY_STATE['signals_found']} signals "
            f"across {_REPLAY_STATE['ticks_completed']} ticks"
        )

    except Exception as e:
        _REPLAY_STATE["status"] = "ERROR"
        _REPLAY_STATE["error"] = str(e)
        logger.error(f"[Replay] Fatal error: {e}\n{traceback.format_exc()}")
    finally:
        TimeUtils.clear_replay()
