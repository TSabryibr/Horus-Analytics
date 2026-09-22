import datetime
import json

from fastapi.testclient import TestClient

from api import app
from core.signals.followups import build_followup_draft_message, process_signal_followups, send_signal_followup
from database import (
    Portfolio,
    PublishedSignalFollowUp,
    PublishedSignalLifecycle,
    SignalDelivery,
    SignalRecommendation,
    SignalRun,
)


client = TestClient(app, raise_server_exceptions=False)


def _seed_followup(*, queue_state: str = "READY", trigger_state: str = "TP1_HIT") -> PublishedSignalFollowUp:
    run = SignalRun.create(
        status="COMPLETED",
        scan_type="DAILY",
        run_date=datetime.date(2026, 4, 22),
        started_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        completed_at=datetime.datetime(2026, 4, 22, 10, 5, 0),
    )
    portfolio = Portfolio.create(name=f"Followup {queue_state} {trigger_state}", type="USER")
    recommendation = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8.3,
        confidence=81.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER", "target_price_2": 115.0}),
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        status="SENT",
        provider_message_id="501",
        sent_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
    )
    lifecycle = PublishedSignalLifecycle.create(
        recommendation=recommendation,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker="COMI",
        side="BUY",
        lane="swing",
        source_module="SCANNER",
        operating_mode="AUTOPILOT",
        channel="TELEGRAM",
        published_message_id="501",
        state=trigger_state,
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        opened_at=datetime.datetime(2026, 4, 22, 10, 10, 0),
        tp1_hit_at=datetime.datetime(2026, 4, 22, 11, 0, 0) if trigger_state in {"TP1_HIT", "TP2_HIT"} else None,
        closed_at=datetime.datetime(2026, 4, 22, 12, 0, 0) if trigger_state in {"TP2_HIT", "STOP_LOSS_HIT"} else None,
        entry_price_planned=100.0,
        entry_price_filled=100.0,
        stop_loss_initial=95.0,
        stop_loss_active=100.0 if trigger_state == "TP1_HIT" else 95.0,
        target_price_1=110.0,
        target_price_2=115.0,
        close_price=115.0 if trigger_state == "TP2_HIT" else 95.0 if trigger_state == "STOP_LOSS_HIT" else None,
        close_reason=trigger_state,
        details_json=json.dumps({"confidence": 81.0}),
    )
    return PublishedSignalFollowUp.create(
        lifecycle=lifecycle,
        recommendation=recommendation,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker="COMI",
        side="BUY",
        lane="swing",
        source_module="SCANNER",
        operating_mode="AUTOPILOT",
        channel="TELEGRAM",
        trigger_state=trigger_state,
        message_type="CLOSE" if trigger_state in {"TP2_HIT", "STOP_LOSS_HIT"} else "UPDATE",
        queue_state=queue_state,
        draft_message=f"HORUS {'CLOSE' if trigger_state in {'TP2_HIT', 'STOP_LOSS_HIT'} else 'UPDATE'}\nTicker: COMI",
        ready_at=datetime.datetime(2026, 4, 22, 12, 1, 0) if queue_state == "READY" else None,
        details_json=json.dumps({"trigger_state": trigger_state}),
    )


def test_send_signal_followup_marks_job_sent_and_records_message_id():
    followup = _seed_followup(queue_state="READY", trigger_state="TP1_HIT")

    updated = send_signal_followup(
        followup,
        send_message_fn=lambda _message: {"ok": True, "result": {"message_id": 701}},
    )

    refreshed = PublishedSignalFollowUp.get_by_id(updated.id)
    assert refreshed.queue_state == "SENT"
    assert refreshed.telegram_message_id == "701"
    assert refreshed.sent_at is not None
    assert refreshed.last_error is None


def test_send_signal_followup_uses_frozen_destination_chat_id():
    followup = _seed_followup(queue_state="READY", trigger_state="TP1_HIT")
    followup.destination_type = "SUBSCRIBER"  # type: ignore[assignment]
    followup.destination_id = "client-77"  # type: ignore[assignment]
    followup.destination_name = "Type One Client"  # type: ignore[assignment]
    followup.destination_chat_id = "100200300"  # type: ignore[assignment]
    followup.save()

    sent = []
    updated = send_signal_followup(
        followup,
        send_message_fn=lambda message, **kwargs: sent.append((message, kwargs)) or {"ok": True, "result": {"message_id": 702}},
    )

    assert updated.queue_state == "SENT"
    assert sent[0][1]["chat_id"] == "100200300"


