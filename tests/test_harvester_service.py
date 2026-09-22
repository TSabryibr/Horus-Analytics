import os
import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api import app
from data_engine.harvester_service import get_service_status, PID_FILE, STATUS_FILE

client = TestClient(app, raise_server_exceptions=False)

@pytest.fixture(autouse=True)
def clean_harvester_files():
    # Remove mock PID and STATUS files before and after tests
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass
    if STATUS_FILE.exists():
        try:
            STATUS_FILE.unlink()
        except OSError:
            pass
    yield
    if PID_FILE.exists():
        try:
            PID_FILE.unlink()
        except OSError:
            pass
    if STATUS_FILE.exists():
        try:
            STATUS_FILE.unlink()
        except OSError:
            pass

def test_get_service_status_stopped():
    status = get_service_status()
    assert status["running"] is False
    assert status["status"] == "stopped"

def test_get_service_status_running():
    # Mock PID_FILE with current python process ID (which is definitely running during tests)
    current_pid = os.getpid()
    PID_FILE.write_text(str(current_pid))
    
    # Mock status metadata
    STATUS_FILE.write_text(json.dumps({
        "status": "idle",
        "last_run_success": True
    }))
    
    status = get_service_status()
    assert status["running"] is True
    assert status["pid"] == current_pid
    assert status["status"] == "idle"
    assert status["last_run_success"] is True

def test_harvester_api_status_endpoint():
    response = client.get("/api/v1/system/harvester/status")
    assert response.status_code == 200
    data = response.json()
    assert data["running"] is False
    assert data["status"] == "stopped"

def test_harvester_api_start_stop_endpoints():
    with patch('data_engine.harvester_service.start_service') as mock_start, \
         patch('data_engine.harvester_service.stop_service') as mock_stop:
         
        # Start
        resp_start = client.post("/api/v1/system/harvester/start")
        assert resp_start.status_code == 200
        assert resp_start.json()["status"] == "success"
        mock_start.assert_called_once()
        
        # Stop
        resp_stop = client.post("/api/v1/system/harvester/stop")
        assert resp_stop.status_code == 200
        assert resp_stop.json()["status"] == "success"
        mock_stop.assert_called_once()
