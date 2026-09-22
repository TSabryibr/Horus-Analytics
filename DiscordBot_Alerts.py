"""
DISCORD ALERTS MODULE
=====================
Handles sending notifications to Discord via webhooks.
"""

from core.settings import settings
import requests
import logging

logger = logging.getLogger("horus.discord")

def send_discord_webhook(content: str, embeds: list = None):
    """
    Sends a message to the configured Discord webhook.
    """
    if not settings.DISCORD_ENABLED or not settings.DISCORD_WEBHOOK_URL:
        return {"status": "skipped", "message": "Discord disabled or no URL"}
        
    payload = {
        "content": content,
        "username": "Horus Analytics",
        "avatar_url": "https://raw.githubusercontent.com/TSabryibr/Horus-Analytics-II/main/horus%201.PNG"
    }
    
    if embeds:
        payload["embeds"] = embeds
        
    try:
        response = requests.post(settings.DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Discord webhook error: {e}")
        return {"status": "error", "message": str(e)}

def send_signal_alert(ticker, signal_type, price, score, rationale):
    """
    Formated signal alert for Discord.
    """
    color = 0x00FF00 if signal_type == "BUY" else 0xFF0000
    embed = {
        "title": f"🚀 {signal_type} SIGNAL: {ticker}",
        "description": "\n".join(rationale),
        "color": color,
        "fields": [
            {"name": "Price", "value": f"{price:.4f}", "inline": True},
            {"name": "Alpha Score", "value": f"{score}/100", "inline": True}
        ],
        "footer": {"text": "Horus Intelligence Engine"}
    }
    return send_discord_webhook("", embeds=[embed])
