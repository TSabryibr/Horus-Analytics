import glob

from fastapi.testclient import TestClient

import database
from api import app
import api
from routes import shared


client = TestClient(app, raise_server_exceptions=False)


def test_provisioning_state_model_persists_durable_metadata():
    assert hasattr(database, "ProvisioningState")

    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)

    row = ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=21,
        status="RUNNING",
        mode="AUTOMATIC",
        last_error=None,
    )

    fetched = ProvisioningState.get_by_id(row.id)

    assert fetched.name == "HISTORICAL_SIGNAL_PROVISIONING"
    assert fetched.target_trading_days == 252
    assert fetched.completed_trading_days == 21
    assert fetched.status == "RUNNING"
    assert fetched.mode == "AUTOMATIC"


def test_set_provisioning_state_maps_runtime_state_into_system_state():
    assert hasattr(shared, "set_provisioning_state")

    shared.set_provisioning_state(
        "RUNNING",
        target_trading_days=252,
        completed_trading_days=18,
        message="Provisioning historical signal context.",
    )
    running = shared.get_system_state_snapshot()

    assert running["status"] == "PROVISIONING"
    assert running["bootstrap_complete"] is False
    assert running["provisioning_status"] == "RUNNING"
    assert running["provisioning_target_trading_days"] == 252
    assert running["provisioning_completed_trading_days"] == 18

    shared.set_provisioning_state(
        "COMPLETED_WITH_WARNINGS",
        target_trading_days=252,
        completed_trading_days=200,
        message="Provisioning completed with limited historical coverage.",
    )
    completed = shared.get_system_state_snapshot()

    assert completed["status"] == "READY"
    assert completed["bootstrap_complete"] is True
    assert completed["provisioning_status"] == "COMPLETED_WITH_WARNINGS"
    assert completed["provisioning_target_trading_days"] == 252
    assert completed["provisioning_completed_trading_days"] == 200


def test_hard_reset_clears_provisioning_metadata(monkeypatch):
    assert hasattr(database, "ProvisioningState")

    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=252,
        status="COMPLETED",
        mode="AUTOMATIC",
    )
    assert ProvisioningState.select().count() == 1

    monkeypatch.setattr(glob, "glob", lambda *args, **kwargs: [])

    token = client.get("/api/v1/system/hard-reset/token").json()["token"]
    response = client.post("/api/v1/system/hard-reset", json={"token": token})

    assert response.status_code == 200

    database.initialize_db()
    assert ProvisioningState.select().count() == 0


def test_should_run_startup_provisioning_when_metadata_missing():
    assert api._should_run_startup_provisioning() is True


def test_should_skip_startup_provisioning_when_completed_target_is_met():
    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=252,
        status="COMPLETED",
        mode="AUTOMATIC",
    )

    assert api._should_run_startup_provisioning() is False


def test_should_skip_startup_provisioning_when_completed_with_warnings():
    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=200,
        status="COMPLETED_WITH_WARNINGS",
        mode="AUTOMATIC",
    )

    assert api._should_run_startup_provisioning() is False


def test_should_skip_startup_provisioning_when_error_state():
    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=50,
        status="ERROR",
        mode="AUTOMATIC",
        last_error="Provider failure",
    )

    assert api._should_run_startup_provisioning() is False


def test_should_run_startup_provisioning_when_incomplete():
    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=50,
        status="RUNNING",
        mode="AUTOMATIC",
    )

    assert api._should_run_startup_provisioning() is True


def test_should_skip_startup_provisioning_on_db_exception(monkeypatch):
    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)

    def _raise_error(*args, **kwargs):
        raise RuntimeError("Simulated database read failure")

    monkeypatch.setattr(ProvisioningState, "get_or_none", _raise_error)
    assert api._should_run_startup_provisioning() is False


def test_run_startup_provisioning_if_needed_marks_ready_after_automatic_run(monkeypatch):
    calls = []

    def _fake_run_backfill(days, mode, progress_callback=None):
        calls.append((days, mode))
        return {
            "status": "COMPLETED",
            "total_days": 252,
            "signals_found": 12,
            "target_kind": "TRADING_DAYS",
        }

    monkeypatch.setattr(api, "run_backfill", _fake_run_backfill)

    result = api._run_startup_provisioning_if_needed()

    assert calls == [(252, "AUTOMATIC")]
    assert result["status"] == "COMPLETED"

    state = shared.get_system_state_snapshot()
    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert state["provisioning_status"] == "COMPLETED"
    assert state["provisioning_target_trading_days"] == 252


