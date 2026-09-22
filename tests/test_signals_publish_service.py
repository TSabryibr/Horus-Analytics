from core.settings import settings
import datetime
import json
from types import SimpleNamespace

from database import Client, Portfolio, SignalDelivery, SignalRecommendation, SignalRun
from core import TimeUtils
from core.signals.publishing import (
    build_delivery_message,
    publish_signal_run_logic,
    retry_failed_deliveries_logic,
    serialize_delivery,
)
from core.signals.runs import set_guard_state


def test_serialize_delivery_round_trip():
    run = SignalRun.create(status="COMPLETED")
    portfolio = Portfolio.create(name="Serialize Portfolio", type="USER")
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="SUBSCRIBER",
        destination_id="42",
        destination_name="Type One Client",
        destination_chat_id="100200300",
        status="FAILED",
        attempts=2,
        provider_message_id="abc123",
        last_error="transport down",
        sent_at=datetime.datetime(2026, 3, 17, 12, 30, 0),
    )

    payload = serialize_delivery(delivery)

    assert payload["run_id"] == run.id
    assert payload["portfolio_id"] == portfolio.id
    assert payload["portfolio_name"] == "Serialize Portfolio"
    assert payload["service_tier"] == "SIGNALS_ONLY"
    assert payload["destination_type"] == "SUBSCRIBER"
    assert payload["destination_id"] == "42"
    assert payload["destination_name"] == "Type One Client"
    assert payload["destination_chat_id"] == "100200300"
    assert payload["attempts"] == 2
    assert payload["last_error"] == "transport down"


def test_build_delivery_message_uses_portfolio_name_and_empty_fallback():
    run = SignalRun.create(run_date=TimeUtils.today())
    portfolio = Portfolio.create(name="Workspace One", type="USER")

    message = build_delivery_message(
        run,
        [],
        portfolio,
        recommendation_target2_fn=lambda _rec: 0.0,
    )

    assert "Workspace: Workspace One" in message
    assert "No active recommendations" in message


