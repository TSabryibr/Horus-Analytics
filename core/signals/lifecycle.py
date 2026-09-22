import datetime
import json
from typing import Any, Callable, Optional

from core import TimeUtils
from core.DataManager import DataManager
from database import (
    SignalRecommendation,
    SignalDelivery,
    Portfolio,
    HorusExecution,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    SignalExecutionAttribution,
    SignalRun,
)
from .followups import create_lifecycle_followup_job
from typing import List

from core.signals.desk import (
    _desk_lane_key,
    _recommendation_source_module,
    _recommendation_target2,
)
from core.signals.outcomes import project_published_signal_lifecycle_outcome as _signals_project_published_signal_lifecycle_outcome



_ACTIVE_STATES = ("PUBLISHED", "OPEN", "TP1_HIT")


def _price_touched(side: str, low_price: float, high_price: float, level: Optional[float]) -> bool:
    if level is None:
        return False
    price = float(level)
    if price <= 0:
        return False
    return low_price <= price <= high_price


def _ambiguous_levels_for_state(
    lifecycle: PublishedSignalLifecycle,
    low_price: float,
    high_price: float,
) -> list[str]:
    side = str(lifecycle.side or "BUY").upper()
    touched: list[str] = []

    if lifecycle.state == "PUBLISHED":
        if _price_touched(side, low_price, high_price, lifecycle.entry_price_planned):
            touched.append("entry")
        if _price_touched(side, low_price, high_price, lifecycle.stop_loss_active):
            touched.append("stop")
        if _price_touched(side, low_price, high_price, lifecycle.target_price_1):
            touched.append("tp1")
        if _price_touched(side, low_price, high_price, lifecycle.target_price_2):
            touched.append("tp2")
        return touched if len(touched) > 1 else []

    if lifecycle.state == "OPEN":
        if _price_touched(side, low_price, high_price, lifecycle.stop_loss_active):
            touched.append("stop")
        if _price_touched(side, low_price, high_price, lifecycle.target_price_1):
            touched.append("tp1")
        return touched if len(touched) > 1 else []

    if lifecycle.state == "TP1_HIT":
        if _price_touched(side, low_price, high_price, lifecycle.stop_loss_active):
            touched.append("stop")
        if _price_touched(side, low_price, high_price, lifecycle.target_price_2):
            touched.append("tp2")
        return touched if len(touched) > 1 else []

    return []


def _latest_bar_payload(
    ticker: str,
    *,
    intraday_fetch_fn: Callable[..., Any] = DataManager.get_intraday_data,
) -> Optional[tuple[Any, datetime.datetime]]:
    frame = intraday_fetch_fn(ticker, limit=1, refresh_if_stale=False)
    if frame is None or frame.empty:
        return None
    return frame.iloc[-1], frame.index[-1]


def _event_price_context(lifecycle: PublishedSignalLifecycle, extra: Optional[dict] = None) -> dict:
    payload = {
        "ticker": lifecycle.ticker,
        "entry_price_planned": lifecycle.entry_price_planned,
        "entry_price_filled": lifecycle.entry_price_filled,
        "stop_loss_active": lifecycle.stop_loss_active,
        "target_price_1": lifecycle.target_price_1,
        "target_price_2": lifecycle.target_price_2,
    }
    if extra:
        payload.update(extra)
    return payload


def _append_lifecycle_event(
    lifecycle: PublishedSignalLifecycle,
    *,
    event_type: str,
    from_state: Optional[str],
    to_state: Optional[str],
    event_source: str = "MONITOR",
    actor_type: str = "SYSTEM",
    actor_id: Optional[str] = None,
    event_time: Optional[datetime.datetime] = None,
    price_context: Optional[dict] = None,
    notes: Optional[str] = None,
) -> PublishedSignalLifecycleEvent:
    return PublishedSignalLifecycleEvent.create(
        lifecycle=lifecycle,
        event_type=str(event_type or "").upper(),
        from_state=from_state,
        to_state=to_state,
        event_source=str(event_source or "MONITOR").upper(),
        actor_type=str(actor_type or "SYSTEM").upper(),
        actor_id=actor_id,
        event_time=event_time or TimeUtils.now(),
        price_context_json=json.dumps(price_context or {}),
        notes=notes,
    )


