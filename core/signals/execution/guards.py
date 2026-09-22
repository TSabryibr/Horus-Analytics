"""
EXECUTION GUARDS & OPERATOR LOCKOUT
===================================
Live execution armed checks, operator lockout, realized loss limits, and portfolio heat monitors.
"""

import json
import logging
import datetime
from typing import Tuple

from core.settings import settings
from core import TimeUtils, RiskManager, AlertManager
from core import subscriptions
from database import Portfolio, Position, Trade, SignalAuditEvent

logger = logging.getLogger('SignalExecutor.Guards')

_HEAT_BLOCK_LOG_STATE: dict[tuple, int] = {}
_LIVE_GUARD_LOG_STATE: dict[tuple, int] = {}


import sys

def _get_guard_symbol(name: str, fallback):
    mod = sys.modules.get("core.signals.executor")
    if mod is not None and hasattr(mod, name):
        val = getattr(mod, name)
        if val is not None and val is not fallback:
            return val
    return fallback


def _get_guard_logger():
    mod = sys.modules.get("core.signals.executor")
    if mod is not None and hasattr(mod, "logger"):
        return getattr(mod, "logger")
    return logger


def _log_live_guard_block(kind: str, run_id: int | None = None) -> int:
    time_utils = _get_guard_symbol("TimeUtils", TimeUtils)
    g_logger = _get_guard_logger()
    day_key = str(time_utils.today())
    key = (kind, day_key)
    repeat_count = int(_LIVE_GUARD_LOG_STATE.get(key, 0) + 1)
    _LIVE_GUARD_LOG_STATE[key] = repeat_count

    if kind == "pending_entries":
        message = "[SignalExecutor] Pending entries blocked by live execution guard."
    else:
        message = f"[SignalExecutor] Live execution guard blocked run_id={run_id}"

    if repeat_count == 1:
        g_logger.warning(message)
    else:
        g_logger.info("%s repeat_count=%s", message, repeat_count)
    return repeat_count


def _record_heat_block(portfolio: Portfolio, heat_reason: str, heat_val: float) -> int:
    time_utils = _get_guard_symbol("TimeUtils", TimeUtils)
    alert_mgr = _get_guard_symbol("AlertManager", AlertManager)
    g_logger = _get_guard_logger()
    key = (
        time_utils.today().isoformat(),
        getattr(portfolio, "id", None) or getattr(portfolio, "name", "UNKNOWN"),
        heat_reason,
    )
    repeat_count = int(_HEAT_BLOCK_LOG_STATE.get(key, 0) + 1)
    _HEAT_BLOCK_LOG_STATE[key] = repeat_count
    if repeat_count == 1:
        g_logger.critical(f"[HEAT] Execution halted for {portfolio.name}: {heat_reason} ({heat_val}%)")
        if subscriptions.automated_main_channel_signal_allowed(subscriptions.MANAGED_ADVISORY):
            alert_mgr.broadcast_alert(
                "*PORTFOLIO HEAT LIMIT REACHED*\n"
                f"Portfolio: {portfolio.name}\n"
                f"Heat: {heat_val:.2f}%\n"
                "Auto-Entries halted."
            )
        else:
            g_logger.info("[SignalExecutor] Heat alert suppressed by managed-advisory channel policy.")
    else:
        g_logger.warning(
            f"[HEAT] Repeated execution halt for {portfolio.name}: {heat_reason} "
            f"({heat_val}%) repeat_count={repeat_count}"
        )
    return repeat_count


def _check_portfolio_heat(portfolio: Portfolio) -> Tuple[bool, str, float]:
    from .sizing import _resolve_account_size

    current_settings = _get_guard_symbol("settings", settings)
    risk_mgr = _get_guard_symbol("RiskManager", RiskManager)

    if not getattr(current_settings, "HEAT_PROTECTION_ENABLED", True):
        return True, "heat_protection_disabled", 0.0

    open_positions = list(Position.select().where((Position.status == "OPEN") & (Position.portfolio == portfolio.id)))
    account_size = _resolve_account_size(portfolio)
    heat_input = [{'ticker': p.ticker, 'entry': p.entry_price, 'sl': p.stop_loss, 'shares': p.shares} for p in open_positions if p.stop_loss]
    current_heat = risk_mgr.calculate_portfolio_heat(heat_input, account_size)
    max_heat = getattr(current_settings, 'MAX_PORTFOLIO_HEAT', 6.0)
    if current_heat >= max_heat:
        return False, "heat_limit_reached", current_heat
    return True, "ok", current_heat


def _safe_setting_float(name: str, default: float) -> float:
    try:
        return float(getattr(settings, name, default))
    except (TypeError, ValueError):
        return float(default)


def _safe_setting_int(name: str, default: int) -> int:
    try:
        return int(getattr(settings, name, default))
    except (TypeError, ValueError):
        return int(default)


def _emit_operator_event(
    event_type: str,
    *,
    severity: str = "INFO",
    message: str | None = None,
    details: dict | None = None,
    portfolio: Portfolio | None = None,
) -> None:
    try:
        SignalAuditEvent.create(
            event_type=str(event_type or "").upper().strip() or "OPERATOR_EVENT",
            severity=str(severity or "INFO").upper().strip() or "INFO",
            actor_type="OPERATOR",
            actor_id=None,
            portfolio=portfolio,
            entity_type="PORTFOLIO" if portfolio is not None else None,
            entity_id=str(getattr(portfolio, "id", "")) if portfolio is not None else None,
            message=message,
            details_json=json.dumps(details or {}, default=str),
        )
    except Exception:
        pass


