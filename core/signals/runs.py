from core.signals.guard import (
    get_guard_state as _signals_get_guard_state,
    set_guard_state as _signals_set_guard_state,
    serialize_guard_state as _signals_serialize_guard_state,
    guard_context as _signals_guard_context,
    serialize_run as _signals_serialize_run,
)
from core.signals.models import DailyRunRequest, PublishSignalsRequest, RetryFailedDeliveriesRequest, RebuildOutcomesRequest, WalkforwardValidationRequest, GuardStateUpdateRequest, SignalDeskModeUpdateRequest, SignalDeskPromotionRequest, SignalDeskAutopilotRequest, SignalLifecycleOverrideRequest, SignalFollowUpActionRequest
from core.settings import settings
from core.auth import get_api_key
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, List, Optional, Callable
import datetime
import json
import os
import time
from core import DailyScanner
from core import TelegramBot_Alerts
from core import TimeUtils
from peewee import fn
from core.signals.desk import _recommendation_target2 as _signals_recommendation_target2
from core.signals.boundary import (
    bool_env as _signals_bool_env,
    error_context as _signals_error_context,
    float_env as _signals_float_env,
    freshness_context as _signals_freshness_context,
    get_publish_window_status as _signals_get_publish_window_status,
    int_env as _signals_int_env,
    noop_context as _signals_noop_context,
    parse_run_date as _signals_parse_run_date,
    validated_publish_channel as _signals_validated_publish_channel,
    validation_error as _signals_validation_error,
    window_context as _signals_window_context,
)

from core.signals.outcomes import (
    get_signal_audit_summary as _signals_get_signal_audit_summary,
    get_signal_calibration as _signals_get_signal_calibration,
    get_signal_outcomes as _signals_get_signal_outcomes,
    get_walkforward_validation_latest as _signals_get_walkforward_validation_latest,
    list_signal_audit_events as _signals_list_signal_audit_events,
    project_published_signal_lifecycle_outcome as _signals_project_published_signal_lifecycle_outcome,
    rebuild_signal_outcomes as _signals_rebuild_signal_outcomes,
    serialize_audit_event as _signals_serialize_audit_event,
    upsert_signal_outcome as _signals_upsert_signal_outcome,
)
from core.signals.workspace import (
    get_signals_sla as _signals_get_signals_sla,
    get_workspace_signal_performance as _signals_get_workspace_signal_performance,
    portfolio_window_metrics as _signals_portfolio_window_metrics,
)
from core.signals.followups import (
    get_signal_followup_summary as _signals_get_signal_followup_summary,
    process_signal_followups as _signals_process_signal_followups,
    requeue_signal_followup as _signals_requeue_signal_followup,
    send_signal_followup as _signals_send_signal_followup,
    suppress_signal_followup as _signals_suppress_signal_followup,
)
from database import (
    Signal,
    SignalRun,
    SignalRecommendation,
    SignalDelivery,
    SignalOutcome,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    PublishedSignalFollowUp,
    SignalValidationRun,
    SignalGuardState,
    SignalDeskState,
    SignalAuditEvent,
    Portfolio,
    Position,
    Trade,
    db,
)
from core.signals.lifecycle import (
    override_published_signal_lifecycle as _signals_override_published_signal_lifecycle,
    _create_published_signal_lifecycle_records,
)
from core.signals.audit import _emit_audit_event
from routes.data import evaluate_data_freshness_logic
from core.exclusions import get_excluded_tickers_upper, is_excluded_ticker, normalize_ticker
from core.signals.desk import (
    _SIGNAL_DESK_MODES,
    _SIGNAL_DESK_LANES,
    _parse_json_object,
    _default_signal_desk_policy,
    _default_signal_desk_queue,
    _get_signal_desk_state,
    _serialize_signal_desk_autopilot,
    _update_signal_desk_autopilot_state,
    _normalize_signal_lane,
    _get_signal_desk_queue,
    _save_signal_desk_queue,
    _desk_lane_key,
    _SIGNAL_SIDE_SOURCE_VALUES,
    _serialize_signal_desk_candidate,
    _dedupe_signal_desk_recommendations,
    _recommendation_source_module,
    _evaluate_signal_desk_autopilot,
    _serialize_manual_queue_candidate,
    _empty_signal_lane,
    _build_signal_desk_payload,
    _compute_tp2,
    _recommendation_target2
)


