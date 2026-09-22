"""
RISK GATES & VALIDATION
=======================
Mimir WFA verification, whale trap enforcement, correlation, macro regime, and live risk contracts.
"""

import json
import logging
from typing import Tuple, Any
from numbers import Real
import pandas as pd

from core.settings import settings
from core import WalkForwardValidation, RiskManager
from core.DataManager import DataManager
from core.sovereign_confluence import sovereign_confluence_engine as confluence_engine
from database import Portfolio, Position, SignalRun, SignalRecommendation
from .guards import (
    _safe_setting_float,
    _safe_setting_int,
    _compute_realized_loss_state,
)
from .sizing import (
    _resolve_account_size,
    _calculate_shares,
    _check_velocity_limit,
)

logger = logging.getLogger('SignalExecutor.RiskGates')


def _check_nonzero_cost_assumptions() -> Tuple[bool, str, dict]:
    require_nonzero = bool(getattr(settings, "LIVE_REQUIRE_NONZERO_COSTS", True))
    if not require_nonzero:
        return True, "disabled", {"required": False}
    commission_pct = _safe_setting_float("COMMISSION_PCT", 0.0)
    slippage_pct = _safe_setting_float("SLIPPAGE_PCT", 0.0)
    if commission_pct <= 0:
        return False, "commission_non_positive", {"commission_pct": commission_pct}
    if slippage_pct <= 0:
        return False, "slippage_non_positive", {"slippage_pct": slippage_pct}
    return True, "ok", {"commission_pct": commission_pct, "slippage_pct": slippage_pct}


