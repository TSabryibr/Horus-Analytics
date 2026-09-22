import datetime
import json
from typing import Any, Callable, Optional

from fastapi import HTTPException

from core import TimeUtils
from database import (
    PublishedSignalLifecycle,
    SignalAuditEvent,
    SignalOutcome,
    SignalRecommendation,
    SignalRun,
    SignalValidationRun,
)

from .boundary import parse_run_date, validation_error
from core.signals.guard import get_guard_state, serialize_guard_state


def upsert_signal_outcome(
    *,
    recommendation: SignalRecommendation,
    run: SignalRun,
    outcome_status: str,
    entry_date: Optional[datetime.datetime] = None,
    exit_date: Optional[datetime.datetime] = None,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    pnl: Optional[float] = None,
    pnl_pct: Optional[float] = None,
    notes: Optional[str] = None,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
):
    existing = SignalOutcome.get_or_none(SignalOutcome.recommendation == recommendation)
    holding_days = None
    if entry_date and exit_date:
        holding_days = max(0, int((exit_date - entry_date).total_seconds() // 86400))

    payload = {
        "run": run,
        "ticker": recommendation.ticker,
        "outcome_status": outcome_status,
        "entry_date": entry_date,
        "exit_date": exit_date,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "pnl": pnl,
        "pnl_pct": pnl_pct,
        "holding_days": holding_days,
        "computed_at": now_fn(),
        "notes": notes,
    }
    if existing:
        for key, value in payload.items():
            setattr(existing, key, value)
        existing.save()
        return existing
    return SignalOutcome.create(recommendation=recommendation, **payload)


def _signed_price_pnl_pct(side: str, entry_price: Optional[float], exit_price: Optional[float]) -> Optional[float]:
    entry = float(entry_price or 0.0)
    exit_value = float(exit_price or 0.0)
    if entry <= 0 or exit_value <= 0:
        return None
    if str(side or "BUY").upper() == "SELL":
        return ((entry - exit_value) / entry) * 100.0
    return ((exit_value - entry) / entry) * 100.0


def _signed_price_pnl(side: str, entry_price: Optional[float], exit_price: Optional[float]) -> Optional[float]:
    entry = float(entry_price or 0.0)
    exit_value = float(exit_price or 0.0)
    if entry <= 0 or exit_value <= 0:
        return None
    if str(side or "BUY").upper() == "SELL":
        return entry - exit_value
    return exit_value - entry


def project_published_signal_lifecycle_outcome(
    lifecycle: PublishedSignalLifecycle,
    *,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
):
    recommendation = lifecycle.recommendation
    run = lifecycle.run
    if recommendation is None or run is None:
        return None

    state = str(lifecycle.state or "").upper()
    entry_date = lifecycle.opened_at or lifecycle.published_at
    entry_price = lifecycle.entry_price_filled or lifecycle.entry_price_planned
    side = recommendation.side

    if state in {"OPEN", "TP1_HIT"} and entry_date and entry_price:
        milestone_exit = lifecycle.target_price_1 if state == "TP1_HIT" else None
        milestone_pnl = _signed_price_pnl(side, entry_price, milestone_exit) if milestone_exit else None
        milestone_pnl_pct = _signed_price_pnl_pct(side, entry_price, milestone_exit) if milestone_exit else None
        note_suffix = "TP1 milestone reached." if state == "TP1_HIT" else "Lifecycle is open."
        return upsert_signal_outcome(
            recommendation=recommendation,
            run=run,
            outcome_status="OPEN",
            entry_date=entry_date,
            entry_price=entry_price,
            exit_price=milestone_exit,
            pnl=milestone_pnl,
            pnl_pct=milestone_pnl_pct,
            notes=f"Projected from published lifecycle state {state}. {note_suffix}",
            now_fn=now_fn,
        )

    if state == "TP2_HIT":
        exit_price = lifecycle.close_price or lifecycle.target_price_2 or lifecycle.target_price_1
        return upsert_signal_outcome(
            recommendation=recommendation,
            run=run,
            outcome_status="CLOSED",
            entry_date=entry_date,
            exit_date=lifecycle.closed_at or lifecycle.last_market_event_at or now_fn(),
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=_signed_price_pnl(side, entry_price, exit_price),
            pnl_pct=_signed_price_pnl_pct(side, entry_price, exit_price),
            notes="Projected from published lifecycle state TP2_HIT.",
            now_fn=now_fn,
        )

    if state == "STOP_LOSS_HIT":
        exit_price = lifecycle.close_price or lifecycle.stop_loss_active or lifecycle.stop_loss_initial
        return upsert_signal_outcome(
            recommendation=recommendation,
            run=run,
            outcome_status="CLOSED",
            entry_date=entry_date,
            exit_date=lifecycle.closed_at or lifecycle.last_market_event_at or now_fn(),
            entry_price=entry_price,
            exit_price=exit_price,
            pnl=_signed_price_pnl(side, entry_price, exit_price),
            pnl_pct=_signed_price_pnl_pct(side, entry_price, exit_price),
            notes=f"Projected from published lifecycle state STOP_LOSS_HIT ({lifecycle.close_reason or 'stop'}).",
            now_fn=now_fn,
        )

    if state in {"EXPIRED", "CANCELLED"}:
        return upsert_signal_outcome(
            recommendation=recommendation,
            run=run,
            outcome_status="NO_TRADE",
            entry_date=None,
            exit_date=lifecycle.closed_at or lifecycle.last_market_event_at or now_fn(),
            entry_price=None,
            exit_price=None,
            pnl=None,
            pnl_pct=None,
            notes=f"Projected from published lifecycle state {state}.",
            now_fn=now_fn,
        )

    return None


def serialize_audit_event(event: SignalAuditEvent):
    details = None
    if event.details_json:
        try:
            details = json.loads(event.details_json)
        except Exception:
            details = {"raw": event.details_json}
    return {
        "id": event.id,
        "event_type": event.event_type,
        "severity": event.severity,
        "actor_type": event.actor_type,
        "actor_id": event.actor_id,
        "run_id": event.run.id if event.run else None,
        "portfolio_id": event.portfolio.id if event.portfolio else None,
        "entity_type": event.entity_type,
        "entity_id": event.entity_id,
        "message": event.message,
        "details": details,
        "created_at": event.created_at.isoformat() if event.created_at else None,
    }


def list_signal_audit_events(
    *,
    limit: int = 200,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    actor_type: Optional[str] = None,
    run_id: Optional[int] = None,
    portfolio_id: Optional[int] = None,
    since: Optional[str] = None,
    validation_error_fn: Callable[..., dict] = validation_error,
    serialize_audit_event_fn: Callable[[SignalAuditEvent], dict] = serialize_audit_event,
):
    if limit < 1 or limit > 5000:
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "limit_out_of_range",
                "limit must be between 1 and 5000",
                parameter="limit",
                provided=limit,
                min=1,
                max=5000,
            ),
        )

    query = SignalAuditEvent.select()
    if event_type:
        query = query.where(SignalAuditEvent.event_type == event_type.upper())
    if severity:
        query = query.where(SignalAuditEvent.severity == severity.upper())
    if actor_type:
        query = query.where(SignalAuditEvent.actor_type == actor_type.upper())
    if run_id is not None:
        query = query.where(SignalAuditEvent.run == run_id)
    if portfolio_id is not None:
        query = query.where(SignalAuditEvent.portfolio == portfolio_id)
    if since:
        try:
            since_dt = datetime.datetime.fromisoformat(since)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=validation_error_fn(
                    "invalid_since",
                    "since must be ISO datetime (YYYY-MM-DDTHH:MM:SS)",
                    parameter="since",
                    since=since,
                ),
            ) from exc
        query = query.where(SignalAuditEvent.created_at >= since_dt)

    events = list(query.order_by(SignalAuditEvent.created_at.desc()).limit(limit))
    return {
        "count": len(events),
        "filters": {
            "event_type": event_type.upper() if event_type else None,
            "severity": severity.upper() if severity else None,
            "actor_type": actor_type.upper() if actor_type else None,
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "since": since,
            "limit": limit,
        },
        "events": [serialize_audit_event_fn(event) for event in events],
    }


