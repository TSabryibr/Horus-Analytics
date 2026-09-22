import datetime
import json

from fastapi.testclient import TestClient

from api import app
from core.signals.followups import create_lifecycle_followup_job
from core.signals.lifecycle import reconcile_pre_close_previews
from database import (
    HorusExecution,
    Portfolio,
    PublishedSignalFollowUp,
    PublishedSignalLifecycle,
    SignalExecutionAttribution,
    SignalDelivery,
    SignalRecommendation,
    SignalRun,
)
from core.signals.runs import set_guard_state


client = TestClient(app, raise_server_exceptions=False)


def _seed_completed_run(scan_type: str = "DAILY") -> SignalRun:
    return SignalRun.create(
        status="COMPLETED",
        scan_type=scan_type,
        run_date=datetime.date(2026, 4, 22),
        started_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        completed_at=datetime.datetime(2026, 4, 22, 10, 5, 0),
    )


def _seed_lifecycle(*, state: str = "AMBIGUOUS", operating_mode: str = "MANUAL") -> PublishedSignalLifecycle:
    run = _seed_completed_run(scan_type="DAILY")
    portfolio = Portfolio.create(name=f"FollowUp {state} {operating_mode}", type="USER")
    recommendation = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8.7,
        confidence=83.0,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER", "target_price_2": 115.0}),
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="SUBSCRIBER",
        destination_id="client-77",
        destination_name="Type One Client",
        destination_chat_id="100200300",
        status="SENT",
        provider_message_id="88",
        sent_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
    )
    return PublishedSignalLifecycle.create(
        recommendation=recommendation,
        run=run,
        delivery=delivery,
        portfolio=portfolio,
        ticker="COMI",
        side="BUY",
        lane="swing",
        source_module="SCANNER",
        operating_mode=operating_mode,
        channel="TELEGRAM",
        published_message_id="88",
        state=state,
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 10, 0, 0),
        opened_at=datetime.datetime(2026, 4, 22, 10, 5, 0),
        entry_price_planned=100.0,
        entry_price_filled=100.0 if state != "PUBLISHED" else None,
        stop_loss_initial=95.0,
        stop_loss_active=95.0,
        target_price_1=110.0,
        target_price_2=115.0,
        details_json=json.dumps({"confidence": 83.0}),
    )


def test_publish_signal_run_does_not_create_followup_for_published_state(monkeypatch):
    monkeypatch.setattr(
        "core.signals.publishing.TelegramBot_Alerts.send_message",
        lambda _message, **kwargs: {"ok": True, "result": {"message_id": 77}},
    )
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    run = _seed_completed_run(scan_type="DAILY")
    portfolio = Portfolio.create(name="No FollowUp Yet", type="USER")
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
    assert PublishedSignalFollowUp.select().count() == 0


def test_lifecycle_override_creates_followups_once_with_mode_aware_queue_state():
    lifecycle = _seed_lifecycle(state="AMBIGUOUS", operating_mode="AI_ASSIST")

    tp1_response = client.post(
        f"/api/v1/signals/lifecycle/{lifecycle.id}/override",
        json={"action": "RECLASSIFY", "target_state": "TP1_HIT", "notes": "resolved ambiguity"},
    )
    assert tp1_response.status_code == 200, tp1_response.text

    followup = PublishedSignalFollowUp.get(PublishedSignalFollowUp.lifecycle == lifecycle)
    assert followup.trigger_state == "TP1_HIT"
    assert followup.message_type == "UPDATE"
    assert followup.queue_state == "READY"
    assert followup.service_tier == "SIGNALS_ONLY"
    assert followup.destination_type == "SUBSCRIBER"
    assert followup.destination_id == "client-77"
    assert followup.destination_name == "Type One Client"
    assert followup.destination_chat_id == "100200300"
    assert "HORUS UPDATE" in str(followup.draft_message or "")
    assert PublishedSignalFollowUp.select().count() == 1

    tp2_response = client.post(
        f"/api/v1/signals/lifecycle/{lifecycle.id}/override",
        json={"action": "MARK_TP2", "close_price": 115.0, "notes": "full target reached"},
    )
    assert tp2_response.status_code == 200, tp2_response.text

    followups = list(
        PublishedSignalFollowUp.select()
        .where(PublishedSignalFollowUp.lifecycle == lifecycle)
        .order_by(PublishedSignalFollowUp.id.asc())
    )
    assert len(followups) == 2
    assert followups[1].trigger_state == "TP2_HIT"
    assert followups[1].message_type == "CLOSE"
    assert followups[1].queue_state == "READY"

    tp2_repeat = client.post(
        f"/api/v1/signals/lifecycle/{lifecycle.id}/override",
        json={"action": "MARK_TP2", "close_price": 115.0, "notes": "repeat close"},
    )
    assert tp2_repeat.status_code == 200, tp2_repeat.text
    assert PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.lifecycle == lifecycle).count() == 2


