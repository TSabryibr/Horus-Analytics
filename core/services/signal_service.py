"""
HORUS ANALYTICS - SIGNAL DOMAIN SERVICE
=======================================
Clean service layer encapsulating signal generation, recommendation tracking,
desk summaries, publishing, and execution attributions.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from core.signals.desk import (
    _build_signal_desk_payload,
    _get_signal_desk_state,
)
from core.signals.publishing import (
    publish_signal_run_logic,
    retry_failed_deliveries_logic,
)
from database import SignalRun

logger = logging.getLogger("horus.services.signals")


class SignalService:
    """Institutional signal domain service."""

    def get_desk_payload(self) -> Dict[str, Any]:
        """Builds full signal desk telemetry payload."""
        return _build_signal_desk_payload()

    def get_latest_run(self) -> Optional[Dict[str, Any]]:
        """Retrieves metadata of the most recent pipeline scan run."""
        latest = SignalRun.select().order_by(SignalRun.run_date.desc()).first()
        if not latest:
            return None
        return {
            "id": latest.id,
            "run_date": latest.run_date.isoformat() if latest.run_date else None,
            "scan_type": getattr(latest, "scan_type", "DAILY"),
            "status": getattr(latest, "status", "COMPLETED"),
        }

    def get_run_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves historical signal run executions."""
        runs = SignalRun.select().order_by(SignalRun.run_date.desc()).limit(limit)
        return [
            {
                "id": r.id,
                "run_date": r.run_date.isoformat() if r.run_date else None,
                "scan_type": getattr(r, "scan_type", "DAILY"),
                "status": getattr(r, "status", "COMPLETED"),
            }
            for r in runs
        ]

    def publish_signals(self, req: Any) -> Dict[str, Any]:
        """Dispatches verified signals to subscriber endpoints."""
        return publish_signal_run_logic(req)

    def retry_deliveries(self, req: Any) -> Dict[str, Any]:
        """Retries failed delivery attempts."""
        return retry_failed_deliveries_logic(req)


# Singleton service instance
signal_service = SignalService()
