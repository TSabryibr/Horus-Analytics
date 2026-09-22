import os
from pathlib import Path

# Use a state file in the workspace directory
STATE_FILE = Path(__file__).resolve().parents[2] / ".tmp" / "kill_switch.state"

def set_kill_switch(active: bool) -> None:
    """Sets the global emergency kill switch state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text("true" if active else "false", encoding="utf-8")

def is_kill_switch_active() -> bool:
    """Checks if the global emergency kill switch is active."""
    if not STATE_FILE.exists():
        return False
    try:
        content = STATE_FILE.read_text(encoding="utf-8").strip().lower()
        return content == "true"
    except Exception:
        # Fail closed/safe in case of read errors
        return True
