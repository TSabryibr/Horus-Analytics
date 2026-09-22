from core.settings import settings
from core.auth import get_api_key
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, List, Optional, Callable
import datetime
import json
import os
import time

from core.signals.models import DailyRunRequest, PublishSignalsRequest, RetryFailedDeliveriesRequest, RebuildOutcomesRequest, WalkforwardValidationRequest, GuardStateUpdateRequest, SignalDeskModeUpdateRequest, SignalDeskPromotionRequest, SignalDeskAutopilotRequest, SignalLifecycleOverrideRequest, SignalFollowUpActionRequest
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
from core.signals.runs import (
    get_guard_state as _signals_get_guard_state,
    guard_context as _signals_guard_context,
    run_daily_signals_logic as _signals_run_daily_signals_logic,
    run_walkforward_validation_logic as _signals_run_walkforward_validation_logic,
    serialize_guard_state as _signals_serialize_guard_state,
    serialize_run as _signals_serialize_run,
    set_guard_state as _signals_set_guard_state,
)
from core.signals.publishing import (
    build_delivery_message as _signals_build_delivery_message,
    increment_reason_count as _signals_increment_reason_count,
    publish_signal_run_logic as _signals_publish_signal_run_logic,
    retry_failed_deliveries_logic as _signals_retry_failed_deliveries_logic,
    serialize_delivery as _signals_serialize_delivery,
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
from core.signals.lifecycle import override_published_signal_lifecycle as _signals_override_published_signal_lifecycle
from routes.data import evaluate_data_freshness_logic
from core.exclusions import get_excluded_tickers_upper, is_excluded_ticker, normalize_ticker

public_router = APIRouter(tags=["signals"])
router = APIRouter(tags=["signals"], dependencies=[Depends(get_api_key)])

























from core.signals.lifecycle import _published_signal_expiry, _lifecycle_details_payload, _serialize_published_signal_lifecycle_event, _serialize_published_signal_lifecycle, _published_signal_lifecycle_summary, _create_lifecycle_event, _create_published_signal_lifecycle_records, _project_lifecycle_outcome
from core.signals.followup import _serialize_signal_followup, _published_signal_followup_summary
from core.signals.runs import run_daily_signals_logic, run_walkforward_validation_logic, publish_signal_run_logic, _retry_failed_deliveries_logic, _build_recommendation, _build_delivery_message, _recommendation_window, _upsert_outcome, _rebuild_outcomes_for_run, _portfolio_window_metrics
from core.signals.desk import trigger_signal_desk_autopilot_logic, _autopilot_error_message
from core.signals.audit import _emit_audit_event
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



from core.signals.lifecycle import _PUBLISHED_SIGNAL_LIFECYCLE_STATES




































@router.post("/api/v1/signals/runs/daily")
def run_daily_signals(
    req: DailyRunRequest,
):
    return run_daily_signals_logic(req)


@public_router.get("/api/v1/signals/runs/{run_id}")
def get_signal_run(run_id: int):
    run = SignalRun.get_or_none(SignalRun.id == run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "signal_run_not_found",
                "Run not found",
                run_id=run_id,
            ),
        )
    return {"run": _signals_serialize_run(run)}


@public_router.get("/api/v1/signals/runs")
def list_signal_runs(run_date: Optional[str] = None, scan_type: Optional[str] = None):
    query = SignalRun.select()
    if run_date:
        rd = _signals_parse_run_date(run_date)
        query = query.where(SignalRun.run_date == rd)
    if scan_type:
        query = query.where(SignalRun.scan_type == scan_type.upper())
    runs = list(query.order_by(SignalRun.started_at.desc()).limit(100))
    return {"runs": [_signals_serialize_run(r) for r in runs]}


@router.get("/api/v1/signals/desk")
def get_signal_desk():
    return {"desk": _build_signal_desk_payload()}


