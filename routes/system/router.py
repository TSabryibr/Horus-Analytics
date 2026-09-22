"""
ROUTES SYSTEM ROUTER
====================
FastAPI routers for public and authenticated system management endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Query

from core.auth import get_api_key

from .maintenance import (
    confirm_holiday_logic,
    create_backup_logic,
    delete_holiday_logic,
    get_backfill_status_logic,
    get_backups_logic,
    get_hard_reset_token_logic,
    hard_reset_system_logic,
    list_holidays_logic,
    restore_backup_logic,
    stale_override_toggle_logic,
    start_historical_backfill_logic,
    upsert_holidays_logic,
)
from .telemetry import (
    confirm_operator_trading_plan_logic,
    get_audit_logs_logic,
    get_boot_system_status_logic,
    get_full_system_status_logic,
    get_live_execution_guard_logic,
    get_memory_diagnostics_logic,
    get_operator_deviation_journal_logic,
    get_operator_end_of_day_review_logic,
    get_operator_trading_plan_status_logic,
    get_system_integrity_report_logic,
    get_system_status_logic,
    record_operator_deviation_logic,
    set_live_execution_guard_logic,
)

public_router = APIRouter(tags=["system"])
router = APIRouter(tags=["system"], dependencies=[Depends(get_api_key)])


def _get_refresh_pipeline_state():
    import sys
    mod = sys.modules.get("routes.system")
    if mod and hasattr(mod, "refresh_pipeline_state"):
        return getattr(mod, "refresh_pipeline_state")
    from core.pipeline import refresh_pipeline_state
    return refresh_pipeline_state


@public_router.post("/api/v1/system/stale-override")
def stale_override_toggle(payload: dict):
    return stale_override_toggle_logic(payload)


@public_router.post("/api/v1/system/confirm-holiday")
def confirm_holiday(payload: dict = Body(...)):
    return confirm_holiday_logic(payload)


@router.get("/api/v1/system/holidays")
def list_holidays(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
):
    return list_holidays_logic(start_date=start_date, end_date=end_date)


@router.post("/api/v1/system/holidays")
def upsert_holidays(payload: dict = Body(...)):
    return upsert_holidays_logic(payload)


@router.delete("/api/v1/system/holidays/{holiday_date}")
def delete_holiday(holiday_date: str):
    return delete_holiday_logic(holiday_date)


@public_router.get("/api/v1/system/status")
def get_system_status():
    fn = _get_refresh_pipeline_state()
    from routes.shared import get_durable_provisioning_state
    payload = fn()
    payload.update(get_durable_provisioning_state())
    return payload


@public_router.get("/api/v1/system/boot-status")
def get_boot_system_status():
    return get_boot_system_status_logic()


@public_router.get("/api/v1/system/full-status")
def get_full_system_status():
    return get_full_system_status_logic()


@router.get("/api/v1/system/diagnostics/memory")
def get_memory_diagnostics():
    return get_memory_diagnostics_logic()


@router.get("/api/v1/system/live-execution")
def get_live_execution_guard():
    return get_live_execution_guard_logic()


@router.post("/api/v1/system/live-execution")
def set_live_execution_guard(payload: dict = Body(...)):
    return set_live_execution_guard_logic(payload)


@router.get("/api/v1/system/operator/trading-plan/status")
def get_operator_trading_plan_status():
    return get_operator_trading_plan_status_logic()


@router.post("/api/v1/system/operator/trading-plan/confirm")
def confirm_operator_trading_plan(payload: dict = Body(...)):
    return confirm_operator_trading_plan_logic(payload)


@router.post("/api/v1/system/operator/deviation")
def record_operator_deviation(payload: dict = Body(...)):
    return record_operator_deviation_logic(payload)


@router.get("/api/v1/system/operator/deviation-journal")
def get_operator_deviation_journal(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
):
    return get_operator_deviation_journal_logic(
        date_from=date_from,
        date_to=date_to,
        category=category,
        limit=limit,
    )


@router.get("/api/v1/system/operator/end-of-day-review")
def get_operator_end_of_day_review(date: Optional[str] = Query(None), persist: bool = Query(False)):
    return get_operator_end_of_day_review_logic(date=date, persist=persist)


@router.get("/api/v1/system/audit-logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
):
    return get_audit_logs_logic(
        limit=limit,
        offset=offset,
        event_type=event_type,
        severity=severity,
    )


@router.get("/api/v1/system/integrity-report")
def get_system_integrity_report():
    return get_system_integrity_report_logic()


@router.get("/api/v1/system/harvester/status")
def get_harvester_status():
    from data_engine.harvester_service import get_service_status
    return get_service_status()


@router.post("/api/v1/system/harvester/start")
def start_harvester_service():
    from data_engine.harvester_service import start_service
    try:
        start_service()
        return {"status": "success", "message": "Harvester service start triggered."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/system/harvester/stop")
def stop_harvester_service():
    from data_engine.harvester_service import stop_service
    try:
        stop_service()
        return {"status": "success", "message": "Harvester service stop triggered."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/system/hard-reset/token")
def get_hard_reset_token():
    return get_hard_reset_token_logic()


@router.post("/api/v1/system/hard-reset")
def hard_reset_system(payload: dict):
    return hard_reset_system_logic(payload)


@router.post("/api/v1/system/backfill")
def start_historical_backfill(
    background_tasks: BackgroundTasks,
    days: int | None = None,
    universe: str | None = None,
    signal_lanes: str | None = None,
):
    return start_historical_backfill_logic(
        background_tasks=background_tasks,
        days=days,
        universe_choice=universe,
        signal_lanes=signal_lanes,
    )


@public_router.get("/api/v1/system/backfill/status")
def get_backfill_status():
    return get_backfill_status_logic()


@public_router.get("/api/v1/system/backups")
def get_backups():
    return get_backups_logic()


@public_router.post("/api/v1/system/backups")
def create_backup(payload: dict = Body(default={})):
    return create_backup_logic(payload)


@public_router.post("/api/v1/system/backups/restore")
def restore_backup(payload: dict = Body(...)):
    return restore_backup_logic(payload)
