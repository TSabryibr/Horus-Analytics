from core.signals.publishing import publish_signal_run_logic, serialize_delivery
from core.signals.guard import get_guard_state, serialize_guard_state, set_guard_state, guard_context, serialize_run
from core.signals.models import DailyRunRequest, PublishSignalsRequest, RetryFailedDeliveriesRequest, RebuildOutcomesRequest, WalkforwardValidationRequest, GuardStateUpdateRequest, SignalDeskModeUpdateRequest, SignalDeskPromotionRequest, SignalDeskAutopilotRequest, SignalLifecycleOverrideRequest, SignalFollowUpActionRequest
from core.signals.audit import _emit_audit_event
import json
import datetime
import os
from typing import Optional

from fastapi import HTTPException

from core import TimeUtils
from database import SignalDeskState, SignalRun, SignalRecommendation, SignalDelivery
from core.signals.boundary import validation_error, error_context as _signals_error_context

def _float_env(name: str, default: float) -> float:
    try:
        val = os.getenv(name)
        if val is not None:
            return float(val)
    except (ValueError, TypeError):
        pass
    return default





_SIGNAL_DESK_MODES = {"MANUAL", "AI_ASSIST", "AUTOPILOT"}
_SIGNAL_DESK_LANES = {"INTRADAY": "intraday", "SWING": "swing", "POSITION": "position"}


def _parse_json_object(raw_value: Optional[str], fallback: Optional[dict] = None) -> dict:
    if not raw_value:
        return dict(fallback or {})
    try:
        parsed = json.loads(raw_value)
    except Exception:
        return dict(fallback or {})
    return parsed if isinstance(parsed, dict) else dict(fallback or {})


def _default_signal_desk_policy() -> dict:
    return {
        "signal_types": ["INTRADAY", "SWING", "POSITION"],
        "confidence_floor": 70,
        "source_modules": [],
        "min_candidates": 1,
        "batch_limits": {
            "intraday": 6,
            "swing": 6,
            "position": 4,
        },
    }


def _default_signal_desk_queue() -> dict:
    return {
        "intraday": [],
        "swing": [],
        "position": [],
    }


def _get_signal_desk_state() -> SignalDeskState:
    desk, _ = SignalDeskState.get_or_create(
        name="PRIMARY",
        defaults={
            "operating_mode": "MANUAL",
            "autopilot_armed": False,
            "publish_policy_json": json.dumps(_default_signal_desk_policy()),
        },
    )
    return desk


def _serialize_signal_desk_autopilot(desk: SignalDeskState) -> dict:
    return {
        "status": str(desk.autopilot_status or "IDLE").upper(),
        "last_run_id": desk.last_autopilot_run_id,
        "last_attempted_at": desk.last_autopilot_attempted_at.isoformat() if desk.last_autopilot_attempted_at else None,
        "last_published_at": desk.last_autopilot_published_at.isoformat() if desk.last_autopilot_published_at else None,
        "last_error": desk.last_autopilot_error,
        "summary": _parse_json_object(desk.autopilot_summary_json, fallback={}),
    }


def _update_signal_desk_autopilot_state(
    desk: SignalDeskState,
    *,
    status: str,
    run_id: Optional[int] = None,
    attempted_at: Optional[datetime.datetime] = None,
    published_at: Optional[datetime.datetime] = None,
    last_error: Optional[str] = None,
    summary: Optional[dict] = None,
) -> None:
    desk.autopilot_status = str(status or "IDLE").upper()
    desk.last_autopilot_run_id = run_id
    desk.last_autopilot_attempted_at = attempted_at
    desk.last_autopilot_published_at = published_at
    desk.last_autopilot_error = last_error
    if summary is not None:
        desk.autopilot_summary_json = json.dumps(summary)
    desk.updated_at = TimeUtils.now()
    desk.save()


def _normalize_signal_lane(value: str) -> str:
    normalized = str(value or "").upper().strip()
    lane = _SIGNAL_DESK_LANES.get(normalized)
    if not lane:
        raise HTTPException(
            status_code=422,
            detail=validation_error(
                "invalid_signal_lane",
                "Lane must be one of INTRADAY, SWING, or POSITION.",
                parameter="lane",
                lane=value,
            ),
        )
    return lane


def _get_signal_desk_queue(desk: SignalDeskState) -> dict:
    queue = _parse_json_object(desk.manual_queue_json, fallback=_default_signal_desk_queue())
    normalized = _default_signal_desk_queue()
    for lane, items in queue.items():
        if lane in normalized and isinstance(items, list):
            normalized[lane] = items
    return normalized


