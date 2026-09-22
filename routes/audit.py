from fastapi import APIRouter, Depends, Query
from core.auth import get_api_key
from core.audit import get_recent_logs
from typing import List, Optional

router = APIRouter(tags=["audit"], dependencies=[Depends(get_api_key)])

@router.get("/api/v1/system/audit")
def get_system_audit_trail(
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None
):
    """
    Returns recent system audit logs for institutional verification.
    """
    logs = get_recent_logs(limit=limit, category=category)
    return {
        "status": "success",
        "logs": logs
    }