def test_run_startup_provisioning_if_needed_reuses_persisted_warning_state():
    ProvisioningState = database.ProvisioningState
    database.db.create_tables([ProvisioningState], safe=True)
    ProvisioningState.create(
        target_trading_days=252,
        completed_trading_days=252,
        status="COMPLETED_WITH_WARNINGS",
        mode="AUTOMATIC",
        last_error="Provisioning completed with limited historical coverage.",
    )

    result = api._run_startup_provisioning_if_needed()

    assert result["status"] == "COMPLETED_WITH_WARNINGS"

    state = shared.get_system_state_snapshot()
    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert state["provisioning_status"] == "COMPLETED_WITH_WARNINGS"
    assert state["provisioning_target_trading_days"] == 252
    assert state["provisioning_completed_trading_days"] == 252
    assert state["provisioning_error"] == "Provisioning completed with limited historical coverage."


def test_finalize_startup_ready_state_after_completed_provisioning():
    api._finalize_startup_ready_state(
        {
            "status": "COMPLETED",
            "total_days": 252,
            "signals_found": 12,
            "target_kind": "TRADING_DAYS",
        }
    )

    state = shared.get_system_state_snapshot()
    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert state["progress"] == 100
    assert state["step"] == "Ready"
    assert state["message"] == "Horus Terminal Online"


def test_finalize_startup_ready_state_preserves_warning_completion():
    api._finalize_startup_ready_state(
        {
            "status": "COMPLETED_WITH_WARNINGS",
            "total_days": 200,
            "signals_found": 12,
            "target_kind": "TRADING_DAYS",
            "error": "Provisioning completed with limited historical coverage.",
        }
    )

    state = shared.get_system_state_snapshot()
    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert state["progress"] == 100
    assert state["step"] == "Ready"
    assert state["message"] == "Horus Terminal Online (historical provisioning completed with warnings)"
    assert state["provisioning_status"] == "COMPLETED_WITH_WARNINGS"
    assert state["provisioning_error"] == "Provisioning completed with limited historical coverage."


def test_run_startup_provisioning_if_needed_marks_ready_after_warning_completion(monkeypatch):
    def _fake_run_backfill(days, mode, progress_callback=None):
        return {
            "status": "COMPLETED_WITH_WARNINGS",
            "total_days": 200,
            "signals_found": 12,
            "target_kind": "TRADING_DAYS",
            "error": "Provisioning completed with limited historical coverage.",
        }

    monkeypatch.setattr(api, "run_backfill", _fake_run_backfill)

    result = api._run_startup_provisioning_if_needed()

    assert result["status"] == "COMPLETED_WITH_WARNINGS"

    state = shared.get_system_state_snapshot()
    assert state["status"] == "READY"
    assert state["bootstrap_complete"] is True
    assert state["provisioning_status"] == "COMPLETED_WITH_WARNINGS"
    assert state["provisioning_target_trading_days"] == 252
    assert state["provisioning_completed_trading_days"] == 200
    assert state["provisioning_error"] == "Provisioning completed with limited historical coverage."


def test_run_startup_provisioning_if_needed_marks_error_when_backfill_returns_error(monkeypatch):
    def _fake_run_backfill(days, mode, progress_callback=None):
        return {
            "status": "ERROR",
            "total_days": 10,
            "signals_found": 0,
            "target_kind": "TRADING_DAYS",
            "error": "Provisioning failed for all 10 replay day(s).",
        }

    monkeypatch.setattr(api, "run_backfill", _fake_run_backfill)

    result = api._run_startup_provisioning_if_needed()

    assert result["status"] == "ERROR"

    state = shared.get_system_state_snapshot()
    assert state["status"] == "ERROR"
    assert state["bootstrap_complete"] is False
    assert state["provisioning_status"] == "ERROR"
    assert state["provisioning_target_trading_days"] == 252
    assert state["provisioning_completed_trading_days"] == 10
    assert state["provisioning_error"] == "Provisioning failed for all 10 replay day(s)."


def test_run_startup_provisioning_if_enabled_skips_automatic_backfill(monkeypatch):
    calls = []

    monkeypatch.setattr(
        api,
        "_run_startup_provisioning_if_needed",
        lambda: calls.append("called") or {"status": "COMPLETED"},
    )

    result = api._run_startup_provisioning_if_enabled()

    assert result is None
    assert calls == []
