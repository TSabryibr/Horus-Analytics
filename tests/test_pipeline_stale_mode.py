from core.settings import settings
from fastapi.testclient import TestClient

import pytest

import api


client = TestClient(api.app)


@pytest.fixture(autouse=True)
def ensure_trading_day(monkeypatch):
    import config.app_factory as app_factory
    monkeypatch.setattr(app_factory, "_is_non_trading_day", lambda: False)


def _pipeline_state(state: str) -> dict:
    return {
        "bootstrap_complete": True,
        "status": "READY",
        "pipeline_state": state,
        "message": f"pipeline={state}",
    }


def test_read_endpoint_accessible_in_stale_mode(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))

    response = client.get("/api/v1/scanner/status")
    assert response.status_code == 200


def test_live_status_endpoint_accessible_in_stale_mode(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))
    monkeypatch.setattr("routes.live.settings.is_market_open", lambda: False)
    monkeypatch.setattr("routes.live.LiveFeedManager.is_running", lambda: False)
    monkeypatch.setattr("routes.live.LiveFeedManager.get_last_update_time", lambda: None)
    monkeypatch.setattr("routes.live.LiveFeedManager.get_session_stats", lambda: {})

    response = client.get("/api/v1/live/status")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "success"


def test_scanner_history_endpoint_accessible_in_stale_mode(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))

    response = client.get("/api/v1/scanner/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_active_endpoint_blocked_in_stale_mode(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))

    response = client.post("/api/v1/strategy/apply", json={"params": {"RISK_PER_TRADE": 1.0}})
    assert response.status_code == 503
    body = response.json()
    assert body.get("status") == "stale_mode"
    assert body.get("pipeline_state") == "STALE"
    assert body.get("bootstrap_complete") is True
    assert body.get("method") == "POST"
    assert body.get("path") == "/api/v1/strategy/apply"


def test_active_endpoint_allowed_in_fresh_mode(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("FRESH"))

    # Assuming strategy apply logic itself might return 422 or process, we just want to ensure it's not 503
    response = client.post("/api/v1/strategy/apply", json={"params": {"RISK_PER_TRADE": 1.0}})
    assert response.status_code != 503


def test_strategy_backtest_endpoint_allowed_in_stale_mode(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))
    monkeypatch.setattr(
        "routes.strategy.PortfolioSimulator.run_simulation",
        lambda **kwargs: {
            "total_return": 12.5,
            "final_value": 112500,
            "trades": [],
            "daily_values": [100000, 101500, 112500],
        },
    )

    response = client.post(
        "/api/v1/strategy/backtest",
        json={"index": "EGX30", "capital": 100000, "params": {"SL_PCT": 2.0}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "success"
    assert body.get("config", {}).get("index") == "EGX30"


@pytest.mark.parametrize("path", [
    "/api/v1/strategy/start",
    "/api/v1/optimizer/start",
])
def test_strategy_optimizer_research_endpoints_allowed_in_stale_mode(monkeypatch, path):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))
    monkeypatch.setattr("routes.strategy.background_optimize_task", lambda _index: None)

    response = client.post(path, params={"index": "EGX30"})

    assert response.status_code == 200
    body = response.json()
    assert body.get("started") in {True, False}


def test_stale_mode_response_includes_expected_trading_day(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("SYNCING"))
    monkeypatch.setattr(
        "routes.data.get_data_status_logic",
        lambda: {
            "last_updated": "2026-03-26",
            "history": {"expected_last_working_day": "2026-03-26"},
        },
    )

    response = client.post("/api/v1/scanner/start")

    assert response.status_code == 503
    body = response.json()
    assert body.get("status") == "stale_mode"
    assert body.get("last_updated") == "2026-03-26"
    assert body.get("expected_date") == "2026-03-26"


def test_startup_gate_response_exposes_request_context(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: {
            "bootstrap_complete": False,
            "status": "STARTING",
            "pipeline_state": "STARTING",
            "message": "System booting",
        },
    )

    response = client.post("/api/v1/strategy/apply", json={"params": {"RISK_PER_TRADE": 1.0}})

    assert response.status_code == 503
    body = response.json()
    assert body.get("status") == "unavailable"
    assert body.get("bootstrap_complete") is False
    assert body.get("pipeline_state") == "STARTING"
    assert body.get("method") == "POST"
    assert body.get("path") == "/api/v1/strategy/apply"