def test_publish_signal_run_logic_marks_dry_run_delivery(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    portfolio = Portfolio.create(name="Dry Run Portfolio", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=80,
        state="ACTIVE",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[portfolio.id],
        channel="TELEGRAM",
        dry_run=True,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        build_delivery_message_fn=lambda *_args, **_kwargs: "message",
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda _message, **_kwargs: {"ok": True},
    )

    delivery = SignalDelivery.get(SignalDelivery.run == run, SignalDelivery.portfolio == portfolio)
    assert result["status"] == "completed"
    assert result["summary"]["dry_run"] == 1
    assert delivery.status == "DRY_RUN"


def test_publish_signal_run_logic_aggregates_failure_reasons(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    portfolio = Portfolio.create(name="Failure Portfolio", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=80,
        state="ACTIVE",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[portfolio.id],
        channel="TELEGRAM",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        build_delivery_message_fn=lambda *_args, **_kwargs: "message",
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda _message, **_kwargs: {"ok": False, "description": "transport down"},
    )

    delivery = SignalDelivery.get(SignalDelivery.run == run, SignalDelivery.portfolio == portfolio)
    assert result["summary"]["failed"] == 1
    assert result["summary"]["failure_reasons"]["transport down"] == 1
    assert delivery.status == "FAILED"
    assert delivery.last_error == "transport down"


def test_publish_signal_run_logic_excludes_blocked_and_downgrades_watch_only(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    portfolio = Portfolio.create(name="Enforcement Portfolio", type="USER")

    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=80,
        state="ACTIVE",
        rationale_json=json.dumps({
            "enforcement_state": "ALLOW",
            "enforcement_reason": "not_enforced",
            "enforcement_profile": "EGX30_GUARDED",
            "trap_risk_band": "MEDIUM",
            "whale_alignment": "SUPPORTIVE",
        }),
    )
    SignalRecommendation.create(
        run=run,
        ticker="FWRY",
        side="BUY",
        entry_price=20,
        stop_loss=18,
        target_price=23,
        score=7,
        confidence=70,
        state="ACTIVE",
        rationale_json=json.dumps({
            "enforcement_state": "WATCH_ONLY",
            "enforcement_reason": "distribution_conflict",
            "enforcement_profile": "EGX70_HARDENED",
            "trap_risk_band": "MEDIUM",
            "whale_alignment": "CONFLICT",
        }),
    )
    SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=10,
        stop_loss=8.5,
        target_price=11.5,
        score=6,
        confidence=60,
        state="ACTIVE",
        rationale_json=json.dumps({
            "enforcement_state": "BLOCK_EXECUTION",
            "enforcement_reason": "severe_trap_risk",
            "enforcement_profile": "EGX70_HARDENED",
            "trap_risk_band": "SEVERE",
            "whale_alignment": "NEUTRAL",
        }),
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[portfolio.id],
        channel="TELEGRAM",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    sent_messages = []
    audit_events = []
    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: audit_events.append(kwargs),
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda message, **kwargs: sent_messages.append(message) or {"ok": True, "result": {"message_id": 7}},
    )

    assert result["summary"]["sent"] == 1
    assert result["summary"]["enforcement"] == {
        "actionable_count": 1,
        "watch_only_count": 1,
        "blocked_count": 1,
        "counts_by_reason": {
            "distribution_conflict": 1,
            "severe_trap_risk": 1,
        },
        "watch_only_tickers": ["FWRY"],
        "blocked_tickers": ["HRHO"],
    }
    assert result["summary"]["calibration"]["rollout_mode"] == "compare_only"
    assert result["summary"]["calibration"]["market_segments"]["EGX30"]["active_enforcement_profile"] == "EGX30_GUARDED"
    assert result["summary"]["calibration"]["market_segments"]["EGX30"]["rollback_profile"] == "EGX30_BALANCED"
    assert result["summary"]["calibration"]["market_segments"]["EGX70"]["active_enforcement_profile"] == "EGX70_HARDENED"
    assert result["summary"]["calibration"]["market_segments"]["EGX70"]["rollback_profile"] == "EGX70_STRICT"
    assert result["summary"]["calibration"]["market_segments"]["EGX30"]["calibration_summary"]["candidates"]["EGX30_BALANCED"]["deltas"]["allow_delta"] == 1
    assert result["summary"]["promotion"] == {
        "market_segments": {
            "EGX30": {
                "previous_active_profile": "EGX30_BALANCED",
                "new_active_profile": "EGX30_GUARDED",
                "rollback_profile": "EGX30_BALANCED",
                "promotion_rationale": "candidate_profile_promoted",
                "promotion_evidence": {"source": "threshold_calibration_review"},
            },
            "EGX70": {
                "previous_active_profile": "EGX70_STRICT",
                "new_active_profile": "EGX70_HARDENED",
                "rollback_profile": "EGX70_STRICT",
                "promotion_rationale": "candidate_profile_promoted",
                "promotion_evidence": {"source": "threshold_calibration_review"},
            },
        },
    }
    assert len(sent_messages) == 1
    assert "*COMI* (BUY)" in sent_messages[0]
    assert "*FWRY* (BUY)" not in sent_messages[0]
    assert "*HRHO* (BUY)" not in sent_messages[0]
    assert "WATCHLIST" in sent_messages[0]
    assert "FWRY" in sent_messages[0]
    assert all(event["event_type"] != "PUBLISH_RECOMMENDATION_BLOCKED" or event["entity_id"] == "HRHO" for event in audit_events)
    event_types = {event["event_type"] for event in audit_events}
    assert "PUBLISH_RECOMMENDATION_BLOCKED" in event_types
    assert "PUBLISH_RECOMMENDATION_WATCH_ONLY" in event_types
    completed = next(event for event in audit_events if event["event_type"] == "PUBLISH_COMPLETED")
    assert completed["details"]["summary"]["calibration"]["rollout_mode"] == "compare_only"
    assert completed["details"]["summary"]["promotion"]["market_segments"]["EGX70"]["new_active_profile"] == "EGX70_HARDENED"


def test_publish_signal_run_logic_can_filter_run_recommendations(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    portfolio = Portfolio.create(name="Filtered Portfolio", type="USER")
    allowed = SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )
    SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=10,
        stop_loss=9,
        target_price=11.5,
        score=6,
        confidence=61,
        state="ACTIVE",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[portfolio.id],
        channel="TELEGRAM",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    sent_messages = []
    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda message, **kwargs: sent_messages.append(message) or {"ok": True, "result": {"message_id": 9}},
        recommendation_filter_fn=lambda rec: rec.id == allowed.id,
    )

    assert result["summary"]["sent"] == 1
    assert len(sent_messages) == 1
    assert "*COMI* (BUY)" in sent_messages[0]
    assert "*HRHO* (BUY)" not in sent_messages[0]


