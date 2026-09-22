from core.settings import settings
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api import app
import time
from pathlib import Path

client = TestClient(app, raise_server_exceptions=False)

def test_apply_params_attribute_injection():
    """POST /api/strategy/apply should not allow overwriting internal module attributes."""
    original_path = settings.SETTINGS_FILE
    
    response = client.post("/api/v1/strategy/apply", json={
        "params": {
            "SETTINGS_FILE": "HACKED_PATH.json",
            "LOOKBACK": 99
        }
    })
    
    assert response.status_code == 200
    # Now it should NOT overwrite SETTINGS_FILE because of the whitelist
    assert settings.SETTINGS_FILE == original_path
    assert settings.LOOKBACK == 99
    assert response.json()["count"] == 1 # Only LOOKBACK applied

def test_backtest_invalid_inputs():
    """POST /api/strategy/backtest should handle invalid capital and params."""
    # Negative capital
    response = client.post("/api/v1/strategy/backtest", json={
        "capital": -1000,
        "index": "EGX30"
    })
    assert response.status_code == 400
    assert "capital must be > 0" in response.json()["detail"]

def test_optimization_concurrency():
    """Starting optimization twice should be handled via the new lock."""
    # Reset state to IDLE just in case
    from routes import shared
    shared.OPTIMIZATION_STATE["status"] = "IDLE"
    
    # Start first (mocked to take some time)
    with patch("core.strategy.optimize.Optimizer.run_optimization_api", lambda *args, **kwargs: time.sleep(1)):
        res1 = client.post("/api/v1/strategy/start", params={"index": "EGX30"})
        assert res1.status_code == 200
        
        # Start second immediately
        res2 = client.post("/api/v1/strategy/start", params={"index": "EGX30"})
        assert res2.status_code == 200
        assert "already running" in res2.json()["message"].lower()

def test_strategy_health_empty_data(monkeypatch, tmp_path):
    """GET /api/strategy/health should handle empty data gracefully."""
    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", tmp_path / "strategy_health_cache.json", raising=False)
    from core.strategy.health_cache import reset_strategy_health_cache
    reset_strategy_health_cache()
    # Mock SignalAccuracyChecker to return empty
    monkeypatch.setattr("core.SignalAccuracyChecker.run_accuracy_check", lambda **kwargs: {'summary': {}})
    
    response = client.get("/api/v1/strategy/health")
    assert response.status_code == 200
    data = response.json()
    assert data["win_rate"] == 0
    assert data["total_signals"] == 0


def test_strategy_health_reuses_short_lived_cache(monkeypatch, tmp_path):
    from core.strategy.health_cache import reset_strategy_health_cache

    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", tmp_path / "strategy_health_cache.json", raising=False)
    reset_strategy_health_cache()
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "60")
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": 3})

    calls = {"count": 0}

    def fake_accuracy_check(**kwargs):
        calls["count"] += 1
        return {"summary": {"win_rate": 51.2, "total_signals": 42, "avg_gain_pct": 3.4}}

    monkeypatch.setattr("core.SignalAccuracyChecker.run_accuracy_check", fake_accuracy_check)

    first = client.get("/api/v1/strategy/health", params={"days": 60})
    second = client.get("/api/v1/strategy/health", params={"days": 60})

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] == 1
    assert first.json() == second.json()


def test_strategy_health_cache_invalidates_when_data_version_changes(monkeypatch, tmp_path):
    from core.strategy.health_cache import reset_strategy_health_cache

    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", tmp_path / "strategy_health_cache.json", raising=False)
    reset_strategy_health_cache()
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "60")
    version = {"value": 5}
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": version["value"]})

    calls = {"count": 0}

    def fake_accuracy_check(**kwargs):
        calls["count"] += 1
        return {"summary": {"win_rate": 60.0, "total_signals": 12, "avg_gain_pct": 1.5}}

    monkeypatch.setattr("core.SignalAccuracyChecker.run_accuracy_check", fake_accuracy_check)

    response_one = client.get("/api/v1/strategy/health", params={"days": 60})
    version["value"] = 6
    response_two = client.get("/api/v1/strategy/health", params={"days": 60})

    assert response_one.status_code == 200
    assert response_two.status_code == 200
    assert calls["count"] == 2


def test_strategy_health_cache_ttl_starts_after_payload_is_built(monkeypatch, tmp_path):
    from core.strategy.health_cache import reset_strategy_health_cache

    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", tmp_path / "strategy_health_cache.json", raising=False)
    reset_strategy_health_cache()
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "5")
    current_time = {"value": 200.0}
    monkeypatch.setattr("routes.strategy.time.time", lambda: current_time["value"])
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": 4})

    calls = {"count": 0}

    def fake_accuracy_check(**kwargs):
        calls["count"] += 1
        current_time["value"] += 6.0
        return {"summary": {"win_rate": 60.0, "total_signals": 12, "avg_gain_pct": 1.5}}

    monkeypatch.setattr("core.SignalAccuracyChecker.run_accuracy_check", fake_accuracy_check)

    first = client.get("/api/v1/strategy/health", params={"days": 60})
    second = client.get("/api/v1/strategy/health", params={"days": 60})

    assert first.status_code == 200
    assert second.status_code == 200
    assert calls["count"] == 1


