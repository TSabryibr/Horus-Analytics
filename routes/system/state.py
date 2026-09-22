"""
ROUTES SYSTEM STATE
===================
System state serializers, live guard status, and operator lockout logic.
"""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any, Optional

from fastapi import HTTPException

from core import TimeUtils
from core.settings import settings
from database import (
    Holiday,
    Portfolio,
    ProvisioningState,
    PublishedSignalLifecycle,
    SignalAuditEvent,
    SignalDeskState,
    SignalRecommendation,
    SignalRun,
    db,
)
from routes.shared import (
    get_durable_provisioning_state,
    scheduler,
)

logger = logging.getLogger("horus.api.system.state")


def _get_system_dep(name: str, default: Any = None) -> Any:
    import sys
    mod = sys.modules.get("routes.system")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    return default


_OPERATOR_DEVIATION_CATEGORIES = {
    "valid_signal_skipped",
    "invalid_manual_trade",
    "manual_trade_taken",
    "exit_rule_violation",
    "stop_modification",
    "manual_override",
}


def _serialize_provisioning_state() -> dict:
    row = ProvisioningState.get_or_none(ProvisioningState.name == "HISTORICAL_SIGNAL_PROVISIONING")
    if row is None:
        return {}

    return {
        "durable_status": str(row.status or "IDLE").upper(),
        "target_trading_days": int(row.target_trading_days or 0),
        "completed_trading_days": int(row.completed_trading_days or 0),
        "mode": str(row.mode or "AUTOMATIC").upper(),
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
        "last_error": row.last_error,
    }


def _serialize_telegram_config() -> dict:
    return {
        "configured": bool(settings.TELEGRAM_TOKEN and settings.CHAT_ID),
        "chat_id": settings.CHAT_ID,
        "enabled": settings.TELEGRAM_ENABLED,
    }


