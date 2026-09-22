from core.settings import settings
from core.exclusions import is_excluded_ticker
import datetime
from fastapi.testclient import TestClient

from api import app
from database import (
    Portfolio,
    SignalRecommendation,
    SignalRun,
    SignalDelivery,
    SignalOutcome,
    SignalGuardState,
    SignalValidationRun,
    SignalAuditEvent,
    Trade,
)

import pytest
from core.signals.guard import set_guard_state

client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_guard_and_settings(monkeypatch):
    set_guard_state(is_blocked=False, reason=None, source="TEST", details=None)
    monkeypatch.setattr(settings, "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "", raising=False)


def _mock_signals(count=1):
    signals = []
    for i in range(count):
        signals.append(
            {
                "Ticker": f"TST{i+1}",
                "Signal_Type": "BUY",
                "Entry_Price": 10.0 + i,
                "Stop_Loss": 9.5 + i,
                "Target_Price": 11.0 + i,
                "Target_Price_2": 11.44 + i,
                "Score": 7 + i,
                "RSI": 62.0,
                "Volume_x": 2.2,
                "Sector": "Test",
                "Confirmation": "CONFIRMED",
            }
        )
    monitored = [{"Ticker": "AAA"}, {"Ticker": "BBB"}]
    return signals, monitored, 50.0, "CAUTIOUS"


def test_daily_run_is_idempotent_without_force(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    payload = {"run_date": "2026-02-11", "scan_type": "DAILY", "force": False}
    r1 = client.post("/api/v1/signals/runs/daily", json=payload)
    assert r1.status_code == 200
    assert r1.json()["status"] == "completed"

    r2 = client.post("/api/v1/signals/runs/daily", json=payload)
    assert r2.status_code == 200
    assert r2.json()["status"] == "existing"

    runs = SignalRun.select().where(
        (SignalRun.run_date == datetime.date(2026, 2, 11)) &
        (SignalRun.scan_type == "DAILY")
    ).count()
    assert runs == 1


def test_daily_run_force_reruns_existing(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    payload = {"run_date": "2026-02-10", "scan_type": "DAILY", "force": False}
    first = client.post("/api/v1/signals/runs/daily", json=payload).json()
    run_id = first["run"]["id"]
    assert first["run"]["signals_count"] == 1

    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(2),
    )
    second = client.post("/api/v1/signals/runs/daily", json={**payload, "force": True})
    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "completed"
    assert body["run"]["id"] == run_id
    assert body["run"]["signals_count"] == 2
    assert SignalRecommendation.select().where(SignalRecommendation.run == run_id).count() == 2


def test_intraday_runs_with_distinct_run_keys_create_distinct_runs(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="INTRADAY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False, is_pre_close=False: _mock_signals(1),
    )

    first = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-04", "scan_type": "INTRADAY", "run_key": "2026-02-04:INTRADAY:11:00", "force": False},
    )
    second = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-04", "scan_type": "INTRADAY", "run_key": "2026-02-04:INTRADAY:11:05", "force": False},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "completed"
    assert second.json()["status"] == "completed"
    assert first.json()["run"]["id"] != second.json()["run"]["id"]

    runs = SignalRun.select().where(
        (SignalRun.run_date == datetime.date(2026, 2, 4)) &
        (SignalRun.scan_type == "INTRADAY")
    )
    assert runs.count() == 2


def test_pre_close_run_scan_type_is_supported(monkeypatch):
    scan_calls = []
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="PRE_CLOSE": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda **kwargs: scan_calls.append(kwargs) or _mock_signals(1),
    )

    response = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-03", "scan_type": "PRE_CLOSE", "run_key": "2026-02-03:PRE_CLOSE", "force": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["run"]["scan_type"] == "PRE_CLOSE"
    assert body["run"]["run_key"] == "2026-02-03:PRE_CLOSE"
    assert scan_calls == [{"index_choice": "EGX30", "is_intraday": False, "is_pre_close": True}]


