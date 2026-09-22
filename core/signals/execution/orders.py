"""
ORDERS, ATTRIBUTION & MESSAGING
================================
Order execution routing, position tracking, audit attribution, and Telegram message dispatching.
"""

import json
import logging
from typing import Any, Optional, Tuple
from numbers import Real
import pandas as pd

import sys
from core import PositionTracker, TelegramBot_Alerts, TimeUtils
from core import subscriptions
from core.DataManager import DataManager
from database import (
    HorusExecution,
    Portfolio,
    Position,
    SignalExecutionAttribution,
    SignalRecommendation,
    SignalRun,
)
from core.signals.routing import resolve_target_portfolio
from core.strategy_profile_portfolios import resolve_strategy_profile_portfolio
from core.horus.telegram import build_open_message, build_update_message, build_skip_message, recommendation_target2


def _get_executor_symbol(name: str, fallback):
    mod = sys.modules.get("core.signals.executor")
    if mod is not None and hasattr(mod, name):
        val = getattr(mod, name)
        if val is not None and val is not fallback:
            return val
    return fallback


from .guards import (
    _safe_setting_float,
)
from .sizing import (
    _calculate_shares,
    _check_execution_capacity,
)
from .risk_gates import (
    _is_regime_filter_enabled,
    _check_macro_regime,
    _check_live_risk_contract,
)

logger = logging.getLogger('SignalExecutor.Orders')


def _send_main_channel_signal_message(message: str) -> dict:
    if not subscriptions.automated_main_channel_signal_allowed():
        logger.info("[SignalExecutor] Main channel signal message suppressed by channel policy.")
        return {"ok": False, "suppressed": True, "description": "main_channel_signal_level_policy"}
    tb_alerts = _get_executor_symbol("TelegramBot_Alerts", TelegramBot_Alerts)
    return tb_alerts.send_message(message)


def _get_trigger_source(run: SignalRun) -> str:
    st = str(run.scan_type or "INTRADAY").upper()
    if st == "DAILY": return "DAILY_NEXT_OPEN"
    return st


def _resolve_lane(scan_type: str) -> str:
    normalized = str(scan_type or "").upper().strip()
    if normalized == "INTRADAY":
        return "INTRADAY"
    if normalized in {"PRE_CLOSE", "DAILY", "DAILY_NEXT_OPEN"}:
        return "SWING"
    if normalized == "WEEKLY":
        return "POSITION"
    return "SWING"


def _resolve_execution_portfolio(scan_type: str, recommendations: list[SignalRecommendation]) -> Optional[Portfolio]:
    return resolve_target_portfolio(scan_type)


def _find_cross_portfolio_signal_position(portfolio: Portfolio, ticker: str) -> Optional[Position]:
    signal_portfolio_names = {"Intraday Signals", "Swing Signals", "Position Signals"}
    current_name = str(getattr(portfolio, "name", "") or "")
    if current_name not in signal_portfolio_names:
        return None

    return (
        Position.select(Position, Portfolio)
        .join(Portfolio)
        .where(
            (Position.status == "OPEN")
            & (Position.ticker == str(ticker or "").upper())
            & (Portfolio.type == "SYSTEM")
            & (Portfolio.name.in_(signal_portfolio_names))
            & (Position.portfolio != portfolio.id)
        )
        .order_by(Position.entry_date.desc(), Position.id.desc())
        .first()
    )


def _get_existing_position_update_skip(position: Position, rec: SignalRecommendation) -> Tuple[Optional[str], dict]:
    previous = {
        "position_id": getattr(position, "id", None),
        "entry_price": float(position.entry_price or 0.0),
        "stop_loss": float(position.stop_loss or 0.0),
        "target_price": float(position.target_price or 0.0),
        "target_price_2": float(position.target_price_2 or 0.0),
        "tp1_hit": bool(getattr(position, "tp1_hit", False)),
    }
    requested = {
        "entry_price": float(rec.entry_price or 0.0),
        "stop_loss": float(rec.stop_loss or 0.0),
        "target_price": float(rec.target_price or 0.0),
        "target_price_2": float(recommendation_target2(rec) or 0.0),
    }

    if previous["tp1_hit"]:
        return "existing_position_already_managed_after_tp1", {
            "reason": "existing_position_already_managed_after_tp1",
            "previous": previous,
            "requested": requested,
        }

    existing_entry = previous["entry_price"]
    requested_entry = requested["entry_price"]
    if existing_entry > 0 and requested_entry > 0:
        drift_pct = abs(requested_entry - existing_entry) / existing_entry * 100.0
        max_drift_pct = _safe_setting_float(
            "EXISTING_SIGNAL_UPDATE_MAX_ENTRY_DRIFT_PCT",
            1.5,
        )
        if drift_pct > max_drift_pct:
            return "existing_position_entry_mismatch", {
                "reason": "existing_position_entry_mismatch",
                "entry_drift_pct": drift_pct,
                "max_entry_drift_pct": max_drift_pct,
                "previous": previous,
                "requested": requested,
            }

    return None, {}