def _save_signal_desk_queue(desk: SignalDeskState, queue: dict) -> None:
    normalized = _default_signal_desk_queue()
    for lane, items in queue.items():
        if lane in normalized and isinstance(items, list):
            normalized[lane] = items
    desk.manual_queue_json = json.dumps(normalized)


def _desk_lane_key(run: Optional[SignalRun], rec: SignalRecommendation) -> str:
    scan_type = str(getattr(run, "scan_type", "") or "").upper()
    horizon_days = int(rec.horizon_days or 0)
    if scan_type in {"INTRADAY", "PRE_CLOSE"} or horizon_days <= 1:
        return "intraday"
    if horizon_days <= 10:
        return "swing"
    return "position"


_SIGNAL_SIDE_SOURCE_VALUES = {"BUY", "SELL", "LONG", "SHORT"}


def _serialize_signal_desk_candidate(rec: SignalRecommendation) -> dict:
    run = getattr(rec, "run", None)
    rationale = _parse_json_object(rec.rationale_json, fallback={})
    lane = _desk_lane_key(run, rec)
    return {
        "id": rec.id,
        "run_id": run.id if run else None,
        "ticker": rec.ticker,
        "side": rec.side,
        "entry_price": rec.entry_price,
        "stop_loss": rec.stop_loss,
        "target_price": rec.target_price,
        "target_price_2": _recommendation_target2(rec),
        "score": rec.score,
        "confidence": rec.confidence,
        "horizon_days": rec.horizon_days,
        "scan_type": getattr(run, "scan_type", None),
        "lane": lane,
        "source_module": _recommendation_source_module(rec) or None,
        "strategy_profile_id": rationale.get("strategy_profile_id"),
        "strategy_profile_name": rationale.get("strategy_profile_name"),
        "strategy_profile_source_type": rationale.get("strategy_profile_source_type"),
        "strategy_profile_market": rationale.get("strategy_profile_market"),
        "strategy_profile_timeframe": rationale.get("strategy_profile_timeframe"),
        "origin": "RECOMMENDATION",
        "rationale": rationale,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
    }


def _dedupe_signal_desk_recommendations(recommendations: list[SignalRecommendation]) -> list[SignalRecommendation]:
    seen: set[tuple[str, str]] = set()
    deduped: list[SignalRecommendation] = []
    for rec in recommendations:
        lane = _desk_lane_key(getattr(rec, "run", None), rec)
        ticker = str(rec.ticker or "").upper().strip()
        if not ticker:
            continue
        key = (lane, ticker)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(rec)
    return deduped


def _recommendation_source_module(rec: SignalRecommendation) -> str:
    rationale = _parse_json_object(rec.rationale_json, fallback={})
    source_module = str(rationale.get("source_module") or "").upper().strip()
    if source_module:
        return source_module
    source = str(rationale.get("source") or "").upper().strip()
    if source in _SIGNAL_SIDE_SOURCE_VALUES and getattr(rec, "run", None) is not None:
        return "SCANNER"
    return source


