import json
import datetime
from core.settings import settings

from fastapi.testclient import TestClient

from api import app
from database import Portfolio, SignalDelivery, SignalRecommendation, SignalRun


client = TestClient(app, raise_server_exceptions=False)


def test_get_signal_desk_returns_grouped_candidates_and_defaults():
    intraday_run = SignalRun.create(status="COMPLETED", scan_type="INTRADAY")
    daily_run = SignalRun.create(status="COMPLETED", scan_type="DAILY")

    SignalRecommendation.create(
        run=intraday_run,
        ticker="COMI",
        side="BUY",
        entry_price=82,
        stop_loss=79,
        target_price=87,
        score=8,
        confidence=81,
        horizon_days=1,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )
    SignalRecommendation.create(
        run=daily_run,
        ticker="HRHO",
        side="BUY",
        entry_price=24,
        stop_loss=22,
        target_price=28,
        score=7,
        confidence=73,
        horizon_days=5,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "ORACLE"}),
    )
    SignalRecommendation.create(
        run=daily_run,
        ticker="SWDY",
        side="BUY",
        entry_price=41,
        stop_loss=38,
        target_price=49,
        score=9,
        confidence=88,
        horizon_days=20,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "WHALES"}),
    )

    response = client.get("/api/v1/signals/desk")

    assert response.status_code == 200
    payload = response.json()["desk"]

    assert payload["operating_mode"] == "MANUAL"
    assert payload["autopilot_armed"] is False
    assert payload["lanes"]["intraday"]["count"] == 1
    assert payload["lanes"]["swing"]["count"] == 1
    assert payload["lanes"]["position"]["count"] == 1
    assert payload["lanes"]["intraday"]["candidates"][0]["ticker"] == "COMI"
    assert payload["lanes"]["swing"]["candidates"][0]["ticker"] == "HRHO"
    assert payload["lanes"]["position"]["candidates"][0]["ticker"] == "SWDY"
    assert payload["active_run"]["id"] == daily_run.id
    assert payload["failed_delivery_count"] == 0


def test_get_signal_desk_deduplicates_repeated_ticker_candidates():
    old_run = SignalRun.create(
        status="COMPLETED",
        scan_type="INTRADAY",
        run_date=datetime.date(2026, 5, 20),
        completed_at=datetime.datetime(2026, 5, 20, 13, 55),
    )
    latest_run = SignalRun.create(
        status="COMPLETED",
        scan_type="INTRADAY",
        run_date=datetime.date(2026, 5, 20),
        completed_at=datetime.datetime(2026, 5, 20, 14, 5),
    )
    SignalRecommendation.create(
        run=old_run,
        ticker="COMI",
        side="BUY",
        entry_price=81,
        stop_loss=78,
        target_price=86,
        score=7,
        confidence=75,
        horizon_days=1,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )
    SignalRecommendation.create(
        run=latest_run,
        ticker="COMI",
        side="BUY",
        entry_price=82,
        stop_loss=79,
        target_price=87,
        score=8,
        confidence=81,
        horizon_days=1,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )

    response = client.get("/api/v1/signals/desk")

    assert response.status_code == 200
    intraday_lane = response.json()["desk"]["lanes"]["intraday"]
    assert intraday_lane["count"] == 1
    assert [candidate["ticker"] for candidate in intraday_lane["candidates"]] == ["COMI"]
    assert intraday_lane["candidates"][0]["run_id"] == latest_run.id
    assert intraday_lane["candidates"][0]["entry_price"] == 82


def test_get_signal_desk_surfaces_failed_delivery_summary_for_active_run():
    run = SignalRun.create(status="COMPLETED", scan_type="DAILY")
    portfolio = Portfolio.create(name="Desk Failure Portfolio", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=82,
        stop_loss=79,
        target_price=87,
        score=8,
        confidence=81,
        horizon_days=5,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )
    SignalDelivery.create(
        run=run,
        portfolio=portfolio,
        channel="TELEGRAM",
        status="FAILED",
        attempts=2,
        last_error="transport down",
    )

    response = client.get("/api/v1/signals/desk")

    assert response.status_code == 200
    payload = response.json()["desk"]
    assert payload["failed_delivery_count"] == 1
    assert payload["latest_failed_delivery"]["status"] == "FAILED"
    assert payload["latest_failed_delivery"]["last_error"] == "transport down"