def test_provisioning_gate_response_exposes_provisioning_context(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: {
            "bootstrap_complete": False,
            "status": "PROVISIONING",
            "pipeline_state": "STARTING",
            "provisioning_status": "RUNNING",
            "provisioning_target_trading_days": 252,
            "provisioning_completed_trading_days": 18,
            "message": "Provisioning historical signal context.",
        },
    )

    response = client.post("/api/v1/strategy/apply", json={"params": {"RISK_PER_TRADE": 1.0}})

    assert response.status_code == 503
    body = response.json()
    assert body.get("status") == "unavailable"
    assert body.get("system_state") == "PROVISIONING"
    assert body.get("provisioning_status") == "RUNNING"
    assert body.get("provisioning_target_trading_days") == 252
    assert body.get("provisioning_completed_trading_days") == 18


def test_boot_status_endpoint_is_accessible_during_bootstrap(monkeypatch):
    boot_snapshot = {
        "bootstrap_complete": False,
        "status": "STARTING",
        "pipeline_state": "STARTING",
        "message": "System booting",
        "freshness": {},
        "sync_worker": {},
        "stale_mode": False,
    }
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: dict(boot_snapshot),
    )
    monkeypatch.setattr("routes.system.refresh_pipeline_state", lambda force=False: dict(boot_snapshot))
    # The boot-status payload resolves refresh_pipeline_state from core.pipeline
    # at call time (routes/system/state.py), so patch it there too.
    monkeypatch.setattr("core.pipeline.refresh_pipeline_state", lambda force=False: dict(boot_snapshot))

    response = client.get("/api/v1/system/boot-status")

    assert response.status_code == 200
    body = response.json()
    assert body.get("pipeline_state") == "STARTING"
    assert body.get("message") == "System booting"


@pytest.mark.parametrize("path", [
    "/api/v1/scanner/start",
    "/api/v1/live/start",
    "/api/v1/live/stop",
])
def test_scanner_live_endpoints_blocked_in_stale_mode(monkeypatch, path):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _pipeline_state("STALE"))

    response = client.post(path)
    assert response.status_code == 503
    body = response.json()
    assert body.get("status") == "stale_mode"
    assert body.get("pipeline_state") == "STALE"


def test_stale_gate_path_helper():
    assert api._is_stale_blocked_action("POST", "/api/v1/scanner/start")
    assert api._is_stale_blocked_action("POST", "/api/v1/live/start")
    assert api._is_stale_blocked_action("POST", "/api/v1/live/stop")
    assert api._is_stale_blocked_action("POST", "/api/v1/strategy/apply")
    assert not api._is_stale_blocked_action("POST", "/api/v1/strategy/backtest")
    assert not api._is_stale_blocked_action("POST", "/api/v1/strategy/start")
    assert not api._is_stale_blocked_action("POST", "/api/v1/optimizer/start")
    assert not api._is_stale_blocked_action("GET", "/api/v1/scanner/start")
    assert not api._is_stale_blocked_action("GET", "/api/v1/scanner/status")
    assert not api._is_stale_blocked_action("GET", "/api/v1/live/status")


def test_pipeline_degraded_when_mubasher_unreachable(monkeypatch):
    from core.pipeline import _derive_pipeline_state_from_freshness

    monkeypatch.setattr("core.pipeline.settings.is_market_open", lambda: True)
    monkeypatch.setattr("core.pipeline.settings.SESSION_MODE", "LIVE")

    freshness = {
        "history": {"ok": True, "kpis": {"fresh_ratio": 1.0}},
        "intraday": {"ok": False, "kpis": {"live_ratio": 0.0}},
    }

    state, msg, metrics = _derive_pipeline_state_from_freshness(freshness)

    assert state == "DEGRADED"
    assert metrics["degradation_reason"] == "intraday_provider_unreachable"
    assert "unreachable" in msg.lower()


def test_sync_worker_detects_unreachable_provider(monkeypatch, tmp_path):
    from data_engine.pipeline_worker import AdaptiveSyncWorker
    import logging

    mubasher_root = tmp_path / "Mubasher"
    user_data = mubasher_root / "UserData" / "user1"
    user_data.mkdir(parents=True)

    monkeypatch.setattr("data_engine.pipeline_worker.settings", settings)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB")
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root))
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "user1")
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setenv("TEST_MUBASHER_REACHABILITY_CHECK", "1")

    worker = AdaptiveSyncWorker(logger=logging.getLogger())

    assert worker._is_mubasher_unreachable() is True

    intraday_dir = user_data / "Intraday" / "CASE"
    intraday_dir.mkdir(parents=True)
    db_file = intraday_dir / "INTRADAY_MASTER.db"
    db_file.write_text("FAKE")

    assert worker._is_mubasher_unreachable() is False

    import time
    import os
    old_time = time.time() - 3600
    os.utime(db_file, (old_time, old_time))
    assert worker._is_mubasher_unreachable() is True