def get_signal_audit_summary(
    *,
    days: int = 30,
    validation_error_fn: Callable[..., dict] = validation_error,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
    serialize_audit_event_fn: Callable[[SignalAuditEvent], dict] = serialize_audit_event,
):
    if days < 1 or days > 3650:
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "days_out_of_range",
                "days must be between 1 and 3650",
                parameter="days",
                provided=days,
                min=1,
                max=3650,
            ),
        )

    since_dt = now_fn() - datetime.timedelta(days=days)
    events = list(
        SignalAuditEvent.select()
        .where(SignalAuditEvent.created_at >= since_dt)
        .order_by(SignalAuditEvent.created_at.desc())
    )

    by_event_type = {}
    by_severity = {}
    by_actor_type = {}
    for event in events:
        by_event_type[event.event_type] = by_event_type.get(event.event_type, 0) + 1
        by_severity[event.severity] = by_severity.get(event.severity, 0) + 1
        by_actor_type[event.actor_type] = by_actor_type.get(event.actor_type, 0) + 1

    latest = events[0] if events else None
    return {
        "window_days": days,
        "from": since_dt.isoformat(),
        "to": now_fn().isoformat(),
        "total_events": len(events),
        "by_event_type": dict(sorted(by_event_type.items(), key=lambda kv: kv[0])),
        "by_severity": dict(sorted(by_severity.items(), key=lambda kv: kv[0])),
        "by_actor_type": dict(sorted(by_actor_type.items(), key=lambda kv: kv[0])),
        "latest_event": serialize_audit_event_fn(latest) if latest else None,
    }