def test_publish_signal_run_logic_fans_out_to_entitled_type_one_subscribers(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )
    entitled = Client.create(
        name="Type One Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="100200300",
    )
    Client.create(
        name="Missing Chat Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[],
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    sent = []
    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda message, **kwargs: sent.append((message, kwargs)) or {"ok": True, "result": {"message_id": 9}},
    )

    assert result["summary"]["sent"] == 1
    assert len(sent) == 1
    assert sent[0][1]["chat_id"] == "100200300"
    delivery = SignalDelivery.get(
        (SignalDelivery.run == run)
        & (SignalDelivery.destination_type == "SUBSCRIBER")
        & (SignalDelivery.destination_id == str(entitled.id))
    )
    assert delivery.service_tier == "SIGNALS_ONLY"
    assert delivery.destination_name == "Type One Client"
    assert delivery.destination_chat_id == "100200300"


def test_publish_signal_run_logic_reuses_legacy_portfolio_delivery_without_destination_id(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    portfolio = Portfolio.create(name="Legacy Portfolio Delivery", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )
    legacy_delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        destination_type="PORTFOLIO",
        destination_id=None,
        status="FAILED",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[portfolio.id],
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda _message, **_kwargs: {"ok": True, "result": {"message_id": 13}},
    )

    assert result["summary"]["sent"] == 1
    assert SignalDelivery.select().where(SignalDelivery.run == run).count() == 1
    refreshed = SignalDelivery.get_by_id(legacy_delivery.id)
    assert refreshed.status == "SENT"
    assert refreshed.destination_id == str(portfolio.id)
    assert refreshed.destination_name == "Legacy Portfolio Delivery"


def test_publish_signal_run_logic_records_content_tier_for_higher_tier_subscriber_delivery():
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )
    subscriber = Client.create(
        name="Type Two Client",
        subscription_tier="SIGNALS_PLUS_PORTFOLIO_RECS",
        telegram_chat_id="400500600",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[],
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda _message, **_kwargs: {"ok": True, "result": {"message_id": 11}},
    )

    delivery = SignalDelivery.get(
        (SignalDelivery.run == run)
        & (SignalDelivery.destination_type == "SUBSCRIBER")
        & (SignalDelivery.destination_id == str(subscriber.id))
    )
    assert delivery.service_tier == "SIGNALS_ONLY"


def test_publish_signal_run_logic_includes_main_channel_when_policy_allows(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_2", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-100main", raising=False)

    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[],
        channel="TELEGRAM",
        service_tier="SIGNALS_PLUS_PORTFOLIO_RECS",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    sent = []
    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda message, **kwargs: sent.append((message, kwargs)) or {"ok": True, "result": {"message_id": 10}},
    )

    assert result["summary"]["sent"] == 1
    assert sent[0][1]["chat_id"] == "-100main"
    delivery = SignalDelivery.get(
        (SignalDelivery.run == run)
        & (SignalDelivery.destination_type == "MAIN_CHANNEL")
        & (SignalDelivery.destination_id == "main")
    )
    assert delivery.service_tier == "SIGNALS_PLUS_PORTFOLIO_RECS"
    assert delivery.destination_name == "Main Telegram Channel"


def test_publish_signal_run_logic_can_limit_automated_destinations(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "type_1", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-100main", raising=False)

    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    Portfolio.create(name="User Workspace", type="USER")
    subscriber = Client.create(
        name="Type One Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="100200300",
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[],
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        include_portfolios=False,
        include_subscribers=True,
        include_main_channel=False,
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    sent = []
    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda message, **kwargs: sent.append((message, kwargs)) or {"ok": True, "result": {"message_id": 10}},
    )

    assert result["summary"]["sent"] == 1
    assert len(sent) == 1
    assert sent[0][1]["chat_id"] == "100200300"
    deliveries = list(SignalDelivery.select().where(SignalDelivery.run == run))
    assert len(deliveries) == 1
    assert deliveries[0].destination_type == "SUBSCRIBER"
    assert deliveries[0].destination_id == str(subscriber.id)


def test_publish_signal_run_logic_retries_only_frozen_delivery_destination():
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    run = SignalRun.create(status="COMPLETED", run_date=TimeUtils.today())
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=85,
        stop_loss=80,
        target_price=95,
        score=8,
        confidence=86,
        state="ACTIVE",
    )
    failed_delivery = SignalDelivery.create(
        run=run,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="SUBSCRIBER",
        destination_id="client-10",
        destination_name="Type One Client",
        destination_chat_id="100200300",
        status="FAILED",
    )
    Client.create(
        name="Other Active Client",
        subscription_tier="SIGNALS_ONLY",
        telegram_chat_id="999888777",
    )

    req = SimpleNamespace(
        run_id=run.id,
        portfolio_ids=[],
        retry_delivery_ids=[failed_delivery.id],
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        dry_run=False,
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
        ignore_guard=False,
    )

    sent = []
    result = publish_signal_run_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        is_telegram_configured_fn=lambda: True,
        send_message_fn=lambda message, **kwargs: sent.append((message, kwargs)) or {"ok": True, "result": {"message_id": 12}},
    )

    assert result["summary"]["sent"] == 1
    assert len(sent) == 1
    assert sent[0][1]["chat_id"] == "100200300"
    refreshed = SignalDelivery.get_by_id(failed_delivery.id)
    assert refreshed.status == "SENT"
    assert refreshed.destination_id == "client-10"


