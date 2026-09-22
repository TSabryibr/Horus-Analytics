import datetime

from fastapi.testclient import TestClient

import api
from api import app
from database import ProvisioningState


client = TestClient(app, raise_server_exceptions=False)


def test_operational_health_endpoint_returns_system_payload():
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["system"] == "Horus Analytics"
    assert "version" in data
    assert "state" in data
    assert "database" in data
    assert "pipeline_state" in data
    assert "timestamp" in data


def test_legacy_health_endpoint_returns_operational_payload():
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["system"] == "Horus Analytics"
    assert "pipeline_state" in data


def test_analytics_health_endpoint_returns_portfolio_diagnosis(monkeypatch):
    monkeypatch.setattr(
        "routes.analytics.Heimdall.get_portfolio_health",
        lambda: {"health": "GOOD", "score": 85},
    )

    response = client.get("/api/v1/analytics/health")

    assert response.status_code == 200
    assert response.json() == {"health": "GOOD", "score": 85}


def test_operational_health_endpoint_reports_provisioning_state(monkeypatch):
    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: {
            "status": "PROVISIONING",
            "message": "Provisioning historical signal context.",
            "step": "Historical Provisioning",
            "progress": 24,
            "bootstrap_complete": False,
            "pipeline_state": "STARTING",
            "provisioning_status": "RUNNING",
            "provisioning_target_trading_days": 252,
            "provisioning_completed_trading_days": 61,
            "freshness": {},
            "stale_mode": False,
        },
    )

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "provisioning"
    assert data["state"] == "PROVISIONING"
    assert data["provisioning_status"] == "RUNNING"
    assert data["provisioning_target_trading_days"] == 252
    assert data["provisioning_completed_trading_days"] == 61


def test_operational_health_endpoint_preserves_runtime_provisioning_error(monkeypatch):
    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: {
            "status": "ERROR",
            "message": "Startup Failed: Historical provisioning failed.",
            "step": "Historical Provisioning",
            "progress": 12,
            "bootstrap_complete": False,
            "pipeline_state": "STARTING",
            "provisioning_status": "ERROR",
            "provisioning_target_trading_days": 252,
            "provisioning_completed_trading_days": 10,
            "provisioning_error": "Provisioning failed for all 10 replay day(s).",
            "freshness": {},
            "stale_mode": False,
        },
    )

    response = client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"
    assert data["state"] == "ERROR"
    assert data["provisioning_status"] == "ERROR"
    assert data["provisioning_error"] == "Provisioning failed for all 10 replay day(s)."


def test_operational_health_endpoint_exposes_durable_provisioning_metadata(monkeypatch):
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=200,
        status="COMPLETED_WITH_WARNINGS",
        mode="AUTOMATIC",
        started_at=datetime.datetime(2026, 3, 20, 8, 0, 0),
        completed_at=datetime.datetime(2026, 3, 24, 9, 30, 0),
        last_error="Provisioning completed with limited historical coverage.",
    )

    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: {
            "status": "READY",
            "message": "System Operational",
            "step": "Ready",
            "progress": 100,
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "provisioning_status": "COMPLETED_WITH_WARNINGS",
            "provisioning_target_trading_days": 252,
            "provisioning_completed_trading_days": 200,
            "freshness": {},
            "stale_mode": False,
        },
    )

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["provisioning_status"] == "COMPLETED_WITH_WARNINGS"
    assert data["last_backfill_status"] == "COMPLETED_WITH_WARNINGS"
    assert data["last_backfill_error"] == "Provisioning completed with limited historical coverage."
    assert data["last_backfill_mode"] == "AUTOMATIC"
    assert data["last_backfill_started_at"] == "2026-03-20T08:00:00"
    assert data["last_backfill_completed_at"] == "2026-03-24T09:30:00"


def test_operational_health_endpoint_separates_runtime_provisioning_from_last_manual_backfill(monkeypatch):
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=252,
        status="COMPLETED",
        mode="MANUAL",
        started_at=datetime.datetime(2026, 3, 20, 8, 0, 0),
        completed_at=datetime.datetime(2026, 3, 24, 9, 30, 0),
        last_error=None,
    )

    monkeypatch.setattr(
        api,
        "refresh_pipeline_state",
        lambda force=False: {
            "status": "READY",
            "message": "System Operational",
            "step": "Ready",
            "progress": 100,
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "provisioning_status": "IDLE",
            "provisioning_target_trading_days": 0,
            "provisioning_completed_trading_days": 0,
            "provisioning_error": None,
            "freshness": {},
            "stale_mode": False,
        },
    )

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["provisioning_status"] == "IDLE"
    assert data["provisioning_target_trading_days"] == 0
    assert data["provisioning_completed_trading_days"] == 0
    assert data["last_backfill_status"] == "COMPLETED"
    assert data["last_backfill_mode"] == "MANUAL"
    assert data["last_backfill_started_at"] == "2026-03-20T08:00:00"
    assert data["last_backfill_completed_at"] == "2026-03-24T09:30:00"