def test_reconcile_pre_close_previews_cancels_unconfirmed_lifecycle_and_pending_entry():
    run_date = datetime.date(2026, 4, 22)
    run = SignalRun.create(
        status="COMPLETED",
        scan_type="PRE_CLOSE",
        run_date=run_date,
        started_at=datetime.datetime(2026, 4, 22, 14, 10, 0),
        completed_at=datetime.datetime(2026, 4, 22, 14, 11, 0),
    )
    portfolio = Portfolio.get(Portfolio.name == "Swing Signals")
    recommendation = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8.5,
        confidence=84.0,
        state="ACTIVE",
        rationale_json=json.dumps(
            {
                "source_module": "SCANNER",
                "target_price_2": 115.0,
                "preview_mode": "DAILY_RULES_LIVE_CLOSE",
            }
        ),
    )
    delivery = SignalDelivery.create(
        run=run,
        portfolio=None,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="SUBSCRIBER",
        destination_id="client-77",
        destination_name="Type One Client",
        destination_chat_id="100200300",
        status="SENT",
        provider_message_id="88",
        sent_at=datetime.datetime(2026, 4, 22, 14, 11, 0),
    )
    lifecycle = PublishedSignalLifecycle.create(
        recommendation=recommendation,
        run=run,
        delivery=delivery,
        portfolio=None,
        ticker="COMI",
        side="BUY",
        lane="swing",
        source_module="SCANNER",
        operating_mode="AUTOPILOT",
        channel="TELEGRAM",
        published_message_id="88",
        state="PUBLISHED",
        resolution_source="AUTO",
        published_at=datetime.datetime(2026, 4, 22, 14, 11, 0),
        entry_price_planned=100.0,
        stop_loss_initial=95.0,
        stop_loss_active=95.0,
        target_price_1=110.0,
        target_price_2=115.0,
        details_json=json.dumps({"confidence": 84.0}),
    )
    execution = HorusExecution.create(
        portfolio=portfolio,
        run=run,
        recommendation=recommendation,
        ticker="COMI",
        state="PENDING_OPEN",
        trigger_source="PRE_CLOSE",
        planned_entry_price=100.0,
        active_stop_loss=95.0,
        active_target_price=110.0,
        details_json=json.dumps({"trigger_source": "PRE_CLOSE"}),
    )
    SignalExecutionAttribution.create(
        execution=execution,
        execution_portfolio=portfolio,
        recommendation=recommendation,
        run=run,
        lane="SWING",
        scan_type="PRE_CLOSE",
        signal_side="BUY",
        signal_state="PENDING_OPEN",
        details_json=json.dumps({"trigger_source": "PRE_CLOSE"}),
    )

    result = reconcile_pre_close_previews(
        run_date=run_date,
        confirmed_tickers={"FWRY"},
        now_fn=lambda: datetime.datetime(2026, 4, 22, 15, 0, 0),
    )

    assert result["summary"]["cancelled_lifecycles"] == 1
    assert result["summary"]["cancelled_pending_entries"] == 1
    refreshed = PublishedSignalLifecycle.get_by_id(lifecycle.id)
    assert refreshed.state == "CANCELLED"
    assert refreshed.close_reason == "PRE_CLOSE_NOT_CONFIRMED"
    followup = PublishedSignalFollowUp.get(PublishedSignalFollowUp.lifecycle == lifecycle)
    assert followup.queue_state == "READY"
    assert followup.trigger_state == "CANCELLED"
    assert "Pre-close signal not confirmed" in followup.draft_message
    assert "Final daily scan did not confirm" in followup.draft_message
    assert HorusExecution.get_by_id(execution.id).state == "SKIPPED"
    assert SignalExecutionAttribution.get(SignalExecutionAttribution.execution == execution.id).signal_state == "SKIPPED"


