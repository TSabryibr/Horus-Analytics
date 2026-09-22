import logging
import pytest
from fastapi.testclient import TestClient

from config.app_factory import create_app
from config.lifespan import _warn_if_auth_disabled_on_non_loopback, _is_loopback_host
from core.auth import is_auth_enforced, is_valid_api_key


@pytest.fixture
def auth_app():
    return create_app()


def test_is_loopback_host_identifies_loopback_correctly():
    assert _is_loopback_host("127.0.0.1") is True
    assert _is_loopback_host("localhost") is True
    assert _is_loopback_host("::1") is True
    assert _is_loopback_host("0.0.0.0") is False
    assert _is_loopback_host("192.168.1.100") is False
    assert _is_loopback_host("10.0.0.1") is False


def test_warn_if_auth_disabled_on_non_loopback_logs_warning(caplog):
    caplog.set_level(logging.WARNING)
    _warn_if_auth_disabled_on_non_loopback("0.0.0.0")
    assert any("[Security]" in record.message for record in caplog.records)


def test_warn_if_auth_disabled_on_loopback_is_silent(caplog):
    caplog.set_level(logging.WARNING)
    caplog.clear()
    _warn_if_auth_disabled_on_non_loopback("127.0.0.1")
    assert not any("[Security]" in record.message for record in caplog.records)


def test_local_default_allows_access_without_api_key(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "disabled")
    client = TestClient(auth_app, raise_server_exceptions=False)

    # Protected canonical route
    res = client.get("/api/v1/portfolio/open")
    assert res.status_code == 200

    # Legacy alias
    res_alias = client.get("/api/v1/positions")
    assert res_alias.status_code == 200


def test_enforced_auth_rejects_missing_key(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "api_key")
    monkeypatch.setenv("HORUS_API_KEY", "test-secret-key-12345")
    client = TestClient(auth_app, raise_server_exceptions=False)

    # Canonical route
    res = client.get("/api/v1/portfolio/open")
    assert res.status_code == 401
    assert res.json()["detail"]["error_reason"] == "api_key_missing"

    # Legacy alias
    res_alias = client.get("/api/v1/positions")
    assert res_alias.status_code == 401
    assert res_alias.json()["detail"]["error_reason"] == "api_key_missing"


def test_enforced_auth_rejects_invalid_key(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "api_key")
    monkeypatch.setenv("HORUS_API_KEY", "test-secret-key-12345")
    client = TestClient(auth_app, raise_server_exceptions=False)

    # Canonical route
    res = client.get("/api/v1/portfolio/open", headers={"x-api-key": "wrong-key"})
    assert res.status_code == 403
    assert res.json()["detail"]["error_reason"] == "api_key_invalid"

    # Legacy alias
    res_alias = client.get("/api/v1/positions", headers={"x-api-key": "wrong-key"})
    assert res_alias.status_code == 403
    assert res_alias.json()["detail"]["error_reason"] == "api_key_invalid"


def test_enforced_auth_handles_unconfigured_server_key(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "api_key")
    monkeypatch.delenv("HORUS_API_KEY", raising=False)
    monkeypatch.delenv("HORUS_ADMIN_API_KEY", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)

    client = TestClient(auth_app, raise_server_exceptions=False)
    res = client.get("/api/v1/portfolio/open", headers={"x-api-key": "some-key"})
    assert res.status_code == 503
    assert res.json()["detail"]["error_reason"] == "api_key_not_configured"


def test_enforced_auth_allows_valid_key(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "api_key")
    monkeypatch.setenv("HORUS_API_KEY", "test-secret-key-12345")
    client = TestClient(auth_app, raise_server_exceptions=False)

    # Canonical route
    res = client.get("/api/v1/portfolio/open", headers={"x-api-key": "test-secret-key-12345"})
    assert res.status_code == 200

    # Legacy alias
    res_alias = client.get("/api/v1/positions", headers={"x-api-key": "test-secret-key-12345"})
    assert res_alias.status_code == 200


def test_websocket_auth_in_enforced_mode(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "api_key")
    monkeypatch.setenv("HORUS_API_KEY", "test-secret-key-12345")
    client = TestClient(auth_app, raise_server_exceptions=False)

    # Connect without key -> fails / closes
    with pytest.raises(Exception):
        with client.websocket_connect("/ws") as ws:
            ws.receive_text()

    # Connect with invalid key -> fails / closes
    with pytest.raises(Exception):
        with client.websocket_connect("/ws?api_key=bad-key") as ws:
            ws.receive_text()

    # Connect with valid query param key -> succeeds
    with client.websocket_connect("/ws?api_key=test-secret-key-12345") as ws:
        pass


def test_websocket_local_default_allows_unauthenticated(monkeypatch, auth_app):
    monkeypatch.setenv("HORUS_AUTH_MODE", "disabled")
    client = TestClient(auth_app, raise_server_exceptions=False)

    with client.websocket_connect("/ws") as ws:
        pass
