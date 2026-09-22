from core.settings import settings
from core.auth import get_api_key
from fastapi import APIRouter, HTTPException, Depends
from core.market.LiveFeedManager import  LiveFeedManager

public_router = APIRouter(tags=["live"])
router = APIRouter(tags=["live"], dependencies=[Depends(get_api_key)])

@router.post("/api/v1/live/start")
def start_live_feed():
    """Start the live market data stream."""
    if not settings.is_market_open():
        return {
            "status": "market_closed",
            "running": LiveFeedManager.is_running(),
            "market_open": False,
            "message": "EGX live feed is available only Sunday-Thursday, 10:00-14:30."
        }
    if LiveFeedManager.is_running():
        return {"status": "already_running", "running": True, "market_open": True}
    try:
        LiveFeedManager.start_monitoring()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start live feed: {e}")
    return {"status": "started", "running": LiveFeedManager.is_running(), "market_open": True}

@router.post("/api/v1/live/stop")
def stop_live_feed():
    """Stop the live market data stream."""
    LiveFeedManager.stop_monitoring()
    return {
        "status": "stopped",
        "running": LiveFeedManager.is_running(),
        "market_open": settings.is_market_open(),
    }

@public_router.get("/api/v1/live/status")
def get_live_status():
    """Get the current status of the live data feed."""
    market_open = settings.is_market_open()
    return {
        "status": "success",
        "running": LiveFeedManager.is_running(),
        "market_open": market_open,
        "session_mode": settings.SESSION_MODE,
        "last_update": LiveFeedManager.get_last_update_time(),
        "stats": LiveFeedManager.get_session_stats(),
        "hours": {
            "start": settings.MARKET_START_TIME,
            "end": settings.MARKET_END_TIME,
            "weekend_days": ["Friday", "Saturday"],
        }
    }


@public_router.get("/api/v1/live/watchdog")
def get_live_watchdog_status(max_stall_minutes: float = 5.0):
    """Query current market feed watchdog heartbeat and lag metrics."""
    from core.market.feed_watchdog import MarketFeedWatchdog
    return MarketFeedWatchdog.check_feed_heartbeat(max_stall_minutes=max_stall_minutes)

