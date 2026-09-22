"""
DRY RUN API ROUTES
==================
End-to-End pipeline fire drill — run the full pipeline once for a specific date.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from core.auth import get_api_key
from core.dryrun_engine import start_dryrun, get_dryrun_status

public_router = APIRouter(tags=["dryrun"])
router = APIRouter(tags=["dryrun"], dependencies=[Depends(get_api_key)])


class DryRunStartRequest(BaseModel):
    date: Optional[str] = Field(default=None, description="Target date in YYYY-MM-DD format (defaults to last trading day)")
    notify: bool = Field(default=False, description="Send Telegram alerts")
    report: bool = Field(default=True, description="Generate signal reports")
    ai_report: bool = Field(default=False, description="Generate AI daily report (slower)")
    profile_id: Optional[int] = Field(default=None, description="Optional scanner profile to use for the dry run")
    use_active_profile: bool = Field(default=False, description="Use the currently activated scanner profile when profile_id is omitted")


@router.post("/api/v1/dryrun/start")
def api_start_dryrun(payload: DryRunStartRequest):
    """Start an end-to-end dry run for a specific date.

    Fires the entire pipeline synchronously: scan → signals → cards → 
    Telegram → report → monitor. All Telegram messages include [🧪 DRY RUN] prefix.
    """
    result = start_dryrun(
        target_date=payload.date,
        notify=payload.notify,
        report=payload.report,
        ai_report=payload.ai_report,
        profile_id=payload.profile_id,
        use_active_profile=payload.use_active_profile,
    )
    return result


@public_router.get("/api/v1/dryrun/status")
def api_dryrun_status():
    """Get the current dry run status.

    Returns step-by-step progress, signals found, Telegram delivery count, 
    and comprehensive timing information.
    """
    return get_dryrun_status()
