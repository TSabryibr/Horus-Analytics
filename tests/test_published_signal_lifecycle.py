from core.settings import settings
import datetime
import json

from fastapi.testclient import TestClient

from api import app
from database import (
    Portfolio,
    PublishedSignalLifecycle,
    PublishedSignalLifecycleEvent,
    SignalDelivery,
    SignalOutcome,
    SignalRecommendation,
    SignalRun,
)
from core.signals.runs import set_guard_state


client = TestClient(app, raise_server_exceptions=False)


def _configure_test_telegram(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "test-token")
    monkeypatch.setattr(settings, "CHAT_ID", "-100123")
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "none", raising=False)


def _seed_completed_run(scan_type: str = "DAILY") -> SignalRun:
    return SignalRun.create(
        status="COMPLETED",
        scan_type=scan_type,
        run_date=datetime.date(2026, 4, 22),
        started_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        completed_at=datetime.datetime(2026, 4, 22, 10, 5, 0),
    )


def test_publish_signal_run_creates_published_signal_lifecycles(monkeypatch):
    _configure_test_telegram(monkeypatch)
    monkeypatch.setattr(
        "core.signals.publishing.TelegramBot_Alerts.send_message",
        lambda _message, **_kwargs: {"ok": True, "result": {"message_id": 77}},
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    run = _seed_completed_run(scan_type="DAILY")
    portfolio = Portfolio.create(name="Lifecycle Portfolio", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85.0,
        stop_loss=80.0,
        target_price=95.0,
        score=8.0,
        confidence=80.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER", "target_price_2": 102.0}),
    )
    SignalRecommendation.create(
        run=run,
        ticker="FWRY",
        side="BUY",
        entry_price=20.0,
        stop_loss=18.0,
        target_price=23.0,
        score=7.0,
        confidence=70.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "ORACLE"}),
    )

    response = client.post(
        "/api/v1/signals/publish",
        json={
            "run_id": run.id,
            "portfolio_ids": [portfolio.id],
            "channel": "TELEGRAM",
            "dry_run": False,
            "max_retries": 0,
            "backoff_ms": 0,
            "enforce_window": False,
            "ignore_guard": False,
        },
    )

    assert response.status_code == 200, response.text
    assert PublishedSignalLifecycle.select().count() == 2

    lifecycle = PublishedSignalLifecycle.get(PublishedSignalLifecycle.ticker == "COMI")
    delivery = SignalDelivery.get(SignalDelivery.run == run, SignalDelivery.portfolio == portfolio)
    assert lifecycle.delivery_id == delivery.id
    assert lifecycle.state == "PUBLISHED"
    assert lifecycle.lane == "swing"
    assert lifecycle.source_module == "SCANNER"
    assert lifecycle.entry_price_planned == 85.0
    assert lifecycle.stop_loss_initial == 80.0
    assert lifecycle.stop_loss_active == 80.0
    assert lifecycle.target_price_1 == 95.0
    assert lifecycle.target_price_2 == 102.0
    assert lifecycle.published_message_id == delivery.provider_message_id

    event = PublishedSignalLifecycleEvent.get(PublishedSignalLifecycleEvent.lifecycle == lifecycle)
    assert event.event_type == "PUBLISHED"
    assert event.to_state == "PUBLISHED"