def rebuild_signal_outcomes(
    req,
    *,
    parse_run_date_fn: Callable[[Optional[str]], datetime.date] = parse_run_date,
    rebuild_outcomes_for_run_fn: Optional[Callable[[SignalRun], dict]] = None,
):
    if rebuild_outcomes_for_run_fn is None:
        raise RuntimeError("rebuild_outcomes_for_run_fn is required")

    runs_query = SignalRun.select().where(SignalRun.status == "COMPLETED")
    if req.run_id is not None:
        runs_query = runs_query.where(SignalRun.id == req.run_id)
    else:
        if req.from_date:
            runs_query = runs_query.where(SignalRun.run_date >= parse_run_date_fn(req.from_date))
        if req.to_date:
            runs_query = runs_query.where(SignalRun.run_date <= parse_run_date_fn(req.to_date))
    runs = list(runs_query.order_by(SignalRun.run_date.desc()).limit(200))
    if not runs:
        return {"status": "noop", "message": "No completed runs found for rebuild.", "results": []}

    results = [rebuild_outcomes_for_run_fn(run) for run in runs]
    return {
        "status": "completed",
        "runs_processed": len(results),
        "results": results,
    }


def get_signal_outcomes(
    *,
    run_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    outcome_status: Optional[str] = None,
    limit: int = 200,
    validation_error_fn: Callable[..., dict] = validation_error,
    parse_run_date_fn: Callable[[Optional[str]], datetime.date] = parse_run_date,
):
    if limit < 1 or limit > 5000:
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "limit_out_of_range",
                "limit must be between 1 and 5000",
                parameter="limit",
                provided=limit,
                min=1,
                max=5000,
            ),
        )

    query = SignalOutcome.select().join(SignalRun).switch(SignalOutcome).join(SignalRecommendation)
    if run_id is not None:
        query = query.where(SignalOutcome.run == run_id)
    if from_date:
        query = query.where(SignalRun.run_date >= parse_run_date_fn(from_date))
    if to_date:
        query = query.where(SignalRun.run_date <= parse_run_date_fn(to_date))
    if outcome_status:
        query = query.where(SignalOutcome.outcome_status == outcome_status.upper())

    outcomes = list(query.order_by(SignalOutcome.computed_at.desc()).limit(limit))
    data = []
    for outcome in outcomes:
        rec = outcome.recommendation
        data.append(
            {
                "id": outcome.id,
                "run_id": outcome.run.id if outcome.run else None,
                "run_date": outcome.run.run_date.strftime("%Y-%m-%d") if outcome.run and outcome.run.run_date else None,
                "ticker": outcome.ticker,
                "outcome_status": outcome.outcome_status,
                "entry_date": outcome.entry_date.isoformat() if outcome.entry_date else None,
                "exit_date": outcome.exit_date.isoformat() if outcome.exit_date else None,
                "entry_price": outcome.entry_price,
                "exit_price": outcome.exit_price,
                "pnl": outcome.pnl,
                "pnl_pct": outcome.pnl_pct,
                "holding_days": outcome.holding_days,
                "confidence": rec.confidence if rec else None,
                "score": rec.score if rec else None,
                "side": rec.side if rec else None,
                "computed_at": outcome.computed_at.isoformat() if outcome.computed_at else None,
                "notes": outcome.notes,
            }
        )
    return {"count": len(data), "outcomes": data}


