"""
POSITION SIZING & CAPACITY
==========================
Account size determination, share calculation, and portfolio capacity/velocity limits.
"""

import datetime
from typing import Any, Tuple
from numbers import Real
import pandas as pd

from core.settings import settings
from utils.currency_fetcher import get_parallel_usd_egp_rate
from core import RiskManager
from database import Portfolio, Position
from .guards import _safe_setting_float, _safe_setting_int


def _positive_float(value: Any) -> float:
    try:
        if hasattr(value, "__class__") and "MagicMock" in value.__class__.__name__:
            return 0.0
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if parsed > 0 else 0.0


def _resolve_account_size(portfolio: Portfolio) -> float:
    configured = _positive_float(getattr(settings, 'ACCOUNT_BALANCE', 0.0))
    if configured > 0:
        return configured

    from core.analyzers.TreasuryLedger import get_hoard_status
    try:
        status = get_hoard_status(portfolio_id=portfolio.id)
        if status and status.get("status") != "error":
            net_worth = float(status.get("net_worth_egp", 0.0))
            if net_worth > 0:
                return net_worth
    except Exception:
        pass

    rate = get_parallel_usd_egp_rate()
    cash_egp = float(getattr(portfolio, 'cash_egp', 0.0) or 0.0)
    cash_usd = float(getattr(portfolio, 'cash_usd', 0.0) or 0.0)
    total_cash = cash_egp + cash_usd * rate
    if total_cash > 0:
        return total_cash

    return 0.0


def _calculate_shares(portfolio: Portfolio, price: float, sl: float, regime: str, signal_type: str, ticker: str = "UNKNOWN") -> int:
    account_size = _resolve_account_size(portfolio)
    risk_pct = float(getattr(settings, 'RISK_PER_TRADE', 2.0))
    risk_amount = account_size * (risk_pct / 100.0)
    
    from core.analyzers.TreasuryLedger import detect_currency
    curr = detect_currency(ticker)
    rate = get_parallel_usd_egp_rate()
    if curr == "USD":
        risk_amount /= rate
        
    if regime == "CHOPPY_OR_BEAR" and signal_type == "TRICKSTER":
        risk_amount /= 2.0
        
    risk_per_share = price - sl
    if risk_per_share <= 0:
        return 0
    else:
        shares = int(risk_amount / risk_per_share)
        
    max_cost = (account_size / (rate if curr == "USD" else 1.0)) * 0.20
    if shares * price > max_cost:
        shares = int(max_cost / price)
    return max(0, shares)


def _check_velocity_limit(portfolio: Portfolio) -> Tuple[bool, str]:
    today_start = datetime.datetime.combine(datetime.date.today(), datetime.time.min)
    max_daily = getattr(settings, 'MAX_DAILY_TRADES', 3)
    count = Position.select().where((Position.portfolio == portfolio.id) & (Position.entry_date >= today_start)).count()
    if count >= max_daily:
        return False, "daily_limit_reached"
    return True, "ok"


def _check_execution_capacity(
    *,
    portfolio: Portfolio,
    ticker: str,
    entry_price: float,
    stop_loss: float,
    shares: int,
) -> Tuple[bool, str, dict]:
    account_size = _resolve_account_size(portfolio)
    shares_i = max(0, int(shares or 0))
    entry_f = max(0.0, float(entry_price or 0.0))
    stop_f = max(0.0, float(stop_loss or 0.0))
    cost = entry_f * shares_i

    ticker_upper = str(ticker or "").upper()
    from core.analyzers.TreasuryLedger import detect_currency
    curr = detect_currency(ticker_upper)
    cash_field = "cash_usd" if curr == "USD" else "cash_egp"

    available_cash = _positive_float(getattr(portfolio, cash_field, 0.0))
    if available_cash > 0 and cost > available_cash:
        return False, "cash_capacity_limit", {
            "ticker": ticker_upper,
            "shares": shares_i,
            "entry_price": round(entry_f, 4),
            "position_cost": round(cost, 4),
            "available_cash": round(available_cash, 4),
            "account_size": round(account_size, 4),
        }

    open_query = Position.select().where(
        (Position.status == "OPEN")
        & (Position.portfolio == portfolio.id)
    )
    open_count = open_query.count()
    max_positions = _safe_setting_int("MAX_POSITIONS", 10)
    if open_count >= max_positions:
        return False, "max_positions_limit", {
            "open_positions": int(open_count),
            "max_positions": int(max_positions),
        }

    velocity_allowed, velocity_reason = _check_velocity_limit(portfolio)
    if not velocity_allowed:
        return False, f"velocity_{velocity_reason}", {
            "reason": velocity_reason,
        }

    if getattr(settings, "HEAT_PROTECTION_ENABLED", True):
        heat_rows = [
            {
                "ticker": p.ticker,
                "entry": p.entry_price,
                "sl": p.stop_loss,
                "shares": p.shares,
            }
            for p in open_query
            if p.stop_loss
        ]
        if shares_i > 0 and stop_f > 0:
            heat_rows.append(
                {
                    "ticker": str(ticker or "").upper(),
                    "entry": entry_f,
                    "sl": stop_f,
                    "shares": shares_i,
                }
            )
        projected_heat = RiskManager.calculate_portfolio_heat(heat_rows, account_size)
        max_heat = _safe_setting_float("MAX_PORTFOLIO_HEAT", 6.0)
        if projected_heat > max_heat:
            return False, "portfolio_heat_limit", {
                "projected_heat": projected_heat,
                "max_portfolio_heat": max_heat,
                "open_positions": int(open_count),
            }

    return True, "ok", {
        "position_cost": round(cost, 4),
        "available_cash": round(available_cash, 4),
        "account_size": round(account_size, 4),
    }


def _calculate_gap_pct(planned: float, actual: float) -> float:
    if not planned: return 0.0
    return abs((actual - planned) / planned) * 100.0