def test_publish_signal_run_upserts_lifecycle_without_duplication(monkeypatch):
    _configure_test_telegram(monkeypatch)
    monkeypatch.setattr(
        "core.signals.publishing.TelegramBot_Alerts.send_message",
        lambda _message, **_kwargs: {"ok": True, "result": {"message_id": 81}},
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    run = _seed_completed_run(scan_type="INTRADAY")
    portfolio = Portfolio.create(name="Idempotent Lifecycle Portfolio", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85.0,
        stop_loss=80.0,
        target_price=95.0,
        score=8.0,
        confidence=80.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )

    payload = {
        "run_id": run.id,
        "portfolio_ids": [portfolio.id],
        "channel": "TELEGRAM",
        "dry_run": False,
        "max_retries": 0,
        "backoff_ms": 0,
        "enforce_window": False,
        "ignore_guard": False,
    }
    first = client.post("/api/v1/signals/publish", json=payload)
    second = client.post("/api/v1/signals/publish", json=payload)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert PublishedSignalLifecycle.select().count() == 1
    assert PublishedSignalLifecycleEvent.select().count() == 1


def test_lifecycle_summary_and_detail_endpoints_expose_records():
    run = _seed_completed_run(scan_type="DAILY")
    portfolio = Portfolio.create(name="Lifecycle Summary Portfolio", type="USER")
    recommendation = SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=30.0,
        stop_loss=28.0,
        target_price=35.0,
        score=9.0,
        confidence=90.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "ANALYTICS"}),
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        status="SENT",
        provider_message_id="42",
        sent_at=datetime.datetime(2026, 4, 22, 11, 0, 0),
    )
    lifecycle = PublishedSignalLifecycle.create(
        recommendation=recommendation,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker="HRHO",
        side="BUY",
        lane="position",
        source_module="ANALYTICS",
        operating_mode="AI_ASSIST",
        channel="TELEGRAM",
        published_message_id="42",
        state="PUBLISHED",
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 11, 0, 0),
        expires_at=datetime.datetime(2026, 5, 2, 11, 0, 0),
        entry_price_planned=30.0,
        stop_loss_initial=28.0,
        stop_loss_active=28.0,
        target_price_1=35.0,
        target_price_2=36.4,
        details_json=json.dumps({"confidence": 90.0}),
    )
    PublishedSignalLifecycleEvent.create(
        lifecycle=lifecycle,
        event_type="PUBLISHED",
        from_state=None,
        to_state="PUBLISHED",
        event_source="AUTO",
        actor_type="SYSTEM",
        event_time=datetime.datetime(2026, 4, 22, 11, 0, 0),
        price_context_json=json.dumps({"entry_price_planned": 30.0}),
        notes="Created from publish",
    )

    summary_response = client.get("/api/v1/signals/lifecycle/summary")
    assert summary_response.status_code == 200
    summary_body = summary_response.json()
    assert summary_body["total"] == 1
    assert summary_body["counts_by_state"]["PUBLISHED"] == 1
    assert summary_body["counts_by_lane"]["position"] == 1

    list_response = client.get("/api/v1/signals/lifecycle", params={"ticker": "HRHO"})
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["count"] == 1
    assert list_body["lifecycles"][0]["ticker"] == "HRHO"
    assert list_body["lifecycles"][0]["source_module"] == "ANALYTICS"

    detail_response = client.get(f"/api/v1/signals/lifecycle/{lifecycle.id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()["lifecycle"]
    assert detail_body["id"] == lifecycle.id
    assert detail_body["events"][0]["event_type"] == "PUBLISHED"


def test_system_boot_status_includes_signal_lifecycle_summary():
    response = client.get("/api/v1/system/boot-status")
    assert response.status_code == 200
    body = response.json()
    assert "signal_lifecycle" in body
    assert "total" in body["signal_lifecycle"]


def test_lifecycle_override_endpoint_writes_admin_event_and_projects_outcome():
    run = _seed_completed_run(scan_type="DAILY")
    portfolio = Portfolio.create(name="Lifecycle Override Portfolio", type="USER")
    recommendation = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=9.0,
        confidence=88.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER", "target_price_2": 115.0}),
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        status="SENT",
        provider_message_id="55",
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
        operating_mode="MANUAL",
        channel="TELEGRAM",
        published_message_id="55",
        state="AMBIGUOUS",
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        opened_at=datetime.datetime(2026, 4, 22, 10, 5, 0),
        entry_price_planned=100.0,
        entry_price_filled=100.0,
        stop_loss_initial=95.0,
        stop_loss_active=95.0,
        target_price_1=110.0,
        target_price_2=115.0,
        details_json=json.dumps({"confidence": 88.0}),
    )

    tp1_response = client.post(
        f"/api/v1/signals/lifecycle/{lifecycle.id}/override",
        json={"action": "RECLASSIFY", "target_state": "TP1_HIT", "notes": "resolved ambiguity"},
    )
    assert tp1_response.status_code == 200, tp1_response.text
    tp1_body = tp1_response.json()["lifecycle"]
    assert tp1_body["state"] == "TP1_HIT"
    assert tp1_body["stop_loss_active"] == 100.0

    tp2_response = client.post(
        f"/api/v1/signals/lifecycle/{lifecycle.id}/override",
        json={"action": "MARK_TP2", "close_price": 115.0, "notes": "full target reached"},
    )
    assert tp2_response.status_code == 200, tp2_response.text
    tp2_body = tp2_response.json()["lifecycle"]
    assert tp2_body["state"] == "TP2_HIT"

    outcome = SignalOutcome.get(SignalOutcome.recommendation == recommendation)
    assert outcome.outcome_status == "CLOSED"
    assert round(float(outcome.pnl_pct), 4) == 15.0

    events_response = client.get(
        "/api/v1/signals/lifecycle-event-log",
        params={"lifecycle_id": lifecycle.id, "actor_type": "ADMIN"},
    )
    assert events_response.status_code == 200
    events = events_response.json()["events"]
    assert len(events) >= 2
    assert any(event["event_type"] == "ADMIN_RECLASSIFY" for event in events)
    assert any(event["event_type"] == "ADMIN_MARK_TP2" for event in events)