def _serialize_signal_desk_summary() -> dict:
    row = SignalDeskState.get_or_none(SignalDeskState.name == "PRIMARY")
    if row is None:
        return {
            "configured": False,
            "operating_mode": "MANUAL",
            "autopilot_armed": False,
            "autopilot_status": "IDLE",
            "queued_candidate_count": 0,
            "lanes": {"intraday": 0, "swing": 0, "position": 0},
        }

    lanes = _signal_desk_lane_counts(row)
    return {
        "configured": True,
        "operating_mode": str(row.operating_mode or "MANUAL").upper(),
        "autopilot_armed": bool(row.autopilot_armed),
        "autopilot_status": str(row.autopilot_status or "IDLE").upper(),
        "queued_candidate_count": sum(lanes.values()),
        "lanes": lanes,
        "last_autopilot_run_id": row.last_autopilot_run_id,
        "last_autopilot_published_at": row.last_autopilot_published_at.isoformat() if row.last_autopilot_published_at else None,
        "last_autopilot_error": row.last_autopilot_error,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _signal_desk_lane_key(run: Optional[SignalRun], rec: SignalRecommendation) -> str:
    scan_type = str(getattr(run, "scan_type", "") or "").upper()
    horizon_days = int(rec.horizon_days or 0)
    if scan_type in {"INTRADAY", "PRE_CLOSE"} or horizon_days <= 1:
        return "intraday"
    if horizon_days <= 10:
        return "swing"
    return "position"


def _signal_desk_lane_counts(row: SignalDeskState) -> dict[str, int]:
    lanes = {"intraday": 0, "swing": 0, "position": 0}
    try:
        manual_queue = json.loads(row.manual_queue_json or "{}")
        if isinstance(manual_queue, dict):
            for lane in lanes:
                items = manual_queue.get(lane) or []
                if isinstance(items, list):
                    lanes[lane] += len(items)
    except Exception:
        pass

    recommendations = (
        SignalRecommendation.select(SignalRecommendation, SignalRun)
        .join(SignalRun)
        .where(
            (SignalRecommendation.state == "ACTIVE") &
            (SignalRun.status == "COMPLETED")
        )
    )
    for recommendation in recommendations:
        lanes[_signal_desk_lane_key(recommendation.run, recommendation)] += 1

    return lanes


def _serialize_published_signal_lifecycle_summary() -> dict:
    total = PublishedSignalLifecycle.select().count()
    now_value = TimeUtils.now()
    active_states = ("PUBLISHED", "OPEN", "TP1_HIT", "AMBIGUOUS")
    ambiguous_count = PublishedSignalLifecycle.select().where(
        PublishedSignalLifecycle.state == "AMBIGUOUS"
    ).count()
    active_count = PublishedSignalLifecycle.select().where(
        PublishedSignalLifecycle.state.in_(active_states)
    ).count()
    stale_active_count = PublishedSignalLifecycle.select().where(
        (PublishedSignalLifecycle.state.in_(active_states)) &
        (PublishedSignalLifecycle.expires_at.is_null(False)) &
        (PublishedSignalLifecycle.expires_at < now_value)
    ).count()
    monitor_status = "ATTENTION" if ambiguous_count > 0 or stale_active_count > 0 else "READY"
    latest = (
        PublishedSignalLifecycle.select()
        .order_by(PublishedSignalLifecycle.published_at.desc(), PublishedSignalLifecycle.id.desc())
        .first()
    )
    return {
        "configured": total > 0,
        "total": total,
        "active_count": active_count,
        "ambiguous_count": ambiguous_count,
        "stale_active_count": stale_active_count,
        "monitor_status": monitor_status,
        "latest_published_at": latest.published_at.isoformat() if latest and latest.published_at else None,
    }


def _serialize_signal_followup_summary() -> dict:
    from core.signals.followups import get_signal_followup_summary
    return get_signal_followup_summary(now_fn=TimeUtils.now)


def _safe_json_load(raw):
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _day_bounds(day_value: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    start = datetime.datetime.combine(day_value, datetime.time.min)
    return start, start + datetime.timedelta(days=1)


def _parse_iso_date(date_value: str, *, field_name: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(str(date_value))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{field_name} must use YYYY-MM-DD format.") from exc


def _serialize_holiday(row: Holiday) -> dict:
    return {
        "id": row.id,
        "date": row.date.isoformat() if row.date else None,
        "description": row.description or "",
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def _upsert_holiday(holiday_date: datetime.date, description: str | None = None) -> Holiday:
    row, created = Holiday.get_or_create(
        date=holiday_date,
        defaults={"description": description or "EGX market holiday"},
    )
    if not created and description is not None:
        row.description = description or row.description
        row.save()
    return row


def _emit_operator_event(
    event_type: str,
    *,
    severity: str = "INFO",
    message: str | None = None,
    details: dict | None = None,
    run: SignalRun | None = None,
    portfolio: Portfolio | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
):
    try:
        SignalAuditEvent.create(
            event_type=str(event_type or "").upper().strip() or "OPERATOR_EVENT",
            severity=str(severity or "INFO").upper().strip() or "INFO",
            actor_type="OPERATOR",
            actor_id=None,
            run=run,
            portfolio=portfolio,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            details_json=json.dumps(details or {}, default=str),
        )
    except Exception:
        pass


def _latest_plan_confirmation(today_value: datetime.date | None = None):
    day_value = today_value or TimeUtils.today()
    day_start, day_end = _day_bounds(day_value)
    return (
        SignalAuditEvent.select()
        .where(
            (SignalAuditEvent.event_type == "OPERATOR_PLAN_CONFIRMED")
            & (SignalAuditEvent.created_at >= day_start)
            & (SignalAuditEvent.created_at < day_end)
        )
        .order_by(SignalAuditEvent.created_at.desc(), SignalAuditEvent.id.desc())
        .first()
    )


def _manual_override_abuse_state(today_value: datetime.date | None = None) -> dict:
    day_value = today_value or TimeUtils.today()
    day_start, day_end = _day_bounds(day_value)
    max_per_day = max(1, int(getattr(settings, "LIVE_MAX_MANUAL_OVERRIDES_PER_DAY", 3) or 3))
    count = (
        SignalAuditEvent.select()
        .where(
            (SignalAuditEvent.event_type == "OPERATOR_MANUAL_OVERRIDE")
            & (SignalAuditEvent.created_at >= day_start)
            & (SignalAuditEvent.created_at < day_end)
        )
        .count()
    )
    return {
        "today": str(day_value),
        "manual_override_count": int(count),
        "max_manual_overrides_per_day": int(max_per_day),
        "lockout_active": bool(int(count) >= int(max_per_day)),
    }


def _serialize_trading_plan_status(today_value: datetime.date | None = None) -> dict:
    require_confirmation = bool(getattr(settings, "LIVE_REQUIRE_DAILY_PLAN_CONFIRMATION", True))
    plan_event = _latest_plan_confirmation(today_value)
    details = _safe_json_load(plan_event.details_json) if plan_event else {}
    return {
        "required": require_confirmation,
        "confirmed_today": bool(plan_event is not None),
        "confirmed_at": plan_event.created_at.isoformat() if plan_event and plan_event.created_at else None,
        "plan": details if details else None,
    }


def _build_operator_lockout_summary(today_value: datetime.date | None = None) -> dict:
    from core.signals.executor import SignalExecutor

    day_value = today_value or TimeUtils.today()
    override_state = _manual_override_abuse_state(day_value)
    portfolios = list(
        Portfolio.select()
        .where(Portfolio.name.in_(["Intraday Signals", "Swing Signals", "Position Signals"]))
        .order_by(Portfolio.id.asc())
    )
    loss_lockouts: list[dict] = []
    max_daily_loss_pct = float(getattr(settings, "LIVE_MAX_DAILY_LOSS_PCT", 3.0) or 3.0)
    max_consecutive_losses = max(1, int(getattr(settings, "LIVE_MAX_CONSECUTIVE_LOSSES", 4) or 4))
    for portfolio in portfolios:
        account_size = float(SignalExecutor._resolve_account_size(portfolio))
        if account_size <= 0:
            continue
        loss_state = SignalExecutor._compute_realized_loss_state(portfolio, account_size)
        reasons = []
        if float(loss_state.get("daily_loss_pct", 0.0) or 0.0) >= max_daily_loss_pct:
            reasons.append("daily_loss_limit")
        if int(loss_state.get("consecutive_losses", 0) or 0) >= max_consecutive_losses:
            reasons.append("consecutive_losses_limit")
        if reasons:
            loss_lockouts.append(
                {
                    "portfolio_id": portfolio.id,
                    "portfolio_name": portfolio.name,
                    "reasons": reasons,
                    "loss_state": loss_state,
                }
            )
    return {
        "today": str(day_value),
        "manual_override": override_state,
        "loss_lockouts": loss_lockouts,
        "lockout_active": bool(override_state.get("lockout_active")) or bool(loss_lockouts),
    }


def _serialize_live_execution_guard() -> dict:
    today_value = TimeUtils.today()
    guard_enabled = bool(getattr(settings, "LIVE_ARM_GUARD_ENABLED", False))
    armed = bool(settings.is_live_execution_armed(today_value))
    plan_status = _serialize_trading_plan_status(today_value)
    lockout_status = _build_operator_lockout_summary(today_value)
    return {
        "guard_enabled": guard_enabled,
        "auto_trade_enabled": bool(getattr(settings, "AUTO_TRADE_ENABLED", False)),
        "armed": armed,
        "armed_raw": bool(getattr(settings, "LIVE_EXECUTION_ARMED", False)),
        "armed_on": getattr(settings, "LIVE_EXECUTION_ARMED_ON", None),
        "today": str(today_value),
        "expires_daily": guard_enabled,
        "trading_plan": plan_status,
        "lockout": lockout_status,
    }


def _db_connection_available() -> bool:
    try:
        db_obj = _get_system_dep("db", db)
        db_obj.connect(reuse_if_open=True)
        return True
    except Exception as e:
        logger.error(f"System status DB connection failed: {e}")
        return False


def _build_boot_status_payload(system_state: Optional[dict] = None) -> dict:
    from core.pipeline import refresh_pipeline_state
    refresh_fn = _get_system_dep("refresh_pipeline_state", refresh_pipeline_state)
    durable_prov_fn = _get_system_dep("get_durable_provisioning_state", get_durable_provisioning_state)
    scheduler_obj = _get_system_dep("scheduler", scheduler)
    if system_state is None:
        system_state = refresh_fn()
        system_state.update(durable_prov_fn())

    return {
        "app_name": getattr(settings, "APP_NAME", "Horus Analytics"),
        "app_version": getattr(settings, "APP_VERSION", "1.0.0"),
        "system_ready": system_state.get("status") == "READY",
        "message": system_state.get("message", "System Operational"),
        "pipeline_state": system_state.get("pipeline_state", "UNKNOWN"),
        "provisioning_status": system_state.get("provisioning_status"),
        "provisioning_target_trading_days": system_state.get("provisioning_target_trading_days"),
        "provisioning_completed_trading_days": system_state.get("provisioning_completed_trading_days"),
        "provisioning_error": system_state.get("provisioning_error"),
        "stale_mode": bool(system_state.get("stale_mode", False)),
        "freshness": system_state.get("freshness", {}),
        "sync_worker": system_state.get("sync_worker", {}),
        "db_connected": _db_connection_available(),
        "scheduler": {"running": getattr(scheduler_obj, "running", False)},
        "telegram": _serialize_telegram_config(),
        "signal_desk": _serialize_signal_desk_summary(),
        "signal_lifecycle": _serialize_published_signal_lifecycle_summary(),
        "signal_followups": _serialize_signal_followup_summary(),
        "live_execution": _serialize_live_execution_guard(),
        "timestamp": TimeUtils.now().isoformat(),
    } | durable_prov_fn()