def _project_lifecycle_outcome(lifecycle: PublishedSignalLifecycle) -> None:
    try:
        _signals_project_published_signal_lifecycle_outcome(lifecycle, now_fn=TimeUtils.now)
    except Exception:
        pass


def _coerce_run_date(value: Any) -> datetime.date:
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value)[0:10])


def _json_dict(value: Any) -> dict:
    try:
        payload = json.loads(value or "{}")
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _has_lifecycle_event(lifecycle: PublishedSignalLifecycle, event_type: str) -> bool:
    return PublishedSignalLifecycleEvent.select().where(
        (PublishedSignalLifecycleEvent.lifecycle == lifecycle)
        & (PublishedSignalLifecycleEvent.event_type == str(event_type or "").upper().strip())
    ).exists()


def _mark_execution_skipped(execution: HorusExecution, *, reason: str, now_value: datetime.datetime) -> None:
    details = _json_dict(execution.details_json)
    details["reason"] = reason
    details["cancelled_at"] = now_value.isoformat()
    execution.state = "SKIPPED"
    execution.close_reason = reason
    execution.details_json = json.dumps(details)
    execution.updated_at = now_value
    execution.save()
    attribution = SignalExecutionAttribution.get_or_none(SignalExecutionAttribution.execution == execution.id)
    if attribution is not None:
        attribution.signal_state = "SKIPPED"
        attribution.updated_at = now_value
        attribution.save()


def _transition_lifecycle(
    lifecycle: PublishedSignalLifecycle,
    *,
    to_state: str,
    event_type: str,
    event_time: datetime.datetime,
    event_source: str = "MONITOR",
    actor_type: str = "SYSTEM",
    actor_id: Optional[str] = None,
    notes: Optional[str] = None,
    close_reason: Optional[str] = None,
    close_price: Optional[float] = None,
    entry_price_filled: Optional[float] = None,
    stop_loss_active: Optional[float] = None,
    tp1_hit_at: Optional[datetime.datetime] = None,
) -> None:
    lifecycle_any: Any = lifecycle
    from_state = str(lifecycle_any.state or "")
    lifecycle_any.state = to_state
    lifecycle_any.last_market_event_at = event_time
    lifecycle_any.updated_at = event_time
    if entry_price_filled is not None:
        lifecycle_any.entry_price_filled = float(entry_price_filled)
    if stop_loss_active is not None:
        lifecycle_any.stop_loss_active = float(stop_loss_active)
    if tp1_hit_at is not None:
        lifecycle_any.tp1_hit_at = tp1_hit_at
    if to_state == "OPEN" and lifecycle_any.opened_at is None:
        lifecycle_any.opened_at = event_time
    if to_state in {"TP2_HIT", "STOP_LOSS_HIT", "EXPIRED", "CANCELLED"}:
        lifecycle_any.closed_at = event_time
    if close_reason is not None:
        lifecycle_any.close_reason = close_reason
    if close_price is not None:
        lifecycle_any.close_price = float(close_price)
    lifecycle_any.save()
    _append_lifecycle_event(
        lifecycle,
        event_type=event_type,
        from_state=from_state,
        to_state=to_state,
        event_source=event_source,
        actor_type=actor_type,
        actor_id=actor_id,
        event_time=event_time,
        price_context=_event_price_context(
            lifecycle,
            {
                "close_reason": close_reason,
                "close_price": close_price,
            },
        ),
        notes=notes,
    )
    _project_lifecycle_outcome(lifecycle)
    try:
        create_lifecycle_followup_job(lifecycle, now_fn=TimeUtils.now)
    except Exception:
        pass