def test_stale_data_blocks_publish_run(monkeypatch):
    fresh_mock = lambda run_date=None, scan_type="DAILY": {
        "run_date": run_date,
        "scan_type": scan_type,
        "overall_ok": False,
        "history": {"ok": False},
        "intraday": {"ok": False},
    }
    monkeypatch.setattr("routes.signals.evaluate_data_freshness_logic", fresh_mock)
    monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic", fresh_mock)

    response = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-09", "scan_type": "DAILY", "force": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["run"]["status"] == "BLOCKED"


def test_publish_creates_one_delivery_per_user_portfolio(monkeypatch):
    Portfolio.create(name="Client A", type="USER")
    Portfolio.create(name="Client B", type="USER")

    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-08", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "channel": "TELEGRAM", "dry_run": True},
    )
    assert pub_resp.status_code == 200
    pub = pub_resp.json()
    assert pub["summary"]["dry_run"] == 2

    deliveries = client.get(f"/api/v1/signals/deliveries?run_id={run_id}")
    assert deliveries.status_code == 200
    data = deliveries.json()["deliveries"]
    assert len(data) == 2
    assert all(d["status"] == "DRY_RUN" for d in data)
    assert SignalDelivery.select().where(SignalDelivery.run == run_id).count() == 2


def test_recommendations_endpoint_returns_active_signals(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(2),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-07", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    rec_resp = client.get(f"/api/v1/signals/recommendations?run_id={run_id}")
    assert rec_resp.status_code == 200
    recs = rec_resp.json()["recommendations"]
    assert len(recs) == 2
    assert all("confidence" in r for r in recs)
    assert all("rationale" in r for r in recs)
    assert all("target_price_2" in r for r in recs)
    assert all(float(r["target_price_2"]) > float(r["target_price"]) for r in recs)


def test_publish_retries_failed_delivery_then_succeeds(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-06", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    Portfolio.create(name="Client Retry", type="USER")

    monkeypatch.setattr("routes.signals.settings.TELEGRAM_TOKEN", "token")
    monkeypatch.setattr("routes.signals.settings.CHAT_ID", "chat")

    calls = {"n": 0}

    def _fake_send(_message):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"ok": False, "description": "temporary network issue"}
        return {"ok": True, "result": {"message_id": 12345}}

    monkeypatch.setattr("routes.signals.TelegramBot_Alerts.send_message", _fake_send)

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={
            "run_id": run_id,
            "channel": "TELEGRAM",
            "dry_run": False,
            "max_retries": 2,
            "backoff_ms": 1,
        },
    )
    assert pub_resp.status_code == 200
    body = pub_resp.json()
    assert body["summary"]["sent"] == 1
    assert calls["n"] >= 2

    deliveries = client.get(f"/api/v1/signals/deliveries?run_id={run_id}").json()["deliveries"]
    d = deliveries[0]
    assert d["status"] == "SENT"
    assert d["attempts"] >= 2


def test_publish_message_contains_tp1_and_tp2(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-05", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    Portfolio.create(name="Client TP2", type="USER")
    monkeypatch.setattr("routes.signals.settings.TELEGRAM_TOKEN", "token")
    monkeypatch.setattr("routes.signals.settings.CHAT_ID", "chat")

    captured = {"message": ""}

    def _fake_send(message):
        captured["message"] = message
        return {"ok": True, "result": {"message_id": 777}}

    monkeypatch.setattr("routes.signals.TelegramBot_Alerts.send_message", _fake_send)

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "channel": "TELEGRAM", "dry_run": False, "max_retries": 0},
    )
    assert pub_resp.status_code == 200
    assert "TP1:" in captured["message"]
    assert "TP2:" in captured["message"]