@router.post("/api/v1/signals/desk/mode")
def update_signal_desk_mode(req: SignalDeskModeUpdateRequest):
    operating_mode = str(req.operating_mode or "").upper().strip()
    if operating_mode not in _SIGNAL_DESK_MODES:
        raise HTTPException(
            status_code=422,
            detail=_signals_validation_error(
                "invalid_operating_mode",
                "Operating mode must be one of MANUAL, AI_ASSIST, or AUTOPILOT.",
                parameter="operating_mode",
                operating_mode=operating_mode,
            ),
        )

    desk = _get_signal_desk_state()
    desk.operating_mode = operating_mode
    if req.autopilot_armed is not None:
        desk.autopilot_armed = bool(req.autopilot_armed)
    if req.publish_policy is not None:
        next_policy = _default_signal_desk_policy()
        next_policy.update(req.publish_policy)
        desk.publish_policy_json = json.dumps(next_policy)
    desk.updated_at = TimeUtils.now()
    desk.save()

    _emit_audit_event(
        event_type="SIGNAL_DESK_MODE_UPDATED",
        actor_type="ADMIN",
        entity_type="SIGNAL_DESK",
        entity_id=desk.name,
        message="Signal desk operating mode updated",
        details={
            "operating_mode": desk.operating_mode,
            "autopilot_armed": desk.autopilot_armed,
            "publish_policy": _parse_json_object(desk.publish_policy_json, fallback=_default_signal_desk_policy()),
        },
    )
    return {"desk": _build_signal_desk_payload()}


@router.post("/api/v1/signals/desk/promote")
def promote_signal_desk_candidate(req: SignalDeskPromotionRequest):
    lane_key = _normalize_signal_lane(req.lane)
    desk = _get_signal_desk_state()
    queue = _get_signal_desk_queue(desk)

    queue[lane_key] = [
        item for item in queue.get(lane_key, [])
        if str(item.get("ticker", "")).upper() != req.ticker.upper().strip()
    ]
    queue[lane_key].insert(0, {
        "id": f"manual-{lane_key}-{req.ticker.upper().strip()}",
        "ticker": req.ticker.upper().strip(),
        "side": str(req.side or "BUY").upper().strip(),
        "entry_price": req.entry_price,
        "stop_loss": req.stop_loss,
        "target_price": req.target_price,
        "score": req.score,
        "confidence": req.confidence,
        "horizon_days": req.horizon_days,
        "source_module": str(req.source_module or "MANUAL").upper().strip(),
        "rationale": req.rationale or {},
        "promoted_at": TimeUtils.now().isoformat(),
    })
    _save_signal_desk_queue(desk, queue)
    desk.updated_at = TimeUtils.now()
    desk.save()

    _emit_audit_event(
        event_type="SIGNAL_DESK_CANDIDATE_PROMOTED",
        actor_type="ADMIN",
        entity_type="SIGNAL_DESK",
        entity_id=desk.name,
        message="Candidate promoted into desk lane",
        details={
            "lane": lane_key,
            "ticker": req.ticker.upper().strip(),
            "source_module": str(req.source_module or "MANUAL").upper().strip(),
        },
    )
    return {"desk": _build_signal_desk_payload()}






@router.post("/api/v1/signals/desk/autopilot")
def trigger_signal_desk_autopilot(req: SignalDeskAutopilotRequest):
    return trigger_signal_desk_autopilot_logic(req)


@router.get("/api/v1/signals/recommendations")
def get_signal_recommendations(run_id: Optional[int] = None, portfolio_id: Optional[int] = None):
    run = None
    if run_id is not None:
        run = SignalRun.get_or_none(SignalRun.id == run_id)
    else:
        run = (
            SignalRun.select()
            .where(SignalRun.status == "COMPLETED")
            .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc())
            .first()
        )
    if not run:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "signal_run_not_found",
                "Signal run not found",
                run_id=run_id,
            ),
        )

    portfolio_context = None
    if portfolio_id is not None:
        portfolio_context = Portfolio.get_or_none((Portfolio.id == portfolio_id) & (Portfolio.type == "USER"))
        if not portfolio_context:
            raise HTTPException(
                status_code=404,
                detail=_signals_error_context(
                    "not_found",
                    "user_portfolio_not_found",
                    "USER portfolio not found",
                    portfolio_id=portfolio_id,
                ),
            )

    recs = (
        SignalRecommendation.select()
        .where((SignalRecommendation.run == run) & (SignalRecommendation.state == "ACTIVE"))
        .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc())
    )
    excluded = get_excluded_tickers_upper()
    recs = [rec for rec in recs if not is_excluded_ticker(rec.ticker, excluded)]
    data = [
        {
            "id": rec.id,
            "ticker": rec.ticker,
            "side": rec.side,
            "entry_price": rec.entry_price,
            "stop_loss": rec.stop_loss,
            "target_price": rec.target_price,
            "target_price_2": _signals_recommendation_target2(rec),
            "score": rec.score,
            "confidence": rec.confidence,
            "rationale": json.loads(rec.rationale_json) if rec.rationale_json else None,
            "invalidation_rule": rec.invalidation_rule,
            "horizon_days": rec.horizon_days,
            "regime": rec.regime,
            "data_cutoff_at": rec.data_cutoff_at.isoformat() if rec.data_cutoff_at else None,
        }
        for rec in recs
    ]

    return {
        "run": _signals_serialize_run(run),
        "portfolio_context": (
            {
                "id": portfolio_context.id,
                "name": portfolio_context.name,
                "type": portfolio_context.type,
            }
            if portfolio_context
            else None
        ),
        "recommendations": data,
    }


