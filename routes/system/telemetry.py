"""
ROUTES SYSTEM TELEMETRY
=======================
System diagnostics, memory metrics, operator reviews, deviations, and audit logs.
"""

from __future__ import annotations

import datetime
import logging
import os
import threading
import time
from typing import Optional

from fastapi import Body, HTTPException, Query

from core import TimeUtils
from core.settings import settings
from database import (
    HorusExecution,
    Portfolio,
    Signal,
    SignalAuditEvent,
    SignalRecommendation,
    SignalRun,
    Trade,
)
from routes.shared import scheduler

from .state import (
    _OPERATOR_DEVIATION_CATEGORIES,
    _build_boot_status_payload,
    _build_operator_lockout_summary,
    _day_bounds,
    _emit_operator_event,
    _get_system_dep,
    _latest_plan_confirmation,
    _parse_iso_date,
    _safe_json_load,
    _serialize_live_execution_guard,
    _serialize_telegram_config,
    _serialize_trading_plan_status,
)

logger = logging.getLogger("horus.api.system.telemetry")


def get_system_status_logic() -> dict:
    from core.pipeline import refresh_pipeline_state
    from routes.shared import get_durable_provisioning_state
    refresh_fn = _get_system_dep("refresh_pipeline_state", refresh_pipeline_state)
    durable_prov_fn = _get_system_dep("get_durable_provisioning_state", get_durable_provisioning_state)
    payload = refresh_fn()
    payload.update(durable_prov_fn())
    return payload


def get_boot_system_status_logic() -> dict:
    return _build_boot_status_payload()


def get_full_system_status_logic() -> dict:
    from routes.data import get_data_status_logic
    system_state = get_system_status_logic()
    boot_payload = _build_boot_status_payload(system_state=system_state)

    try:
        data_status = get_data_status_logic()
    except Exception as e:
        data_status = {"status": "ERROR", "message": f"Data Status Error: {str(e)}"}

    scheduler_obj = _get_system_dep("scheduler", scheduler)
    jobs = []
    if hasattr(scheduler_obj, "get_jobs"):
        for job in scheduler_obj.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else None,
                "trigger": str(job.trigger),
            })

    alerts_config = {
        "telegram": _serialize_telegram_config(),
        "discord": {
            "configured": bool(settings.DISCORD_WEBHOOK_URL),
            "enabled": settings.DISCORD_ENABLED,
        },
    }

    total_signals = Signal.select().where(Signal.date <= TimeUtils.today()).count()
    last_signal = Signal.select().where(Signal.date <= TimeUtils.today()).order_by(Signal.date.desc()).first()

    try:
        from database.backup import get_backup_status
        backup_status = get_backup_status()
    except Exception as e:
        backup_status = {"configured": True, "status": "ERROR", "error": str(e)}

    try:
        from core.signals.sla import compute_delivery_sla_metrics
        delivery_sla = compute_delivery_sla_metrics(days=7)
    except Exception as e:
        delivery_sla = {"sla_compliant": False, "error": str(e)}

    return boot_payload | {
        "data_status": data_status,
        "scheduler": {"running": getattr(scheduler_obj, "running", False), "jobs": jobs},
        "alerts": alerts_config,
        "metrics": {
            "total_signals": total_signals,
            "last_signal_date": last_signal.date.strftime("%Y-%m-%d") if last_signal else None,
        },
        "database_backup": backup_status,
        "delivery_sla": delivery_sla,
    }



def get_memory_diagnostics_logic() -> dict:
    result = {
        "pid": os.getpid(),
        "timestamp": time.time(),
    }

    try:
        import psutil
        proc = psutil.Process(os.getpid())
        mem = proc.memory_info()
        result["rss_mb"] = round(mem.rss / 1048576, 1)
        result["vms_mb"] = round(mem.vms / 1048576, 1)
        result["threads_count"] = proc.num_threads()
        try:
            result["open_files_count"] = len(proc.open_files())
        except Exception:
            result["open_files_count"] = None
    except ImportError:
        result["psutil"] = "not_available"

    result["thread_inventory"] = [
        {"name": t.name, "daemon": t.daemon, "alive": t.is_alive()}
        for t in threading.enumerate()
    ]

    import tracemalloc
    if tracemalloc.is_tracing():
        snapshot = tracemalloc.take_snapshot()
        top = snapshot.statistics("lineno")[:20]
        result["tracemalloc_top_20"] = [
            {"file": str(s.traceback), "size_kb": round(s.size / 1024, 1), "count": s.count}
            for s in top
        ]
    else:
        result["tracemalloc"] = "disabled (set TRACEMALLOC=1 to enable)"

    return result


def get_live_execution_guard_logic() -> dict:
    return {"status": "success", "live_execution": _serialize_live_execution_guard()}