def _get_rec_json(rec: SignalRecommendation, key: str, default: Any = None) -> Any:
    if not rec or not rec.rationale_json: return default
    try:
        payload = json.loads(rec.rationale_json)
        return payload.get(key, default)
    except Exception:
        return default


def _get_next_open_price(ticker: str) -> Tuple[Optional[float], Optional[str]]:
    try:
        df = DataManager.get_intraday_data(ticker, limit=1, refresh_if_stale=False)
        if df is not None and not df.empty:
            return float(df.iloc[0]['Open']), df.index[0].isoformat()
    except Exception as e:
        logger.debug(f"Failed to get next open price for {ticker}: {e}", exc_info=True)
    return None, None


def _validate_signal(rec: SignalRecommendation) -> Tuple[bool, str, dict]:
    from core.settings import settings
    def _is_number(val: Any) -> bool:
        return isinstance(val, Real) and not pd.isna(val)

    entry = rec.entry_price
    stop = rec.stop_loss
    target = rec.target_price
    if not all(_is_number(v) for v in (entry, stop, target)):
        return False, "invalid_values", {"entry": entry, "stop_loss": stop, "target_price": target}

    entry_f = float(entry)
    stop_f = float(stop)
    target_f = float(target)
    score_f = float(getattr(rec, "score", 0.0) or 0.0)
    confidence_f = float(getattr(rec, "confidence", 0.0) or 0.0)
    if entry_f <= 0 or stop_f <= 0 or target_f <= 0:
        return False, "invalid_non_positive_prices", {"entry": entry_f, "stop_loss": stop_f, "target_price": target_f}
    min_score = max(0.0, float(getattr(settings, "MIN_SIGNAL_SCORE", 0.0)))
    if score_f < min_score:
        return False, "below_min_signal_score", {"score": score_f, "minimum": min_score}
    min_confidence = max(0.0, float(getattr(settings, "MIN_SIGNAL_CONFIDENCE", 0.0)))
    if confidence_f < min_confidence:
        return False, "below_min_signal_confidence", {"confidence": confidence_f, "minimum": min_confidence}

    signal_type = str(getattr(rec, "side", "") or "").upper()
    if signal_type == "BUY":
        if target_f <= entry_f:
            return False, "invalid_target_not_above_entry", {"entry": entry_f, "target_price": target_f}
        if stop_f >= entry_f:
            return False, "invalid_stop_not_below_entry", {"entry": entry_f, "stop_loss": stop_f}
        risk = entry_f - stop_f
        reward = target_f - entry_f
        if risk <= 0:
            return False, "invalid_risk_distance", {"entry": entry_f, "stop_loss": stop_f}
        min_rr = max(0.0, float(getattr(settings, "MIN_RISK_REWARD", 1.0)))
        rr = reward / risk
        if rr < min_rr:
            return False, "invalid_risk_reward", {"risk_reward": rr, "minimum": min_rr}

    return True, "ok", {}


def _persist_execution(portfolio: Portfolio, run: SignalRun, rec: SignalRecommendation, state: str, details: dict) -> HorusExecution:
    execution = HorusExecution.create(
        portfolio=portfolio,
        run=run,
        recommendation=rec,
        ticker=rec.ticker,
        state=state,
        trigger_source=_get_trigger_source(run),
        planned_entry_price=float(rec.entry_price),
        active_stop_loss=float(rec.stop_loss),
        active_target_price=float(rec.target_price),
        details_json=json.dumps(details),
        created_at=TimeUtils.now(),
        updated_at=TimeUtils.now(),
    )
    _upsert_execution_attribution(
        execution=execution,
        execution_portfolio=portfolio,
        run=run,
        recommendation=rec,
        state=state,
        details=details,
    )
    return execution


