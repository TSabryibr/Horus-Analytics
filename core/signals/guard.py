from typing import Any, Optional, Callable
from database import SignalGuardState, SignalRun, SignalRecommendation, SignalDelivery
import datetime
import json
from core import TimeUtils

def serialize_run(run: SignalRun):
    return {
        "id": run.id,
        "run_date": run.run_date.strftime("%Y-%m-%d") if run.run_date else None,
        "scan_type": run.scan_type,
        "run_key": run.run_key,
        "status": run.status,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "universe_count": run.universe_count,
        "signals_count": run.signals_count,
        "published_count": run.published_count,
        "model_version": run.model_version,
        "error": run.error,
        "recommendations_count": SignalRecommendation.select().where(SignalRecommendation.run == run).count(),
        "deliveries_count": SignalDelivery.select().where(SignalDelivery.run == run).count(),
    }


def get_guard_state():
    try:
        state, _ = SignalGuardState.get_or_create(name="PUBLISH")
        return state
    except Exception as exc:
        if "no such table" in str(exc).lower():
            import database
            database.initialize_db()
            state, _ = SignalGuardState.get_or_create(name="PUBLISH")
            return state
        raise


def serialize_guard_state(state: SignalGuardState):
    return {
        "name": state.name,
        "is_blocked": state.is_blocked,
        "reason": state.reason,
        "source": state.source,
        "details": json.loads(state.details_json) if state.details_json else None,
        "updated_at": state.updated_at.isoformat() if state.updated_at else None,
    }


def guard_context(
    state: SignalGuardState,
    *,
    serialize_guard_state_fn: Callable[[SignalGuardState], dict] = serialize_guard_state,
) -> dict:
    guard = serialize_guard_state_fn(state)
    return {
        "block_type": "guard",
        "block_reason": guard["reason"] or "guard_blocked",
        "guard": guard,
        "guard_reason": guard["reason"],
        "guard_source": guard["source"],
        "guard_details": guard["details"],
    }


def set_guard_state(
    is_blocked: bool,
    reason: Optional[str],
    source: str,
    details: Optional[dict] = None,
    *,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
    get_guard_state_fn: Callable[[], SignalGuardState] = get_guard_state,
):
    state = get_guard_state_fn()
    state.is_blocked = is_blocked
    state.reason = reason
    state.source = source
    state.details_json = json.dumps(details) if details is not None else None
    state.updated_at = now_fn()
    state.save()
    return state


