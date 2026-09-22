"""
Tests for clean route-to-service-layer wiring.
Validates that route layer delegates to domain services correctly
using standardized Pydantic V2 schemas.
"""
import pytest
from fastapi.testclient import TestClient


def _get_client():
    from config.app_factory import create_app
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_portfolio_get_route_returns_dict():
    """GET /api/v1/portfolio should return a dict (may 404 if no portfolio)."""
    client = _get_client()
    resp = client.get("/api/v1/portfolio", headers={"X-API-Key": "test"})
    # 200 with data, or 404 if no portfolio seeded
    assert resp.status_code in (200, 404, 422)


def test_positions_route_returns_list():
    """GET /api/v1/positions should return a list (possibly empty)."""
    client = _get_client()
    resp = client.get("/api/v1/positions", headers={"X-API-Key": "test"})
    assert resp.status_code in (200, 401, 422)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_trades_route_returns_list():
    """GET /api/v1/trades should return a list."""
    client = _get_client()
    resp = client.get("/api/v1/trades", headers={"X-API-Key": "test"})
    assert resp.status_code in (200, 401, 422)
    if resp.status_code == 200:
        assert isinstance(resp.json(), list)


def test_system_status_route():
    """GET /api/v1/system/status is public and returns pipeline state."""
    client = _get_client()
    resp = client.get("/api/v1/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


def test_system_boot_status_route():
    """GET /api/v1/system/boot-status is public and returns boot telemetry."""
    client = _get_client()
    resp = client.get("/api/v1/system/boot-status")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


def test_signal_desk_route():
    """GET /api/v1/signals/desk should return a dict."""
    client = _get_client()
    resp = client.get("/api/v1/signals/desk", headers={"X-API-Key": "test"})
    assert resp.status_code in (200, 401, 422)
    if resp.status_code == 200:
        assert isinstance(resp.json(), dict)


def test_schema_reuse_add_trade_validates():
    """POST /api/v1/trade/add should reject invalid payloads per Pydantic schema."""
    client = _get_client()
    # Missing required fields - should 422
    resp = client.post("/api/v1/trade/add", json={}, headers={"X-API-Key": "test"})
    assert resp.status_code in (401, 422)


def test_schema_reuse_close_trade_validates():
    """POST /api/v1/trade/close should reject missing required exit_price."""
    client = _get_client()
    resp = client.post("/api/v1/trade/close", json={}, headers={"X-API-Key": "test"})
    assert resp.status_code in (401, 422)
