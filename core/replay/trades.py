"""
REPLAY TRADES & PORTFOLIO
=========================
Mock position lifecycle management, sizing, and exit simulation for Market Replay.
"""

import datetime
from types import SimpleNamespace
from typing import Any

from core.settings import settings
from core import TimeUtils
from utils.logger import setup_logger
from .state import _REPLAY_STATE, REPLAY_PREFIX, _safe_float, _resolve_dispatch, _get_timeutils

logger = setup_logger("horus.replay.trades")


def _replay_telegram_config() -> tuple[str | None, str | None]:
    """Return explicit test credentials unless replay is opted into live channel routing."""
    if bool(_REPLAY_STATE.get("live_channel_routing")):
        return None, None
    from core import TelegramBot_Alerts
    return TelegramBot_Alerts._test_telegram_config()


def _get_simulation_portfolio():
    """Helper to safely get or create the simulation portfolio."""
    from database import Portfolio
    try:
        port = Portfolio.get_or_none(Portfolio.name == "Intraday Simulation")
        if port:
            return port

        return Portfolio.create(
            name="Intraday Simulation",
            type="SYSTEM",
            auto_manage=True,
            cash_egp=1000000.0
        )
    except Exception as e:
        logger.error(f"[Replay] Critical error accessing simulation portfolio: {e}")
        return None


def _clear_simulation_portfolio():
    """Reset Intraday Simulation cash and positions at the start of a clean replay run."""
    from database import Position, Trade
    try:
        port = _get_simulation_portfolio()
        if port:
            Position.delete().where(Position.portfolio == port).execute()
            Trade.delete().where(Trade.portfolio == port).execute()
            port.cash_egp = 1000000.0  # type: ignore[assignment]
            port.cash_usd = 0.0  # type: ignore[assignment]
            port.save()
            logger.info("[Replay] Reset Intraday Simulation portfolio for new session.")
    except Exception as e:
        logger.debug(f"[Replay] Cleanup skipped: {e}")


def _load_open_replay_positions() -> list[dict]:
    """Load open Intraday Simulation positions back into replay monitor state."""
    from database import Position

    port = _get_simulation_portfolio()
    if not port:
        return []

    trades = []
    query = (
        Position.select()
        .where((Position.portfolio == port) & (Position.status == "OPEN"))
        .order_by(Position.entry_date.asc(), Position.id.asc())
    )
    for position in query:
        tp1 = float(position.target_price or 0)
        tp2 = float(position.target_price_2 or tp1)
        trades.append({
            "ticker": position.ticker,
            "side": "BUY",
            "state": "TP1_HIT" if bool(position.tp1_hit) else "OPEN",
            "shares": int(position.shares or 0),
            "entry_price": float(position.entry_price or 0),
            "stop_loss": float(position.stop_loss or 0),
            "tp1": tp1,
            "tp2": tp2,
            "tp1_hit": bool(position.tp1_hit),
            "exit_reason": None,
            "entry_at": position.entry_date.isoformat() if position.entry_date else None,
            "exit_at": None,
            "exit_price": None,
        })
    return trades


def _summarize_replay_trades(trades: list[dict]) -> dict:
    """Count replay position lifecycle states for status, logs, and reports."""
    open_trades = [trade for trade in trades if trade.get("state") in {"OPEN", "TP1_HIT"}]
    closed_trades = [trade for trade in trades if trade.get("state") == "CLOSED"]
    tp1_hits = [
        trade for trade in trades
        if trade.get("state") == "TP1_HIT"
        or bool(trade.get("tp1_hit"))
        or trade.get("exit_reason") in {"target_2", "breakeven_stop"}
    ]
    return {
        "open_positions": len(open_trades),
        "closed_positions": len(closed_trades),
        "tp1_hits": len(tp1_hits),
        "tp2_exits": len([trade for trade in closed_trades if trade.get("exit_reason") == "target_2"]),
        "stop_loss_exits": len([trade for trade in closed_trades if trade.get("exit_reason") == "stop_loss"]),
        "breakeven_stop_exits": len([trade for trade in closed_trades if trade.get("exit_reason") == "breakeven_stop"]),
    }


