from core.signals.guard import get_guard_state, serialize_guard_state, set_guard_state, guard_context, serialize_run
from core.signals.models import DailyRunRequest, PublishSignalsRequest, RetryFailedDeliveriesRequest, RebuildOutcomesRequest, WalkforwardValidationRequest, GuardStateUpdateRequest, SignalDeskModeUpdateRequest, SignalDeskPromotionRequest, SignalDeskAutopilotRequest, SignalLifecycleOverrideRequest, SignalFollowUpActionRequest
from core.settings import settings
from core.auth import get_api_key
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, model_validator
from typing import Annotated, List, Optional, Callable
import datetime
import json
import os
import time
from core import DailyScanner
from core import TelegramBot_Alerts
from core import TimeUtils
from peewee import fn
from core.signals.desk import _recommendation_target2 as _signals_recommendation_target2
from core.signals.boundary import (
    bool_env as _signals_bool_env,
    error_context as _signals_error_context,
    float_env as _signals_float_env,
    freshness_context as _signals_freshness_context,
    get_publish_window_status as _signals_get_publish_window_status,
    int_env as _signals_int_env,
    noop_context as _signals_noop_context,
    parse_run_date as _signals_parse_run_date,
    validated_publish_channel as _signals_validated_publish_channel,
    validation_error as _signals_validation_error,
    window_context as _signals_window_context,
)
from core.signals.publishing import (
    build_delivery_message as _signals_build_delivery_message,
    increment_reason_count as _signals_increment_reason_count,
    publish_signal_run_logic as _signals_publish_signal_run_logic,
    retry_failed_deliveries_logic as _signals_retry_failed_deliveries_logic,
    serialize_delivery as _signals_serialize_delivery,
)
from core.signals.outcomes import (
    get_signal_audit_summary as _signals_get_signal_audit_summary,
    get_signal_calibration as _signals_get_signal_calibration,
    get_signal_outcomes as _signals_get_signal_outcomes,
    get_walkforward_validation_latest as _signals_get_walkforward_validation_latest,
    list_signal_audit_events as _signals_list_signal_audit_events,
    project_published_signal_lifecycle_outcome as _signals_project_published_signal_lifecycle_outcome,
    rebuild_signal_outcomes as _signals_rebuild_signal_outcomes,
    serialize_audit_event as _signals_serialize_audit_event,
    upsert_signal_outcome as _signals_upsert_signal_outcome,
)
from core.signals.workspace import (
    get_signals_sla as _signals_get_signals_sla,
    get_workspace_signal_performance as _signals_get_workspace_signal_performance,
    portfolio_window_metrics as _signals_portfolio_window_metrics,
)
from core.signals.followups import (
    get_signal_followup_summary as _signals_get_signal_followup_summary,
    process_signal_followups as _signals_process_signal_followups,
    requeue_signal_followup as _signals_requeue_signal_followup,
    send_signal_followup as _signals_send_signal_followup,
    suppress_signal_followup as _signals_suppress_signal_followup,
)
from database import (
    Signal,
    SignalRun,
    SignalRecommendation,
    SignalDelivery,
    SignalOutcome,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    PublishedSignalFollowUp,
    SignalValidationRun,
    SignalGuardState,
    SignalDeskState,
    SignalAuditEvent,
    Portfolio,
    Position,
    Trade,
    db,
)
from core.signals.lifecycle import override_published_signal_lifecycle as _signals_override_published_signal_lifecycle
from routes.data import evaluate_data_freshness_logic
from core.exclusions import get_excluded_tickers_upper, is_excluded_ticker, normalize_ticker
from core.signals.desk import (
    _SIGNAL_DESK_MODES,
    _SIGNAL_DESK_LANES,
    _parse_json_object,
    _default_signal_desk_policy,
    _default_signal_desk_queue,
    _get_signal_desk_state,
    _serialize_signal_desk_autopilot,
    _update_signal_desk_autopilot_state,
    _normalize_signal_lane,
    _get_signal_desk_queue,
    _save_signal_desk_queue,
    _desk_lane_key,
    _SIGNAL_SIDE_SOURCE_VALUES,
    _serialize_signal_desk_candidate,
    _dedupe_signal_desk_recommendations,
    _recommendation_source_module,
    _evaluate_signal_desk_autopilot,
    _serialize_manual_queue_candidate,
    _empty_signal_lane,
    _build_signal_desk_payload,
    _compute_tp2,
    _recommendation_target2
)


def _serialize_signal_followup(followup: PublishedSignalFollowUp) -> dict:
    try:
        details = json.loads(followup.details_json or "{}")
        if not isinstance(details, dict):
            details = {}
    except Exception:
        details = {}
    return {
        "id": followup.id,
        "lifecycle_id": followup.lifecycle.id if followup.lifecycle else None,
        "recommendation_id": followup.recommendation.id if followup.recommendation else None,
        "run_id": followup.run.id if followup.run else None,
        "delivery_id": followup.delivery.id if followup.delivery else None,
        "portfolio_id": followup.portfolio.id if followup.portfolio else None,
        "portfolio_name": followup.portfolio.name if followup.portfolio else None,
        "ticker": followup.ticker,
        "side": followup.side,
        "lane": followup.lane,
        "source_module": followup.source_module,
        "operating_mode": followup.operating_mode,
        "channel": followup.channel,
        "service_tier": followup.service_tier,
        "destination_type": followup.destination_type,
        "destination_id": followup.destination_id,
        "destination_name": followup.destination_name,
        "destination_chat_id": followup.destination_chat_id,
        "trigger_state": followup.trigger_state,
        "message_type": followup.message_type,
        "queue_state": followup.queue_state,
        "draft_message": followup.draft_message,
        "telegram_message_id": followup.telegram_message_id,
        "retry_count": int(followup.retry_count or 0),
        "last_attempted_at": followup.last_attempted_at.isoformat() if followup.last_attempted_at else None,
        "ready_at": followup.ready_at.isoformat() if followup.ready_at else None,
        "sent_at": followup.sent_at.isoformat() if followup.sent_at else None,
        "suppressed_at": followup.suppressed_at.isoformat() if followup.suppressed_at else None,
        "suppression_reason": followup.suppression_reason,
        "last_error": followup.last_error,
        "details": details,
        "created_at": followup.created_at.isoformat() if followup.created_at else None,
        "updated_at": followup.updated_at.isoformat() if followup.updated_at else None,
    }


def _published_signal_followup_summary() -> dict:
    return _signals_get_signal_followup_summary(now_fn=TimeUtils.now)