def test_create_lifecycle_followup_job_reuses_legacy_followup_without_destination_id():
    lifecycle = _seed_lifecycle(state="TP1_HIT", operating_mode="AI_ASSIST")
    legacy = PublishedSignalFollowUp.create(
        lifecycle=lifecycle,
        recommendation=lifecycle.recommendation,
        run=lifecycle.run,
        delivery=lifecycle.delivery,
        portfolio=lifecycle.portfolio,
        ticker=lifecycle.ticker,
        side=lifecycle.side,
        lane=lifecycle.lane,
        source_module=lifecycle.source_module,
        operating_mode=lifecycle.operating_mode,
        channel=lifecycle.channel,
        trigger_state="TP1_HIT",
        message_type="UPDATE",
        queue_state="READY",
        draft_message="Legacy follow-up",
        details_json=json.dumps({"trigger_state": "TP1_HIT"}),
    )

    followup = create_lifecycle_followup_job(lifecycle)

    assert followup.id == legacy.id
    assert PublishedSignalFollowUp.select().where(PublishedSignalFollowUp.lifecycle == lifecycle).count() == 1
    refreshed = PublishedSignalFollowUp.get_by_id(legacy.id)
    assert refreshed.destination_type == "SUBSCRIBER"
    assert refreshed.destination_id == "client-77"
    assert refreshed.destination_name == "Type One Client"
    assert refreshed.destination_chat_id == "100200300"


def test_followup_endpoints_and_system_boot_summary_expose_queue_state():
    lifecycle = _seed_lifecycle(state="TP1_HIT", operating_mode="MANUAL")

    response = client.post(
        f"/api/v1/signals/lifecycle/{lifecycle.id}/override",
        json={"action": "MARK_STOP_LOSS", "close_price": 100.0, "notes": "breakeven stop hit"},
    )
    assert response.status_code == 200, response.text

    summary_response = client.get("/api/v1/signals/followups/summary")
    assert summary_response.status_code == 200
    summary_body = summary_response.json()
    assert summary_body["total"] == 1
    assert summary_body["pending_count"] == 1
    assert summary_body["destination_counts"] == {"SUBSCRIBER": 1}
    assert summary_body["service_tier_counts"] == {"SIGNALS_ONLY": 1}

    list_response = client.get("/api/v1/signals/followups", params={"queue_state": "PENDING"})
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["count"] == 1
    assert list_body["followups"][0]["trigger_state"] == "STOP_LOSS_HIT"
    assert list_body["followups"][0]["message_type"] == "CLOSE"
    assert "HORUS CLOSE" in list_body["followups"][0]["draft_message"]

    detail_response = client.get(f"/api/v1/signals/followups/{list_body['followups'][0]['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["followup"]["queue_state"] == "PENDING"

    boot_response = client.get("/api/v1/system/boot-status")
    assert boot_response.status_code == 200
    boot_body = boot_response.json()
    assert "signal_followups" in boot_body
    assert boot_body["signal_followups"]["total"] == 1