def test_retry_failed_deliveries_logic_returns_noop_without_failures():
    run = SignalRun.create(status="COMPLETED")

    req = SimpleNamespace(
        run_id=run.id,
        channel="TELEGRAM",
        max_retries=0,
        backoff_ms=0,
        enforce_window=False,
    )

    events = []
    result = retry_failed_deliveries_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: events.append(kwargs),
        publish_signal_run_logic_fn=lambda _req: (_ for _ in ()).throw(AssertionError("should not publish")),
    )

    assert result["status"] == "noop"
    assert result["noop_reason"] == "no_failed_deliveries"
    assert events[-1]["event_type"] == "PUBLISH_RETRY_NOOP"


def test_retry_failed_deliveries_logic_delegates_to_publish():
    run = SignalRun.create(status="COMPLETED")
    portfolio = Portfolio.create(name="Retry Portfolio", type="USER")
    delivery = SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        destination_type="PORTFOLIO",
        destination_id=str(portfolio.id),
        status="FAILED",
    )

    req = SimpleNamespace(
        run_id=run.id,
        channel="TELEGRAM",
        max_retries=2,
        backoff_ms=250,
        enforce_window=True,
    )

    captured = {}

    def fake_publish(publish_req):
        captured["run_id"] = publish_req.run_id
        captured["portfolio_ids"] = publish_req.portfolio_ids
        captured["retry_delivery_ids"] = publish_req.retry_delivery_ids
        captured["max_retries"] = publish_req.max_retries
        captured["backoff_ms"] = publish_req.backoff_ms
        captured["enforce_window"] = publish_req.enforce_window
        return {"status": "completed", "summary": {"failed": 0}}

    result = retry_failed_deliveries_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        publish_signal_run_logic_fn=fake_publish,
        retry_request_builder_fn=lambda **kwargs: SimpleNamespace(**kwargs),
    )

    assert result["status"] == "completed"
    assert captured == {
        "run_id": run.id,
        "portfolio_ids": [],
        "retry_delivery_ids": [delivery.id],
        "max_retries": 2,
        "backoff_ms": 250,
        "enforce_window": True,
    }


def test_retry_failed_deliveries_logic_can_retry_subscriber_deliveries():
    run = SignalRun.create(status="COMPLETED")
    delivery = SignalDelivery.create(
        run=run,
        portfolio=None,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="SUBSCRIBER",
        destination_id="client-10",
        destination_name="Type One Client",
        destination_chat_id="100200300",
        status="FAILED",
    )

    req = SimpleNamespace(
        run_id=run.id,
        channel="TELEGRAM",
        max_retries=1,
        backoff_ms=0,
        enforce_window=False,
    )

    captured = {}

    def fake_publish(publish_req):
        captured["retry_delivery_ids"] = publish_req.retry_delivery_ids
        captured["service_tier"] = publish_req.service_tier
        return {"status": "completed", "summary": {"failed": 0}}

    result = retry_failed_deliveries_logic(
        req,
        emit_audit_event_fn=lambda **kwargs: None,
        publish_signal_run_logic_fn=fake_publish,
        retry_request_builder_fn=lambda **kwargs: SimpleNamespace(**kwargs),
    )

    assert result["status"] == "completed"
    assert captured == {
        "retry_delivery_ids": [delivery.id],
        "service_tier": "SIGNALS_ONLY",
    }
