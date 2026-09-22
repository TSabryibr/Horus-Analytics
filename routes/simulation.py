from fastapi import APIRouter, HTTPException, Depends
import datetime
from core import TimeUtils
from core.auth import get_api_key

public_router = APIRouter(tags=["simulation"])
router = APIRouter(tags=["simulation"], dependencies=[Depends(get_api_key)])

@router.post("/api/v1/simulate/start")
def start_simulation(payload: dict):
    date_str = payload.get("date")
    if not date_str: raise HTTPException(status_code=400, detail="Date required (YYYY-MM-DD)")
    try:
        target = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        TimeUtils.set_simulation(target)
        from routes.shared import purge_all_caches
        purge_all_caches()
        return {"status": "active", "date": date_str}
    except Exception as e: raise HTTPException(status_code=400, detail=f"Invalid format: {e}")

@router.post("/api/v1/simulate/stop")
def stop_simulation():
    TimeUtils.clear_simulation()
    from routes.shared import purge_all_caches
    purge_all_caches()
    return {"status": "live"}

@public_router.get("/api/v1/simulate/status")
@public_router.get("/api/v1/simulation/status")
def get_simulation_status():
    status = TimeUtils.is_simulating()
    date = TimeUtils.get_simulation_date().strftime("%Y-%m-%d") if status else None
    return {
        "status": "success",
        "active": status,
        "simulating": status, # Alias for compatibility
        "date": date
    }