def reconcile_pre_close_previews(
    *,
    run_date: Any,
    confirmed_tickers: set[str] | list[str] | tuple[str, ...],
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
) -> dict[str, Any]:
    run_date_value = _coerce_run_date(run_date)
    confirmed = {
        str(ticker or "").strip().upper()
        for ticker in (confirmed_tickers or set())
        if str(ticker or "").strip()
    }
    pre_close_runs = list(
        SignalRun.select()
        .where(
            (SignalRun.run_date == run_date_value)
            & (SignalRun.scan_type == "PRE_CLOSE")
            & (SignalRun.status == "COMPLETED")
        )
    )
    summary = {
        "pre_close_runs": len(pre_close_runs),
        "confirmed_tickers": len(confirmed),
        "confirmed_lifecycles": 0,
        "cancelled_lifecycles": 0,
        "cancelled_pending_entries": 0,
    }
    if not pre_close_runs:
        return {"status": "completed", "summary": summary}

    run_ids = [run.id for run in pre_close_runs]
    now_value = now_fn()
    lifecycles = list(
        PublishedSignalLifecycle.select()
        .where(
            (PublishedSignalLifecycle.run.in_(run_ids))  # type: ignore
            & (PublishedSignalLifecycle.state.in_(("PUBLISHED", "OPEN", "TP1_HIT")))  # type: ignore
        )
        .order_by(PublishedSignalLifecycle.published_at.asc(), PublishedSignalLifecycle.id.asc())  # type: ignore
    )

    for lifecycle in lifecycles:
        ticker = str(lifecycle.ticker or "").strip().upper()
        if not ticker:
            continue
        details = _json_dict(lifecycle.details_json)
        if ticker in confirmed:
            details["pre_close_confirmation"] = {
                "status": "CONFIRMED",
                "confirmed_at": now_value.isoformat(),
            }
            lifecycle.details_json = json.dumps(details)
            lifecycle.updated_at = now_value
            lifecycle.save()
            if not _has_lifecycle_event(lifecycle, "PRE_CLOSE_CONFIRMED"):
                _append_lifecycle_event(
                    lifecycle,
                    event_type="PRE_CLOSE_CONFIRMED",
                    from_state=lifecycle.state,
                    to_state=lifecycle.state,
                    event_source="DAILY_CONFIRMATION",
                    actor_type="SYSTEM",
                    event_time=now_value,
                    price_context=_event_price_context(lifecycle),
                    notes="Final daily scan confirmed the pre-close preview.",
                )
            summary["confirmed_lifecycles"] += 1
            continue

        details["pre_close_confirmation"] = {
            "status": "NOT_CONFIRMED",
            "cancelled_at": now_value.isoformat(),
        }
        lifecycle.details_json = json.dumps(details)
        _transition_lifecycle(
            lifecycle,
            to_state="CANCELLED",
            event_type="PRE_CLOSE_NOT_CONFIRMED",
            event_time=now_value,
            event_source="DAILY_CONFIRMATION",
            actor_type="SYSTEM",
            close_reason="PRE_CLOSE_NOT_CONFIRMED",
            notes="Final daily scan did not confirm the pre-close preview.",
        )
        summary["cancelled_lifecycles"] += 1

    pending_entries = list(
        HorusExecution.select()
        .where(
            (HorusExecution.run.in_(run_ids))  # type: ignore
            & (HorusExecution.state == "PENDING_OPEN")
        )
        .order_by(HorusExecution.created_at.asc(), HorusExecution.id.asc())  # type: ignore
    )
    for execution in pending_entries:
        ticker = str(execution.ticker or "").strip().upper()
        if ticker and ticker in confirmed:
            continue
        _mark_execution_skipped(
            execution,
            reason="PRE_CLOSE_NOT_CONFIRMED",
            now_value=now_value,
        )
        summary["cancelled_pending_entries"] += 1

    return {"status": "completed", "summary": summary}


def _handle_expiry(
    lifecycle: PublishedSignalLifecycle,
    *,
    now_value: datetime.datetime,
) -> bool:
    if lifecycle.state != "PUBLISHED":
        return False
    if lifecycle.expires_at is None or lifecycle.expires_at > now_value:
        return False
    _transition_lifecycle(
        lifecycle,
        to_state="EXPIRED",
        event_type="EXPIRED",
        event_time=now_value,
        event_source="MONITOR",
        actor_type="SYSTEM",
        close_reason="ENTRY_NOT_REACHED",
        notes="Signal expired before the planned entry was reached.",
    )
    return True


