from core.settings import settings
from fastapi import APIRouter, HTTPException, Depends
from core.auth import get_api_key
from core import WebhookManager

router = APIRouter(tags=["notifications"], dependencies=[Depends(get_api_key)])

@router.get("/api/v1/notifications/webhook/status")
def get_webhook_status():
    """Returns the current webhook configuration status."""
    return {
        "enabled": settings.WEBHOOK_ENABLED,
        "url_configured": bool(settings.WEBHOOK_URL),
        "url_preview": f"{settings.WEBHOOK_URL[:10]}..." if settings.WEBHOOK_URL else None
    }

@router.post("/api/v1/notifications/webhook/test")
def test_webhook():
    """Sends a test PING event to the configured webhook."""
    if not settings.WEBHOOK_URL:
        raise HTTPException(status_code=400, detail="Webhook URL not configured.")
    
    result = WebhookManager.test_webhook()
    if result.get("status") == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("message", "Webhook test failed"))