def _build_recommendation(signal: dict, run: SignalRun, regime: str):
    ticker = normalize_ticker(signal.get("Ticker"))
    if not ticker or is_excluded_ticker(ticker):
        return None

    score = int(signal.get("Score", 0))
    raw_confidence = signal.get("Confidence", signal.get("confidence", float(score) * 10.0))
    confidence = max(0.0, min(100.0, float(raw_confidence)))
    min_score = float(getattr(settings, "MIN_SIGNAL_SCORE", 0.0))
    min_confidence = float(getattr(settings, "MIN_SIGNAL_CONFIDENCE", 0.0))
    if float(score) < min_score:
        return None
    if confidence < min_confidence:
        return None
    entry = float(signal.get("Entry_Price", 0))
    sl = float(signal.get("Stop_Loss", 0))
    tp = float(signal.get("Target_Price", 0))
    side = "BUY" if str(signal.get("Signal_Type", "BUY")).upper() == "BUY" else str(signal.get("Signal_Type")).upper()
    raw_tp2 = signal.get("Target_Price_2")
    try:
        tp2 = float(raw_tp2) if raw_tp2 is not None else _compute_tp2(side, tp)
    except (TypeError, ValueError):
        tp2 = _compute_tp2(side, tp)
    if tp2 <= 0:
        tp2 = _compute_tp2(side, tp)
    rationale = {
        "score": score,
        "rsi": signal.get("RSI"),
        "volume_x": signal.get("Volume_x", signal.get("Volume_Spike")),
        "confirmation": signal.get("Confirmation"),
        "sector": signal.get("Sector"),
        "source_module": "SCANNER",
        "source": signal.get("Signal_Type"),
        "signal_side": side,
        "target_price_2": tp2,
        "whale_signal": signal.get("Whale_Signal"),
        "whale_strength": signal.get("Whale_Strength"),
        "whale_alignment": signal.get("Whale_Alignment"),
        "whale_reason": signal.get("Whale_Reason"),
        "trap_risk_score": signal.get("Trap_Risk_Score"),
        "trap_risk_band": signal.get("Trap_Risk_Band"),
        "trap_risk_reason": signal.get("Trap_Risk_Reason"),
        "enforcement_state": signal.get("Enforcement_State"),
        "enforcement_visibility": signal.get("Enforcement_Visibility"),
        "enforcement_reason": signal.get("Enforcement_Reason"),
        "enforcement_notes": signal.get("Enforcement_Notes"),
        "enforcement_profile": signal.get("Enforcement_Profile"),
        "strategy_profile_id": signal.get("Scanner_Profile_Id"),
        "strategy_profile_name": signal.get("Scanner_Profile_Name"),
        "strategy_profile_source_type": signal.get("Scanner_Profile_Source_Type"),
        "strategy_profile_market": signal.get("Scanner_Profile_Market"),
        "strategy_profile_timeframe": signal.get("Scanner_Profile_Timeframe"),
        "preview_mode": signal.get("preview_mode"),
        "preview_source": signal.get("preview_source"),
        "preview_close": signal.get("preview_close"),
        "preview_volume": signal.get("preview_volume"),
        "preview_date": str(signal.get("preview_date")) if signal.get("preview_date") is not None else None,
        "signal_id": signal.get("Signal_Id")
    }
    invalidation_rule = f"Invalidate if close below {sl:.4f}" if side == "BUY" else f"Invalidate if close above {sl:.4f}"
    horizon_days = 1 if run.scan_type in {"INTRADAY", "PRE_CLOSE"} else 5

    return SignalRecommendation(
        run=run,
        ticker=ticker,
        side=side,
        entry_price=entry,
        stop_loss=sl,
        target_price=tp,
        score=score,
        confidence=confidence,
        rationale_json=json.dumps(rationale),
        invalidation_rule=invalidation_rule,
        horizon_days=horizon_days,
        regime=regime,
        data_cutoff_at=TimeUtils.now(),
        state="ACTIVE",
    )