def monitor_published_signal_lifecycles(
    *,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
    latest_bar_fn: Callable[[str], Optional[tuple[Any, datetime.datetime]]] = _latest_bar_payload,
) -> dict[str, Any]:
    summary = {
        "opened": 0,
        "tp1_hit": 0,
        "closed_tp2": 0,
        "closed_stop": 0,
        "expired": 0,
        "ambiguous": 0,
        "failed": 0,
    }
    now_value = now_fn()
    active_lifecycles = list(
        PublishedSignalLifecycle.select()
        .where(PublishedSignalLifecycle.state.in_(_ACTIVE_STATES))  # type: ignore
        .order_by(PublishedSignalLifecycle.published_at.asc(), PublishedSignalLifecycle.id.asc())  # type: ignore
    )

    for lifecycle in active_lifecycles:
        try:
            if _handle_expiry(lifecycle, now_value=now_value):
                summary["expired"] += 1
                continue

            payload = latest_bar_fn(lifecycle.ticker)
            if not payload:
                continue
            last_bar, bar_time = payload
            if lifecycle.published_at and bar_time < lifecycle.published_at:
                continue

            low_price = float(last_bar["Low"])
            high_price = float(last_bar["High"])
            ambiguous_levels = _ambiguous_levels_for_state(lifecycle, low_price, high_price)
            if ambiguous_levels:
                _transition_lifecycle(
                    lifecycle,
                    to_state="AMBIGUOUS",
                    event_type="AMBIGUOUS",
                    event_time=bar_time,
                    event_source="MONITOR",
                    actor_type="SYSTEM",
                    notes=f"Same-bar sequencing is ambiguous: {', '.join(ambiguous_levels)}.",
                )
                summary["ambiguous"] += 1
                continue

            side = str(lifecycle.side or "BUY").upper()

            if lifecycle.state == "PUBLISHED" and _price_touched(side, low_price, high_price, lifecycle.entry_price_planned):
                _transition_lifecycle(
                    lifecycle,
                    to_state="OPEN",
                    event_type="OPENED",
                    event_time=bar_time,
                    event_source="MONITOR",
                    actor_type="SYSTEM",
                    entry_price_filled=float(lifecycle.entry_price_planned or 0.0),
                    notes="Market price reached the planned entry.",
                )
                summary["opened"] += 1
                continue

            if lifecycle.state == "OPEN" and _price_touched(side, low_price, high_price, lifecycle.target_price_1):
                breakeven_stop = float(lifecycle.entry_price_filled or lifecycle.entry_price_planned or lifecycle.stop_loss_active or 0.0)
                _transition_lifecycle(
                    lifecycle,
                    to_state="TP1_HIT",
                    event_type="TP1_HIT",
                    event_time=bar_time,
                    event_source="MONITOR",
                    actor_type="SYSTEM",
                    stop_loss_active=breakeven_stop,
                    tp1_hit_at=bar_time,
                    notes="Target 1 hit; active stop moved to breakeven.",
                )
                summary["tp1_hit"] += 1
                continue

            if lifecycle.state == "OPEN" and _price_touched(side, low_price, high_price, lifecycle.stop_loss_active):
                _transition_lifecycle(
                    lifecycle,
                    to_state="STOP_LOSS_HIT",
                    event_type="STOP_LOSS_HIT",
                    event_time=bar_time,
                    event_source="MONITOR",
                    actor_type="SYSTEM",
                    close_reason="STOP_LOSS_HIT",
                    close_price=float(lifecycle.stop_loss_active or 0.0),
                    notes="Active stop loss was reached before TP1.",
                )
                summary["closed_stop"] += 1
                continue

            if lifecycle.state == "TP1_HIT" and _price_touched(side, low_price, high_price, lifecycle.target_price_2):
                _transition_lifecycle(
                    lifecycle,
                    to_state="TP2_HIT",
                    event_type="TP2_HIT",
                    event_time=bar_time,
                    event_source="MONITOR",
                    actor_type="SYSTEM",
                    close_reason="TP2_HIT",
                    close_price=float(lifecycle.target_price_2 or 0.0),
                    notes="Target 2 reached after TP1.",
                )
                summary["closed_tp2"] += 1
                continue

            if lifecycle.state == "TP1_HIT" and _price_touched(side, low_price, high_price, lifecycle.stop_loss_active):
                _transition_lifecycle(
                    lifecycle,
                    to_state="STOP_LOSS_HIT",
                    event_type="STOP_LOSS_HIT",
                    event_time=bar_time,
                    event_source="MONITOR",
                    actor_type="SYSTEM",
                    close_reason="BREAKEVEN_STOP_HIT",
                    close_price=float(lifecycle.stop_loss_active or 0.0),
                    notes="Breakeven stop was reached after TP1.",
                )
                summary["closed_stop"] += 1
        except Exception:
            summary["failed"] += 1

    return {"status": "completed", "summary": summary}