def _evaluate_signal_desk_autopilot(run: Optional[SignalRun] = None) -> dict:
    desk = _get_signal_desk_state()
    policy = _parse_json_object(desk.publish_policy_json, fallback=_default_signal_desk_policy())
    batch_limits = policy.get("batch_limits") if isinstance(policy.get("batch_limits"), dict) else {}
    source_modules = {
        str(item).upper().strip()
        for item in (policy.get("source_modules") or [])
        if str(item).strip()
    }
    allowed_signal_types = {
        str(item).upper().strip()
        for item in (policy.get("signal_types") or _default_signal_desk_policy()["signal_types"])
        if str(item).strip()
    }
    confidence_floor = float(policy.get("confidence_floor") or 0)
    min_candidates = max(1, int(policy.get("min_candidates") or 1))

    if run is None:
        run = (
            SignalRun.select()
            .where(SignalRun.status == "COMPLETED")
            .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc(), SignalRun.id.desc())
            .first()
        )
    if run is None:
        return {
            "status": "BLOCKED",
            "reason": "no_completed_run",
            "eligible_recommendation_ids": [],
            "run_id": None,
            "eligible_count": 0,
            "blocked_count": 0,
            "lane_counts": {"intraday": 0, "swing": 0, "position": 0},
            "blocked_reasons": {"no_completed_run": 1},
            "policy": policy,
        }

    recommendations = list(
        SignalRecommendation.select()
        .where((SignalRecommendation.run == run) & (SignalRecommendation.state == "ACTIVE"))
        .order_by(SignalRecommendation.score.desc(), SignalRecommendation.confidence.desc(), SignalRecommendation.id.desc())
    )
    lane_counts = {"intraday": 0, "swing": 0, "position": 0}
    blocked_reasons: dict[str, int] = {}
    eligible_ids: list[int] = []

    for rec in recommendations:
        lane = _desk_lane_key(run, rec)
        reasons: list[str] = []
        lane_signal_type = lane.upper()
        if allowed_signal_types and lane_signal_type not in allowed_signal_types:
            reasons.append("lane_not_allowed")
        if float(rec.confidence or 0) < confidence_floor:
            reasons.append("confidence_below_floor")
        source_module = _recommendation_source_module(rec)
        if source_modules and source_module not in source_modules:
            reasons.append("source_not_allowed")
        lane_limit = int(batch_limits.get(lane) or 0)
        if lane_limit > 0 and lane_counts[lane] >= lane_limit:
            reasons.append("lane_limit_reached")

        if reasons:
            for reason in reasons:
                blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1
            continue

        lane_counts[lane] += 1
        eligible_ids.append(rec.id)

    status = "READY"
    reason = None
    if str(desk.operating_mode or "MANUAL").upper() != "AUTOPILOT":
        status = "BLOCKED"
        reason = "autopilot_mode_inactive"
        blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1
    elif not desk.autopilot_armed:
        status = "BLOCKED"
        reason = "autopilot_not_armed"
        blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1
    elif len(eligible_ids) < min_candidates:
        status = "BLOCKED"
        reason = "insufficient_policy_eligible_candidates"
        blocked_reasons[reason] = blocked_reasons.get(reason, 0) + 1

    return {
        "status": status,
        "reason": reason,
        "run_id": run.id,
        "eligible_recommendation_ids": eligible_ids,
        "eligible_count": len(eligible_ids),
        "blocked_count": max(0, len(recommendations) - len(eligible_ids)),
        "lane_counts": lane_counts,
        "blocked_reasons": blocked_reasons,
        "policy": policy,
    }


def _serialize_manual_queue_candidate(candidate: dict, lane: str) -> dict:
    rationale = candidate.get("rationale") or {}
    return {
        "id": candidate.get("id"),
        "run_id": None,
        "ticker": candidate.get("ticker"),
        "side": candidate.get("side", "BUY"),
        "entry_price": candidate.get("entry_price"),
        "stop_loss": candidate.get("stop_loss"),
        "target_price": candidate.get("target_price"),
        "target_price_2": candidate.get("target_price_2") or _compute_tp2(candidate.get("side", "BUY"), float(candidate.get("target_price") or 0)),
        "score": candidate.get("score", 0.0),
        "confidence": candidate.get("confidence", 0.0),
        "horizon_days": candidate.get("horizon_days"),
        "scan_type": candidate.get("scan_type"),
        "lane": lane,
        "source_module": candidate.get("source_module"),
        "strategy_profile_id": candidate.get("strategy_profile_id") or rationale.get("strategy_profile_id"),
        "strategy_profile_name": candidate.get("strategy_profile_name") or rationale.get("strategy_profile_name"),
        "strategy_profile_source_type": candidate.get("strategy_profile_source_type") or rationale.get("strategy_profile_source_type"),
        "strategy_profile_market": candidate.get("strategy_profile_market") or rationale.get("strategy_profile_market"),
        "strategy_profile_timeframe": candidate.get("strategy_profile_timeframe") or rationale.get("strategy_profile_timeframe"),
        "origin": "MANUAL_QUEUE",
        "rationale": rationale,
        "created_at": candidate.get("promoted_at"),
    }


def _empty_signal_lane(key: str, label: str) -> dict:
    return {
        "key": key,
        "label": label,
        "count": 0,
        "candidates": [],
    }