def _compute_crisis_correlation(tickers: list[str]) -> float:
    clean = list(dict.fromkeys([str(t or "").upper() for t in tickers if str(t or "").strip()]))
    if len(clean) < 2:
        return 0.0
    matrix = RiskManager.get_correlation_matrix(clean)
    if matrix is None or matrix.empty:
        return 0.0
    max_corr = 0.0
    cols = list(matrix.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            value = matrix.iloc[i, j]
            try:
                corr = abs(float(value))
            except (TypeError, ValueError):
                continue
            if corr > max_corr:
                max_corr = corr
    return round(max_corr, 4)


def _compute_liquidity_exit_capacity(
    portfolio: Portfolio,
    ticker: str,
    entry_price: float,
    shares: int,
) -> dict:
    positions = list(
        Position.select().where(
            (Position.status == "OPEN")
            & (Position.portfolio == portfolio.id)
        )
    )
    exposure_rows = [
        {
            "ticker": str(p.ticker or "").upper(),
            "value": max(0.0, float(p.shares or 0) * float(p.current_price or p.entry_price or 0.0)),
        }
        for p in positions
    ]
    if shares > 0 and entry_price > 0:
        exposure_rows.append(
            {
                "ticker": str(ticker or "").upper(),
                "value": float(shares) * float(entry_price),
            }
        )

    max_participation_pct = 0.0
    worst_ticker = None
    missing_data: list[str] = []
    for row in exposure_rows:
        symbol = row["ticker"]
        if not symbol:
            continue
        df = DataManager.get_stock_data(symbol, include_live=False)
        if df is None or df.empty or "Close" not in df.columns or "Volume" not in df.columns:
            missing_data.append(symbol)
            continue
        recent = df.tail(20)
        adv_dollar = float((recent["Close"] * recent["Volume"]).mean() or 0.0)
        if adv_dollar <= 0:
            missing_data.append(symbol)
            continue
        participation_pct = (float(row["value"]) / adv_dollar) * 100.0
        if participation_pct > max_participation_pct:
            max_participation_pct = participation_pct
            worst_ticker = symbol
    return {
        "max_exit_participation_pct": round(max_participation_pct, 4),
        "worst_ticker": worst_ticker,
        "missing_liquidity_data": sorted(set(missing_data)),
    }


def _check_live_risk_contract(
    *,
    portfolio: Portfolio,
    ticker: str,
    entry_price: float,
    stop_loss: float,
    shares: int,
) -> Tuple[bool, str, dict]:
    cost_ok, cost_reason, cost_data = _check_nonzero_cost_assumptions()
    if not cost_ok:
        return False, cost_reason, cost_data

    account_size = _resolve_account_size(portfolio)
    if account_size <= 0:
        return False, "missing_account_size", {"account_size": account_size}

    risk_per_share = max(0.0, float(entry_price) - float(stop_loss))
    per_trade_risk = risk_per_share * max(0, int(shares))
    per_trade_risk_pct = (per_trade_risk / account_size) * 100.0 if account_size > 0 else 0.0
    max_risk_per_trade_pct = _safe_setting_float(
        "LIVE_MAX_RISK_PER_TRADE_PCT",
        _safe_setting_float("RISK_PER_TRADE", 2.0),
    )
    if per_trade_risk_pct > max_risk_per_trade_pct:
        return False, "per_trade_risk_limit", {
            "per_trade_risk_pct": round(per_trade_risk_pct, 4),
            "max_risk_per_trade_pct": round(max_risk_per_trade_pct, 4),
        }

    loss_state = _compute_realized_loss_state(portfolio, account_size)
    max_daily_loss_pct = _safe_setting_float("LIVE_MAX_DAILY_LOSS_PCT", 3.0)
    if float(loss_state.get("daily_loss_pct", 0.0) or 0.0) >= max_daily_loss_pct:
        return False, "daily_loss_limit", {**loss_state, "max_daily_loss_pct": max_daily_loss_pct}

    max_weekly_loss_pct = _safe_setting_float("LIVE_MAX_WEEKLY_LOSS_PCT", 6.0)
    if float(loss_state.get("weekly_loss_pct", 0.0) or 0.0) >= max_weekly_loss_pct:
        return False, "weekly_loss_limit", {**loss_state, "max_weekly_loss_pct": max_weekly_loss_pct}

    max_consecutive_losses = _safe_setting_int("LIVE_MAX_CONSECUTIVE_LOSSES", 4)
    if int(loss_state.get("consecutive_losses", 0) or 0) >= max_consecutive_losses:
        return False, "consecutive_losses_limit", {**loss_state, "max_consecutive_losses": max_consecutive_losses}

    cooldown_minutes = _safe_setting_float("LIVE_LOSS_COOLDOWN_MINUTES", 60.0)
    elapsed = loss_state.get("cooldown_minutes_since_last_loss")
    if elapsed is not None and float(elapsed) < cooldown_minutes:
        return False, "loss_cooldown_active", {
            **loss_state,
            "cooldown_minutes_required": cooldown_minutes,
        }

    max_drawdown_pct = _safe_setting_float("LIVE_MAX_DRAWDOWN_PCT", 20.0)
    if float(loss_state.get("max_drawdown_pct", 0.0) or 0.0) >= max_drawdown_pct:
        return False, "max_drawdown_limit", {**loss_state, "max_drawdown_limit_pct": max_drawdown_pct}

    max_stress_drawdown_pct = _safe_setting_float("LIVE_MAX_STRESS_DRAWDOWN_PCT", 35.0)
    if float(loss_state.get("stressed_drawdown_pct", 0.0) or 0.0) >= max_stress_drawdown_pct:
        return False, "stressed_drawdown_limit", {**loss_state, "max_stress_drawdown_pct": max_stress_drawdown_pct}

    open_tickers = [
        str(p.ticker or "").upper()
        for p in Position.select(Position.ticker).where((Position.status == "OPEN") & (Position.portfolio == portfolio.id))
    ]
    crisis_corr = _compute_crisis_correlation(open_tickers + [ticker])
    max_crisis_corr = _safe_setting_float("LIVE_MAX_CRISIS_CORRELATION", 0.85)
    if crisis_corr > max_crisis_corr:
        return False, "crisis_correlation_limit", {
            "crisis_correlation": crisis_corr,
            "max_crisis_correlation": max_crisis_corr,
        }

    liquidity = _compute_liquidity_exit_capacity(
        portfolio=portfolio,
        ticker=ticker,
        entry_price=float(entry_price),
        shares=int(shares),
    )
    max_exit_participation_pct = _safe_setting_float("LIVE_MAX_LIQUIDITY_EXIT_PCT", 5.0)
    if float(liquidity.get("max_exit_participation_pct", 0.0) or 0.0) > max_exit_participation_pct:
        return False, "liquidity_exit_capacity_limit", {
            **liquidity,
            "max_liquidity_exit_pct": max_exit_participation_pct,
        }

    return True, "ok", {
        "per_trade_risk_pct": round(per_trade_risk_pct, 4),
        "loss_state": loss_state,
        "crisis_correlation": crisis_corr,
        "liquidity": liquidity,
    }


def _check_entry_gate(ticker: str) -> Tuple[bool, str, dict]:
    try:
        gate = WalkForwardValidation.get_trade_permission(ticker.upper(), fail_closed=True)
        if not isinstance(gate, dict): return False, "invalid_response", {}
        return bool(gate.get("allowed", False)), str(gate.get("reason", "blocked")), gate
    except Exception as e:
        return False, "lookup_error", {"error": str(e)}


def _check_whale_trap(rec: SignalRecommendation) -> bool:
    from .orders import _get_rec_json
    return str(_get_rec_json(rec, "Enforcement_State", "ALLOW")).upper() != "BLOCK_EXECUTION"


def _check_sovereign_confluence(ticker: str, signal_type: str) -> bool:
    if signal_type != 'BUY': return True
    trap = confluence_engine.get_active_trap(ticker)
    return not (trap and trap.get("type") == "SOVEREIGN_BEAR_TRAP")


def _check_correlation(portfolio: Portfolio, ticker: str) -> Tuple[bool, str, dict]:
    try:
        open_tickers = [p.ticker for p in Position.select(Position.ticker).where((Position.status == "OPEN") & (Position.portfolio == portfolio.id))]
        res = RiskManager.check_new_trade_correlation(open_tickers, ticker)
        if not res.get('is_safe', True):
            return False, "high_correlation", {"culprit": res.get('most_correlated_with')}
        return True, "ok", {}
    except Exception as e:
        return False, "check_failed", {"error": str(e)}


def _check_sector_limit(portfolio: Portfolio, ticker: str) -> Tuple[bool, str, dict]:
    try:
        open_tickers = [p.ticker for p in Position.select(Position.ticker).where((Position.status == "OPEN") & (Position.portfolio == portfolio.id))]
        allowed, warning = RiskManager.check_sector_exposure(ticker, open_tickers)
        if not allowed:
            return False, "limit_exceeded", {"warning": warning}
        return True, "ok", {}
    except Exception as e:
        return False, "check_failed", {"error": str(e)}


def _is_regime_filter_enabled() -> bool:
    return bool(getattr(settings, "REGIME_FILTER_ENABLED", False))


def _check_macro_regime(signal_type: str) -> Tuple[str, dict]:
    try:
        egx_df = DataManager.get_stock_data("EGX30", source="CSV", folder=settings.METASTOCK_HISTORY_FOLDER)
        if egx_df is not None and len(egx_df) >= 20:
            egx_close = egx_df['Close'].iloc[-1]
            ema10 = egx_df['Close'].ewm(span=10, adjust=False).mean().iloc[-1]
            ema20 = egx_df['Close'].ewm(span=20, adjust=False).mean().iloc[-1]
            if egx_close > ema10 and ema10 > ema20:
                return "STRONG_BULL", {"close": egx_close, "ema10": ema10, "ema20": ema20}
            return "CHOPPY_OR_BEAR", {"close": egx_close, "ema10": ema10, "ema20": ema20}
        return "UNKNOWN", {"reason": "insufficient_market_data"}
    except Exception as e:
        logger.error(f"Regime filter error: {e}")
        return "UNKNOWN", {"error": str(e)}


import sys


def _get_executor_dispatch(name: str, fallback):
    mod = sys.modules.get("core.signals.executor")
    if mod is not None:
        cls = getattr(mod, "SignalExecutor", None)
        if cls is not None and hasattr(cls, name):
            val = getattr(cls, name)
            if val is not fallback:
                return val
        if hasattr(mod, name):
            val = getattr(mod, name)
            if val is not fallback:
                return val
    return fallback


def _run_risk_gates(portfolio: Portfolio, run: SignalRun, rec: SignalRecommendation) -> Tuple[bool, str, dict]:
    """Runs the sequential risk gate pipeline."""
    from .orders import _get_rec_json

    check_cost_fn = _get_executor_dispatch("_check_nonzero_cost_assumptions", _check_nonzero_cost_assumptions)
    cost_ok, cost_reason, cost_data = check_cost_fn()
    if not cost_ok:
        return False, f"cost_{cost_reason}", cost_data
    
    # 1. Mimir WFA Gate
    check_entry_fn = _get_executor_dispatch("_check_entry_gate", _check_entry_gate)
    allowed, reason, gate_data = check_entry_fn(rec.ticker)
    if not allowed: return False, f"mimir_{reason}", gate_data

    # 2. Whale Trap Enforcement
    check_whale_fn = _get_executor_dispatch("_check_whale_trap", _check_whale_trap)
    if not check_whale_fn(rec):
        return False, "whale_trap_blocked", {"state": _get_rec_json(rec, "Enforcement_State", "ALLOW")}

    # 3. Sovereign Confluence
    check_sov_fn = _get_executor_dispatch("_check_sovereign_confluence", _check_sovereign_confluence)
    if not check_sov_fn(rec.ticker, rec.side):
        return False, "sovereign_bear_trap", {}

    # 4. Correlation Check
    check_corr_fn = _get_executor_dispatch("_check_correlation", _check_correlation)
    allowed, reason, data = check_corr_fn(portfolio, rec.ticker)
    if not allowed: return False, f"correlation_{reason}", data

    # 5. Sector Exposure
    check_sec_fn = _get_executor_dispatch("_check_sector_limit", _check_sector_limit)
    allowed, reason, data = check_sec_fn(portfolio, rec.ticker)
    if not allowed: return False, f"sector_{reason}", data

    # 6. Velocity Limit
    check_vel_fn = _get_executor_dispatch("_check_velocity_limit", _check_velocity_limit)
    allowed, reason = check_vel_fn(portfolio)
    if not allowed: return False, f"velocity_{reason}", {}

    # 7. Macro Regime
    regime_enabled_fn = _get_executor_dispatch("_is_regime_filter_enabled", _is_regime_filter_enabled)
    regime_filter_enabled = regime_enabled_fn()
    check_macro_fn = _get_executor_dispatch("_check_macro_regime", _check_macro_regime)
    regime, regime_data = (
        check_macro_fn(rec.side)
        if regime_filter_enabled
        else ("REGIME_FILTER_DISABLED", {"reason": "settings_disabled"})
    )
    if regime_filter_enabled:
        if regime == "UNKNOWN" and rec.side == "BUY":
            return False, "macro_regime_unavailable", regime_data
        if regime == "CHOPPY_OR_BEAR" and rec.side == "BUY":
            return False, "macro_regime_blocked", regime_data

    calc_shares_fn = _get_executor_dispatch("_calculate_shares", _calculate_shares)
    tentative_shares = calc_shares_fn(
        portfolio=portfolio,
        ticker=rec.ticker,
        price=float(rec.entry_price),
        sl=float(rec.stop_loss),
        regime=regime,
        signal_type=str(rec.side or "BUY").upper(),
    )
    check_contract_fn = _get_executor_dispatch("_check_live_risk_contract", _check_live_risk_contract)
    contract_ok, contract_reason, contract_data = check_contract_fn(
        portfolio=portfolio,
        ticker=str(rec.ticker or "").upper(),
        entry_price=float(rec.entry_price),
        stop_loss=float(rec.stop_loss),
        shares=tentative_shares,
    )
    if not contract_ok:
        return False, f"risk_contract_{contract_reason}", contract_data

    return True, "allowed", {}