@router.get("/api/v1/signals/audit/events")
def list_signal_audit_events(
    limit: int = 200,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    actor_type: Optional[str] = None,
    run_id: Optional[int] = None,
    portfolio_id: Optional[int] = None,
    since: Optional[str] = None,
):
    return _signals_list_signal_audit_events(
        limit=limit,
        event_type=event_type,
        severity=severity,
        actor_type=actor_type,
        run_id=run_id,
        portfolio_id=portfolio_id,
        since=since,
        validation_error_fn=_signals_validation_error,
        serialize_audit_event_fn=_signals_serialize_audit_event,
    )


@router.get("/api/v1/signals/audit/summary")
def get_signal_audit_summary(
    days: int = 30,
):
    return _signals_get_signal_audit_summary(
        days=days,
        validation_error_fn=_signals_validation_error,
        now_fn=TimeUtils.now,
        serialize_audit_event_fn=_signals_serialize_audit_event,
    )


@router.post("/api/v1/signals/outcomes/rebuild")
def rebuild_signal_outcomes(
    req: RebuildOutcomesRequest,
):
    return _signals_rebuild_signal_outcomes(
        req,
        parse_run_date_fn=_signals_parse_run_date,
        rebuild_outcomes_for_run_fn=_rebuild_outcomes_for_run,
    )


@router.get("/api/v1/signals/outcomes")
def get_signal_outcomes(
    run_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    outcome_status: Optional[str] = None,
    limit: int = 200,
):
    return _signals_get_signal_outcomes(
        run_id=run_id,
        from_date=from_date,
        to_date=to_date,
        outcome_status=outcome_status,
        limit=limit,
        validation_error_fn=_signals_validation_error,
        parse_run_date_fn=_signals_parse_run_date,
    )


@router.get("/api/v1/signals/calibration")
def get_signal_calibration(window: int = 90, include_breakdowns: bool = True):
    return _signals_get_signal_calibration(
        window=window,
        include_breakdowns=include_breakdowns,
        validation_error_fn=_signals_validation_error,
        today_fn=TimeUtils.today,
    )




@router.post("/api/v1/signals/validation/walkforward/run")
def run_walkforward_validation(
    req: WalkforwardValidationRequest,
):
    return run_walkforward_validation_logic(req)


@router.get("/api/v1/signals/validation/walkforward/latest")
def get_walkforward_validation_latest():
    return _signals_get_walkforward_validation_latest(
        get_guard_state_fn=_signals_get_guard_state,
        serialize_guard_state_fn=_signals_serialize_guard_state,
    )


@router.get("/api/v1/signals/guard")
def get_signal_guard_state(
):
    return {"guard_state": _signals_serialize_guard_state(_signals_get_guard_state())}


@router.post("/api/v1/signals/guard")
def set_signal_guard_state(
    req: GuardStateUpdateRequest,
):
    updated = _signals_set_guard_state(
        is_blocked=req.is_blocked,
        reason=req.reason,
        source=req.source,
        details=req.details,
    )
    _emit_audit_event(
        event_type="GUARD_UPDATED_MANUAL",
        severity="WARN" if req.is_blocked else "INFO",
        actor_type="ADMIN",
        entity_type="SIGNAL_GUARD",
        entity_id=updated.name,
        message="Guard state changed manually",
        details={
            "is_blocked": req.is_blocked,
            "reason": req.reason,
            "source": req.source,
            "details": req.details,
        },
    )
    return {"guard_state": _signals_serialize_guard_state(updated)}




@router.get("/api/v1/signals/performance/workspace")
def get_workspace_signal_performance(portfolio_id: int, windows: str = "30,60,90"):
    return _signals_get_workspace_signal_performance(
        portfolio_id=portfolio_id,
        windows=windows,
        error_context_fn=_signals_error_context,
        validation_error_fn=_signals_validation_error,
        portfolio_window_metrics_fn=_signals_portfolio_window_metrics,
        get_guard_state_fn=_signals_get_guard_state,
        serialize_guard_state_fn=_signals_serialize_guard_state,
    )




