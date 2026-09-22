import json
from database import Portfolio, SignalAuditEvent
from database import SignalRun
from typing import Optional, List, Dict, Any
from core.signals.models import DailyRunRequest, PublishSignalsRequest, RetryFailedDeliveriesRequest, RebuildOutcomesRequest, WalkforwardValidationRequest, GuardStateUpdateRequest, SignalDeskModeUpdateRequest, SignalDeskPromotionRequest, SignalDeskAutopilotRequest, SignalLifecycleOverrideRequest, SignalFollowUpActionRequest


def _emit_audit_event(
    event_type: str,
    severity: str = "INFO",
    actor_type: str = "SYSTEM",
    actor_id: Optional[str] = None,
    run: Optional[SignalRun] = None,
    portfolio: Optional[Portfolio] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    message: Optional[str] = None,
    details: Optional[dict] = None,
):
    """
    Best-effort append-only compliance log.
    Logging failures must never break the primary flow.
    """
    try:
        SignalAuditEvent.create(
            event_type=event_type.upper().strip(),
            severity=severity.upper().strip(),
            actor_type=actor_type.upper().strip(),
            actor_id=actor_id,
            run=run,
            portfolio=portfolio,
            entity_type=entity_type,
            entity_id=entity_id,
            message=message,
            details_json=json.dumps(details, default=str) if details is not None else None,
        )
    except Exception:
        pass
