"""
WEBHOOK MANAGER
===============
Handles sending system events to generic HTTP webhooks.
"""

from core.settings import settings
import requests
import json
import logging
from core import TimeUtils

logger = logging.getLogger("horus.webhooks")

def send_webhook(event_type: str, data: dict):
    """
    Posts JSON data to the configured global webhook.
    """
    if not settings.WEBHOOK_ENABLED or not settings.WEBHOOK_URL:
        return {"status": "skipped", "message": "Webhook disabled or no URL"}
        
    payload = {
        "event": event_type.upper(),
        "timestamp": TimeUtils.now().isoformat(),
        "data": data
    }
    
    try:
        # Avoid circular imports by not using AuditEngine here
        # Log to DB if needed would be done by the caller
        response = requests.post(
            settings.WEBHOOK_URL, 
            json=payload, 
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return {"status": "success", "code": response.status_code}
    except Exception as e:
        logger.error(f"Webhook delivery failed for {event_type}: {e}")
        return {"status": "error", "message": str(e)}

def test_webhook():
    """Sends a ping event to verify the webhook URL."""
    return send_webhook("PING", {"message": "Horus Analytics Webhook Test Connection"})