def get_signal_calibration(
    *,
    window: int = 90,
    include_breakdowns: bool = True,
    validation_error_fn: Callable[..., dict] = validation_error,
    today_fn: Callable[[], datetime.date] = TimeUtils.today,
):
    if window < 1 or window > 3650:
        raise HTTPException(
            status_code=400,
            detail=validation_error_fn(
                "window_out_of_range",
                "window must be between 1 and 3650",
                parameter="window",
                provided=window,
                min=1,
                max=3650,
            ),
        )
    since = today_fn() - datetime.timedelta(days=window - 1)
    outcomes = list(
        SignalOutcome.select()
        .join(SignalRun)
        .switch(SignalOutcome)
        .join(SignalRecommendation)
        .where((SignalRun.run_date >= since) & (SignalOutcome.outcome_status == "CLOSED"))
    )
    if not outcomes:
        empty = {
            "window_days": window,
            "from_date": since.strftime("%Y-%m-%d"),
            "to_date": today_fn().strftime("%Y-%m-%d"),
            "closed_signals": 0,
            "overall": {"win_rate_pct": 0.0, "avg_pnl_pct": 0.0},
            "confidence_bins": [],
        }
        if include_breakdowns:
            empty["regime_breakdown"] = {}
            empty["sector_breakdown"] = {}
        return empty

    def bin_label(confidence: float) -> str:
        low = int(max(0, min(100, (confidence // 10) * 10)))
        high = min(100, low + 9)
        if low == 100:
            return "100-100"
        return f"{low:02d}-{high:02d}"

    def sector_from_recommendation(rec: Optional[SignalRecommendation]) -> str:
        if not rec or not rec.rationale_json:
            return "Unknown"
        try:
            payload = json.loads(rec.rationale_json)
            return payload.get("sector") or "Unknown"
        except Exception:
            return "Unknown"

    def build_calibration_block(source_outcomes):
        bins = {}
        wins = 0
        total_pnl_pct = 0.0
        for outcome in source_outcomes:
            conf = outcome.recommendation.confidence if outcome.recommendation else 0.0
            label = bin_label(conf)
            bins.setdefault(label, {"count": 0, "wins": 0, "sum_pnl_pct": 0.0})
            pnl_pct = float(outcome.pnl_pct or 0.0)
            bins[label]["count"] += 1
            bins[label]["sum_pnl_pct"] += pnl_pct
            total_pnl_pct += pnl_pct
            if pnl_pct > 0:
                bins[label]["wins"] += 1
                wins += 1

        rows = []
        for label in sorted(bins.keys()):
            item = bins[label]
            count = item["count"]
            rows.append(
                {
                    "bin": label,
                    "count": count,
                    "win_rate_pct": round((item["wins"] / count) * 100, 2) if count else 0.0,
                    "avg_pnl_pct": round(item["sum_pnl_pct"] / count, 4) if count else 0.0,
                }
            )
        total = len(source_outcomes)
        return {
            "count": total,
            "win_rate_pct": round((wins / total) * 100, 2) if total else 0.0,
            "avg_pnl_pct": round(total_pnl_pct / total, 4) if total else 0.0,
            "confidence_bins": rows,
        }

    overall = build_calibration_block(outcomes)
    response = {
        "window_days": window,
        "from_date": since.strftime("%Y-%m-%d"),
        "to_date": today_fn().strftime("%Y-%m-%d"),
        "closed_signals": overall["count"],
        "overall": {
            "win_rate_pct": overall["win_rate_pct"],
            "avg_pnl_pct": overall["avg_pnl_pct"],
        },
        "confidence_bins": overall["confidence_bins"],
    }
    if include_breakdowns:
        regime_map = {}
        sector_map = {}
        for outcome in outcomes:
            rec = outcome.recommendation
            regime = rec.regime if rec and rec.regime else "Unknown"
            sector = sector_from_recommendation(rec)
            regime_map.setdefault(regime, []).append(outcome)
            sector_map.setdefault(sector, []).append(outcome)
        response["regime_breakdown"] = {
            regime: build_calibration_block(values)
            for regime, values in sorted(regime_map.items(), key=lambda item: item[0])
        }
        response["sector_breakdown"] = {
            sector: build_calibration_block(values)
            for sector, values in sorted(sector_map.items(), key=lambda item: item[0])
        }
    return response


def get_walkforward_validation_latest(
    *,
    get_guard_state_fn=get_guard_state,
    serialize_guard_state_fn: Callable[[Any], dict] = serialize_guard_state,
):

    latest = SignalValidationRun.select().order_by(SignalValidationRun.created_at.desc()).first()
    if not latest:
        return {"status": "empty", "validation": None}
    return {
        "status": "ok",
        "validation": {
            "id": latest.id,
            "run_date": latest.run_date.strftime("%Y-%m-%d"),
            "window_days": latest.window_days,
            "closed_signals": latest.closed_signals,
            "win_rate_pct": latest.win_rate_pct,
            "avg_pnl_pct": latest.avg_pnl_pct,
            "status": latest.status,
            "degradation_reason": latest.degradation_reason,
            "details": json.loads(latest.details_json) if latest.details_json else None,
            "created_at": latest.created_at.isoformat() if latest.created_at else None,
        },
        "guard_state": serialize_guard_state_fn(get_guard_state_fn()),
    }