def test_update_signal_desk_mode_persists_mode_and_policy():
    response = client.post(
        "/api/v1/signals/desk/mode",
        json={
            "operating_mode": "AUTOPILOT",
            "autopilot_armed": True,
            "publish_policy": {
                "confidence_floor": 78,
                "source_modules": ["SCANNER", "ORACLE"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["desk"]
    assert payload["operating_mode"] == "AUTOPILOT"
    assert payload["autopilot_armed"] is True
    assert payload["publish_policy"]["confidence_floor"] == 78
    assert payload["publish_policy"]["source_modules"] == ["SCANNER", "ORACLE"]

    follow_up = client.get("/api/v1/signals/desk")

    assert follow_up.status_code == 200
    persisted = follow_up.json()["desk"]
    assert persisted["operating_mode"] == "AUTOPILOT"
    assert persisted["autopilot_armed"] is True
    assert persisted["publish_policy"]["confidence_floor"] == 78
    assert persisted["autopilot"]["status"] == "IDLE"


def test_promote_signal_candidate_adds_manual_queue_candidate_to_lane():
    response = client.post(
        "/api/v1/signals/desk/promote",
        json={
            "lane": "SWING",
            "ticker": "ORAS",
            "side": "BUY",
            "entry_price": 12.5,
            "stop_loss": 11.8,
            "target_price": 14.9,
            "confidence": 77,
            "score": 7.7,
            "source_module": "ORACLE",
            "rationale": {
                "summary": "Compression resolved with improving breadth.",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()["desk"]
    assert payload["lanes"]["swing"]["count"] == 1
    assert payload["lanes"]["swing"]["candidates"][0]["ticker"] == "ORAS"
    assert payload["lanes"]["swing"]["candidates"][0]["source_module"] == "ORACLE"
    assert payload["lanes"]["swing"]["candidates"][0]["origin"] == "MANUAL_QUEUE"

    follow_up = client.get("/api/v1/signals/desk")
    assert follow_up.status_code == 200
    persisted = follow_up.json()["desk"]
    assert persisted["lanes"]["swing"]["candidates"][0]["ticker"] == "ORAS"


def test_signal_desk_autopilot_blocks_when_policy_filters_everything():
    run = SignalRun.create(status="COMPLETED", scan_type="DAILY")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=82,
        stop_loss=79,
        target_price=87,
        score=8,
        confidence=62,
        horizon_days=5,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )
    client.post(
        "/api/v1/signals/desk/mode",
        json={
            "operating_mode": "AUTOPILOT",
            "autopilot_armed": True,
            "publish_policy": {"confidence_floor": 80},
        },
    )

    response = client.post("/api/v1/signals/desk/autopilot", json={"run_id": run.id})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert payload["autopilot"]["status"] == "BLOCKED"
    assert payload["autopilot"]["summary"]["blocked_reasons"]["confidence_below_floor"] == 1


def test_signal_desk_autopilot_treats_legacy_buy_source_as_scanner():
    run = SignalRun.create(status="COMPLETED", scan_type="DAILY")
    Portfolio.create(name="Autopilot Channel", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=82,
        stop_loss=79,
        target_price=87,
        score=8,
        confidence=81,
        horizon_days=5,
        state="ACTIVE",
        rationale_json=json.dumps({"source": "BUY"}),
    )
    client.post(
        "/api/v1/signals/desk/mode",
        json={
            "operating_mode": "AUTOPILOT",
            "autopilot_armed": True,
            "publish_policy": {
                "source_modules": ["SCANNER"],
                "batch_limits": {"intraday": 6, "swing": 6, "position": 4},
            },
        },
    )

    response = client.post(
        "/api/v1/signals/desk/autopilot",
        json={"run_id": run.id, "dry_run": True, "enforce_window": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["autopilot"]["summary"]["eligible_count"] == 1
    assert "source_not_allowed" not in payload["autopilot"]["summary"]["blocked_reasons"]


def test_signal_desk_autopilot_publishes_only_policy_eligible_recommendations(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)
    run = SignalRun.create(status="COMPLETED", scan_type="DAILY")
    Portfolio.create(name="Autopilot Channel", type="USER")
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=82,
        stop_loss=79,
        target_price=87,
        score=8,
        confidence=81,
        horizon_days=5,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "SCANNER"}),
    )
    SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=24,
        stop_loss=22,
        target_price=28,
        score=7,
        confidence=66,
        horizon_days=5,
        state="ACTIVE",
        rationale_json=json.dumps({"source_module": "ORACLE"}),
    )
    client.post(
        "/api/v1/signals/desk/mode",
        json={
            "operating_mode": "AUTOPILOT",
            "autopilot_armed": True,
            "publish_policy": {
                "confidence_floor": 70,
                "source_modules": ["SCANNER"],
                "batch_limits": {"intraday": 6, "swing": 6, "position": 4},
            },
        },
    )

    response = client.post("/api/v1/signals/desk/autopilot", json={"run_id": run.id, "dry_run": True, "enforce_window": False})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["autopilot"]["status"] == "COMPLETED"
    assert payload["autopilot"]["summary"]["eligible_count"] == 1
    assert payload["autopilot"]["summary"]["publish_summary"]["dry_run"] == 1