def test_publish_window_enforcement_blocks_old_run(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-05", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={
            "run_id": run_id,
            "channel": "TELEGRAM",
            "dry_run": True,
            "enforce_window": True,
        },
    )
    assert pub_resp.status_code == 400
    detail = pub_resp.json()["detail"]
    assert "Publish blocked by window" in detail["message"]
    assert detail["block_type"] == "window"
    assert detail["window"]["reason"] == "run_date_mismatch"


def test_retry_failed_deliveries_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-04", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    Portfolio.create(name="Client Retry Endpoint", type="USER")
    monkeypatch.setattr("routes.signals.settings.TELEGRAM_TOKEN", "token")
    monkeypatch.setattr("routes.signals.settings.CHAT_ID", "chat")

    # First publish fails
    monkeypatch.setattr(
        "routes.signals.TelegramBot_Alerts.send_message",
        lambda _message: {"ok": False, "description": "transport down"},
    )
    first = client.post(
        "/api/v1/signals/publish",
        json={
            "run_id": run_id,
            "channel": "TELEGRAM",
            "dry_run": False,
            "max_retries": 0,
        },
    )
    assert first.status_code == 200
    assert first.json()["summary"]["failed"] == 1

    # Retry endpoint succeeds
    monkeypatch.setattr(
        "routes.signals.TelegramBot_Alerts.send_message",
        lambda _message: {"ok": True, "result": {"message_id": 321}},
    )
    retry = client.post(
        "/api/v1/signals/publish/retry",
        json={"run_id": run_id, "channel": "TELEGRAM", "max_retries": 1, "backoff_ms": 1},
    )
    assert retry.status_code == 200
    assert retry.json()["summary"]["sent"] == 1


def test_retry_latest_failed_deliveries_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-03", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200

    Portfolio.create(name="Client Retry Latest", type="USER")
    monkeypatch.setattr("routes.signals.settings.TELEGRAM_TOKEN", "token")
    monkeypatch.setattr("routes.signals.settings.CHAT_ID", "chat")

    monkeypatch.setattr(
        "routes.signals.TelegramBot_Alerts.send_message",
        lambda _message: {"ok": False, "description": "temporary fail"},
    )
    first = client.post(
        "/api/v1/signals/publish",
        json={"channel": "TELEGRAM", "dry_run": False, "max_retries": 0},
    )
    assert first.status_code == 200
    assert first.json()["summary"]["failed"] == 1

    monkeypatch.setattr(
        "routes.signals.TelegramBot_Alerts.send_message",
        lambda _message: {"ok": True, "result": {"message_id": 456}},
    )
    retry = client.post("/api/v1/signals/publish/retry-latest")
    assert retry.status_code == 200
    assert retry.json()["summary"]["sent"] == 1


def test_signals_sla_endpoint(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-02", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    Portfolio.create(name="Client SLA", type="USER")
    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "channel": "TELEGRAM", "dry_run": True},
    )
    assert pub_resp.status_code == 200

    sla_resp = client.get("/api/v1/signals/ops/sla?days=60")
    assert sla_resp.status_code == 200
    data = sla_resp.json()
    assert "runs" in data
    assert "deliveries" in data
    assert "success_rate_pct" in data["deliveries"]


def test_outcomes_rebuild_and_query(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-02-01", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]
    run = SignalRun.get_by_id(run_id)

    p = Portfolio.select().first()
    entry_dt = (run.started_at or datetime.datetime.now()) + datetime.timedelta(hours=1)
    exit_dt = entry_dt + datetime.timedelta(days=1)
    Trade.create(
        portfolio=p,
        ticker="TST1",
        shares=100,
        entry_price=10.0,
        exit_price=11.0,
        entry_date=entry_dt,
        exit_date=exit_dt,
        pnl=100.0,
        pnl_pct=10.0,
        reason="TARGET",
        currency="EGP",
    )

    rebuild = client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run_id})
    assert rebuild.status_code == 200
    body = rebuild.json()
    assert body["status"] == "completed"
    assert body["results"][0]["closed"] == 1

    outcomes = client.get(f"/api/v1/signals/outcomes?run_id={run_id}")
    assert outcomes.status_code == 200
    out_data = outcomes.json()["outcomes"]
    assert len(out_data) == 1
    assert out_data[0]["outcome_status"] == "CLOSED"
    assert SignalOutcome.select().where(SignalOutcome.run == run_id).count() == 1


