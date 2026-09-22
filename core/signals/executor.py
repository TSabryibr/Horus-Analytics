"""
SIGNAL EXECUTOR — Main Facade & Pipeline
========================================
Refactored orchestrator delegating domain subtasks to `core.signals.execution`.
Preserves full backward compatibility for all static methods and call signatures.
"""

import json
import logging
from typing import Any, Optional, Tuple

from core.settings import settings
from core import AlertManager, PositionTracker, RiskManager, TelegramBot_Alerts, TimeUtils
from database import (
    HorusExecution,
    Portfolio,
    Position,
    SignalRecommendation,
    SignalRun,
)
from core.horus.telegram import (
    build_open_message,
    build_update_message,
    build_skip_message,
    recommendation_target2,
)
import sys

def _get_executor_symbol(name: str, fallback):
    mod = sys.modules.get("core.signals.executor")
    if mod is not None and hasattr(mod, name):
        val = getattr(mod, name)
        if val is not None and val is not fallback:
            return val
    return fallback


from .execution import (
    _HEAT_BLOCK_LOG_STATE,
    _LIVE_GUARD_LOG_STATE,
    _log_live_guard_block,
    _record_heat_block,
    _check_portfolio_heat,
    _safe_setting_float,
    _safe_setting_int,
    _emit_operator_event,
    _manual_override_abuse_state,
    _compute_realized_loss_state,
    _check_operator_lockout,
    _positive_float,
    _resolve_account_size,
    _calculate_shares,
    _check_velocity_limit,
    _check_execution_capacity,
    _calculate_gap_pct,
    _check_nonzero_cost_assumptions,
    _compute_crisis_correlation,
    _compute_liquidity_exit_capacity,
    _check_live_risk_contract,
    _check_entry_gate,
    _check_whale_trap,
    _check_sovereign_confluence,
    _check_correlation,
    _check_sector_limit,
    _is_regime_filter_enabled,
    _check_macro_regime,
    _run_risk_gates,
    _send_main_channel_signal_message,
    _get_trigger_source,
    _resolve_lane,
    _resolve_execution_portfolio,
    _find_cross_portfolio_signal_position,
    _get_existing_position_update_skip,
    _get_rec_json,
    _get_next_open_price,
    _validate_signal,
    _persist_execution,
    _upsert_execution_attribution,
    _sync_execution_attribution_state,
    _handle_update,
    _handle_open,
)

logger = logging.getLogger('SignalExecutor')