def test_followup_copy_matches_type_one_action_and_closure_rules():
    tp1 = _seed_followup(queue_state="READY", trigger_state="TP1_HIT").lifecycle
    tp2 = _seed_followup(queue_state="READY", trigger_state="TP2_HIT").lifecycle
    stopped = _seed_followup(queue_state="READY", trigger_state="STOP_LOSS_HIT").lifecycle
    expired = _seed_followup(queue_state="READY", trigger_state="EXPIRED").lifecycle
    pre_close_cancelled = _seed_followup(queue_state="READY", trigger_state="CANCELLED").lifecycle
    pre_close_cancelled.close_reason = "PRE_CLOSE_NOT_CONFIRMED"  # type: ignore[attr-defined]
    pre_close_cancelled.save()

    assert "Move stop loss to breakeven" in build_followup_draft_message(tp1, trigger_state="TP1_HIT")
    assert "Keep Target 2 active" in build_followup_draft_message(tp1, trigger_state="TP1_HIT")
    assert "Signal fully closed. No further action." in build_followup_draft_message(tp2, trigger_state="TP2_HIT")
    assert "Signal fully closed. No further action." in build_followup_draft_message(stopped, trigger_state="STOP_LOSS_HIT")
    assert "Signal expired and is closed. No further action." in build_followup_draft_message(expired, trigger_state="EXPIRED")
    assert "Pre-close signal not confirmed" in build_followup_draft_message(pre_close_cancelled, trigger_state="CANCELLED")


def test_send_signal_followup_marks_job_failed_and_increments_retry_count():
    followup = _seed_followup(queue_state="READY", trigger_state="STOP_LOSS_HIT")

    updated = send_signal_followup(
        followup,
        send_message_fn=lambda _message: {"ok": False, "description": "telegram down"},
    )

    refreshed = PublishedSignalFollowUp.get_by_id(updated.id)
    assert refreshed.queue_state == "FAILED"
    assert refreshed.retry_count == 1
    assert refreshed.last_error == "telegram down"


def test_process_signal_followups_sends_only_ready_jobs():
    ready = _seed_followup(queue_state="READY", trigger_state="TP2_HIT")
    _seed_followup(queue_state="PENDING", trigger_state="TP1_HIT")

    result = process_signal_followups(
        limit=10,
        send_message_fn=lambda _message: {"ok": True, "result": {"message_id": 801}},
    )

    assert result["summary"] == {"processed": 1, "sent": 1, "failed": 0}
    assert PublishedSignalFollowUp.get_by_id(ready.id).queue_state == "SENT"
    assert PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.queue_state == "PENDING").count() == 1


def test_followup_action_endpoints_handle_send_retry_suppress_and_resend(monkeypatch):
    followup = _seed_followup(queue_state="READY", trigger_state="TP1_HIT")
    monkeypatch.setattr(
        "routes.signals.TelegramBot_Alerts.send_message",
        lambda _message: {"ok": True, "result": {"message_id": 901}},
    )

    send_response = client.post(
        f"/api/v1/signals/followups/{followup.id}/action",
        json={"action": "SEND_NOW"},
    )
    assert send_response.status_code == 200, send_response.text
    assert send_response.json()["followup"]["queue_state"] == "SENT"

    resend_response = client.post(
        f"/api/v1/signals/followups/{followup.id}/action",
        json={"action": "RESEND"},
    )
    assert resend_response.status_code == 200, resend_response.text
    assert resend_response.json()["followup"]["queue_state"] == "READY"

    suppress_response = client.post(
        f"/api/v1/signals/followups/{followup.id}/action",
        json={"action": "SUPPRESS", "reason": "hold update"},
    )
    assert suppress_response.status_code == 200, suppress_response.text
    assert suppress_response.json()["followup"]["queue_state"] == "SUPPRESSED"

    retry_response = client.post(
        f"/api/v1/signals/followups/{followup.id}/action",
        json={"action": "RETRY"},
    )
    assert retry_response.status_code == 200, retry_response.text
    assert retry_response.json()["followup"]["queue_state"] == "SENT"


def test_followup_process_endpoint_returns_batch_summary(monkeypatch):
    _seed_followup(queue_state="READY", trigger_state="TP2_HIT")
    monkeypatch.setattr(
        "routes.signals.TelegramBot_Alerts.send_message",
        lambda _message: {"ok": True, "result": {"message_id": 999}},
    )

    response = client.post("/api/v1/signals/followups/process", json={"limit": 5})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["summary"]["processed"] == 1
    assert body["summary"]["sent"] == 1
    assert body["summary_snapshot"]["sent_count"] == 1


def test_scheduled_followup_processing_runs_successfully(monkeypatch):
    from core.scheduling import scheduled_followup_processing
    monkeypatch.setattr("core.settings.settings.is_market_open", lambda: True)
    _seed_followup(queue_state="READY", trigger_state="TP2_HIT")
    
    sent_messages = []
    monkeypatch.setattr(
        "core.signals.followups.TelegramBot_Alerts.send_message",
        lambda text, **kwargs: (sent_messages.append(text) or {"ok": True, "result": {"message_id": 12345}})
    )
    
    scheduled_followup_processing()
    assert len(sent_messages) == 1