def test_calibration_endpoint_from_closed_outcomes(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(2),
    )

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-01-31", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]
    run = SignalRun.get_by_id(run_id)

    p = Portfolio.select().first()
    base_dt = (run.started_at or datetime.datetime.now()) + datetime.timedelta(hours=2)
    Trade.create(
        portfolio=p,
        ticker="TST1",
        shares=100,
        entry_price=10.0,
        exit_price=11.0,
        entry_date=base_dt,
        exit_date=base_dt + datetime.timedelta(days=1),
        pnl=100.0,
        pnl_pct=10.0,
        reason="TARGET",
        currency="EGP",
    )
    Trade.create(
        portfolio=p,
        ticker="TST2",
        shares=100,
        entry_price=11.0,
        exit_price=10.5,
        entry_date=base_dt,
        exit_date=base_dt + datetime.timedelta(days=1),
        pnl=-50.0,
        pnl_pct=-4.5454,
        reason="STOP_LOSS",
        currency="EGP",
    )

    rebuild = client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run_id})
    assert rebuild.status_code == 200

    calib = client.get("/api/v1/signals/calibration?window=3650")
    assert calib.status_code == 200
    c = calib.json()
    assert c["closed_signals"] >= 2
    assert "overall" in c
    assert len(c["confidence_bins"]) >= 1
    assert "regime_breakdown" in c
    assert "sector_breakdown" in c


def test_walkforward_validation_auto_blocks_and_unblocks(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-01-30", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]
    run = SignalRun.get_by_id(run_id)

    p = Portfolio.select().first()
    base_dt = (run.started_at or datetime.datetime.now()) + datetime.timedelta(hours=1)
    Trade.create(
        portfolio=p,
        ticker="TST1",
        shares=100,
        entry_price=10.0,
        exit_price=9.0,
        entry_date=base_dt,
        exit_date=base_dt + datetime.timedelta(days=1),
        pnl=-100.0,
        pnl_pct=-10.0,
        reason="STOP_LOSS",
        currency="EGP",
    )

    rebuild = client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run_id})
    assert rebuild.status_code == 200

    val_fail = client.post(
        "/api/v1/signals/validation/walkforward/run",
        json={
            "window_days": 3650,
            "min_closed_signals": 1,
            "min_win_rate_pct": 60,
            "min_avg_pnl_pct": 0.1,
            "max_consecutive_weak_weeks": 1,
            "auto_block": True,
            "auto_unblock": True,
        },
    )
    assert val_fail.status_code == 200
    body_fail = val_fail.json()
    assert body_fail["status"] == "fail"
    assert body_fail["guard_state"]["is_blocked"] is True
    assert SignalGuardState.select().first().is_blocked is True
    assert SignalValidationRun.select().count() >= 1

    blocked_publish = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "channel": "TELEGRAM", "dry_run": True},
    )
    assert blocked_publish.status_code == 400
    detail = blocked_publish.json()["detail"]
    assert "Publish blocked by guard" in detail["message"]
    assert detail["guard"]["is_blocked"] is True

    val_pass = client.post(
        "/api/v1/signals/validation/walkforward/run",
        json={
            "window_days": 3650,
            "min_closed_signals": 1,
            "min_win_rate_pct": 0,
            "min_avg_pnl_pct": -100,
            "max_consecutive_weak_weeks": 10,
            "auto_block": True,
            "auto_unblock": True,
        },
    )
    assert val_pass.status_code == 200
    body_pass = val_pass.json()
    assert body_pass["status"] == "pass"
    assert body_pass["guard_state"]["is_blocked"] is False


