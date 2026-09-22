import os
import json
import datetime
from pathlib import Path
from typing import Any, Dict

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
AUDIT_LOG_FILE = LOG_DIR / "audit.jsonl"

def log_audit_event(category: str, action: str, details: Dict[str, Any], status: str = "success") -> None:
    """
    Logs a structured JSON event to the audit trail.
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        payload = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "category": category,
            "action": action,
            "status": status,
            "details": details
        }
        with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
    except Exception:
        # Prevent logging failures from affecting core app logic
        pass
