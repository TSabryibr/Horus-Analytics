import os
import pytest
from fastapi.testclient import TestClient

import api
from config.app_factory import create_app
from config.lifespan import _run_startup_provisioning_if_enabled
from routes import shared


def test_lifespan_provisioning_skips_when_env_disabled(monkeypatch):
    monkeypatch.setenv("HORUS_ENABLE_STARTUP_PROVISIONING", "false")
    result = _run_startup_provisioning_if_enabled()
    assert result is None


def test_lifespan_provisioning_runs_when_env_enabled(monkeypatch):
    monkeypatch.setenv("HORUS_ENABLE_STARTUP_PROVISIONING", "true")

    called = []

    def _fake_needed():
        called.append(True)
        return {
            "status": "COMPLETED",
            "total_days": 252,
            "signals_found": 5,
            "target_kind": "TRADING_DAYS",
        }

    monkeypatch.setattr(api, "_run_startup_provisioning_if_needed", _fake_needed)
    result = _run_startup_provisioning_if_enabled()

    assert called == [True]
    assert result is not None
    assert result["status"] == "COMPLETED"


def test_lifespan_ready_state_finalization_with_warning():
    from config.lifespan import _finalize_startup_ready_state

    _finalize_startup_ready_state({"status": "COMPLETED_WITH_WARNINGS"})
    state = shared.get_system_state_snapshot()

    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert "warnings" in state["message"].lower()


def test_lifespan_ready_state_finalization_standard():
    from config.lifespan import _finalize_startup_ready_state

    _finalize_startup_ready_state({"status": "COMPLETED"})
    state = shared.get_system_state_snapshot()

    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert state["message"] == "Horus Terminal Online"
