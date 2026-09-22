from fastapi.testclient import TestClient

from api import app
from core import TimeUtils
client = TestClient(app, raise_server_exceptions=False)


def test_start_simulation_sets_date():
    try:
        res = client.post("/api/v1/simulate/start", json={"date": "2025-06-15"})
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "active"
        assert body["date"] == "2025-06-15"
        assert TimeUtils.is_simulating() is True
    finally:
        TimeUtils.clear_simulation()


def test_start_simulation_bad_date_returns_400():
    res = client.post("/api/v1/simulate/start", json={"date": "not-a-date"})
    assert res.status_code == 400


def test_start_simulation_missing_date_returns_400():
    res = client.post("/api/v1/simulate/start", json={})
    assert res.status_code == 400


def test_stop_simulation_returns_live():
    # First start, then stop
    client.post("/api/v1/simulate/start", json={"date": "2025-01-01"})
    res = client.post("/api/v1/simulate/stop")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "live"
    assert TimeUtils.is_simulating() is False


def test_simulation_status_when_inactive():
    TimeUtils.clear_simulation()
    res = client.get("/api/v1/simulate/status")
    assert res.status_code == 200
    body = res.json()
    assert body["active"] is False
    assert body["date"] is None


def test_simulation_lifecycle():
    try:
        # Start
        client.post("/api/v1/simulate/start", json={"date": "2025-03-20"})
        status = client.get("/api/v1/simulate/status").json()
        assert status["active"] is True
        assert status["date"] == "2025-03-20"

        # Stop
        client.post("/api/v1/simulate/stop")
        status = client.get("/api/v1/simulate/status").json()
        assert status["active"] is False
        assert status["date"] is None
    finally:
        TimeUtils.clear_simulation()


def test_dryrun_start_forwards_profile_selection(monkeypatch):
    captured = {}

    def _fake_start_dryrun(**kwargs):
        captured.update(kwargs)
        return {"status": "started", "date": kwargs.get("target_date"), "profile_id": kwargs.get("profile_id")}

    monkeypatch.setattr("routes.dryrun.start_dryrun", _fake_start_dryrun)

    res = client.post(
        "/api/v1/dryrun/start",
        json={
            "date": "2026-04-30",
            "notify": False,
            "report": True,
            "ai_report": False,
            "profile_id": 42,
            "use_active_profile": False,
        },
    )

    assert res.status_code == 200
    assert res.json()["profile_id"] == 42
    assert captured["target_date"] == "2026-04-30"
    assert captured["profile_id"] == 42
    assert captured["use_active_profile"] is False