def _upsert_execution_attribution(
    execution: HorusExecution,
    execution_portfolio: Portfolio,
    run: SignalRun,
    recommendation: SignalRecommendation,
    state: str,
    details: dict,
) -> None:
    strategy_profile_name = str(
        _get_rec_json(recommendation, "strategy_profile_name", "") or ""
    ).strip()
    strategy_source_type = str(
        _get_rec_json(
            recommendation,
            "strategy_profile_source_type",
            _get_rec_json(recommendation, "source_type", ""),
        )
        or ""
    ).strip()
    strategy_portfolio = resolve_strategy_profile_portfolio(strategy_profile_name) if strategy_profile_name else None
    attribution_details = {
        "trigger_source": _get_trigger_source(run),
        "details": details or {},
    }
    SignalExecutionAttribution.create(
        execution=execution,
        execution_portfolio=execution_portfolio,
        strategy_portfolio=strategy_portfolio,
        recommendation=recommendation,
        run=run,
        lane=_resolve_lane(run.scan_type),
        scan_type=str(run.scan_type or "").upper(),
        strategy_profile_name=strategy_profile_name or None,
        strategy_source_type=strategy_source_type or None,
        signal_side=str(getattr(recommendation, "side", "") or "").upper() or None,
        signal_state=str(state or "").upper() or None,
        details_json=json.dumps(attribution_details),
        created_at=TimeUtils.now(),
        updated_at=TimeUtils.now(),
    )


def _sync_execution_attribution_state(execution: HorusExecution, state: str) -> None:
    attribution = SignalExecutionAttribution.get_or_none(
        SignalExecutionAttribution.execution == execution.id
    )
    if attribution is None:
        return
    attribution.signal_state = str(state or "").upper() or attribution.signal_state
    attribution.updated_at = TimeUtils.now()
    attribution.save()


def _handle_update(portfolio: Portfolio, run: SignalRun, rec: SignalRecommendation, position: Position) -> bool:
    tp2 = recommendation_target2(rec)
    previous = {
        "stop_loss": float(position.stop_loss or 0.0),
        "target_price": float(position.target_price or 0.0),
        "target_price_2": float(position.target_price_2 or 0.0),
    }
    
    success = PositionTracker.update_position(
        ticker=rec.ticker,
        sl=float(rec.stop_loss),
        tp=float(rec.target_price),
        tp2=float(tp2) if tp2 is not None else None,
        portfolio_id=portfolio.id,
    )
    
    if success:
        execution = _persist_execution(portfolio, run, rec, "UPDATED", {
            "previous": previous,
            "updated": {"stop_loss": float(rec.stop_loss), "target_price": float(rec.target_price), "target_price_2": float(tp2 or 0.0)}
        })
        build_upd_msg = _get_executor_symbol("build_update_message", build_update_message)
        tg_resp = _send_main_channel_signal_message(build_upd_msg(portfolio, rec, execution))
        if tg_resp.get("ok"):
            msg_id = (tg_resp.get("result") or {}).get("message_id")
            execution.update_message_id = str(msg_id) if msg_id else None
            execution.save()
        logger.info(
            "[SignalExecutor] run_id=%s ticker=%s action=UPDATED execution_id=%s stop_loss=%.4f target_price=%.4f",
            run.id,
            rec.ticker,
            execution.id,
            float(rec.stop_loss),
            float(rec.target_price),
        )
        return True
    logger.warning("[SignalExecutor] run_id=%s ticker=%s action=UPDATE_FAILED", run.id, rec.ticker)
    return False