def _build_delivery_message(run: SignalRun, recommendations: List[SignalRecommendation], portfolio: Optional[Portfolio], watch_only_recommendations: Optional[List[SignalRecommendation]] = None) -> str:
    from core.signals.publishing import build_delivery_message
    return build_delivery_message(run, recommendations, portfolio, recommendation_target2_fn=_signals_recommendation_target2, watch_only_recommendations=watch_only_recommendations)
def _recommendation_window(run: SignalRun, rec: SignalRecommendation):
    start = run.completed_at or run.started_at or datetime.datetime.combine(run.run_date, datetime.time.min)
    horizon = rec.horizon_days if rec.horizon_days and rec.horizon_days > 0 else 5
    end = start + datetime.timedelta(days=horizon)
    return start, end


def _upsert_outcome(
    rec: SignalRecommendation,
    run: SignalRun,
    outcome_status: str,
    entry_date: Optional[datetime.datetime] = None,
    exit_date: Optional[datetime.datetime] = None,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    pnl: Optional[float] = None,
    pnl_pct: Optional[float] = None,
    notes: Optional[str] = None,
):
    return _signals_upsert_signal_outcome(
        recommendation=rec,
        run=run,
        outcome_status=outcome_status,
        entry_date=entry_date,
        exit_date=exit_date,
        entry_price=entry_price,
        exit_price=exit_price,
        pnl=pnl,
        pnl_pct=pnl_pct,
        notes=notes,
        now_fn=TimeUtils.now,
    )


def _rebuild_outcomes_for_run(run: SignalRun):
    recs = list(SignalRecommendation.select().where(SignalRecommendation.run == run))
    rebuilt = 0
    closed = 0
    opened = 0
    no_trade = 0

    for rec in recs:
        window_start, window_end = _recommendation_window(run, rec)

        trade = (
            Trade.select()
            .where(
                (Trade.ticker == rec.ticker) &
                (Trade.entry_date >= window_start) &
                (Trade.entry_date <= window_end)
            )
            .order_by(Trade.exit_date.asc())
            .first()
        )
        if trade:
            pnl = trade.pnl if trade.pnl is not None else ((trade.exit_price - trade.entry_price) * trade.shares)
            pnl_pct = trade.pnl_pct
            if pnl_pct is None and trade.entry_price:
                pnl_pct = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
            _upsert_outcome(
                rec=rec,
                run=run,
                outcome_status="CLOSED",
                entry_date=trade.entry_date,
                exit_date=trade.exit_date,
                entry_price=trade.entry_price,
                exit_price=trade.exit_price,
                pnl=pnl,
                pnl_pct=pnl_pct,
                notes=f"Matched trade id={trade.id}",
            )
            closed += 1
            rebuilt += 1
            continue

        position = (
            Position.select()
            .where(
                (Position.ticker == rec.ticker) &
                (Position.status == "OPEN") &
                (Position.entry_date >= window_start) &
                (Position.entry_date <= window_end)
            )
            .order_by(Position.entry_date.asc())
            .first()
        )
        if position:
            current = position.current_price if position.current_price else position.entry_price
            pnl = (current - position.entry_price) * position.shares
            pnl_pct = ((current - position.entry_price) / position.entry_price) * 100 if position.entry_price else 0.0
            _upsert_outcome(
                rec=rec,
                run=run,
                outcome_status="OPEN",
                entry_date=position.entry_date,
                exit_date=None,
                entry_price=position.entry_price,
                exit_price=current,
                pnl=pnl,
                pnl_pct=pnl_pct,
                notes=f"Matched open position id={position.id}",
            )
            opened += 1
            rebuilt += 1
            continue

        _upsert_outcome(
            rec=rec,
            run=run,
            outcome_status="NO_TRADE",
            notes="No trade or open position matched recommendation window",
        )
        no_trade += 1
        rebuilt += 1

    return {
        "run_id": run.id,
        "rebuilt": rebuilt,
        "closed": closed,
        "open": opened,
        "no_trade": no_trade,
    }