def override_published_signal_lifecycle(
    lifecycle: PublishedSignalLifecycle,
    *,
    action: str,
    notes: Optional[str] = None,
    fill_price: Optional[float] = None,
    close_price: Optional[float] = None,
    target_state: Optional[str] = None,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
) -> PublishedSignalLifecycle:
    lifecycle_any: Any = lifecycle
    action_key = str(action or "").upper().strip()
    event_time = now_fn()
    current_state = str(lifecycle_any.state or "").upper()

    if action_key == "FORCE_OPEN":
        entry_price = float(fill_price or lifecycle_any.entry_price_filled or lifecycle_any.entry_price_planned or 0.0)
        if entry_price <= 0:
            raise ValueError("force_open requires a valid entry/fill price.")
        _transition_lifecycle(
            lifecycle,
            to_state="OPEN",
            event_type="ADMIN_FORCE_OPEN",
            event_time=event_time,
            event_source="ADMIN",
            actor_type="ADMIN",
            entry_price_filled=entry_price,
            notes=notes or "Admin forced lifecycle open.",
        )
        return lifecycle

    if action_key == "CORRECT_FILL_PRICE":
        next_fill = float(fill_price or 0.0)
        if next_fill <= 0:
            raise ValueError("correct_fill_price requires fill_price.")
        lifecycle_any.entry_price_filled = next_fill
        if current_state == "TP1_HIT":
            lifecycle_any.stop_loss_active = next_fill
        lifecycle_any.updated_at = event_time
        lifecycle_any.save()
        _append_lifecycle_event(
            lifecycle,
            event_type="ADMIN_CORRECT_FILL_PRICE",
            from_state=current_state,
            to_state=current_state,
            event_source="ADMIN",
            actor_type="ADMIN",
            event_time=event_time,
            price_context=_event_price_context(lifecycle, {"corrected_fill_price": next_fill}),
            notes=notes or "Admin corrected fill price.",
        )
        _project_lifecycle_outcome(lifecycle)
        return lifecycle

    if action_key == "MARK_TP1":
        breakeven_stop = float(lifecycle_any.entry_price_filled or lifecycle_any.entry_price_planned or 0.0)
        if breakeven_stop <= 0:
            raise ValueError("mark_tp1 requires an opened lifecycle with a valid entry price.")
        _transition_lifecycle(
            lifecycle,
            to_state="TP1_HIT",
            event_type="ADMIN_MARK_TP1",
            event_time=event_time,
            event_source="ADMIN",
            actor_type="ADMIN",
            stop_loss_active=breakeven_stop,
            tp1_hit_at=event_time,
            notes=notes or "Admin marked TP1 hit and moved stop to breakeven.",
        )
        return lifecycle

    if action_key == "MARK_TP2":
        resolved_close = float(close_price or lifecycle_any.target_price_2 or lifecycle_any.target_price_1 or 0.0)
        if resolved_close <= 0:
            raise ValueError("mark_tp2 requires a valid close price or target.")
        _transition_lifecycle(
            lifecycle,
            to_state="TP2_HIT",
            event_type="ADMIN_MARK_TP2",
            event_time=event_time,
            event_source="ADMIN",
            actor_type="ADMIN",
            close_reason="TP2_HIT",
            close_price=resolved_close,
            notes=notes or "Admin marked TP2 hit.",
        )
        return lifecycle

    if action_key == "MARK_STOP_LOSS":
        resolved_close = float(close_price or lifecycle_any.stop_loss_active or lifecycle_any.stop_loss_initial or 0.0)
        if resolved_close <= 0:
            raise ValueError("mark_stop_loss requires a valid close price or stop loss.")
        close_reason = "BREAKEVEN_STOP_HIT" if current_state == "TP1_HIT" else "STOP_LOSS_HIT"
        _transition_lifecycle(
            lifecycle,
            to_state="STOP_LOSS_HIT",
            event_type="ADMIN_MARK_STOP_LOSS",
            event_time=event_time,
            event_source="ADMIN",
            actor_type="ADMIN",
            close_reason=close_reason,
            close_price=resolved_close,
            notes=notes or "Admin marked stop loss hit.",
        )
        return lifecycle

    if action_key == "CANCEL":
        _transition_lifecycle(
            lifecycle,
            to_state="CANCELLED",
            event_type="ADMIN_CANCEL",
            event_time=event_time,
            event_source="ADMIN",
            actor_type="ADMIN",
            close_reason="ADMIN_CANCELLED",
            notes=notes or "Admin cancelled lifecycle.",
        )
        return lifecycle

    if action_key in {"REOPEN", "RECLASSIFY"}:
        resolved_target = str(target_state or "OPEN").upper().strip()
        allowed_targets = {"PUBLISHED", "OPEN", "TP1_HIT", "TP2_HIT", "STOP_LOSS_HIT", "CANCELLED", "EXPIRED"}
        if resolved_target not in allowed_targets:
            raise ValueError("target_state is invalid for reopen/reclassify.")
        if action_key == "RECLASSIFY" and current_state != "AMBIGUOUS":
            raise ValueError("reclassify is only valid for ambiguous lifecycles.")
        next_fill = fill_price
        next_close = close_price
        next_stop = None
        next_tp1_at = None
        close_reason = lifecycle_any.close_reason
        if resolved_target == "OPEN":
            next_fill = float(fill_price or lifecycle_any.entry_price_filled or lifecycle_any.entry_price_planned or 0.0)
            if next_fill <= 0:
                raise ValueError("reopen to OPEN requires a valid fill price.")
            close_reason = None
            next_close = None
            lifecycle_any.closed_at = None
        elif resolved_target == "TP1_HIT":
            next_fill = float(fill_price or lifecycle_any.entry_price_filled or lifecycle_any.entry_price_planned or 0.0)
            if next_fill <= 0:
                raise ValueError("reopen to TP1_HIT requires a valid fill price.")
            next_stop = next_fill
            next_tp1_at = event_time
            close_reason = None
            next_close = None
            lifecycle_any.closed_at = None
        elif resolved_target in {"TP2_HIT", "STOP_LOSS_HIT"}:
            next_close = float(close_price or lifecycle_any.close_price or lifecycle_any.stop_loss_active or lifecycle_any.target_price_2 or 0.0)
            if next_close <= 0:
                raise ValueError("terminal reclassification requires close_price or lifecycle exit levels.")
        else:
            next_close = None
        _transition_lifecycle(
            lifecycle,
            to_state=resolved_target,
            event_type=f"ADMIN_{action_key}",
            event_time=event_time,
            event_source="ADMIN",
            actor_type="ADMIN",
            entry_price_filled=next_fill,
            stop_loss_active=next_stop,
            tp1_hit_at=next_tp1_at,
            close_reason=close_reason,
            close_price=next_close,
            notes=notes or f"Admin {action_key.lower()} to {resolved_target}.",
        )
        return lifecycle

    raise ValueError("Unsupported lifecycle override action.")