def _build_signal_desk_payload() -> dict:
    desk = _get_signal_desk_state()
    manual_queue = _get_signal_desk_queue(desk)
    latest_run = (
        SignalRun.select()
        .where(SignalRun.status == "COMPLETED")
        .order_by(SignalRun.run_date.desc(), SignalRun.completed_at.desc(), SignalRun.id.desc())
        .first()
    )
    latest_delivery = (
        SignalDelivery.select()
        .order_by(SignalDelivery.created_at.desc(), SignalDelivery.id.desc())
        .first()
    )
    latest_failed_delivery = None
    failed_delivery_count = 0
    if latest_run is not None:
        latest_failed_delivery = (
            SignalDelivery.select()
            .where((SignalDelivery.run == latest_run) & (SignalDelivery.status == "FAILED"))
            .order_by(SignalDelivery.created_at.desc(), SignalDelivery.id.desc())
            .first()
        )
        failed_delivery_count = SignalDelivery.select().where(
            (SignalDelivery.run == latest_run) & (SignalDelivery.status == "FAILED")
        ).count()
    recommendations = _dedupe_signal_desk_recommendations(list(
        SignalRecommendation.select(SignalRecommendation, SignalRun)
        .join(SignalRun)
        .where(
            (SignalRecommendation.state == "ACTIVE") &
            (SignalRun.status == "COMPLETED")
        )
        .order_by(
            SignalRun.run_date.desc(),
            SignalRun.completed_at.desc(),
            SignalRecommendation.score.desc(),
            SignalRecommendation.confidence.desc(),
            SignalRecommendation.id.desc(),
        )
        .limit(300)
    ))[:60]

    lanes = {
        "intraday": _empty_signal_lane("intraday", "Intraday"),
        "swing": _empty_signal_lane("swing", "Swing"),
        "position": _empty_signal_lane("position", "Position"),
    }
    for lane_key, items in manual_queue.items():
        lanes[lane_key]["candidates"].extend(
            _serialize_manual_queue_candidate(item, lane_key)
            for item in items
        )
    for recommendation in recommendations:
        lane_key = _desk_lane_key(recommendation.run, recommendation)
        lanes[lane_key]["candidates"].append(_serialize_signal_desk_candidate(recommendation))

    for lane in lanes.values():
        lane["count"] = len(lane["candidates"])

    return {
        "name": desk.name,
        "operating_mode": str(desk.operating_mode or "MANUAL").upper(),
        "autopilot_armed": bool(desk.autopilot_armed),
        "publish_policy": _parse_json_object(
            desk.publish_policy_json,
            fallback=_default_signal_desk_policy(),
        ),
        "autopilot": _serialize_signal_desk_autopilot(desk),
        "lane_preferences": _parse_json_object(desk.lane_preferences_json, fallback={}),
        "lanes": lanes,
        "active_run": serialize_run(latest_run) if latest_run else None,
        "latest_delivery": serialize_delivery(latest_delivery) if latest_delivery else None,
        "latest_failed_delivery": serialize_delivery(latest_failed_delivery) if latest_failed_delivery else None,
        "failed_delivery_count": failed_delivery_count,
        "updated_at": desk.updated_at.isoformat() if desk.updated_at else None,
    }

def _compute_tp2(side: str, tp1: float) -> float:
    tp2_pct = max(0.0, _float_env("SIGNAL_TP2_PCT", 4.0))
    if tp1 <= 0:
        return 0.0
    if side.upper() == "SELL":
        return max(0.0, tp1 * (1 - (tp2_pct / 100.0)))
    return tp1 * (1 + (tp2_pct / 100.0))


def _recommendation_target2(rec: SignalRecommendation) -> float:
    if rec and rec.rationale_json:
        try:
            payload = json.loads(rec.rationale_json)
            raw_tp2 = payload.get("target_price_2")
            if raw_tp2 is not None:
                tp2 = float(raw_tp2)
                if tp2 > 0:
                    return tp2
        except Exception:
            pass
    return _compute_tp2(rec.side if rec else "BUY", float(rec.target_price or 0))


def _autopilot_error_message(detail) -> str:
    if isinstance(detail, dict):
        return str(detail.get("message") or detail.get("error_reason") or detail)
    return str(detail)