def set_live_execution_guard_logic(payload: dict) -> dict:
    requested = bool(payload.get("armed", True))
    if requested and not bool(getattr(settings, "AUTO_TRADE_ENABLED", False)):
        raise HTTPException(status_code=409, detail="AUTO_TRADE_ENABLED must be true before arming live execution.")
    if requested and bool(getattr(settings, "LIVE_REQUIRE_DAILY_PLAN_CONFIRMATION", True)):
        if _latest_plan_confirmation(TimeUtils.today()) is None:
            raise HTTPException(
                status_code=409,
                detail="Daily trading plan confirmation is required before arming live execution.",
            )
    if requested and bool(_build_operator_lockout_summary(TimeUtils.today()).get("lockout_active")):
        raise HTTPException(
            status_code=409,
            detail="Operator lockout is active (daily-loss, consecutive-loss, or manual-override limits).",
        )

    if requested:
        settings.arm_live_execution(TimeUtils.today())
        logger.warning("[System] Live execution armed for %s", TimeUtils.today())
    else:
        settings.disarm_live_execution()
        logger.warning("[System] Live execution disarmed.")

    return {"status": "success", "live_execution": _serialize_live_execution_guard()}


def get_operator_trading_plan_status_logic() -> dict:
    today_value = TimeUtils.today()
    return {
        "status": "success",
        "today": str(today_value),
        "trading_plan": _serialize_trading_plan_status(today_value),
        "lockout": _build_operator_lockout_summary(today_value),
    }


def confirm_operator_trading_plan_logic(payload: dict) -> dict:
    checklist_confirmed = bool(payload.get("checklist_confirmed", False))
    if not checklist_confirmed:
        raise HTTPException(status_code=400, detail="checklist_confirmed must be true to confirm today's plan.")

    today_value = TimeUtils.today()
    details = {
        "date": str(today_value),
        "session": str(payload.get("session", "DEFAULT")).strip().upper() or "DEFAULT",
        "max_trades": payload.get("max_trades"),
        "max_risk_per_trade_pct": payload.get("max_risk_per_trade_pct"),
        "max_daily_loss_pct": payload.get("max_daily_loss_pct"),
        "notes": str(payload.get("notes", "") or "").strip() or None,
        "checklist_confirmed": True,
    }
    _emit_operator_event(
        "OPERATOR_PLAN_CONFIRMED",
        severity="INFO",
        message="Daily trading plan confirmed.",
        details=details,
    )
    return {"status": "success", "today": str(today_value), "trading_plan": _serialize_trading_plan_status(today_value)}


def record_operator_deviation_logic(payload: dict) -> dict:
    category = str(payload.get("category", "") or "").strip().lower()
    if category not in _OPERATOR_DEVIATION_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported deviation category. Allowed: {sorted(_OPERATOR_DEVIATION_CATEGORIES)}",
        )

    event_type = "OPERATOR_MANUAL_OVERRIDE" if category == "manual_override" else "OPERATOR_DEVIATION"
    severity = str(payload.get("severity", "INFO") or "INFO").upper().strip() or "INFO"
    message = str(payload.get("message", "") or "").strip() or f"Operator deviation logged: {category}"
    details = {
        "category": category,
        "ticker": str(payload.get("ticker", "") or "").upper() or None,
        "run_id": payload.get("run_id"),
        "recommendation_id": payload.get("recommendation_id"),
        "execution_id": payload.get("execution_id"),
        "reason_note": str(payload.get("reason_note", "") or "").strip() or None,
        "metadata": payload.get("metadata") if isinstance(payload.get("metadata"), dict) else None,
    }

    run = SignalRun.get_or_none(SignalRun.id == details["run_id"]) if details["run_id"] else None
    portfolio_id = payload.get("portfolio_id")
    portfolio = Portfolio.get_or_none(Portfolio.id == portfolio_id) if portfolio_id else None
    _emit_operator_event(
        event_type,
        severity=severity,
        message=message,
        details=details,
        run=run,
        portfolio=portfolio,
        entity_type="TICKER" if details["ticker"] else "SYSTEM",
        entity_id=details["ticker"] or None,
    )

    today_value = TimeUtils.today()
    return {
        "status": "success",
        "today": str(today_value),
        "deviation": details,
        "lockout": _build_operator_lockout_summary(today_value),
    }


def get_operator_deviation_journal_logic(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 200,
) -> dict:
    from_day = _parse_iso_date(date_from, field_name="date_from") if date_from else TimeUtils.today()
    to_day = _parse_iso_date(date_to, field_name="date_to") if date_to else from_day
    if to_day < from_day:
        raise HTTPException(status_code=400, detail="date_to must be on or after date_from.")

    start_dt, _ = _day_bounds(from_day)
    _, end_dt = _day_bounds(to_day)
    query = (
        SignalAuditEvent.select()
        .where(
            (SignalAuditEvent.created_at >= start_dt)
            & (SignalAuditEvent.created_at < end_dt)
            & (SignalAuditEvent.event_type.in_(["OPERATOR_DEVIATION", "OPERATOR_MANUAL_OVERRIDE"]))
        )
        .order_by(SignalAuditEvent.created_at.desc(), SignalAuditEvent.id.desc())
    )

    entries = []
    for event in query.limit(limit):
        details = _safe_json_load(event.details_json)
        event_category = str(details.get("category", "") or "").strip().lower()
        if category and event_category != str(category).strip().lower():
            continue
        entries.append(
            {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity,
                "message": event.message,
                "category": event_category,
                "details": details,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            }
        )

    return {
        "status": "success",
        "date_from": str(from_day),
        "date_to": str(to_day),
        "count": len(entries),
        "entries": entries,
    }