@router.post("/api/v1/signals/publish")
def publish_signal_run(
    req: PublishSignalsRequest,
):
    return publish_signal_run_logic(req)




@router.post("/api/v1/signals/publish/retry")
def retry_failed_deliveries(
    req: RetryFailedDeliveriesRequest,
):
    return _retry_failed_deliveries_logic(req)


@router.get("/api/v1/signals/deliveries")
def get_signal_deliveries(run_id: int):
    run = SignalRun.get_or_none(SignalRun.id == run_id)
    if not run:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "signal_run_not_found",
                "Run not found",
                run_id=run_id,
            ),
        )
    deliveries = (
        SignalDelivery.select()
        .where(SignalDelivery.run == run)
        .order_by(SignalDelivery.created_at.desc())
    )
    return {
        "run": _signals_serialize_run(run),
        "deliveries": [_signals_serialize_delivery(d) for d in deliveries]
    }


@router.post("/api/v1/signals/publish/retry-latest")
def retry_latest_failed_deliveries(
    channel: str = "TELEGRAM",
    max_retries: int = Query(2, ge=0, le=5),
    backoff_ms: int = Query(500, ge=0, le=20000),
    enforce_window: bool = False,
):
    run = (
        SignalRun.select()
        .where(SignalRun.status == "COMPLETED")
        .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc())
        .first()
    )
    if not run:
        return {"status": "noop", "message": "No completed signal run found."}

    req = RetryFailedDeliveriesRequest(
        run_id=run.id,
        channel=channel,
        max_retries=max_retries,
        backoff_ms=backoff_ms,
        enforce_window=enforce_window,
    )
    return _retry_failed_deliveries_logic(req)


@router.get("/api/v1/signals/lifecycle/summary")
def get_published_signal_lifecycle_summary():
    return _published_signal_lifecycle_summary()


@router.get("/api/v1/signals/lifecycle")
def get_published_signal_lifecycles(
    state: Optional[str] = None,
    ticker: Optional[str] = None,
    lane: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    query = PublishedSignalLifecycle.select().order_by(
        PublishedSignalLifecycle.published_at.desc(),
        PublishedSignalLifecycle.id.desc(),
    )
    if state:
        normalized_state = str(state or "").upper().strip()
        if normalized_state not in _PUBLISHED_SIGNAL_LIFECYCLE_STATES:
            raise HTTPException(
                status_code=422,
                detail=_signals_validation_error(
                    "invalid_lifecycle_state",
                    "Lifecycle state filter is invalid.",
                    parameter="state",
                    state=state,
                ),
            )
        query = query.where(PublishedSignalLifecycle.state == normalized_state)
    if ticker:
        query = query.where(fn.Upper(PublishedSignalLifecycle.ticker) == str(ticker).upper().strip())
    if lane:
        normalized_lane = str(lane or "").lower().strip()
        if normalized_lane not in {"intraday", "swing", "position"}:
            raise HTTPException(
                status_code=422,
                detail=_signals_validation_error(
                    "invalid_lifecycle_lane",
                    "Lifecycle lane filter is invalid.",
                    parameter="lane",
                    lane=lane,
                ),
            )
        query = query.where(PublishedSignalLifecycle.lane == normalized_lane)
    lifecycles = list(query.limit(limit))
    return {
        "summary": _published_signal_lifecycle_summary(),
        "count": len(lifecycles),
        "lifecycles": [_serialize_published_signal_lifecycle(lifecycle) for lifecycle in lifecycles],
    }


@router.get("/api/v1/signals/lifecycle/{lifecycle_id}")
def get_published_signal_lifecycle_detail(lifecycle_id: int):
    lifecycle = PublishedSignalLifecycle.get_or_none(PublishedSignalLifecycle.id == lifecycle_id)
    if not lifecycle:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "published_signal_lifecycle_not_found",
                "Published signal lifecycle not found",
                lifecycle_id=lifecycle_id,
            ),
        )
    return {"lifecycle": _serialize_published_signal_lifecycle(lifecycle, include_events=True)}