def trigger_signal_desk_autopilot_logic(req: SignalDeskAutopilotRequest):
    desk = _get_signal_desk_state()
    run = None
    if req.run_id is not None:
        run = SignalRun.get_or_none(SignalRun.id == req.run_id)
        if run is None:
            missing_summary = {
                "status": "BLOCKED",
                "reason": "signal_run_not_found",
                "run_id": req.run_id,
                "eligible_recommendation_ids": [],
                "eligible_count": 0,
                "blocked_count": 0,
                "lane_counts": {"intraday": 0, "swing": 0, "position": 0},
                "blocked_reasons": {"signal_run_not_found": 1},
            }
            _update_signal_desk_autopilot_state(
                desk,
                status="BLOCKED",
                run_id=req.run_id,
                attempted_at=TimeUtils.now(),
                last_error="signal_run_not_found",
                summary=missing_summary,
            )
            return {
                "status": "blocked",
                "run_id": req.run_id,
                "detail": _signals_error_context(
                    "not_found",
                    "signal_run_not_found",
                    "Signal run not found",
                    run_id=req.run_id,
                ),
                "autopilot": _serialize_signal_desk_autopilot(desk),
                "desk": _build_signal_desk_payload(),
            }

    evaluation = _evaluate_signal_desk_autopilot(run=run)
    target_run_id = evaluation.get("run_id")
    if evaluation["status"] != "READY":
        reason = str(evaluation.get("reason") or "autopilot_blocked")
        _update_signal_desk_autopilot_state(
            desk,
            status="BLOCKED",
            run_id=target_run_id,
            attempted_at=TimeUtils.now(),
            last_error=reason,
            summary=evaluation,
        )
        _emit_audit_event(
            event_type="DESK_AUTOPILOT_BLOCKED_POLICY",
            severity="WARN",
            actor_type="SYSTEM",
            entity_type="SIGNAL_DESK",
            entity_id=desk.name,
            run=SignalRun.get_or_none(SignalRun.id == target_run_id) if target_run_id else None,
            message="Signal desk autopilot blocked by desk policy or operating mode",
            details=evaluation,
        )
        return {
            "status": "blocked",
            "run_id": target_run_id,
            "autopilot": _serialize_signal_desk_autopilot(desk),
            "desk": _build_signal_desk_payload(),
        }

    eligible_ids = set(evaluation["eligible_recommendation_ids"])
    attempt_time = TimeUtils.now()
    _update_signal_desk_autopilot_state(
        desk,
        status="RUNNING",
        run_id=target_run_id,
        attempted_at=attempt_time,
        last_error=None,
        summary=evaluation,
    )
    _emit_audit_event(
        event_type="DESK_AUTOPILOT_STARTED",
        severity="INFO",
        actor_type="SYSTEM",
        entity_type="SIGNAL_DESK",
        entity_id=desk.name,
        run=SignalRun.get_or_none(SignalRun.id == target_run_id) if target_run_id else None,
        message="Signal desk autopilot started dispatch evaluation",
        details=evaluation,
    )

    try:
        result = publish_signal_run_logic(
            PublishSignalsRequest(
                run_id=target_run_id,
                channel="TELEGRAM",
                dry_run=req.dry_run,
                max_retries=req.max_retries,
                backoff_ms=req.backoff_ms,
                enforce_window=req.enforce_window,
                ignore_guard=req.ignore_guard,
            ),
            recommendation_filter_fn=lambda rec: rec.id in eligible_ids,
        )
    except HTTPException as exc:
        status = "BLOCKED" if int(getattr(exc, "status_code", 500)) < 500 else "FAILED"
        error_message = _autopilot_error_message(exc.detail)
        failed_summary = {**evaluation, "http_status": getattr(exc, "status_code", 500), "detail": exc.detail}
        _update_signal_desk_autopilot_state(
            desk,
            status=status,
            run_id=target_run_id,
            attempted_at=attempt_time,
            last_error=error_message,
            summary=failed_summary,
        )
        _emit_audit_event(
            event_type="DESK_AUTOPILOT_FAILED",
            severity="WARN" if status == "BLOCKED" else "ERROR",
            actor_type="SYSTEM",
            entity_type="SIGNAL_DESK",
            entity_id=desk.name,
            run=SignalRun.get_or_none(SignalRun.id == target_run_id) if target_run_id else None,
            message="Signal desk autopilot failed during publish execution",
            details=failed_summary,
        )
        return {
            "status": status.lower(),
            "run_id": target_run_id,
            "detail": exc.detail,
            "autopilot": _serialize_signal_desk_autopilot(desk),
            "desk": _build_signal_desk_payload(),
        }

    completion_time = TimeUtils.now()
    completed_summary = {**evaluation, "publish_summary": result.get("summary")}
    _update_signal_desk_autopilot_state(
        desk,
        status="COMPLETED",
        run_id=target_run_id,
        attempted_at=attempt_time,
        published_at=completion_time,
        last_error=None,
        summary=completed_summary,
    )
    _emit_audit_event(
        event_type="DESK_AUTOPILOT_COMPLETED",
        severity="INFO" if result.get("summary", {}).get("failed", 0) == 0 else "WARN",
        actor_type="SYSTEM",
        entity_type="SIGNAL_DESK",
        entity_id=desk.name,
        run=SignalRun.get_or_none(SignalRun.id == target_run_id) if target_run_id else None,
        message="Signal desk autopilot completed publish execution",
        details=completed_summary,
    )
    result["autopilot"] = _serialize_signal_desk_autopilot(desk)
    result["desk"] = _build_signal_desk_payload()
    return result