def _resolve_run_key(req, run_date: datetime.date, scan_type: str) -> str:
    explicit = str(getattr(req, "run_key", "") or "").strip()
    if explicit:
        return explicit
    return f"{run_date.isoformat()}:{scan_type}"


def _signals_run_daily_signals_logic(
    req,
    *,
    parse_run_date_fn,
    validation_error_fn,
    get_guard_state_fn,
    guard_context_fn,
    emit_audit_event_fn,
    serialize_run_fn,
    now_fn,
    freshness_context_fn,
    evaluate_data_freshness_fn,
    get_market_signals_fn,
    build_recommendation_fn,
):
    if evaluate_data_freshness_fn is None:
        raise RuntimeError("evaluate_data_freshness_fn is required")

    run_date = parse_run_date_fn(req.run_date)
    scan_type = req.scan_type.upper()
    if scan_type not in ("DAILY", "INTRADAY", "PRE_CLOSE"):
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "invalid_scan_type",
                "scan_type must be DAILY, INTRADAY, or PRE_CLOSE",
                parameter="scan_type",
                scan_type=scan_type,
            ),
        )
    run_key = _resolve_run_key(req, run_date, scan_type)

    guard = get_guard_state_fn()
    if guard.is_blocked and not req.ignore_guard:
        current_guard_context = guard_context_fn(guard)
        emit_audit_event_fn(
            event_type="RUN_BLOCKED_GUARD",
            severity="WARN",
            actor_type="SYSTEM",
            entity_type="SIGNAL_RUN",
            entity_id=run_key,
            message="Signal run blocked by guard state",
            details={
                "run_date": run_date.strftime("%Y-%m-%d"),
                "scan_type": scan_type,
                **current_guard_context,
            },
        )
        return {
            "status": "blocked",
            "run": None,
            "message": f"Signal pipeline blocked by guard: {guard.reason or 'No reason provided'}",
            **current_guard_context,
        }

    existing = SignalRun.get_or_none(SignalRun.run_key == run_key)
    if existing is None and not getattr(req, "run_key", None):
        existing = SignalRun.get_or_none(
            (SignalRun.run_date == run_date) &
            (SignalRun.scan_type == scan_type)
        )
        if existing and not existing.run_key:
            existing.run_key = run_key
            existing.save()
    if existing and not req.force:
        emit_audit_event_fn(
            event_type="RUN_SKIPPED_EXISTING",
            actor_type="SYSTEM",
            run=existing,
            entity_type="SIGNAL_RUN",
            entity_id=str(existing.id),
            message="Signal run skipped because idempotent run already exists",
            details={
                "run_date": run_date.strftime("%Y-%m-%d"),
                "scan_type": scan_type,
                "force": req.force,
                "run_key": run_key,
            },
        )
        return {
            "status": "existing",
            "run": serialize_run_fn(existing),
            "message": "Run already exists for this run_key. Use force=true to rerun.",
        }

    if existing:
        run = existing
        SignalRecommendation.delete().where(SignalRecommendation.run == run).execute()
        SignalDelivery.delete().where(SignalDelivery.run == run).execute()
    else:
        run = SignalRun.create(run_date=run_date, scan_type=scan_type, run_key=run_key)

    run.status = "RUNNING"
    run.started_at = now_fn()
    run.completed_at = None
    run.universe_count = 0
    run.signals_count = 0
    run.published_count = 0
    run.model_version = req.model_version or "v1"
    run.error = None
    run.run_key = run_key
    run.save()

    freshness = evaluate_data_freshness_fn(run_date=run_date.strftime("%Y-%m-%d"), scan_type=scan_type)
    if not freshness["overall_ok"]:
        current_freshness_context = freshness_context_fn(freshness)
        run.status = "BLOCKED"
        run.error = "Freshness gate failed"
        run.completed_at = now_fn()
        run.save()
        emit_audit_event_fn(
            event_type="RUN_BLOCKED_FRESHNESS",
            severity="WARN",
            actor_type="SYSTEM",
            run=run,
            entity_type="SIGNAL_RUN",
            entity_id=str(run.id),
            message="Signal run blocked by freshness gate",
            details={
                "run_date": run_date.strftime("%Y-%m-%d"),
                "scan_type": scan_type,
                **current_freshness_context,
            },
        )
        return {
            "status": "blocked",
            "run": serialize_run_fn(run),
            "message": "Run blocked by data freshness gate.",
            **current_freshness_context,
        }

    try:
        if build_recommendation_fn is None:
            raise RuntimeError("build_recommendation_fn is required")
        get_market_signals_fn = get_market_signals_fn or DailyScanner.get_market_signals
        is_intraday = scan_type == "INTRADAY"
        scan_kwargs = {
            "index_choice": req.index,
            "is_intraday": is_intraday,
        }
        if scan_type == "PRE_CLOSE":
            scan_kwargs["is_pre_close"] = True
        signals, monitored, breadth, regime = get_market_signals_fn(**scan_kwargs)

        with db.atomic():
            included_signals = 0
            for sig in signals:
                rec = build_recommendation_fn(sig, run=run, regime=regime)
                if rec is None:
                    continue
                rec.save()
                included_signals += 1

                ticker_clean = normalize_ticker(sig.get("Ticker"))
                if not ticker_clean or is_excluded_ticker(ticker_clean):
                    continue
                signal_type = str(sig.get("Signal_Type", "BUY"))
                exists = Signal.select().where(
                    (Signal.ticker == ticker_clean) &
                    (Signal.signal_type == signal_type) &
                    (Signal.date == run_date)
                ).exists()
                if not exists:
                    Signal.create(
                        ticker=ticker_clean,
                        date=run_date,
                        signal_type=signal_type,
                        price=float(sig.get("Entry_Price", 0)),
                        score=int(sig.get("Score", 0)),
                        source=f"RUN:{scan_type}",
                    )

            run.universe_count = len(monitored)
            run.signals_count = included_signals
            run.completed_at = now_fn()
            run.status = "COMPLETED"
            run.error = None
            run.save()
            emit_audit_event_fn(
                event_type="RUN_COMPLETED",
                actor_type="SYSTEM",
                run=run,
                entity_type="SIGNAL_RUN",
                entity_id=str(run.id),
                message="Signal run completed",
                details={
                    "run_date": run.run_date.strftime("%Y-%m-%d") if run.run_date else None,
                    "scan_type": run.scan_type,
                    "run_key": run.run_key,
                    "signals_count": run.signals_count,
                    "monitored_count": run.universe_count,
                    "breadth": breadth,
                    "regime": regime,
                },
            )

        return {
            "status": "completed",
            "run": serialize_run_fn(run),
            "freshness": freshness,
            "summary": {
                "breadth": breadth,
                "regime": regime,
                "signals_count": run.signals_count,
                "monitored_count": len(monitored),
            },
        }
    except Exception as exc:
        run.status = "ERROR"
        run.error = str(exc)
        run.completed_at = now_fn()
        run.save()
        emit_audit_event_fn(
            event_type="RUN_ERROR",
            severity="ERROR",
            actor_type="SYSTEM",
            run=run,
            entity_type="SIGNAL_RUN",
            entity_id=str(run.id),
            message="Signal run failed with exception",
            details={"error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=f"Signal run failed: {exc}") from exc


def _signals_run_walkforward_validation_logic(
    req,
    *,
    now_fn,
    today_fn,
    emit_audit_event_fn,
    get_guard_state_fn,
    set_guard_state_fn,
    serialize_guard_state_fn,
):
    since = today_fn() - datetime.timedelta(days=req.window_days - 1)
    closed_outcomes = list(
        SignalOutcome.select()
        .join(SignalRun)
        .switch(SignalOutcome)
        .join(SignalRecommendation)
        .where(
            (SignalRun.run_date >= since) &
            (SignalOutcome.outcome_status == "CLOSED")
        )
        .order_by(SignalOutcome.exit_date.asc())
    )

    closed = len(closed_outcomes)
    wins = sum(1 for outcome in closed_outcomes if float(outcome.pnl_pct or 0.0) > 0)
    total_pnl_pct = sum(float(outcome.pnl_pct or 0.0) for outcome in closed_outcomes)
    win_rate = round((wins / closed) * 100, 2) if closed else 0.0
    avg_pnl = round(total_pnl_pct / closed, 4) if closed else 0.0

    week_min = req.min_week_win_rate_pct if req.min_week_win_rate_pct is not None else req.min_win_rate_pct
    week_buckets = {}
    for outcome in closed_outcomes:
        ref_dt = outcome.exit_date or outcome.computed_at or now_fn()
        year, week, _ = ref_dt.isocalendar()
        key = f"{year}-W{week:02d}"
        week_buckets.setdefault(key, []).append(float(outcome.pnl_pct or 0.0))

    weekly_rows = []
    longest_weak_streak = 0
    current_weak_streak = 0
    for key in sorted(week_buckets.keys()):
        values = week_buckets[key]
        week_count = len(values)
        week_wins = sum(1 for value in values if value > 0)
        week_win_rate = (week_wins / week_count) * 100 if week_count else 0.0
        week_avg = sum(values) / week_count if week_count else 0.0
        weak = week_win_rate < week_min
        if weak:
            current_weak_streak += 1
            longest_weak_streak = max(longest_weak_streak, current_weak_streak)
        else:
            current_weak_streak = 0
        weekly_rows.append(
            {
                "week": key,
                "count": week_count,
                "win_rate_pct": round(week_win_rate, 2),
                "avg_pnl_pct": round(week_avg, 4),
                "weak": weak,
            }
        )

    fail_reasons = []
    if closed < req.min_closed_signals:
        fail_reasons.append(f"insufficient_closed_signals({closed}<{req.min_closed_signals})")
    if win_rate < req.min_win_rate_pct:
        fail_reasons.append(f"win_rate_below_threshold({win_rate}<{req.min_win_rate_pct})")
    if avg_pnl < req.min_avg_pnl_pct:
        fail_reasons.append(f"avg_pnl_below_threshold({avg_pnl}<{req.min_avg_pnl_pct})")
    if longest_weak_streak >= req.max_consecutive_weak_weeks:
        fail_reasons.append(
            f"consecutive_weak_weeks({longest_weak_streak}>={req.max_consecutive_weak_weeks})"
        )

    status = "PASS" if not fail_reasons else "FAIL"
    details = {
        "window_days": req.window_days,
        "from_date": since.strftime("%Y-%m-%d"),
        "to_date": today_fn().strftime("%Y-%m-%d"),
        "closed_signals": closed,
        "win_rate_pct": win_rate,
        "avg_pnl_pct": avg_pnl,
        "longest_weak_week_streak": longest_weak_streak,
        "weekly": weekly_rows,
        "thresholds": {
            "min_closed_signals": req.min_closed_signals,
            "min_win_rate_pct": req.min_win_rate_pct,
            "min_avg_pnl_pct": req.min_avg_pnl_pct,
            "min_week_win_rate_pct": week_min,
            "max_consecutive_weak_weeks": req.max_consecutive_weak_weeks,
        },
    }

    validation = SignalValidationRun.create(
        run_date=today_fn(),
        window_days=req.window_days,
        closed_signals=closed,
        win_rate_pct=win_rate,
        avg_pnl_pct=avg_pnl,
        status=status,
        degradation_reason="; ".join(fail_reasons) if fail_reasons else None,
        details_json=json.dumps(details),
    )
    emit_audit_event_fn(
        event_type="WALKFORWARD_VALIDATION_COMPLETED",
        severity="INFO" if status == "PASS" else "WARN",
        actor_type="SYSTEM",
        entity_type="SIGNAL_VALIDATION",
        entity_id=str(validation.id),
        message="Walkforward validation completed",
        details={
            "status": status,
            "fail_reasons": fail_reasons,
            "metrics": {
                "closed_signals": closed,
                "win_rate_pct": win_rate,
                "avg_pnl_pct": avg_pnl,
                "longest_weak_week_streak": longest_weak_streak,
            },
            "thresholds": details["thresholds"],
        },
    )

    guard_state = get_guard_state_fn()
    guard_action = "none"
    if status == "FAIL" and req.auto_block:
        guard_state = set_guard_state_fn(
            is_blocked=True,
            reason=f"walkforward_fail: {'; '.join(fail_reasons)}",
            source="WALKFORWARD",
            details={
                "validation_id": validation.id,
                "status": status,
                "reasons": fail_reasons,
                "metrics": {
                    "closed_signals": closed,
                    "win_rate_pct": win_rate,
                    "avg_pnl_pct": avg_pnl,
                },
            },
        )
        emit_audit_event_fn(
            event_type="GUARD_AUTO_BLOCKED",
            severity="WARN",
            actor_type="SYSTEM",
            entity_type="SIGNAL_GUARD",
            entity_id=guard_state.name,
            message="Guard auto-blocked after validation failure",
            details={
                "validation_id": validation.id,
                "reasons": fail_reasons,
            },
        )
        guard_action = "blocked"
    elif status == "PASS" and req.auto_unblock and guard_state.is_blocked:
        guard_state = set_guard_state_fn(
            is_blocked=False,
            reason="walkforward_pass",
            source="WALKFORWARD",
            details={
                "validation_id": validation.id,
                "status": status,
                "metrics": {
                    "closed_signals": closed,
                    "win_rate_pct": win_rate,
                    "avg_pnl_pct": avg_pnl,
                },
            },
        )
        emit_audit_event_fn(
            event_type="GUARD_AUTO_UNBLOCKED",
            severity="INFO",
            actor_type="SYSTEM",
            entity_type="SIGNAL_GUARD",
            entity_id=guard_state.name,
            message="Guard auto-unblocked after validation pass",
            details={"validation_id": validation.id},
        )
        guard_action = "unblocked"

    return {
        "status": status.lower(),
        "validation": {
            "id": validation.id,
            "run_date": validation.run_date.strftime("%Y-%m-%d"),
            "window_days": validation.window_days,
            "closed_signals": validation.closed_signals,
            "win_rate_pct": validation.win_rate_pct,
            "avg_pnl_pct": validation.avg_pnl_pct,
            "status": validation.status,
            "degradation_reason": validation.degradation_reason,
        },
        "fail_reasons": fail_reasons,
        "guard_action": guard_action,
        "guard_state": serialize_guard_state_fn(guard_state),
        "details": details,
    }
def run_daily_signals_logic(
    req: DailyRunRequest,
    get_market_signals_fn: Optional[Callable[..., tuple]] = None,
    *,
    parse_run_date_fn = _signals_parse_run_date,
    validation_error_fn = _signals_validation_error,
    get_guard_state_fn = _signals_get_guard_state,
    guard_context_fn = _signals_guard_context,
    emit_audit_event_fn = _emit_audit_event,
    serialize_run_fn = _signals_serialize_run,
    now_fn = TimeUtils.now,
    freshness_context_fn = _signals_freshness_context,
    evaluate_data_freshness_fn = None,
    build_recommendation_fn = _build_recommendation,
):
    if evaluate_data_freshness_fn is None:
        evaluate_data_freshness_fn = evaluate_data_freshness_logic
    return _signals_run_daily_signals_logic(
        req,
        parse_run_date_fn=parse_run_date_fn,
        validation_error_fn=validation_error_fn,
        get_guard_state_fn=get_guard_state_fn,
        guard_context_fn=guard_context_fn,
        emit_audit_event_fn=emit_audit_event_fn,
        serialize_run_fn=serialize_run_fn,
        now_fn=now_fn,
        freshness_context_fn=freshness_context_fn,
        evaluate_data_freshness_fn=evaluate_data_freshness_fn,
        get_market_signals_fn=get_market_signals_fn or DailyScanner.get_market_signals,
        build_recommendation_fn=build_recommendation_fn,
    )


def run_walkforward_validation_logic(
    req: WalkforwardValidationRequest,
    *,
    now_fn = TimeUtils.now,
    today_fn = TimeUtils.today,
    emit_audit_event_fn = _emit_audit_event,
    get_guard_state_fn = _signals_get_guard_state,
    set_guard_state_fn = _signals_set_guard_state,
    serialize_guard_state_fn = _signals_serialize_guard_state,
):
    return _signals_run_walkforward_validation_logic(
        req,
        now_fn=now_fn,
        today_fn=today_fn,
        emit_audit_event_fn=emit_audit_event_fn,
        get_guard_state_fn=get_guard_state_fn,
        set_guard_state_fn=set_guard_state_fn,
        serialize_guard_state_fn=serialize_guard_state_fn,
    )


get_guard_state = _signals_get_guard_state
set_guard_state = _signals_set_guard_state
serialize_guard_state = _signals_serialize_guard_state
guard_context = _signals_guard_context
serialize_run = _signals_serialize_run


def publish_signal_run_logic(
    req: PublishSignalsRequest,
    *,
    recommendation_filter_fn: Optional[Callable[[SignalRecommendation], bool]] = None,
):
    result = _signals_publish_signal_run_logic(
        req,
        validated_publish_channel_fn=_signals_validated_publish_channel,
        error_context_fn=_signals_error_context,
        get_guard_state_fn=_signals_get_guard_state,
        guard_context_fn=_signals_guard_context,
        emit_audit_event_fn=_emit_audit_event,
        get_publish_window_status_fn=_signals_get_publish_window_status,
        window_context_fn=_signals_window_context,
        build_delivery_message_fn=_signals_build_delivery_message,
        now_fn=TimeUtils.now,
        sleep_fn=time.sleep,
        increment_reason_count_fn=_signals_increment_reason_count,
        serialize_run_fn=_signals_serialize_run,
        recommendation_filter_fn=recommendation_filter_fn,
        create_lifecycle_records_fn=_create_published_signal_lifecycle_records,
    )
    result.pop("run", None)
    return result


def _retry_failed_deliveries_logic(req: RetryFailedDeliveriesRequest):
    return _signals_retry_failed_deliveries_logic(
        req,
        validated_publish_channel_fn=_signals_validated_publish_channel,
        error_context_fn=_signals_error_context,
        noop_context_fn=_signals_noop_context,
        emit_audit_event_fn=_emit_audit_event,
        publish_signal_run_logic_fn=publish_signal_run_logic,
        retry_request_builder_fn=PublishSignalsRequest,
    )


def _portfolio_window_metrics(portfolio_id: int, window_days: int):
    return _signals_portfolio_window_metrics(
        portfolio_id,
        window_days,
        now_fn=TimeUtils.now,
        today_fn=TimeUtils.today,
    )

from core.signals.publishing import build_delivery_message as _signals_build_delivery_message, increment_reason_count as _signals_increment_reason_count, publish_signal_run_logic as _signals_publish_signal_run_logic, retry_failed_deliveries_logic as _signals_retry_failed_deliveries_logic