def _published_signal_expiry(run: SignalRun, rec: SignalRecommendation, lane: str) -> datetime.datetime:
    base_time = run.completed_at or run.started_at or TimeUtils.now()
    normalized_lane = str(lane or "").lower().strip()
    if normalized_lane == "intraday":
        return datetime.datetime.combine(run.run_date, datetime.time.max)
    if normalized_lane == "position":
        window_days = max(10, int(rec.horizon_days or 10))
        return base_time + datetime.timedelta(days=window_days)
    window_days = max(3, int(rec.horizon_days or 5))
    return base_time + datetime.timedelta(days=window_days)

def _lifecycle_details_payload(rec: SignalRecommendation) -> dict:
    rationale = _json_dict(rec.rationale_json)
    return {
        "rationale": rationale,
        "invalidation_rule": rec.invalidation_rule,
        "confidence": float(rec.confidence or 0.0),
        "score": float(rec.score or 0.0),
        "horizon_days": int(rec.horizon_days or 0),
    }

def _serialize_published_signal_lifecycle_event(event: PublishedSignalLifecycleEvent) -> dict:
    try:
        price_context = json.loads(str(event.price_context_json or "{}"))
        if not isinstance(price_context, dict):
            price_context = {}
    except Exception:
        price_context = {}
    return {
        "id": event.id,
        "lifecycle_id": event.lifecycle.id if event.lifecycle else None,
        "event_type": event.event_type,
        "from_state": event.from_state,
        "to_state": event.to_state,
        "event_source": event.event_source,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "event_time": event.event_time.isoformat() if event.event_time else None,
        "price_context": price_context,
        "notes": event.notes,
    }

