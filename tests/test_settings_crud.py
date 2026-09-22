"""
SETTINGS CRUD TESTS
===================
Tests for routes/settings.py — settings updates, telegram config,
broadcast, exclusion management.
"""

from core.settings import settings
from core.exclusions import add_exclusion, remove_exclusion
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

from api import app

client = TestClient(app, raise_server_exceptions=False)


def test_test_suite_uses_an_isolated_settings_file():
    """API persistence tests must never write to the repository's live settings."""
    repository_settings = (Path(__file__).parents[1] / "settings.json").resolve()

    assert Path(settings.SETTINGS_FILE).resolve() != repository_settings
    assert Path(settings.SETTINGS_FILE).name.startswith(("horus_pytest_settings_", "horus_backend_tests_settings_"))


def test_fresh_app_settings_default_to_mubasher_db(tmp_path, monkeypatch):
    """A fresh settings object should prefer the precise Mubasher DB source."""
    from core.settings import AppSettings

    monkeypatch.delenv("LOCAL_HISTORY_PROVIDER", raising=False)
    monkeypatch.delenv("LOCAL_INTRADAY_PROVIDER", raising=False)
    monkeypatch.setattr(
        AppSettings,
        "get_resource_path",
        lambda self, relative_path: str(tmp_path / "bundle" / relative_path),
    )
    monkeypatch.setattr(
        AppSettings,
        "get_persistent_path",
        lambda self, relative_path: str(tmp_path / "runtime" / relative_path),
    )

    fresh_settings = AppSettings()

    assert fresh_settings.LOCAL_HISTORY_PROVIDER == "MUBASHER_DB"
    assert fresh_settings.LOCAL_INTRADAY_PROVIDER == "MUBASHER_DB"
    assert fresh_settings.LOCAL_TICKS_PROVIDER == "MUBASHER_DB"
    assert fresh_settings.TICK_SYNC_ENABLED is True


def test_loading_settings_from_disk_does_not_rewrite_file(tmp_path, monkeypatch):
    """Loading a preset should hydrate memory without normalizing or rewriting the runtime file."""
    from core.settings import AppSettings

    settings_file = tmp_path / "settings.json"
    settings_payload = {
        "custom": {
            "LOOKBACK": 44,
            "VOL_SPIKE": 1.75,
            "TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL": "type_1",
            "preset_name": "custom",
        }
    }
    settings_file.write_text(json.dumps(settings_payload, indent=4), encoding="utf-8")
    before = settings_file.read_text(encoding="utf-8")

    monkeypatch.setenv("HORUS_SETTINGS_FILE", str(settings_file))

    fresh_settings = AppSettings()

    assert fresh_settings.SETTINGS_FILE == str(settings_file)
    assert fresh_settings.LOOKBACK == 44
    assert fresh_settings.VOL_SPIKE == 1.75
    assert settings_file.read_text(encoding="utf-8") == before