def _manual_override_abuse_state(today_value=None) -> dict:
    if today_value is None:
        today_value = TimeUtils.today()
    day_start = datetime.datetime.combine(today_value, datetime.time.min)
    day_end = day_start + datetime.timedelta(days=1)
    max_per_day = _safe_setting_int("LIVE_MAX_MANUAL_OVERRIDES_PER_DAY", 3)
    count = (
        SignalAuditEvent.select()
        .where(
            (SignalAuditEvent.event_type == "OPERATOR_MANUAL_OVERRIDE")
            & (SignalAuditEvent.created_at >= day_start)
            & (SignalAuditEvent.created_at < day_end)
        )
        .count()
    )
    return {
        "today": str(today_value),
        "manual_override_count": int(count),
        "max_manual_overrides_per_day": int(max_per_day),
        "manual_override_lockout": bool(int(count) >= int(max_per_day)),
    }


def _compute_realized_loss_state(portfolio: Portfolio, account_size: float) -> dict:
    now = TimeUtils.now()
    day_start = datetime.datetime.combine(now.date(), datetime.time.min)
    week_start = day_start - datetime.timedelta(days=day_start.weekday())
    closed_trades = list(
        Trade.select()
        .where(
            (Trade.portfolio == portfolio.id)
            & (Trade.exit_date <= now)
        )
        .order_by(Trade.exit_date.desc())
    )
    daily_loss = 0.0
    weekly_loss = 0.0
    for trade in closed_trades:
        pnl = float(getattr(trade, "pnl", 0.0) or 0.0)
        if pnl >= 0:
            continue
        loss = abs(pnl)
        if trade.exit_date >= day_start:
            daily_loss += loss
        if trade.exit_date >= week_start:
            weekly_loss += loss

    consecutive_losses = 0
    last_loss_exit_at = None
    for trade in closed_trades:
        pnl = float(getattr(trade, "pnl", 0.0) or 0.0)
        if pnl < 0:
            consecutive_losses += 1
            if last_loss_exit_at is None:
                last_loss_exit_at = trade.exit_date
            continue
        break

    asc_trades = list(reversed(closed_trades))
    equity = float(account_size)
    peak = float(account_size)
    max_drawdown_pct = 0.0
    if peak > 0:
        for trade in asc_trades:
            equity += float(getattr(trade, "pnl", 0.0) or 0.0)
            if equity > peak:
                peak = equity
            if peak <= 0:
                continue
            drawdown_pct = ((peak - equity) / peak) * 100.0
            if drawdown_pct > max_drawdown_pct:
                max_drawdown_pct = drawdown_pct

    daily_loss_pct = (daily_loss / account_size) * 100.0 if account_size > 0 else 0.0
    weekly_loss_pct = (weekly_loss / account_size) * 100.0 if account_size > 0 else 0.0
    cooldown_minutes = None
    if last_loss_exit_at is not None:
        cooldown_minutes = max(0.0, (now - last_loss_exit_at).total_seconds() / 60.0)
    return {
        "daily_loss": round(daily_loss, 4),
        "weekly_loss": round(weekly_loss, 4),
        "daily_loss_pct": round(daily_loss_pct, 4),
        "weekly_loss_pct": round(weekly_loss_pct, 4),
        "consecutive_losses": int(consecutive_losses),
        "max_drawdown_pct": round(max_drawdown_pct, 4),
        "stressed_drawdown_pct": round(max_drawdown_pct * 2.0, 4),
        "cooldown_minutes_since_last_loss": round(float(cooldown_minutes), 4) if cooldown_minutes is not None else None,
    }


def _check_operator_lockout(portfolio: Portfolio) -> Tuple[bool, str, dict]:
    from .sizing import _resolve_account_size

    account_size = _resolve_account_size(portfolio)
    if account_size <= 0:
        return True, "account_unavailable", {"account_size": account_size}

    loss_state = _compute_realized_loss_state(portfolio, account_size)
    max_daily_loss_pct = _safe_setting_float("LIVE_MAX_DAILY_LOSS_PCT", 3.0)
    max_consecutive_losses = _safe_setting_int("LIVE_MAX_CONSECUTIVE_LOSSES", 4)
    override_state = _manual_override_abuse_state()

    reasons = []
    if float(loss_state.get("daily_loss_pct", 0.0) or 0.0) >= max_daily_loss_pct:
        reasons.append("daily_loss_limit")
    if int(loss_state.get("consecutive_losses", 0) or 0) >= max_consecutive_losses:
        reasons.append("consecutive_losses_limit")
    if bool(override_state.get("manual_override_lockout")):
        reasons.append("manual_override_abuse")

    if reasons:
        details = {
            "portfolio_id": getattr(portfolio, "id", None),
            "portfolio_name": getattr(portfolio, "name", None),
            "reasons": reasons,
            "loss_state": loss_state,
            "max_daily_loss_pct": max_daily_loss_pct,
            "max_consecutive_losses": max_consecutive_losses,
            "manual_override_state": override_state,
        }
        _emit_operator_event(
            "OPERATOR_LOCKOUT",
            severity="WARN",
            message=f"Operator lockout active for {getattr(portfolio, 'name', 'UNKNOWN')}",
            details=details,
            portfolio=portfolio,
        )
        return False, reasons[0], details
    return True, "ok", {
        "loss_state": loss_state,
        "manual_override_state": override_state,
    }