def _serialize_published_signal_lifecycle(lifecycle: PublishedSignalLifecycle, include_events: bool = False) -> dict:
    try:
        details = json.loads(str(lifecycle.details_json or "{}"))
        if not isinstance(details, dict):
            details = {}
    except Exception:
        details = {}

    payload = {
        "id": lifecycle.id,
        "recommendation_id": lifecycle.recommendation.id if lifecycle.recommendation else None,
        "run_id": lifecycle.run.id if lifecycle.run else None,
        "delivery_id": lifecycle.delivery.id if lifecycle.delivery else None,
        "portfolio_id": lifecycle.portfolio.id if lifecycle.portfolio else None,
        "portfolio_name": lifecycle.portfolio.name if lifecycle.portfolio else None,
        "ticker": lifecycle.ticker,
        "side": lifecycle.side,
        "lane": lifecycle.lane,
        "source_module": lifecycle.source_module,
        "operating_mode": lifecycle.operating_mode,
        "channel": lifecycle.channel,
        "published_message_id": lifecycle.published_message_id,
        "state": lifecycle.state,
        "resolution_source": lifecycle.resolution_source,
        "published_at": lifecycle.published_at.isoformat() if lifecycle.published_at else None,
        "expires_at": lifecycle.expires_at.isoformat() if lifecycle.expires_at else None,
        "opened_at": lifecycle.opened_at.isoformat() if lifecycle.opened_at else None,
        "tp1_hit_at": lifecycle.tp1_hit_at.isoformat() if lifecycle.tp1_hit_at else None,
        "closed_at": lifecycle.closed_at.isoformat() if lifecycle.closed_at else None,
        "entry_price_planned": lifecycle.entry_price_planned,
        "entry_price_filled": lifecycle.entry_price_filled,
        "stop_loss_initial": lifecycle.stop_loss_initial,
        "stop_loss_active": lifecycle.stop_loss_active,
        "target_price_1": lifecycle.target_price_1,
        "target_price_2": lifecycle.target_price_2,
        "close_price": lifecycle.close_price,
        "close_reason": lifecycle.close_reason,
        "override_notes": lifecycle.override_notes,
        "last_market_event_at": lifecycle.last_market_event_at.isoformat() if lifecycle.last_market_event_at else None,
        "details": details,
        "updated_at": lifecycle.updated_at.isoformat() if lifecycle.updated_at else None,
    }
    if include_events:
        events = (
            PublishedSignalLifecycleEvent.select()
            .where(PublishedSignalLifecycleEvent.lifecycle == lifecycle)
            .order_by(PublishedSignalLifecycleEvent.event_time.asc(), PublishedSignalLifecycleEvent.id.asc())  # type: ignore
        )
        payload["events"] = [_serialize_published_signal_lifecycle_event(event) for event in events]
    return payload

_PUBLISHED_SIGNAL_LIFECYCLE_STATES = {
    "PUBLISHED", "OPEN", "TP1_HIT", "TP2_HIT", 
    "STOP_LOSS_HIT", "EXPIRED", "CANCELLED", "AMBIGUOUS"
}

def _published_signal_lifecycle_summary() -> dict:
    total = PublishedSignalLifecycle.select().count()
    counts_by_state: dict[str, int] = {}
    counts_by_lane: dict[str, int] = {}
    
    for state in _PUBLISHED_SIGNAL_LIFECYCLE_STATES:
        counts_by_state[state] = PublishedSignalLifecycle.select().where(PublishedSignalLifecycle.state == state).count()
    for lane in ("intraday", "swing", "position"):
        counts_by_lane[lane] = PublishedSignalLifecycle.select().where(PublishedSignalLifecycle.lane == lane).count()
    active_states = ("PUBLISHED", "OPEN", "TP1_HIT", "AMBIGUOUS")
    active_count = PublishedSignalLifecycle.select().where(PublishedSignalLifecycle.state.in_(active_states)).count()  # type: ignore
    ambiguous_count = counts_by_state.get("AMBIGUOUS", 0)
    latest = (
        PublishedSignalLifecycle.select()
        .order_by(PublishedSignalLifecycle.published_at.desc(), PublishedSignalLifecycle.id.desc())  # type: ignore
        .first()
    )
    return {
        "configured": total > 0,
        "total": total,
        "active_count": active_count,
        "ambiguous_count": ambiguous_count,
        "counts_by_state": counts_by_state,
        "counts_by_lane": counts_by_lane,
        "latest_published_at": latest.published_at.isoformat() if latest and latest.published_at else None,
    }

