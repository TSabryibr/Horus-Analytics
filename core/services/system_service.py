"""
HORUS ANALYTICS - SYSTEM DOMAIN SERVICE
=======================================
Clean service layer encapsulating system health diagnostics, boot telemetry,
market holidays, and audit trail queries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from core import TimeUtils
from core.audit import get_recent_logs, log_event
from core.settings import settings

logger = logging.getLogger("horus.services.system")


class SystemService:
    """Institutional system and telemetry domain service."""

    def get_health_status(self) -> Dict[str, Any]:
        """Calculates fast container readiness/liveness status."""
        import api
        pipeline_state = api.refresh_pipeline_state()
        return {
            "status": "ok" if pipeline_state.get("bootstrap_complete", False) else "starting",
            "pipeline_state": str(pipeline_state.get("pipeline_state", "UNKNOWN")).upper(),
            "bootstrap_complete": bool(pipeline_state.get("bootstrap_complete", False)),
            "timestamp": TimeUtils.now().isoformat(),
        }

    def get_audit_trail(self, limit: int = 100, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves immutable audit logs from database."""
        return get_recent_logs(limit=limit, category=category)

    def record_audit_event(
        self,
        category: str,
        event: str,
        message: str,
        level: str = "INFO",
        ticker: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Records an institutional audit event."""
        log_event(
            category=category,
            event=event,
            message=message,
            level=level,
            ticker=ticker,
            meta=meta,
        )


# Singleton service instance
system_service = SystemService()