@router.get("/api/v1/signals/lifecycle-event-log")
def list_published_signal_lifecycle_events(
    lifecycle_id: Optional[int] = None,
    actor_type: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    query = PublishedSignalLifecycleEvent.select().order_by(
        PublishedSignalLifecycleEvent.event_time.desc(),
        PublishedSignalLifecycleEvent.id.desc(),
    )
    if lifecycle_id is not None:
        query = query.where(PublishedSignalLifecycleEvent.lifecycle == lifecycle_id)
    if actor_type:
        query = query.where(PublishedSignalLifecycleEvent.actor_type == str(actor_type).upper().strip())
    if event_type:
        query = query.where(PublishedSignalLifecycleEvent.event_type == str(event_type).upper().strip())
    events = list(query.limit(limit))
    return {
        "count": len(events),
        "events": [_serialize_published_signal_lifecycle_event(event) for event in events],
    }


@router.get("/api/v1/signals/followups/summary")
def get_published_signal_followup_summary():
    return _published_signal_followup_summary()


@router.get("/api/v1/signals/followups")
def get_published_signal_followups(
    queue_state: Optional[str] = None,
    trigger_state: Optional[str] = None,
    ticker: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
):
    query = PublishedSignalFollowUp.select().order_by(
        PublishedSignalFollowUp.created_at.desc(),
        PublishedSignalFollowUp.id.desc(),
    )
    if queue_state:
        normalized_queue_state = str(queue_state or "").upper().strip()
        if normalized_queue_state not in {"PENDING", "READY", "SENT", "FAILED", "SUPPRESSED"}:
            raise HTTPException(
                status_code=422,
                detail=_signals_validation_error(
                    "invalid_followup_queue_state",
                    "Follow-up queue state filter is invalid.",
                    parameter="queue_state",
                    queue_state=queue_state,
                ),
            )
        query = query.where(PublishedSignalFollowUp.queue_state == normalized_queue_state)
    if trigger_state:
        normalized_trigger_state = str(trigger_state or "").upper().strip()
        if normalized_trigger_state not in {"TP1_HIT", "TP2_HIT", "STOP_LOSS_HIT", "EXPIRED", "CANCELLED"}:
            raise HTTPException(
                status_code=422,
                detail=_signals_validation_error(
                    "invalid_followup_trigger_state",
                    "Follow-up trigger state filter is invalid.",
                    parameter="trigger_state",
                    trigger_state=trigger_state,
                ),
            )
        query = query.where(PublishedSignalFollowUp.trigger_state == normalized_trigger_state)
    if ticker:
        query = query.where(fn.Upper(PublishedSignalFollowUp.ticker) == str(ticker).upper().strip())
    followups = list(query.limit(limit))
    return {
        "summary": _published_signal_followup_summary(),
        "count": len(followups),
        "followups": [_serialize_signal_followup(followup) for followup in followups],
    }


@router.get("/api/v1/signals/followups/{followup_id}")
def get_published_signal_followup_detail(followup_id: int):
    followup = PublishedSignalFollowUp.get_or_none(PublishedSignalFollowUp.id == followup_id)
    if not followup:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "published_signal_followup_not_found",
                "Published signal follow-up not found",
                followup_id=followup_id,
            ),
        )
    return {"followup": _serialize_signal_followup(followup)}


@router.post("/api/v1/signals/followups/process")
def process_published_signal_followups(
    limit: int = Body(default=20, embed=True),
):
    limit = max(1, min(int(limit or 20), 200))
    result = _signals_process_signal_followups(
        limit=limit,
        send_message_fn=TelegramBot_Alerts.send_message,
        now_fn=TimeUtils.now,
    )
    _emit_audit_event(
        event_type="SIGNAL_FOLLOWUP_BATCH_PROCESSED",
        severity="INFO" if result.get("summary", {}).get("failed", 0) == 0 else "WARN",
        actor_type="SYSTEM",
        entity_type="PUBLISHED_SIGNAL_FOLLOWUP",
        entity_id="BATCH",
        message="Processed queued published signal follow-up jobs",
        details=result,
    )
    return {
        **result,
        "summary_snapshot": _published_signal_followup_summary(),
    }