def test_strategy_health_uses_persisted_disk_cache_on_cold_start(monkeypatch, tmp_path):
    from routes.strategy import (
        reset_strategy_health_cache,
        _persist_strategy_health_cache_to_disk,
        _load_strategy_health_cache_from_disk,
    )

    cache_file = tmp_path / "strategy_health_cache.json"
    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "60")
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": 8})
    reset_strategy_health_cache()

    payload = {
        "win_rate": 57.1,
        "total_signals": 21,
        "avg_gain": 4.4,
        "period_days": 60,
    }
    key = (60, 8, "2026-04-01")
    monkeypatch.setattr("routes.strategy.TimeUtils.today", lambda: __import__("datetime").date(2026, 4, 1))
    monkeypatch.setattr("core.strategy.health_cache.time.time", lambda: 1234.0)

    _persist_strategy_health_cache_to_disk(key=key, payload=payload, timestamp=1234.0)
    reset_strategy_health_cache()
    _load_strategy_health_cache_from_disk()

    monkeypatch.setattr(
        "core.SignalAccuracyChecker.run_accuracy_check",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("should use disk cache before recomputing")),
    )

    response = client.get("/api/v1/strategy/health", params={"days": 60})

    assert response.status_code == 200
    assert response.json() == payload


def test_strategy_health_uses_stale_disk_cache_within_grace_window(monkeypatch, tmp_path):
    from routes.strategy import (
        reset_strategy_health_cache,
        _persist_strategy_health_cache_to_disk,
    )

    cache_file = tmp_path / "strategy_health_cache.json"
    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "5")
    monkeypatch.setenv("STRATEGY_HEALTH_DISK_GRACE_TTL_SEC", "600")
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": 8})
    monkeypatch.setattr("routes.strategy.TimeUtils.today", lambda: __import__("datetime").date(2026, 4, 1))
    reset_strategy_health_cache()

    payload = {
        "win_rate": 57.1,
        "total_signals": 21,
        "avg_gain": 4.4,
        "period_days": 60,
    }
    key = (60, 8, "2026-04-01")
    _persist_strategy_health_cache_to_disk(key=key, payload=payload, timestamp=1000.0)
    reset_strategy_health_cache()
    monkeypatch.setattr("core.strategy.health_cache.time.time", lambda: 1010.0)

    monkeypatch.setattr(
        "core.SignalAccuracyChecker.run_accuracy_check",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("stale disk cache should short-circuit cold-start recompute")),
    )

    response = client.get("/api/v1/strategy/health", params={"days": 60})

    assert response.status_code == 200
    assert response.json() == payload


def test_strategy_health_uses_pipeline_refresh_version_for_disk_cache(monkeypatch, tmp_path):
    from routes.strategy import (
        reset_strategy_health_cache,
        _persist_strategy_health_cache_to_disk,
    )

    cache_file = tmp_path / "strategy_health_cache.json"
    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "5")
    monkeypatch.setenv("STRATEGY_HEALTH_DISK_GRACE_TTL_SEC", "600")
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": 0})
    monkeypatch.setattr("core.pipeline.refresh_pipeline_state", lambda force=False: {"data_version": 8})
    monkeypatch.setattr("routes.strategy.TimeUtils.today", lambda: __import__("datetime").date(2026, 4, 1))
    monkeypatch.setattr("core.strategy.health_cache.time.time", lambda: 1010.0)
    reset_strategy_health_cache()

    payload = {
        "win_rate": 57.1,
        "total_signals": 21,
        "avg_gain": 4.4,
        "period_days": 60,
    }
    key = (60, 8, "2026-04-01")
    _persist_strategy_health_cache_to_disk(key=key, payload=payload, timestamp=1000.0)

    monkeypatch.setattr(
        "core.SignalAccuracyChecker.run_accuracy_check",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("pipeline-refresh data_version should unlock disk cache reuse")),
    )

    response = client.get("/api/v1/strategy/health", params={"days": 60})

    assert response.status_code == 200
    assert response.json() == payload


def test_strategy_health_disk_grace_cache_ignores_cross_process_version_drift(monkeypatch, tmp_path):
    from routes.strategy import (
        reset_strategy_health_cache,
        _persist_strategy_health_cache_to_disk,
    )

    cache_file = tmp_path / "strategy_health_cache.json"
    monkeypatch.setattr("core.strategy.health_cache.STRATEGY_HEALTH_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("STRATEGY_HEALTH_CACHE_TTL_SEC", "5")
    monkeypatch.setenv("STRATEGY_HEALTH_DISK_GRACE_TTL_SEC", "600")
    monkeypatch.setattr("core.strategy.health_cache.shared.get_system_state_snapshot", lambda: {"data_version": 0})
    monkeypatch.setattr("core.pipeline.refresh_pipeline_state", lambda force=False: {"data_version": 1})
    monkeypatch.setattr("routes.strategy.TimeUtils.today", lambda: __import__("datetime").date(2026, 4, 1))
    monkeypatch.setattr("core.strategy.health_cache.time.time", lambda: 1010.0)
    reset_strategy_health_cache()

    payload = {
        "win_rate": 57.1,
        "total_signals": 21,
        "avg_gain": 4.4,
        "period_days": 60,
    }
    _persist_strategy_health_cache_to_disk(key=(60, 8, "2026-04-01"), payload=payload, timestamp=1000.0)

    monkeypatch.setattr(
        "core.SignalAccuracyChecker.run_accuracy_check",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("cross-process version drift should not invalidate disk grace cache")),
    )

    response = client.get("/api/v1/strategy/health", params={"days": 60})

    assert response.status_code == 200
    assert response.json() == payload