def test_committed_defaults_load_before_local_settings(tmp_path, monkeypatch):
    """Local settings override committed defaults without replacing unspecified defaults."""
    from core.settings import AppSettings

    bundle_dir = tmp_path / "bundle"
    defaults_file = bundle_dir / "config" / "settings.defaults.json"
    defaults_file.parent.mkdir(parents=True)
    defaults_file.write_text(
        json.dumps({"default": {"LOOKBACK": 31, "VOL_SPIKE": 1.8}}),
        encoding="utf-8",
    )
    local_file = tmp_path / "runtime" / "settings.json"
    local_file.parent.mkdir(parents=True)
    local_file.write_text(
        json.dumps({"custom": {"LOOKBACK": 44}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        AppSettings,
        "get_resource_path",
        lambda self, relative_path: str(bundle_dir / relative_path),
    )
    monkeypatch.setattr(
        AppSettings,
        "get_persistent_path",
        lambda self, relative_path: str(tmp_path / "runtime" / relative_path),
    )
    monkeypatch.delenv("HORUS_SETTINGS_FILE", raising=False)

    fresh_settings = AppSettings()

    assert fresh_settings.LOOKBACK == 44
    assert fresh_settings.VOL_SPIKE == 1.8


def test_settings_payload_includes_tick_source_defaults(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_TICKS_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr(settings, "TICK_SYNC_ENABLED", True, raising=False)

    response = client.get("/api/v1/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["LOCAL_TICKS_PROVIDER"] == "MUBASHER_DB"
    assert data["TICK_SYNC_ENABLED"] is True


# =============================================================================
# POST /api/settings
# =============================================================================

class TestUpdateSettings:
    """Tests for the settings update endpoint."""

    def test_update_settings_success(self, monkeypatch):
        """POST /api/settings should update strategy parameters."""
        monkeypatch.setattr(
            "routes.settings.settings.update",
            lambda payload: True,
        )
        response = client.post("/api/v1/settings", json={"SL_PCT": 3.0, "TP1_PCT": 5.0})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"
        assert "settings" in data

    def test_update_settings_invalid_value(self, monkeypatch):
        """POST /api/settings with invalid values should return 400."""
        monkeypatch.setattr(
            "routes.settings.settings.update",
            MagicMock(side_effect=ValueError("LOOKBACK must be positive")),
        )
        response = client.post("/api/v1/settings", json={"LOOKBACK": -5})
        assert response.status_code == 400
        assert "LOOKBACK must be positive" in response.json()["detail"]

    def test_update_settings_persistence_failure(self, monkeypatch):
        """POST /api/settings should return 500 when persistence fails."""
        monkeypatch.setattr(
            "routes.settings.settings.update",
            lambda payload: False,
        )
        response = client.post("/api/v1/settings", json={"SL_PCT": 3.0})
        assert response.status_code == 500
        assert "persist" in response.json()["detail"].lower()

    def test_update_settings_logs_auto_trade_toggle(self, monkeypatch, caplog):
        settings.AUTO_TRADE_ENABLED = False

        def _update(payload):
            settings.AUTO_TRADE_ENABLED = bool(payload.get("AUTO_TRADE_ENABLED"))
            return True

        monkeypatch.setattr("routes.settings.settings.update", _update)

        with caplog.at_level("INFO", logger="horus.settings"):
            response = client.post("/api/v1/settings", json={"AUTO_TRADE_ENABLED": True})

        assert response.status_code == 200
        assert "AUTO_TRADE_ENABLED update requested=True previous=False current=True changed=True" in caplog.text


# =============================================================================
# TELEGRAM CONFIG
# =============================================================================

class TestTelegramConfig:
    """Tests for telegram configuration endpoints."""

    def test_update_telegram_config(self):
        """POST /api/telegram/config should set token and chat_id."""
        response = client.post("/api/v1/telegram/config", json={
            "token": "test_token_12345",
            "chat_id": "-1001234567890"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["configured"] is True

    def test_broadcast_text_message(self, monkeypatch):
        """POST /api/telegram/broadcast with text message should send."""
        monkeypatch.setattr(
            "routes.settings.TelegramBot_Alerts.send_message",
            lambda msg: {"ok": True, "result": {"message_id": 1}},
        )
        response = client.post("/api/v1/telegram/broadcast", json={
            "message": "Test broadcast message"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"

    def test_broadcast_empty_payload(self):
        """POST /api/telegram/broadcast without message or image should return 400."""
        response = client.post("/api/v1/telegram/broadcast", json={})
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    def test_broadcast_telegram_failure(self, monkeypatch):
        """POST /api/telegram/broadcast should return 502 on Telegram API failure."""
        monkeypatch.setattr(
            "routes.settings.TelegramBot_Alerts.send_message",
            lambda msg: {"ok": False, "description": "Bot token invalid"},
        )
        response = client.post("/api/v1/telegram/broadcast", json={
            "message": "This will fail"
        })
        assert response.status_code == 502
        assert "Telegram API Failed" in response.json()["detail"]

    def test_telegram_test_alert_success(self, monkeypatch):
        """POST /api/telegram/test should send a test alert."""
        monkeypatch.setattr(
            "routes.settings.TelegramBot_Alerts.send_message",
            lambda msg, chat_id=None, token=None: {"ok": True, "result": {"message_id": 42}},
        )
        response = client.post("/api/v1/telegram/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_telegram_test_alert_reports_explicit_target_chat(self, monkeypatch):
        """POST /api/telegram/test should make the tested chat target visible."""
        captured = {}

        def fake_send_message(msg, token=None, chat_id=None):
            captured["token"] = token
            captured["chat_id"] = chat_id
            return {"ok": True, "result": {"message_id": 77}}

        monkeypatch.setattr("routes.settings.TelegramBot_Alerts.send_message", fake_send_message)

        response = client.post(
            "/api/v1/telegram/test",
            json={"token": "123456:token", "chat_id": "1822794531"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["target_chat_id"] == "1822794531"
        assert data["message"] == "Primary Telegram test sent to 1822794531."
        assert captured["chat_id"] == "1822794531"


# =============================================================================
# EXCLUSION MANAGEMENT
# =============================================================================

class TestExclusionManagement:
    """Tests for ticker exclusion CRUD endpoints."""

    def test_add_exclusion(self, monkeypatch):
        """POST /api/exclusions should add a ticker to exclusion list."""
        added = []
        monkeypatch.setattr(
            "routes.settings.add_exclusion",
            lambda t: added.append(t),
        )
        response = client.post("/api/v1/exclusions", json={"ticker": "BAD_STOCK"})
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "BAD_STOCK" in added

    def test_add_exclusion_no_ticker(self):
        """POST /api/exclusions without ticker should return 400."""
        response = client.post("/api/v1/exclusions", json={})
        assert response.status_code == 400
        assert "Ticker required" in response.json()["detail"]

    def test_remove_exclusion(self, monkeypatch):
        """DELETE /api/exclusions/{ticker} should remove a ticker."""
        removed = []
        monkeypatch.setattr(
            "routes.settings.remove_exclusion",
            lambda t: removed.append(t),
        )
        response = client.delete("/api/v1/exclusions/BAD_STOCK")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert "BAD_STOCK" in removed