def _build_risk_sized_replay_trade(signal: dict, entry_at: str) -> tuple[dict | None, str | None]:
    """Build a replay trade using risk sizing and simulation portfolio cash."""
    ticker = str(signal.get("Ticker") or "").strip().upper()
    entry_price = _safe_float(signal.get("Entry_Price"))
    stop_loss = _safe_float(signal.get("Stop_Loss"))
    tp1 = _safe_float(signal.get("Target_Price"))
    tp2 = _safe_float(signal.get("Target_Price_2"), tp1 * 1.04 if tp1 > 0 else 0.0)

    if not ticker:
        return None, "missing ticker"
    if entry_price <= 0 or stop_loss <= 0 or tp1 <= 0:
        return None, "invalid entry/stop/target values"
    if stop_loss >= entry_price:
        return None, "invalid long geometry (stop must be below entry)"

    get_sim_port_fn = _resolve_dispatch("_get_simulation_portfolio", _get_simulation_portfolio)
    portfolio = get_sim_port_fn()
    if not portfolio:
        return None, "simulation portfolio unavailable"
    cash_egp = _safe_float(getattr(portfolio, "cash_egp", 0.0))
    if cash_egp <= 0:
        return None, "insufficient simulation cash"

    risk_pct = _safe_float(getattr(settings, "RISK_PER_TRADE", 2.0), 2.0)
    commission_pct = max(0.0, _safe_float(getattr(settings, "COMMISSION_PCT", 0.0), 0.0))
    slippage_pct = max(0.0, _safe_float(getattr(settings, "SLIPPAGE_PCT", 0.0), 0.0))

    sizing = settings.calculate_position_size(
        entry_price=entry_price,
        stop_loss_price=stop_loss,
        account_balance=cash_egp,
        risk_pct=risk_pct,
        max_position_pct=100,
        ticker=ticker,
    ) or {}
    shares = int(sizing.get("shares") or 0)
    if shares <= 0:
        return None, "risk sizing returned zero shares"

    effective_entry = entry_price * (1.0 + (slippage_pct / 100.0))
    per_share_cost = effective_entry * (1.0 + (commission_pct / 100.0))
    if per_share_cost <= 0:
        return None, "invalid entry pricing after costs"

    max_cash_shares = int(cash_egp // per_share_cost)
    if max_cash_shares <= 0:
        return None, "insufficient simulation cash after costs"
    shares = min(shares, max_cash_shares)
    if shares <= 0:
        return None, "insufficient simulation cash after sizing cap"

    signal_lane = str(signal.get("signal_lane") or ("SWING" if signal.get("is_swing") else "INTRADAY")).upper()
    return (
        {
            "ticker": ticker,
            "side": "BUY",
            "state": "OPEN",
            "shares": shares,
            "entry_price": effective_entry,
            "stop_loss": stop_loss,
            "tp1": tp1,
            "tp2": tp2,
            "tp1_hit": False,
            "exit_reason": None,
            "entry_at": entry_at,
            "exit_at": None,
            "exit_price": None,
            "risk_per_trade_pct": risk_pct,
            "commission_pct": commission_pct,
            "slippage_pct": slippage_pct,
            "apply_costs": True,
            "signal_lane": signal_lane,
            "is_intraday": (signal_lane == "INTRADAY"),
        },
        None,
    )


def _create_mock_replay_position(trade: dict) -> bool:
    """Saves a replay trade as a Position in the simulation portfolio."""
    from database import Position
    try:
        port = _get_simulation_portfolio()
        if not port:
            return False

        pos = Position.get_or_none(
            (Position.portfolio == port) &
            (Position.ticker == trade["ticker"]) &
            (Position.status == "OPEN")
        )
        if pos:
            return True

        shares = int(trade.get("shares") or 1000)
        entry_price = float(trade.get("entry_price") or 0)
        commission_pct = _safe_float(trade.get("commission_pct"), 0.0) if trade.get("apply_costs") else 0.0
        cost = shares * entry_price
        entry_commission = cost * (commission_pct / 100.0)
        total_entry_outflow = cost + entry_commission
        if shares <= 0 or entry_price <= 0:
            logger.info(f"[Replay] Skipped mock position for {trade['ticker']}: invalid size or entry price.")
            return False
        if total_entry_outflow > float(getattr(port, "cash_egp", 0) or 0):
            logger.info(
                f"[Replay] Skipped mock position for {trade['ticker']}: "
                f"insufficient simulation cash. cost={total_entry_outflow:.2f} cash={float(getattr(port, 'cash_egp', 0) or 0):.2f}"
            )
            return False

        entry_dt = datetime.datetime.fromisoformat(trade["entry_at"]) if trade.get("entry_at") else TimeUtils.now()
        with port._meta.database.atomic():
            Position.create(
                portfolio=port,
                ticker=trade["ticker"],
                shares=shares,
                entry_price=entry_price,
                stop_loss=trade["stop_loss"],
                target_price=trade["tp1"],
                target_price_2=trade["tp2"],
                current_price=entry_price,
                entry_date=entry_dt,
                status="OPEN",
                currency="EGP",
            )
            port.cash_egp = float(getattr(port, "cash_egp", 0) or 0) - total_entry_outflow  # type: ignore[assignment]
            port.save()
        return True
    except Exception as e:
        logger.error(f"[Replay] Failed to create mock position for {trade['ticker']}: {e}")
        return False


def _update_mock_position_state(
    ticker: str,
    status: str,
    tp1_hit: bool = False,
    new_sl: float | None = None,
    exit_price: float | None = None,
    exit_reason: str | None = None,
    commission_pct: float = 0.0,
    slippage_pct: float = 0.0,
):
    """Updates the mock position in the DB."""
    from database import Position, Trade
    try:
        port = _get_simulation_portfolio()
        if not port:
            return

        pos = Position.get_or_none((Position.ticker == ticker) & (Position.portfolio == port) & (Position.status == "OPEN"))
        if not pos:
            return

        if status == "CLOSED":
            close_price = float(exit_price if exit_price is not None else pos.current_price or pos.entry_price)
            shares = int(pos.shares or 0)
            entry_notional = shares * float(pos.entry_price or 0)
            effective_close_price = close_price * (1.0 - (max(0.0, slippage_pct) / 100.0))
            proceeds = shares * effective_close_price
            entry_commission = entry_notional * (max(0.0, commission_pct) / 100.0)
            exit_commission = proceeds * (max(0.0, commission_pct) / 100.0)
            net_proceeds = proceeds - exit_commission
            pnl = net_proceeds - (entry_notional + entry_commission)
            exit_dt = TimeUtils.now()
            with port._meta.database.atomic():
                Trade.create(
                    portfolio=port,
                    ticker=ticker,
                    shares=shares,
                    entry_price=pos.entry_price,
                    exit_price=effective_close_price,
                    entry_date=pos.entry_date,
                    exit_date=exit_dt,
                    pnl=pnl,
                    pnl_pct=((effective_close_price - pos.entry_price) / pos.entry_price) * 100 if pos.entry_price else 0,
                    reason=exit_reason or "REPLAY_CLOSE",
                    currency=pos.currency,
                )
                port.cash_egp = float(getattr(port, "cash_egp", 0) or 0) + net_proceeds  # type: ignore[assignment]
                port.save()
                pos.delete_instance()
            return

        pos.tp1_hit = tp1_hit
        if new_sl is not None:
            pos.stop_loss = new_sl
        pos.status = status
        pos.save()
    except Exception as e:
        logger.error(f"[Replay] Failed to update mock position {ticker}: {e}")


def _build_replay_followup_message(
    trade: dict,
    *,
    trigger_state: str,
    close_price: float | None = None,
    close_reason: str | None = None,
) -> str:
    from core.signals.followups import build_followup_draft_message

    lifecycle = SimpleNamespace(
        state=trigger_state,
        side=str(trade.get("side") or "BUY").upper(),
        ticker=str(trade.get("ticker") or "").upper(),
        stop_loss_active=_safe_float(trade.get("stop_loss"), 0.0),
        stop_loss_initial=_safe_float(trade.get("initial_stop_loss") or trade.get("stop_loss"), 0.0),
        target_price_2=_safe_float(trade.get("tp2"), 0.0),
        close_price=close_price,
        close_reason=close_reason,
    )
    return build_followup_draft_message(lifecycle, trigger_state=trigger_state)


def _broadcast_replay_followup(trade: dict, *, trigger_state: str, close_price: float | None = None, close_reason: str | None = None):
    from core import AlertManager, ReportGenerator

    token, chat_id = _replay_telegram_config()

    # Exit cards are strictly reserved for executed trades exiting an open position (TP1, TP2, STOP_LOSS).
    # Cancelled (e.g. unconfirmed pre-close) or expired setups were never filled, so they must NEVER generate an exit card.
    if trigger_state in ("TP1_HIT", "TP2_HIT", "STOP_LOSS_HIT"):
        try:
            ticker = trade.get("ticker") or "UNKNOWN"
            raw_entry = trade.get("entry_price") or trade.get("entry") or trade.get("price") or trade.get("entry_level") or 0.0
            entry_price = float(raw_entry)
            
            if entry_price > 0:
                if trigger_state == "TP1_HIT":
                    evt_exit_price = float(trade.get("tp1") or entry_price)
                    evt_pnl_pct = (((evt_exit_price - entry_price) / entry_price) * 100.0)
                    evt_reason = "TARGET 1"
                elif trigger_state == "TP2_HIT":
                    evt_exit_price = close_price or float(trade.get("tp2") or entry_price)
                    evt_pnl_pct = (((evt_exit_price - entry_price) / entry_price) * 100.0)
                    evt_reason = "TARGET 2"
                else:
                    evt_exit_price = close_price or float(trade.get("stop_loss") or entry_price)
                    evt_pnl_pct = (((evt_exit_price - entry_price) / entry_price) * 100.0)
                    if close_reason == "BREAKEVEN_STOP_HIT" or trade.get("exit_reason") == "breakeven_stop":
                        evt_reason = "BREAKEVEN_STOP"
                    else:
                        evt_reason = "STOP_LOSS"

                card_buf = ReportGenerator.create_exit_card(
                    ticker=ticker,
                    exit_price=evt_exit_price,
                    entry_price=entry_price,
                    pnl_pct=evt_pnl_pct,
                    reason=evt_reason,
                    exit_time=TimeUtils.now()
                )
                caption = f"{REPLAY_PREFIX} {evt_reason.replace('_', ' ')}: {ticker} ({'+' if evt_pnl_pct >= 0 else ''}{evt_pnl_pct:.2f}%)"
                AlertManager.broadcast_image(card_buf, caption=caption, token=token, chat_id=chat_id)
        except Exception as e:
            logger.error(f"[Replay] Follow-up card error for {trade.get('ticker')}: {e}")

    message = _build_replay_followup_message(
        trade,
        trigger_state=trigger_state,
        close_price=close_price,
        close_reason=close_reason,
    )
    return AlertManager.broadcast_alert(message, token=token, chat_id=chat_id)


def _mock_trade_monitor(notify: bool = True):
    """Simulates Trade Monitor during replay using latest intraday prices."""
    from core.DataManager import DataManager
    update_pos_fn = _resolve_dispatch("_update_mock_position_state", _update_mock_position_state)
    
    for trade in list(_REPLAY_STATE["active_trades"]):
        if trade["state"] not in ("OPEN", "TP1_HIT"):
            continue
            
        ticker = trade["ticker"]
        frame = DataManager.get_intraday_data(ticker, limit=1, refresh_if_stale=False)
        if frame is None or frame.empty:
            continue
            
        last_bar = frame.iloc[-1]
        low_price = float(last_bar["Low"])
        high_price = float(last_bar["High"])
        
        # Check TP1
        if trade["state"] == "OPEN" and low_price <= trade["tp1"] <= high_price:
            trade["state"] = "TP1_HIT"
            trade["stop_loss"] = trade["entry_price"]
            trade["tp1_hit"] = True
            
            update_pos_fn(
                ticker,
                "OPEN",
                tp1_hit=True,
                new_sl=trade["stop_loss"],
            )
            
            if notify:
                _broadcast_replay_followup(
                    trade,
                    trigger_state="TP1_HIT",
                )
            continue
            
        # Check TP2
        if trade["state"] == "TP1_HIT" and low_price <= trade["tp2"] <= high_price:
            trade["state"] = "CLOSED"
            trade["exit_reason"] = "target_2"
            trade["exit_price"] = trade["tp2"]
            trade["exit_at"] = TimeUtils.now().isoformat()
            
            update_pos_fn(
                ticker,
                "CLOSED",
                exit_price=trade["tp2"],
                exit_reason="REPLAY_TARGET_2",
                commission_pct=_safe_float(trade.get("commission_pct"), 0.0),
                slippage_pct=_safe_float(trade.get("slippage_pct"), 0.0),
            )
            
            if notify:
                _broadcast_replay_followup(
                    trade,
                    trigger_state="TP2_HIT",
                    close_price=trade["tp2"],
                    close_reason="TP2_HIT",
                )
            continue
            
        # Check Stop Loss
        if low_price <= trade["stop_loss"] <= high_price:
            reason = "Breakeven stop" if trade["state"] == "TP1_HIT" else "Stop loss"
            trade["state"] = "CLOSED"
            trade["exit_reason"] = "breakeven_stop" if reason == "Breakeven stop" else "stop_loss"
            trade["exit_price"] = trade["stop_loss"]
            trade["exit_at"] = TimeUtils.now().isoformat()
            
            update_pos_fn(
                ticker,
                "CLOSED",
                exit_price=trade["stop_loss"],
                exit_reason="REPLAY_BREAKEVEN_STOP" if reason == "Breakeven stop" else "REPLAY_STOP_LOSS",
                commission_pct=_safe_float(trade.get("commission_pct"), 0.0),
                slippage_pct=_safe_float(trade.get("slippage_pct"), 0.0),
            )
            
            if notify:
                _broadcast_replay_followup(
                    trade,
                    trigger_state="STOP_LOSS_HIT",
                    close_price=trade["stop_loss"],
                    close_reason="BREAKEVEN_STOP_HIT" if reason == "Breakeven stop" else "STOP_LOSS_HIT",
                )


def _latest_replay_exit_price(trade: dict) -> float:
    """Return the latest replay-visible close price, falling back to entry."""
    try:
        from core.DataManager import DataManager

        frame = DataManager.get_intraday_data(trade["ticker"], limit=1, refresh_if_stale=False)
        if frame is not None and not frame.empty and "Close" in frame.columns:
            close_price = float(frame.iloc[-1]["Close"])
            if close_price > 0:
                return close_price
    except Exception:
        pass
    return float(trade.get("entry_price") or 0)


def _close_open_replay_positions_at_end() -> int:
    """Optionally flatten open INTRADAY replay positions at session end."""
    closed_count = 0
    for trade in list(_REPLAY_STATE["active_trades"]):
        if trade.get("state") not in {"OPEN", "TP1_HIT"}:
            continue

        if trade.get("signal_lane") == "SWING" or trade.get("is_intraday") is False:
            logger.info(f"[Replay] Preserving SWING position for {trade.get('ticker')} across session boundary.")
            continue

        ticker = trade.get("ticker")
        if not ticker:
            continue

        exit_price = _latest_replay_exit_price(trade)
        trade["state"] = "CLOSED"
        trade["exit_reason"] = "replay_end"
        trade["exit_price"] = exit_price
        trade["exit_at"] = TimeUtils.now().isoformat()
        _update_mock_position_state(
            ticker,
            "CLOSED",
            exit_price=exit_price,
            exit_reason="REPLAY_END_FLATTEN",
            commission_pct=_safe_float(trade.get("commission_pct"), 0.0),
            slippage_pct=_safe_float(trade.get("slippage_pct"), 0.0),
        )
        closed_count += 1

    if closed_count:
        logger.info(f"[Replay] Closed {closed_count} open INTRADAY replay positions at end of replay.")
    return closed_count