class SignalExecutor:
    _HEAT_BLOCK_LOG_STATE = _HEAT_BLOCK_LOG_STATE
    _LIVE_GUARD_LOG_STATE = _LIVE_GUARD_LOG_STATE

    # Delegate static helpers for full backward-compatibility
    _send_main_channel_signal_message = staticmethod(_send_main_channel_signal_message)
    _log_live_guard_block = staticmethod(_log_live_guard_block)
    _resolve_execution_portfolio = staticmethod(_resolve_execution_portfolio)
    _resolve_lane = staticmethod(_resolve_lane)
    _find_cross_portfolio_signal_position = staticmethod(_find_cross_portfolio_signal_position)
    _get_existing_position_update_skip = staticmethod(_get_existing_position_update_skip)
    _record_heat_block = staticmethod(_record_heat_block)
    _run_risk_gates = staticmethod(_run_risk_gates)
    _check_portfolio_heat = staticmethod(_check_portfolio_heat)
    _check_execution_capacity = staticmethod(_check_execution_capacity)
    _safe_setting_float = staticmethod(_safe_setting_float)
    _safe_setting_int = staticmethod(_safe_setting_int)
    _emit_operator_event = staticmethod(_emit_operator_event)
    _manual_override_abuse_state = staticmethod(_manual_override_abuse_state)
    _check_operator_lockout = staticmethod(_check_operator_lockout)
    _check_nonzero_cost_assumptions = staticmethod(_check_nonzero_cost_assumptions)
    _compute_realized_loss_state = staticmethod(_compute_realized_loss_state)
    _compute_crisis_correlation = staticmethod(_compute_crisis_correlation)
    _compute_liquidity_exit_capacity = staticmethod(_compute_liquidity_exit_capacity)
    _check_live_risk_contract = staticmethod(_check_live_risk_contract)
    _check_entry_gate = staticmethod(_check_entry_gate)
    _check_whale_trap = staticmethod(_check_whale_trap)
    _check_sovereign_confluence = staticmethod(_check_sovereign_confluence)
    _check_correlation = staticmethod(_check_correlation)
    _check_sector_limit = staticmethod(_check_sector_limit)
    _check_velocity_limit = staticmethod(_check_velocity_limit)
    _is_regime_filter_enabled = staticmethod(_is_regime_filter_enabled)
    _check_macro_regime = staticmethod(_check_macro_regime)
    _calculate_shares = staticmethod(_calculate_shares)
    _positive_float = staticmethod(_positive_float)
    _resolve_account_size = staticmethod(_resolve_account_size)
    _handle_update = staticmethod(_handle_update)
    _handle_open = staticmethod(_handle_open)
    _persist_execution = staticmethod(_persist_execution)
    _upsert_execution_attribution = staticmethod(_upsert_execution_attribution)
    _sync_execution_attribution_state = staticmethod(_sync_execution_attribution_state)
    _get_trigger_source = staticmethod(_get_trigger_source)
    _validate_signal = staticmethod(_validate_signal)
    _get_next_open_price = staticmethod(_get_next_open_price)
    _calculate_gap_pct = staticmethod(_calculate_gap_pct)
    _get_rec_json = staticmethod(_get_rec_json)

    @staticmethod
    def process_scanner_signals(signals: list, target_portfolio_name: str = "Swing Signals"):
        """
        Legacy adapter for direct scanner signal list execution.
        Dispatches to AutoTrader.process_scanner_signals when legacy unpersisted flow is used.
        """
        import warnings
        from core import AutoTrader
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=DeprecationWarning,
                message="AutoTrader.process_scanner_signals is deprecated",
            )
            return AutoTrader.process_scanner_signals(signals, target_portfolio_name=target_portfolio_name)

    @staticmethod
    def _is_market_open() -> bool:
        """Returns True if the current UTC time falls within EGX trading hours (08:00–12:30 UTC)."""
        return bool(settings.is_market_open())

    @staticmethod
    def execute_run(run_id: int) -> dict:
        """Execute all ACTIVE recommendations from a persisted SignalRun."""
        try:
            run = SignalRun.get_by_id(run_id)
        except SignalRun.DoesNotExist:
            logger.error(f"SignalRun {run_id} not found.")
            return {"status": "error", "message": "SignalRun not found"}

        if not settings.AUTO_TRADE_ENABLED:
            logger.info("Auto-trade disabled, skipping execution.")
            return {"status": "skipped", "message": "Auto-trade disabled"}
            
        from core.risk.kill_switch import is_kill_switch_active
        if is_kill_switch_active():
            logger.error("[SignalExecutor] execute_run blocked: global emergency kill switch is active!")
            return {"status": "blocked", "message": "Global emergency kill switch is active"}
            
        if not settings.is_live_execution_armed(TimeUtils.today()):
            SignalExecutor._log_live_guard_block("execute_run", run_id=run_id)
            return {"status": "skipped", "message": "Live execution guard is not armed for today"}

        scan_type = str(run.scan_type or "INTRADAY").upper()
        recommendations = list(
            SignalRecommendation.select()
            .where((SignalRecommendation.run == run) & (SignalRecommendation.state == "ACTIVE"))
            .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc())
        )

        portfolio = SignalExecutor._resolve_execution_portfolio(scan_type, recommendations)
        if not portfolio:
            logger.error(f"No target portfolio resolved for scan type: {scan_type}")
            return {"status": "skipped", "message": f"No portfolio for {scan_type}"}

        logger.info(
            "[SignalExecutor] execute_run start run_id=%s scan_type=%s portfolio=%s recommendations=%s",
            run.id,
            scan_type,
            getattr(portfolio, "name", None),
            len(recommendations),
        )

        summary = {"opened": 0, "updated": 0, "failed": 0, "skipped": 0, "pending": 0}
        lockout_allowed, lockout_reason, lockout_data = SignalExecutor._check_operator_lockout(portfolio)
        if not lockout_allowed:
            return {
                "status": "blocked",
                "message": "Operator discipline lockout is active",
                "blocked_reason": lockout_reason,
                "lockout": lockout_data,
                "portfolio": portfolio.name,
                "summary": summary,
            }

        # Global Heat Check
        heat_allowed, heat_reason, heat_val = SignalExecutor._check_portfolio_heat(portfolio)
        if not heat_allowed:
            repeat_count = SignalExecutor._record_heat_block(portfolio, heat_reason, heat_val)
            return {
                "status": "blocked",
                "message": "Portfolio heat limit reached",
                "blocked_reason": heat_reason,
                "heat": heat_val,
                "portfolio": portfolio.name,
                "repeat_count": repeat_count,
                "summary": summary,
            }

        for rec in recommendations:
            try:
                # 1. Validation of numbers and execution geometry
                signal_ok, signal_reason, signal_data = SignalExecutor._validate_signal(rec)
                if not signal_ok:
                    logger.warning(
                        "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=%s entry=%s sl=%s tp=%s",
                        run.id,
                        rec.ticker,
                        signal_reason,
                        rec.entry_price,
                        rec.stop_loss,
                        rec.target_price,
                    )
                    SignalExecutor._persist_execution(
                        portfolio,
                        run,
                        rec,
                        "SKIPPED",
                        {"reason": signal_reason, "validation": signal_data},
                    )
                    summary["skipped"] += 1
                    continue

                # 2. Risk Gate Pipeline
                allowed, reason, gate_data = SignalExecutor._run_risk_gates(portfolio, run, rec)
                if not allowed:
                    logger.info(
                        "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=%s gate_data=%s",
                        run.id,
                        rec.ticker,
                        reason,
                        gate_data,
                    )
                    SignalExecutor._persist_execution(portfolio, run, rec, "SKIPPED", {"reason": reason, "gate_data": gate_data})
                    summary["skipped"] += 1
                    continue

                # 3. Decision: Immediate vs Pending
                if scan_type == "DAILY":
                    logger.info(
                        "[SignalExecutor] run_id=%s ticker=%s action=PENDING_OPEN trigger_source=DAILY_NEXT_OPEN",
                        run.id,
                        rec.ticker,
                    )
                    SignalExecutor._persist_execution(portfolio, run, rec, "PENDING_OPEN", {"trigger_source": "DAILY_NEXT_OPEN"})
                    summary["pending"] += 1
                    continue

                # 3b. Intraday market-hours guard
                if scan_type == "INTRADAY" and not SignalExecutor._is_market_open():
                    logger.warning(
                        "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=off_market_hours",
                        run.id,
                        rec.ticker,
                    )
                    SignalExecutor._persist_execution(portfolio, run, rec, "SKIPPED", {"reason": "off_market_hours"})
                    summary["skipped"] += 1
                    continue

                # 4. Check for Update vs Open
                existing_position = Position.get_or_none(
                    (Position.portfolio == portfolio) &
                    (Position.ticker == rec.ticker) &
                    (Position.status == "OPEN")
                )
                
                if existing_position:
                    skip_update_reason, skip_update_details = SignalExecutor._get_existing_position_update_skip(
                        existing_position,
                        rec,
                    )
                    if skip_update_reason:
                        logger.info(
                            "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=%s position_id=%s",
                            run.id,
                            rec.ticker,
                            skip_update_reason,
                            existing_position.id,
                        )
                        SignalExecutor._persist_execution(
                            portfolio,
                            run,
                            rec,
                            "SKIPPED",
                            skip_update_details,
                        )
                        summary["skipped"] += 1
                        continue

                    logger.info(
                        "[SignalExecutor] run_id=%s ticker=%s action=UPDATE_EXISTING position_id=%s",
                        run.id,
                        rec.ticker,
                        existing_position.id,
                    )
                    success = SignalExecutor._handle_update(portfolio, run, rec, existing_position)
                    if success: summary["updated"] += 1
                    else: summary["failed"] += 1
                else:
                    conflicting_position = SignalExecutor._find_cross_portfolio_signal_position(portfolio, rec.ticker)
                    if conflicting_position:
                        conflict_portfolio_name = getattr(conflicting_position.portfolio, "name", None)
                        logger.info(
                            "[SignalExecutor] run_id=%s ticker=%s action=SKIP reason=cross_portfolio_duplicate_open existing_position_id=%s existing_portfolio=%s",
                            run.id,
                            rec.ticker,
                            conflicting_position.id,
                            conflict_portfolio_name,
                        )
                        SignalExecutor._persist_execution(
                            portfolio,
                            run,
                            rec,
                            "SKIPPED",
                            {
                                "reason": "cross_portfolio_duplicate_open",
                                "existing_position_id": conflicting_position.id,
                                "existing_portfolio": conflict_portfolio_name,
                            },
                        )
                        summary["skipped"] += 1
                        continue

                    logger.info(
                        "[SignalExecutor] run_id=%s ticker=%s action=OPEN_NEW",
                        run.id,
                        rec.ticker,
                    )
                    success = SignalExecutor._handle_open(portfolio, run, rec)
                    if success: summary["opened"] += 1
                    else: summary["failed"] += 1

            except Exception as e:
                logger.exception(f"Error processing recommendation {rec.id} ({rec.ticker}): {e}")
                summary["failed"] += 1

        logger.info("[SignalExecutor] execute_run complete run_id=%s summary=%s", run.id, summary)
        return {"status": "completed", "summary": summary}

    @staticmethod
    def execute_pending_entries(max_gap_pct: float | None = None) -> dict:
        """Execute PENDING_OPEN entries across all System portfolios at market open."""
        if not settings.AUTO_TRADE_ENABLED:
            logger.info("[SignalExecutor] Pending entries skipped because auto-trade is disabled.")
            return {"status": "skipped", "message": "Auto-trade disabled", "summary": {"opened": 0, "skipped": 0, "failed": 0}}
            
        from core.risk.kill_switch import is_kill_switch_active
        if is_kill_switch_active():
            logger.error("[SignalExecutor] execute_pending_entries blocked: global emergency kill switch is active!")
            return {"status": "blocked", "message": "Global emergency kill switch is active", "summary": {"opened": 0, "skipped": 0, "failed": 0}}
            
        if not settings.is_live_execution_armed(TimeUtils.today()):
            SignalExecutor._log_live_guard_block("pending_entries")
            return {"status": "skipped", "message": "Live execution guard is not armed for today", "summary": {"opened": 0, "skipped": 0, "failed": 0}}
        if max_gap_pct is None:
            max_gap_pct = SignalExecutor._safe_setting_float("PENDING_ENTRY_MAX_GAP_PCT", 1.5)
        else:
            try:
                max_gap_pct = float(max_gap_pct)
            except (TypeError, ValueError):
                max_gap_pct = SignalExecutor._safe_setting_float("PENDING_ENTRY_MAX_GAP_PCT", 1.5)
        if max_gap_pct <= 0:
            max_gap_pct = SignalExecutor._safe_setting_float("PENDING_ENTRY_MAX_GAP_PCT", 1.5)

        pendings = list(
            HorusExecution.select()
            .where(HorusExecution.state == "PENDING_OPEN")
            .order_by(HorusExecution.created_at.asc())
        )

        summary = {"opened": 0, "skipped": 0, "failed": 0}

        logger.info(
            "[SignalExecutor] execute_pending_entries start pending_count=%s max_gap_pct=%s",
            len(pendings),
            max_gap_pct,
        )
        lockout_cache: dict[int, tuple[bool, str, dict]] = {}

        for execution in pendings:
            try:
                claimed = (
                    HorusExecution.update(state="PROCESSING")
                    .where(
                        (HorusExecution.id == execution.id)
                        & (HorusExecution.state == "PENDING_OPEN")
                    )
                    .execute()
                )
                if claimed == 0:
                    logger.info(
                        "[SignalExecutor] pending_id=%s already claimed by another cycle, skipping.",
                        execution.id,
                    )
                    continue
                execution.state = "PROCESSING"

                rec = execution.recommendation
                portfolio = execution.portfolio
                if not rec or not portfolio:
                    execution.state = "FAILED"
                    execution.details_json = json.dumps({"reason": "missing_context"})
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "FAILED")
                    summary["failed"] += 1
                    continue

                cache_key = int(getattr(portfolio, "id", 0) or 0)
                if cache_key not in lockout_cache:
                    lockout_cache[cache_key] = SignalExecutor._check_operator_lockout(portfolio)
                lockout_allowed, lockout_reason, lockout_data = lockout_cache[cache_key]
                if not lockout_allowed:
                    execution.state = "SKIPPED"
                    execution.details_json = json.dumps(
                        {
                            "reason": f"operator_lockout_{lockout_reason}",
                            "lockout": lockout_data,
                        }
                    )
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "SKIPPED")
                    summary["skipped"] += 1
                    continue

                open_price, open_ts = SignalExecutor._get_next_open_price(rec.ticker)
                if open_price is None:
                    continue

                gap_pct = SignalExecutor._calculate_gap_pct(float(execution.planned_entry_price), open_price)
                
                if gap_pct > float(max_gap_pct):
                    logger.info(
                        "[SignalExecutor] pending_id=%s ticker=%s action=SKIP reason=gap_threshold_exceeded gap_pct=%.4f planned=%.4f actual=%.4f",
                        execution.id,
                        rec.ticker,
                        gap_pct,
                        float(execution.planned_entry_price or 0.0),
                        open_price,
                    )
                    execution.state = "SKIPPED"
                    execution.actual_entry_price = open_price
                    execution.gap_pct = gap_pct
                    execution.details_json = json.dumps({"reason": "gap_threshold_exceeded", "open_ts": open_ts})
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "SKIPPED")
                    SignalExecutor._send_main_channel_signal_message(build_skip_message(portfolio, rec, execution))
                    summary["skipped"] += 1
                    continue

                regime_filter_enabled = SignalExecutor._is_regime_filter_enabled()
                regime, regime_data = (
                    SignalExecutor._check_macro_regime(rec.side)
                    if regime_filter_enabled
                    else ("REGIME_FILTER_DISABLED", {"reason": "settings_disabled"})
                )
                if regime_filter_enabled and regime == "UNKNOWN" and str(rec.side or "").upper() == "BUY":
                    logger.warning(
                        "[SignalExecutor] pending_id=%s ticker=%s action=SKIP reason=macro_regime_unavailable regime_data=%s",
                        execution.id,
                        rec.ticker,
                        regime_data,
                    )
                    execution.state = "SKIPPED"
                    execution.details_json = json.dumps({"reason": "macro_regime_unavailable", "regime_data": regime_data, "open_ts": open_ts})
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "SKIPPED")
                    summary["skipped"] += 1
                    continue
                shares = SignalExecutor._calculate_shares(portfolio, open_price, float(rec.stop_loss), regime, rec.side, ticker=rec.ticker)
                
                if shares <= 0:
                    invalid_risk_distance = (open_price - float(rec.stop_loss)) <= 0
                    fail_reason = "invalid_risk_distance" if invalid_risk_distance else "position_size_zero"
                    logger.warning(
                        "[SignalExecutor] pending_id=%s ticker=%s action=SKIP reason=%s planned=%.4f actual=%.4f",
                        execution.id,
                        rec.ticker,
                        fail_reason,
                        float(execution.planned_entry_price or 0.0),
                        open_price,
                    )
                    execution.state = "SKIPPED"
                    execution.details_json = json.dumps({"reason": fail_reason, "open_ts": open_ts})
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "SKIPPED")
                    summary["skipped"] += 1
                    continue

                contract_ok, contract_reason, contract_data = SignalExecutor._check_live_risk_contract(
                    portfolio=portfolio,
                    ticker=str(rec.ticker or "").upper(),
                    entry_price=float(open_price),
                    stop_loss=float(rec.stop_loss),
                    shares=int(shares),
                )
                if not contract_ok:
                    logger.warning(
                        "[SignalExecutor] pending_id=%s ticker=%s action=SKIP reason=risk_contract_%s data=%s",
                        execution.id,
                        rec.ticker,
                        contract_reason,
                        contract_data,
                    )
                    execution.state = "SKIPPED"
                    execution.details_json = json.dumps(
                        {
                            "reason": f"risk_contract_{contract_reason}",
                            "risk_contract": contract_data,
                            "open_ts": open_ts,
                        }
                    )
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "SKIPPED")
                    summary["skipped"] += 1
                    continue

                capacity_ok, capacity_reason, capacity_data = SignalExecutor._check_execution_capacity(
                    portfolio=portfolio,
                    ticker=str(rec.ticker or "").upper(),
                    entry_price=float(open_price),
                    stop_loss=float(rec.stop_loss),
                    shares=int(shares),
                )
                if not capacity_ok:
                    log_fn = logger.info if capacity_reason == "velocity_daily_limit_reached" else logger.warning
                    log_fn(
                        "[SignalExecutor] pending_id=%s ticker=%s action=SKIP reason=%s data=%s",
                        execution.id,
                        rec.ticker,
                        capacity_reason,
                        capacity_data,
                    )
                    execution.state = "SKIPPED"
                    execution.actual_entry_price = open_price
                    execution.gap_pct = gap_pct
                    execution.details_json = json.dumps(
                        {
                            "reason": capacity_reason,
                            "capacity": capacity_data,
                            "open_ts": open_ts,
                        }
                    )
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "SKIPPED")
                    summary["skipped"] += 1
                    continue

                from core.analyzers.TreasuryLedger import detect_currency
                curr = detect_currency(rec.ticker)
                
                rec_signal_id = None
                try:
                    rationale = json.loads(rec.rationale_json or "{}")
                    rec_signal_id = rationale.get("signal_id")
                except Exception:
                    pass
                pos_tracker = _get_executor_symbol("PositionTracker", PositionTracker)
                opened = pos_tracker.add_position(
                    ticker=rec.ticker,
                    shares=shares,
                    entry_price=open_price,
                    sl=float(rec.stop_loss),
                    tp=float(rec.target_price),
                    tp2=recommendation_target2(rec),
                    portfolio_id=portfolio.id,
                    currency=curr,
                    signal_id=rec_signal_id,
                )
                
                if opened:
                    logger.info(
                        "[SignalExecutor] pending_id=%s ticker=%s action=OPEN shares=%s actual=%.4f gap_pct=%.4f",
                        execution.id,
                        rec.ticker,
                        shares,
                        open_price,
                        gap_pct,
                    )
                    execution.state = "OPEN"
                    execution.actual_entry_price = open_price
                    execution.gap_pct = gap_pct
                    execution.details_json = json.dumps({"shares": shares, "gap_pct": gap_pct, "open_ts": open_ts})
                    build_open_msg = _get_executor_symbol("build_open_message", build_open_message)
                    tg_resp = SignalExecutor._send_main_channel_signal_message(build_open_msg(portfolio, rec, shares, execution))
                    if tg_resp.get("ok"):
                        msg_id = (tg_resp.get("result") or {}).get("message_id")
                        execution.open_message_id = str(msg_id) if msg_id else None
                    execution.save()
                    SignalExecutor._sync_execution_attribution_state(execution, "OPEN")
                    summary["opened"] += 1
                else:
                    logger.warning(
                        "[SignalExecutor] pending_id=%s ticker=%s action=FAIL reason=position_open_failed",
                        execution.id,
                        rec.ticker,
                    )
                    summary["failed"] += 1

            except Exception as e:
                logger.exception(f"Error executing pending {execution.id} ({execution.ticker}): {e}")
                summary["failed"] += 1

        logger.info("[SignalExecutor] execute_pending_entries complete summary=%s", summary)
        return {"status": "completed", "summary": summary}

    execute_pending_daily_entries = execute_pending_entries
