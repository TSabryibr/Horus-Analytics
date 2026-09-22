import json
import warnings
from typing import Any, Optional


from core import PositionTracker, TelegramBot_Alerts, TimeUtils, subscriptions
from core.DataManager import DataManager
from database import HorusExecution, Position, Portfolio, Trade

from .identity import get_horus_portfolio
from .telegram import build_close_message


def _managed_advisory_main_channel_allowed() -> bool:
    return subscriptions.automated_main_channel_signal_allowed(subscriptions.MANAGED_ADVISORY)


def _execution_details(execution: HorusExecution) -> dict[str, Any]:
    try:
        payload = json.loads(execution.details_json or "{}")
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _active_executions(portfolio: Portfolio) -> list[HorusExecution]:
    return list(
        HorusExecution.select()
        .where(
            (HorusExecution.portfolio == portfolio) &
            (HorusExecution.state.in_(["OPEN", "UPDATED"]))
        )
        .order_by(HorusExecution.updated_at.asc(), HorusExecution.id.asc())
    )


def _open_position_for_execution(portfolio: Portfolio, execution: HorusExecution) -> Optional[Position]:
    return Position.get_or_none(
        (Position.portfolio == portfolio) &
        (Position.ticker == execution.ticker) &
        (Position.status == "OPEN")
    )


def _latest_bar(ticker: str):
    intra_df = DataManager.get_intraday_data(ticker, limit=1, refresh_if_stale=False)
    if intra_df is None or intra_df.empty:
        return None
    return intra_df.iloc[-1], intra_df.index[-1]


def _close_reason_for_stop(position: Position, execution: HorusExecution) -> str:
    base_stop = None
    if execution.recommendation and execution.recommendation.stop_loss is not None:
        base_stop = float(execution.recommendation.stop_loss)
    elif execution.planned_entry_price is not None:
        base_stop = float(execution.planned_entry_price)

    current_stop = float(execution.active_stop_loss or position.stop_loss or 0.0)
    details = _execution_details(execution)
    trailing_pct = details.get("trailing_pct")
    if trailing_pct is not None and base_stop is not None and current_stop > float(base_stop):
        return "TRAILING_STOP"
    return "STOP_LOSS"


def _update_trailing_stop(position: Position, execution: HorusExecution, close_price: float) -> bool:
    details = _execution_details(execution)
    trailing_pct = details.get("trailing_pct")
    if trailing_pct is None:
        return False

    potential_stop = float(close_price) * (1 - (float(trailing_pct) / 100.0))
    current_stop = float(execution.active_stop_loss or position.stop_loss or 0.0)
    if potential_stop <= current_stop:
        return False

    if not PositionTracker.update_position(
        ticker=position.ticker,
        sl=float(potential_stop),
        portfolio_id=position.portfolio_id,
    ):
        return False

    trailing_state = {
        "previous_stop_loss": current_stop,
        "current_stop_loss": float(potential_stop),
        "updated_at": TimeUtils.now().isoformat(),
    }
    details["trailing_armed"] = True
    details["trailing_pct"] = float(trailing_pct)
    execution.active_stop_loss = float(potential_stop)
    execution.trailing_state = json.dumps(trailing_state)
    execution.details_json = json.dumps(details)
    execution.updated_at = TimeUtils.now()
    execution.save()
    return True


def _close_execution(position: Position, execution: HorusExecution, exit_price: float, reason: str) -> bool:
    closed = PositionTracker.close_position(
        ticker=position.ticker,
        exit_price=float(exit_price),
        reason=reason,
        portfolio_id=position.portfolio_id,
    )
    if not closed:
        return False

    trade = (
        Trade.select()
        .where((Trade.portfolio == position.portfolio) & (Trade.ticker == position.ticker))
        .order_by(Trade.exit_date.desc(), Trade.id.desc())
        .first()
    )
    execution.state = "CLOSED"
    execution.close_reason = reason
    execution.trade_id = trade.id if trade else None
    execution.updated_at = TimeUtils.now()
    execution.save()

    if not execution.close_message_id and _managed_advisory_main_channel_allowed():
        tg_resp = TelegramBot_Alerts.send_message(build_close_message(position.portfolio, execution, trade))
        if tg_resp.get("ok"):
            message_id = ((tg_resp.get("result") or {}).get("message_id"))
            execution.close_message_id = str(message_id) if message_id is not None else None
            execution.save()

    return True


def monitor_horus_positions() -> dict[str, Any]:
    warnings.warn("monitor_horus_positions is deprecated. Use core.signals.system_monitor.monitor_system_positions instead.", DeprecationWarning, stacklevel=2)
    portfolio = get_horus_portfolio()

    if not portfolio:
        return {"status": "skipped", "summary": {"closed": 0, "updated": 0, "failed": 0}}

    summary = {"closed": 0, "updated": 0, "failed": 0}

    for execution in _active_executions(portfolio):
        position = _open_position_for_execution(portfolio, execution)
        if not position:
            continue

        try:
            bar_payload = _latest_bar(execution.ticker)
            if not bar_payload:
                continue
            last_bar, bar_time = bar_payload
            if bar_time <= position.entry_date:
                continue

            low_price = float(last_bar["Low"])
            high_price = float(last_bar["High"])
            close_price = float(last_bar["Close"])
            active_stop = float(execution.active_stop_loss or position.stop_loss or 0.0)
            active_target = float(execution.active_target_price or position.target_price or 0.0)

            if low_price <= active_stop:
                reason = _close_reason_for_stop(position, execution)
                if _close_execution(position, execution, active_stop, reason):
                    summary["closed"] += 1
                else:
                    summary["failed"] += 1
                continue

            if high_price >= active_target and active_target > 0:
                if _close_execution(position, execution, active_target, "TARGET"):
                    summary["closed"] += 1
                else:
                    summary["failed"] += 1
                continue

            if _update_trailing_stop(position, execution, close_price):
                summary["updated"] += 1
        except Exception:
            summary["failed"] += 1

    return {"status": "completed", "summary": summary}