def test_workspace_performance_endpoint(monkeypatch):
    ok_mock = lambda run_date=None, scan_type="DAILY": {
        "run_date": run_date,
        "scan_type": scan_type,
        "overall_ok": True,
        "history": {"ok": True},
        "intraday": {"ok": True},
    }
    monkeypatch.setattr("routes.signals.evaluate_data_freshness_logic", ok_mock)
    monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic", ok_mock)
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )
    monkeypatch.setattr("routes.signals.is_excluded_ticker", lambda x, y=None: False)

    user_port = Portfolio.create(name="Workspace Perf", type="USER")
    recent_date = (datetime.datetime.now() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": recent_date, "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "portfolio_ids": [user_port.id], "channel": "TELEGRAM", "dry_run": True, "ignore_guard": True},
    )
    assert pub_resp.status_code == 200

    now = datetime.datetime.now()
    Trade.create(
        portfolio=user_port,
        ticker="TST1",
        shares=100,
        entry_price=10.0,
        exit_price=11.0,
        entry_date=now - datetime.timedelta(days=2),
        exit_date=now - datetime.timedelta(days=1),
        pnl=100.0,
        pnl_pct=10.0,
        reason="TARGET",
        currency="EGP",
    )

    perf = client.get(f"/api/v1/signals/performance/workspace?portfolio_id={user_port.id}&windows=30,90")
    assert perf.status_code == 200
    data = perf.json()
    assert data["portfolio"]["id"] == user_port.id
    assert len(data["windows"]) == 2
    w30 = next(w for w in data["windows"] if w["window_days"] == 30)
    assert w30["trades"] >= 1
    assert w30["linked_trades"] >= 1


def test_client_endpoints_removed_in_single_operator_backend():
    assert client.post("/api/v1/clients", json={"name": "Blocked"}).status_code in (404, 405)
    assert client.get("/api/v1/client/signals/recommendations").status_code in (404, 405)


def test_signal_audit_events_capture_client_publish_and_run(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    entitled_port = Portfolio.create(name="Audit Entitled Port", type="USER")

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-01-27", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "portfolio_ids": [entitled_port.id], "channel": "TELEGRAM", "dry_run": True},
    )
    assert pub_resp.status_code == 200

    assert SignalAuditEvent.select().count() >= 2

    events_resp = client.get("/api/v1/signals/audit/events?limit=200")
    assert events_resp.status_code == 200
    body = events_resp.json()
    event_types = {e["event_type"] for e in body["events"]}
    required = {
        "RUN_COMPLETED",
        "PUBLISH_COMPLETED",
    }
    assert required.issubset(event_types)