@router.post("/api/v1/signals/followups/{followup_id}/action")
def act_on_published_signal_followup(followup_id: int, req: SignalFollowUpActionRequest):
    followup = PublishedSignalFollowUp.get_or_none(PublishedSignalFollowUp.id == followup_id)
    if not followup:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "published_signal_followup_not_found",
                "Published signal follow-up not found",
                followup_id=followup_id,
            ),
        )

    action = str(req.action or "").upper().strip()
    try:
        if action == "SEND_NOW":
            updated = _signals_send_signal_followup(
                followup,
                send_message_fn=TelegramBot_Alerts.send_message,
                now_fn=TimeUtils.now,
            )
        elif action == "RETRY":
            updated = _signals_requeue_signal_followup(
                followup,
                force_ready=True,
                now_fn=TimeUtils.now,
            )
            updated = _signals_send_signal_followup(
                updated,
                send_message_fn=TelegramBot_Alerts.send_message,
                now_fn=TimeUtils.now,
            )
        elif action == "SUPPRESS":
            updated = _signals_suppress_signal_followup(
                followup,
                reason=req.reason,
                now_fn=TimeUtils.now,
            )
        elif action == "RESEND":
            updated = _signals_requeue_signal_followup(
                followup,
                force_ready=True,
                now_fn=TimeUtils.now,
            )
        else:
            raise ValueError("Unsupported follow-up action.")
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=_signals_validation_error(
                "invalid_followup_action",
                str(exc),
                parameter="action",
                action=req.action,
            ),
        ) from exc

    _emit_audit_event(
        event_type=f"SIGNAL_FOLLOWUP_{action}",
        severity="INFO" if str(updated.queue_state or "").upper() != "FAILED" else "WARN",
        actor_type="ADMIN",
        run=updated.run,
        portfolio=updated.portfolio,
        entity_type="PUBLISHED_SIGNAL_FOLLOWUP",
        entity_id=str(updated.id),
        message="Published signal follow-up action executed",
        details={
            "action": action,
            "queue_state": updated.queue_state,
            "trigger_state": updated.trigger_state,
            "ticker": updated.ticker,
            "reason": req.reason,
            "retry_count": updated.retry_count,
        },
    )
    return {
        "followup": _serialize_signal_followup(updated),
        "summary": _published_signal_followup_summary(),
    }


@router.post("/api/v1/signals/lifecycle/{lifecycle_id}/override")
def override_published_signal_lifecycle(lifecycle_id: int, req: SignalLifecycleOverrideRequest):
    lifecycle = PublishedSignalLifecycle.get_or_none(PublishedSignalLifecycle.id == lifecycle_id)
    if not lifecycle:
        raise HTTPException(
            status_code=404,
            detail=_signals_error_context(
                "not_found",
                "published_signal_lifecycle_not_found",
                "Published signal lifecycle not found",
                lifecycle_id=lifecycle_id,
            ),
        )

    try:
        updated = _signals_override_published_signal_lifecycle(
            lifecycle,
            action=req.action,
            notes=req.notes,
            fill_price=req.fill_price,
            close_price=req.close_price,
            target_state=req.target_state,
            now_fn=TimeUtils.now,
        )
        _project_lifecycle_outcome(updated)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=_signals_validation_error(
                "invalid_lifecycle_override",
                str(exc),
                parameter="action",
                action=req.action,
                target_state=req.target_state,
            ),
        ) from exc

    _emit_audit_event(
        event_type="PUBLISHED_SIGNAL_LIFECYCLE_OVERRIDE",
        severity="WARN",
        actor_type="ADMIN",
        run=updated.run,
        portfolio=updated.portfolio,
        entity_type="PUBLISHED_SIGNAL_LIFECYCLE",
        entity_id=str(updated.id),
        message="Published signal lifecycle overridden by admin action",
        details={
            "action": str(req.action or "").upper().strip(),
            "target_state": req.target_state,
            "fill_price": req.fill_price,
            "close_price": req.close_price,
            "state": updated.state,
            "ticker": updated.ticker,
        },
    )
    return {"lifecycle": _serialize_published_signal_lifecycle(updated, include_events=True)}


@router.get("/api/v1/signals/ops/sla")
def get_signals_sla(days: int = 30):
    return _signals_get_signals_sla(
        days=days,
        validation_error_fn=_signals_validation_error,
        today_fn=TimeUtils.today,
        now_fn=TimeUtils.now,
        get_guard_state_fn=_signals_get_guard_state,
        serialize_guard_state_fn=_signals_serialize_guard_state,
        serialize_run_fn=_signals_serialize_run,
    )


@router.get("/api/v1/signals/sla")
def get_signals_delivery_sla(days: int = 7, target_latency_ms: float = 5000.0):
    from core.signals.sla import compute_delivery_sla_metrics
    return compute_delivery_sla_metrics(days=days, target_latency_ms=target_latency_ms)