def get_operator_end_of_day_review_logic(date: Optional[str] = None, persist: bool = False) -> dict:
    review_day = _parse_iso_date(date, field_name="date") if date else TimeUtils.today()
    start_dt, end_dt = _day_bounds(review_day)
    runs = list(
        SignalRun.select()
        .where((SignalRun.status == "COMPLETED") & (SignalRun.run_date == review_day))
        .order_by(SignalRun.completed_at.desc(), SignalRun.id.desc())
    )
    run_ids = [run.id for run in runs]
    recommendations = list(
        SignalRecommendation.select()
        .where(
            (SignalRecommendation.run.in_(run_ids))
            & (SignalRecommendation.state == "ACTIVE")
        )
    ) if run_ids else []

    executions = list(
        HorusExecution.select()
        .where((HorusExecution.created_at >= start_dt) & (HorusExecution.created_at < end_dt))
        .order_by(HorusExecution.created_at.asc())
    )
    state_counts: dict[str, int] = {}
    opened_tickers = set()
    for execution in executions:
        state = str(execution.state or "UNKNOWN").upper()
        state_counts[state] = int(state_counts.get(state, 0) + 1)
        if state == "OPEN":
            opened_tickers.add(str(execution.ticker or "").upper())

    intended_tickers = {
        str(rec.ticker or "").upper()
        for rec in recommendations
        if str(rec.ticker or "").strip()
    }
    missed_intent_tickers = sorted(t for t in intended_tickers if t not in opened_tickers)

    manual_trades = list(
        Trade.select()
        .where((Trade.entry_date >= start_dt) & (Trade.entry_date < end_dt))
    )
    manual_trade_tickers = sorted(
        {
            str(trade.ticker or "").upper()
            for trade in manual_trades
            if str(getattr(trade, "reason", "") or "").upper() == "MANUAL"
        }
    )
    off_plan_manual_tickers = sorted(t for t in manual_trade_tickers if t not in intended_tickers)

    deviation_query = list(
        SignalAuditEvent.select()
        .where(
            (SignalAuditEvent.created_at >= start_dt)
            & (SignalAuditEvent.created_at < end_dt)
            & (SignalAuditEvent.event_type.in_(["OPERATOR_DEVIATION", "OPERATOR_MANUAL_OVERRIDE"]))
        )
        .order_by(SignalAuditEvent.created_at.desc(), SignalAuditEvent.id.desc())
    )
    deviation_counts: dict[str, int] = {}
    for event in deviation_query:
        details = _safe_json_load(event.details_json)
        category_name = str(details.get("category", "uncategorized") or "uncategorized").strip().lower()
        deviation_counts[category_name] = int(deviation_counts.get(category_name, 0) + 1)

    review_payload = {
        "date": str(review_day),
        "trading_plan": _serialize_trading_plan_status(review_day),
        "lockout": _build_operator_lockout_summary(review_day),
        "strategy_intent": {
            "runs_completed": len(runs),
            "active_recommendations": len(recommendations),
            "intended_tickers": sorted(intended_tickers),
        },
        "actual_execution": {
            "execution_events": len(executions),
            "state_counts": state_counts,
            "opened_tickers": sorted(opened_tickers),
            "missed_intent_tickers": missed_intent_tickers,
            "manual_trade_tickers": manual_trade_tickers,
            "off_plan_manual_tickers": off_plan_manual_tickers,
        },
        "deviations": {
            "count": len(deviation_query),
            "by_category": dict(sorted(deviation_counts.items(), key=lambda item: item[0])),
        },
    }

    if persist:
        _emit_operator_event(
            "OPERATOR_EOD_REVIEW",
            severity="INFO",
            message=f"Operator end-of-day review generated for {review_day}.",
            details=review_payload,
        )
    return {"status": "success", "review": review_payload}


def get_audit_logs_logic(
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict:
    query = SignalAuditEvent.select()
    if event_type:
        query = query.where(SignalAuditEvent.event_type == event_type.upper())
    if severity:
        query = query.where(SignalAuditEvent.severity == severity.upper())

    total = query.count()
    events = list(query.order_by(SignalAuditEvent.created_at.desc()).limit(limit).offset(offset).dicts())

    for e in events:
        if e.get("created_at"):
            e["created_at"] = e["created_at"].isoformat()

    return {
        "status": "success",
        "total": total,
        "limit": limit,
        "offset": offset,
        "events": events,
    }


def get_system_integrity_report_logic() -> dict:
    from core import AuditEngine
    return AuditEngine.run_system_audit()