def test_signal_audit_endpoints_filters_and_summary(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-01-26", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    run_events = client.get(f"/api/v1/signals/audit/events?run_id={run_id}&event_type=RUN_COMPLETED")
    assert run_events.status_code == 200
    run_body = run_events.json()
    assert run_body["count"] >= 1
    assert all(e["event_type"] == "RUN_COMPLETED" for e in run_body["events"])
    assert all(e["run_id"] == run_id for e in run_body["events"])

    admin_events = client.get("/api/v1/signals/audit/events?actor_type=ADMIN")
    assert admin_events.status_code == 200
    assert all(e["actor_type"] == "ADMIN" for e in admin_events.json()["events"])

    bad_since = client.get("/api/v1/signals/audit/events?since=not-a-date")
    assert bad_since.status_code == 400
    detail = bad_since.json()["detail"]
    assert detail["error_type"] == "validation"
    assert detail["error_reason"] == "invalid_since"
    assert detail["parameter"] == "since"
    assert detail["since"] == "not-a-date"

    summary = client.get("/api/v1/signals/audit/summary?days=30")
    assert summary.status_code == 200
    s = summary.json()
    assert s["total_events"] >= 1
    assert "RUN_COMPLETED" in s["by_event_type"]


def test_signals_security_status_endpoint_removed():
    assert client.get("/api/v1/signals/security/status").status_code in (404, 405)


def test_publish_without_portfolio_ids_targets_user_portfolios(monkeypatch):
    monkeypatch.setattr(
        "routes.signals.evaluate_data_freshness_logic",
        lambda run_date=None, scan_type="DAILY": {
            "run_date": run_date,
            "scan_type": scan_type,
            "overall_ok": True,
            "history": {"ok": True},
            "intraday": {"ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.signals.DailyScanner.get_market_signals",
        lambda index_choice="EGX30", is_intraday=False: _mock_signals(1),
    )

    Portfolio.create(name="Managed A", type="USER")
    Portfolio.create(name="Managed B", type="USER")

    run_resp = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-01-23", "scan_type": "DAILY", "force": True},
    )
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run"]["id"]

    pub_resp = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run_id, "channel": "TELEGRAM", "dry_run": True},
    )
    assert pub_resp.status_code == 200
    body = pub_resp.json()
    assert body["summary"]["dry_run"] == 2

    deliveries = client.get(f"/api/v1/signals/deliveries?run_id={run_id}").json()["deliveries"]
    assert len(deliveries) == 2
    assert all(d["portfolio_id"] is not None for d in deliveries)


def test_publish_endpoint_reports_enforcement_filtered_summary():
    run = SignalRun.create(status="COMPLETED")
    portfolio = Portfolio.create(name="Publish Enforcement", type="USER")

    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100,
        stop_loss=95,
        target_price=110,
        rationale_json='{"enforcement_state":"ALLOW","enforcement_reason":"not_enforced","enforcement_profile":"EGX30_GUARDED","trap_risk_band":"MEDIUM","whale_alignment":"SUPPORTIVE"}',
    )
    SignalRecommendation.create(
        run=run,
        ticker="FWRY",
        side="BUY",
        entry_price=20,
        stop_loss=18,
        target_price=23,
        rationale_json='{"enforcement_state":"WATCH_ONLY","enforcement_reason":"distribution_conflict","enforcement_profile":"EGX70_HARDENED","trap_risk_band":"MEDIUM","whale_alignment":"CONFLICT"}',
    )
    SignalRecommendation.create(
        run=run,
        ticker="HRHO",
        side="BUY",
        entry_price=10,
        stop_loss=8,
        target_price=11,
        rationale_json='{"enforcement_state":"BLOCK_EXECUTION","enforcement_reason":"severe_trap_risk","enforcement_profile":"EGX70_HARDENED","trap_risk_band":"SEVERE","whale_alignment":"NEUTRAL"}',
    )

    response = client.post(
        "/api/v1/signals/publish",
        json={"run_id": run.id, "portfolio_ids": [portfolio.id], "channel": "TELEGRAM", "dry_run": True},
    )

    assert response.status_code == 200
    summary = response.json()["summary"]
    assert summary["dry_run"] == 1
    assert summary["enforcement"]["actionable_count"] == 1
    assert summary["enforcement"]["watch_only_count"] == 1
    assert summary["enforcement"]["blocked_count"] == 1
    assert summary["enforcement"]["watch_only_tickers"] == ["FWRY"]
    assert summary["enforcement"]["blocked_tickers"] == ["HRHO"]
    assert summary["calibration"]["rollout_mode"] == "compare_only"
    assert summary["calibration"]["market_segments"]["EGX70"]["active_enforcement_profile"] == "EGX70_HARDENED"
    assert summary["calibration"]["market_segments"]["EGX70"]["rollback_profile"] == "EGX70_STRICT"
    assert summary["promotion"]["market_segments"]["EGX30"]["new_active_profile"] == "EGX30_GUARDED"
    assert summary["promotion"]["market_segments"]["EGX70"]["new_active_profile"] == "EGX70_HARDENED"