def _handle_open(portfolio: Portfolio, run: SignalRun, rec: SignalRecommendation) -> bool:
    signal_type = str(getattr(rec, "side", None) or _get_rec_json(rec, "source", "BUY") or "BUY").upper()
    regime, _ = (
        _check_macro_regime(signal_type)
        if _is_regime_filter_enabled()
        else ("REGIME_FILTER_DISABLED", {"reason": "settings_disabled"})
    )
    shares = _calculate_shares(
        portfolio,
        float(rec.entry_price),
        float(rec.stop_loss),
        regime,
        signal_type,
        ticker=rec.ticker,
    )
    
    if shares <= 0:
        invalid_risk_distance = (float(rec.entry_price) - float(rec.stop_loss)) <= 0
        fail_reason = "invalid_risk_distance" if invalid_risk_distance else "position_size_zero"
        logger.warning(
            "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=%s entry=%.4f stop_loss=%.4f signal_type=%s",
            run.id,
            rec.ticker,
            fail_reason,
            float(rec.entry_price),
            float(rec.stop_loss),
            signal_type,
        )
        _persist_execution(portfolio, run, rec, "SKIPPED", {"reason": fail_reason})
        return False

    contract_ok, contract_reason, contract_data = _check_live_risk_contract(
        portfolio=portfolio,
        ticker=str(rec.ticker or "").upper(),
        entry_price=float(rec.entry_price),
        stop_loss=float(rec.stop_loss),
        shares=int(shares),
    )
    if not contract_ok:
        logger.warning(
            "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=risk_contract_%s data=%s",
            run.id,
            rec.ticker,
            contract_reason,
            contract_data,
        )
        _persist_execution(
            portfolio,
            run,
            rec,
            "SKIPPED",
            {"reason": f"risk_contract_{contract_reason}", "risk_contract": contract_data},
        )
        return False

    capacity_ok, capacity_reason, capacity_data = _check_execution_capacity(
        portfolio=portfolio,
        ticker=str(rec.ticker or "").upper(),
        entry_price=float(rec.entry_price),
        stop_loss=float(rec.stop_loss),
        shares=int(shares),
    )
    if not capacity_ok:
        log_fn = logger.info if capacity_reason == "velocity_daily_limit_reached" else logger.warning
        log_fn(
            "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=%s data=%s",
            run.id,
            rec.ticker,
            capacity_reason,
            capacity_data,
        )
        _persist_execution(
            portfolio,
            run,
            rec,
            "SKIPPED",
            {"reason": capacity_reason, "capacity": capacity_data},
        )
        return False

    from core.analyzers.TreasuryLedger import detect_currency
    curr = detect_currency(rec.ticker)
    
    rec_signal_id = None
    try:
        rationale = json.loads(rec.rationale_json or "{}")
        rec_signal_id = rationale.get("signal_id")
    except Exception:
        pass

    # === SHADOW BROKER EXECUTION ROUTING ===
    from core.market.ShadowExecutionGateway import ShadowExecutionGateway
    exec_report = ShadowExecutionGateway.place_shadow_order(
        ticker=rec.ticker,
        shares=shares,
        side="BUY",
        theoretical_price=float(rec.entry_price),
        signal_id=rec_signal_id
    )

    if not exec_report.get("success"):
        logger.warning(
            "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=shadow_execution_blocked message=%s",
            run.id,
            rec.ticker,
            exec_report.get("reason", "unknown")
        )
        _persist_execution(
            portfolio,
            run,
            rec,
            "FAILED",
            {"reason": f"shadow_execution_blocked_{exec_report.get('reason')}"}
        )
        return False

    actual_fill_price = float(exec_report["fill_price"])
    slippage_bps = int(exec_report["slippage_bps"])
    latency_ms = int(exec_report["latency_ms"])

    pos_tracker = _get_executor_symbol("PositionTracker", PositionTracker)
    success = pos_tracker.add_position(
        ticker=rec.ticker,
        shares=shares,
        entry_price=actual_fill_price,
        sl=float(rec.stop_loss),
        tp=float(rec.target_price),
        tp2=recommendation_target2(rec),
        portfolio_id=portfolio.id,
        currency=curr,
        slippage_bps=slippage_bps,
        latency_ms=latency_ms,
        signal_id=rec_signal_id,
    )
    
    if success:
        execution = _persist_execution(portfolio, run, rec, "OPEN", {
            "shares": shares,
            "slippage_bps": slippage_bps,
            "latency_ms": latency_ms,
            "fill_price": actual_fill_price
        })
        build_open_msg = _get_executor_symbol("build_open_message", build_open_message)
        tg_resp = _send_main_channel_signal_message(build_open_msg(portfolio, rec, shares, execution))
        if tg_resp.get("ok"):
            msg_id = (tg_resp.get("result") or {}).get("message_id")
            execution.open_message_id = str(msg_id) if msg_id else None
            execution.save()
        logger.info(
            "[SignalExecutor] run_id=%s ticker=%s action=OPENED execution_id=%s shares=%s entry=%.4f stop_loss=%.4f target_price=%.4f",
            run.id,
            rec.ticker,
            execution.id,
            shares,
            float(rec.entry_price),
            float(rec.stop_loss),
            float(rec.target_price),
        )
        return True
    else:
        logger.warning("[SignalExecutor] run_id=%s ticker=%s action=OPEN_FAILED reason=position_open_failed", run.id, rec.ticker)
        _persist_execution(portfolio, run, rec, "FAILED", {"reason": "position_open_failed"})
        return False