def _create_lifecycle_event(
    lifecycle: PublishedSignalLifecycle,
    *,
    event_type: str,
    from_state: Optional[str],
    to_state: Optional[str],
    event_source: str = "AUTO",
    actor_type: str = "SYSTEM",
    actor_id: Optional[str] = None,
    event_time: Optional[datetime.datetime] = None,
    price_context: Optional[dict] = None,
    notes: Optional[str] = None,
) -> PublishedSignalLifecycleEvent:
    return PublishedSignalLifecycleEvent.create(
        lifecycle=lifecycle,
        event_type=str(event_type or "").upper(),
        from_state=from_state,
        to_state=to_state,
        event_source=str(event_source or "AUTO").upper(),
        actor_type=str(actor_type or "SYSTEM").upper(),
        actor_id=actor_id,
        event_time=event_time or TimeUtils.now(),
        price_context_json=json.dumps(price_context or {}),
        notes=notes,
    )

def _create_published_signal_lifecycle_records(
    *,
    run: SignalRun,
    delivery: SignalDelivery,
    portfolio: Optional[Portfolio],
    recommendations: List[SignalRecommendation],
    operating_mode: str,
    published_at: Optional[datetime.datetime] = None,
) -> list[PublishedSignalLifecycle]:
    published_at = published_at or TimeUtils.now()
    created: list[PublishedSignalLifecycle] = []
    for rec in recommendations:
        lane = _desk_lane_key(run, rec)
        details = _lifecycle_details_payload(rec)
        lifecycle, was_created = PublishedSignalLifecycle.get_or_create(
            delivery=delivery,
            recommendation=rec,
            defaults={
                "run": run,
                "portfolio": portfolio,
                "ticker": rec.ticker,
                "side": rec.side,
                "lane": lane,
                "source_module": _recommendation_source_module(rec) or None,
                "operating_mode": str(operating_mode or "MANUAL").upper(),
                "channel": delivery.channel,
                "published_message_id": delivery.provider_message_id,
                "state": "PUBLISHED",
                "resolution_source": "AUTO",
                "published_at": published_at,
                "expires_at": _published_signal_expiry(run, rec, lane),
                "entry_price_planned": float(rec.entry_price or 0.0),
                "stop_loss_initial": float(rec.stop_loss or 0.0),
                "stop_loss_active": float(rec.stop_loss or 0.0),
                "target_price_1": float(rec.target_price or 0.0),
                "target_price_2": _recommendation_target2(rec),
                "details_json": json.dumps(details),
                "updated_at": published_at,
            },
        )
        if not was_created:
            lifecycle.run = run
            lifecycle.portfolio = portfolio
            lifecycle.ticker = rec.ticker
            lifecycle.side = rec.side
            lifecycle.lane = lane
            lifecycle.source_module = _recommendation_source_module(rec) or None
            lifecycle.operating_mode = str(operating_mode or lifecycle.operating_mode or "MANUAL").upper()
            lifecycle.channel = delivery.channel
            lifecycle.published_message_id = delivery.provider_message_id
            lifecycle.published_at = published_at
            lifecycle.expires_at = _published_signal_expiry(run, rec, lane)
            lifecycle.entry_price_planned = float(rec.entry_price or 0.0)
            lifecycle.stop_loss_initial = float(rec.stop_loss or 0.0)
            lifecycle.stop_loss_active = float(lifecycle.stop_loss_active or rec.stop_loss or 0.0)
            lifecycle.target_price_1 = float(rec.target_price or 0.0)
            lifecycle.target_price_2 = _recommendation_target2(rec)
            lifecycle.details_json = json.dumps(details)
            lifecycle.updated_at = published_at
            lifecycle.save()
        created.append(lifecycle)
        if was_created:
            _create_lifecycle_event(
                lifecycle,
                event_type="PUBLISHED",
                from_state=None,
                to_state="PUBLISHED",
                event_source="AUTO",
                actor_type="SYSTEM",
                event_time=published_at,
                price_context={
                    "entry_price_planned": lifecycle.entry_price_planned,
                    "stop_loss_initial": lifecycle.stop_loss_initial,
                    "target_price_1": lifecycle.target_price_1,
                    "target_price_2": lifecycle.target_price_2,
                },
                notes="Lifecycle created from successful published Horus signal delivery.",
            )
    return created


