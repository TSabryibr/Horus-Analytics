"""
REPLAY API ROUTES
=================
Market Replay — replay a past trading day in compressed time.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
import io
import datetime
from core.auth import get_api_key
from core.replay_engine import start_replay, start_replay_campaign, stop_replay, get_replay_status
from core.excel_generator import build_replay_excel_report

public_router = APIRouter(tags=["replay"])
router = APIRouter(tags=["replay"], dependencies=[Depends(get_api_key)])


class ReplayStartRequest(BaseModel):
    date: str = Field(..., description="Target date in YYYY-MM-DD format")
    speed: int = Field(default=10, ge=1, le=200, description="Time compression multiplier (e.g., 10 = 10x faster)")
    notify: bool = Field(default=False, description="Send Telegram alerts during replay")
    report: bool = Field(default=False, description="Generate AI report at end of replay")
    profile_id: Optional[int] = Field(default=None, description="Optional scanner profile to use for replay daily phases")
    use_active_profile: bool = Field(default=False, description="Use the currently activated scanner profile when profile_id is omitted")
    close_open_positions_end: bool = Field(default=False, description="Close all open simulation positions when replay finishes")
    live_channel_routing: bool = Field(default=False, description="Route replay alerts through live channel configuration instead of the test bot")


class ReplayCampaignStartRequest(BaseModel):
    start_date: str = Field(..., description="Campaign start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="Campaign end date in YYYY-MM-DD format")
    speed: int = Field(default=10, ge=1, le=200, description="Time compression multiplier (e.g., 10 = 10x faster)")
    notify: bool = Field(default=False, description="Send Telegram alerts during replay")
    report: bool = Field(default=False, description="Generate AI report at end of replay campaign")
    profile_id: Optional[int] = Field(default=None, description="Optional scanner profile to use for replay daily phases")
    use_active_profile: bool = Field(default=False, description="Use the currently activated scanner profile when profile_id is omitted")
    reset_portfolio: bool = Field(default=True, description="Clear Intraday Simulation before campaign starts")
    close_open_positions_end: bool = Field(default=False, description="Close all open simulation positions when campaign finishes")
    allow_missing_intraday_as_holidays: bool = Field(default=False, description="Skip missing intraday weekdays as market holidays")
    live_channel_routing: bool = Field(default=False, description="Route replay alerts through live channel configuration instead of the test bot")


@router.post("/api/v1/replay/start")
def api_start_replay(payload: ReplayStartRequest):
    """Start a market replay session for a past trading day.

    The system replays the trading day in compressed time, running real scans
    at each tick and sending Telegram alerts with [🔄 REPLAY] prefix.
    """
    result = start_replay(
        replay_date=payload.date,
        speed=payload.speed,
        notify=payload.notify,
        report=payload.report,
        profile_id=payload.profile_id,
        use_active_profile=payload.use_active_profile,
        close_open_positions_end=payload.close_open_positions_end,
        live_channel_routing=payload.live_channel_routing,
    )
    return result


@router.post("/api/v1/replay/campaign/start")
def api_start_replay_campaign(payload: ReplayCampaignStartRequest):
    """Start a multi-day replay campaign over loaded intraday records."""
    result = start_replay_campaign(
        start_date=payload.start_date,
        end_date=payload.end_date,
        speed=payload.speed,
        notify=payload.notify,
        report=payload.report,
        profile_id=payload.profile_id,
        use_active_profile=payload.use_active_profile,
        reset_portfolio=payload.reset_portfolio,
        close_open_positions_end=payload.close_open_positions_end,
        allow_missing_intraday_as_holidays=payload.allow_missing_intraday_as_holidays,
        live_channel_routing=payload.live_channel_routing,
    )
    return result


@router.post("/api/v1/replay/stop")
def api_stop_replay():
    """Force-stop the current replay session."""
    return stop_replay()


@public_router.get("/api/v1/replay/status")
def api_replay_status():
    """Get the current replay session status.

    Returns progress percentage, signals found so far, current simulated time, etc.
    """
    return get_replay_status()


@public_router.get("/api/v1/replay/export/excel")
def api_export_replay_excel():
    """Download a styled multi-tab Excel report for the active or completed replay session."""
    status = get_replay_status()
    if not status or status.get("status") == "IDLE":
        ticks = status.get("ticks_completed", 0) if status else 0
        trades = len(status.get("active_trades") or []) if status else 0
        if ticks == 0 and trades == 0:
            raise HTTPException(
                status_code=400,
                detail="No active or completed replay session available for export. Start a replay session first."
            )

    try:
        excel_bytes = build_replay_excel_report(status)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        replay_date = str(status.get("date") or status.get("start_date") or "session").replace("-", "")
        filename = f"Horus_Replay_{replay_date}_{timestamp}.xlsx"

        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel report: {str(e)}")
