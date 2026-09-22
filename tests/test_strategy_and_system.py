"""
STRATEGY & SYSTEM ENDPOINT TESTS
==================================
Tests for routes/strategy.py and routes/system.py — optimization,
backtesting, system status.
"""

from core.settings import settings
import pytest
import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app
from database import Holiday, ProvisioningState, SignalDeskState, SignalRecommendation, SignalRun

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# STRATEGY / OPTIMIZER ENDPOINTS
# =============================================================================

class TestStrategyEndpoints:
    """Tests for strategy optimization and backtesting."""

    def test_optimization_status(self):
        """GET /api/optimizer/status should return optimization state."""
        response = client.get("/api/v1/optimizer/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_start_optimization(self, monkeypatch):
        """POST /api/optimizer/start should start background optimization."""
        monkeypatch.setattr("routes.strategy.background_optimize_task", lambda _index: None)
        response = client.post("/api/v1/optimizer/start", params={"index": "EGX30"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "started" in data
        assert data["index"] == "EGX30"

    def test_start_optimization_invalid_index(self, monkeypatch):
        """POST /api/optimizer/start should reject unsupported index values."""
        monkeypatch.setattr("routes.strategy.background_optimize_task", lambda _index: None)
        response = client.post("/api/v1/optimizer/start", params={"index": "INVALID"})
        assert response.status_code == 400
        assert "Invalid index" in response.json()["detail"]

    def test_apply_optimization_no_params(self):
        """POST /api/strategy/apply with empty params should return error."""
        response = client.post("/api/v1/strategy/apply", json={})
        assert response.status_code == 400
        assert "No params provided" in response.json()["detail"]

    def test_apply_optimization_success(self, monkeypatch):
        """POST /api/strategy/apply should update """
        monkeypatch.setattr(
            "routes.strategy.core_settings.save_settings",
            lambda preset_name: True,
        )
        response = client.post("/api/v1/strategy/apply", json={
            "params": {"SL_PCT": 4.0, "TP1_PCT": 6.0}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "applied"

    def test_apply_optimization_normalizes_lowercase_keys(self, monkeypatch):
        """POST /api/strategy/apply should normalize lowercase param keys."""
        monkeypatch.setattr(
            "routes.strategy.core_settings.save_settings",
            lambda preset_name: True,
        )
        response = client.post("/api/v1/strategy/apply", json={
            "params": {"sl_pct": 4.0, "tp1_pct": 6.0}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2

    def test_apply_optimization_rejects_invalid_rsi_range(self):
        """POST /api/strategy/apply should reject invalid RSI ranges."""
        response = client.post("/api/v1/strategy/apply", json={
            "params": {"RSI_MIN": 90, "RSI_MAX": 80}
        })
        assert response.status_code == 400
        assert "RSI_MIN must be less than RSI_MAX" in response.json()["detail"]

    def test_apply_optimization_rejects_unknown_only_payload(self):
        """POST /api/strategy/apply should fail when no whitelist params are present."""
        response = client.post("/api/v1/strategy/apply", json={
            "params": {"NOT_A_SETTING": 123}
        })
        assert response.status_code == 400
        assert "No valid params provided" in response.json()["detail"]

    def test_apply_optimization_accepts_proposed_settings_payload(self, monkeypatch):
        """POST /api/strategy/apply should accept ExecutionWatchdog proposal payload shape."""
        monkeypatch.setattr(
            "routes.strategy.core_settings.save_settings",
            lambda preset_name: True,
        )
        response = client.post("/api/v1/strategy/apply", json={
            "regime": "BULLISH",
            "changes": [
                {"parameter": "RSI_MIN", "old_value": 55, "new_value": 58, "changed": True}
            ],
            "proposed_settings": {
                "RSI_MIN": 58,
                "SL_PCT": 2.0,
            },
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "applied"
        assert data["count"] >= 1

    def test_apply_optimization_accepts_extended_risk_and_filter_params(self, monkeypatch):
        """POST /api/strategy/apply should normalize and apply expanded risk/filter fields."""
        monkeypatch.setattr(
            "routes.strategy.core_settings.save_settings",
            lambda preset_name: True,
        )
        response = client.post("/api/v1/strategy/apply", json={
            "params": {
                "MIN_SIGNAL_SCORE": 6.5,
                "MIN_SIGNAL_CONFIDENCE": 72.0,
                "MAX_DAILY_TRADES": 4,
                "MAX_PORTFOLIO_HEAT": 7.0,
                "PENDING_ENTRY_MAX_GAP_PCT": 1.2,
                "MAX_PER_SECTOR": 3,
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "applied"
        assert data["count"] == 6

    def test_backtest_simulation_success(self, monkeypatch):
        """POST /api/strategy/backtest should return simulation results."""
        mock_result = {
            "total_return": 15.5,
            "final_value": 115500,
            "trades": [
                {"ticker": "COMI", "pnl": 500, "entry_date": "2025-01-01"},
            ],
            "daily_values": [100000, 100500, 101000],
        }
        monkeypatch.setattr(
            "routes.strategy.PortfolioSimulator.run_simulation",
            lambda **kwargs: mock_result,
        )
        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
            "params": {"SL_PCT": 3.0},
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["config"]["index"] == "EGX30"
        assert data["config"]["capital"] == 100000
        assert "metrics" in data
        assert data["metrics"]["total_return"] == 15.5

    def test_backtest_simulation_error(self, monkeypatch):
        """POST /api/strategy/backtest should return 500 on error."""
        monkeypatch.setattr(
            "routes.strategy.PortfolioSimulator.run_simulation",
            MagicMock(side_effect=Exception("Data loading failed")),
        )
        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
        })
        assert response.status_code == 500
        assert "Data loading failed" in response.json()["detail"]

    def test_backtest_simulation_rejects_invalid_param_ranges(self):
        """POST /api/strategy/backtest should reject invalid RSI ranges."""
        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
            "params": {
                "RSI_MIN": 90,
                "RSI_MAX": 80,
            },
        })
        assert response.status_code == 400
        assert "RSI_MIN must be less than RSI_MAX" in response.json()["detail"]

    def test_backtest_simulation_accepts_extended_risk_and_filter_params(self, monkeypatch):
        """POST /api/strategy/backtest should accept and normalize expanded risk/filter fields."""
        captured_kwargs = {}

        def _mock_run_simulation(**kwargs):
            captured_kwargs.update(kwargs)
            return {
                "total_return": 0.0,
                "final_value": 100000,
                "trades": [],
                "daily_values": [],
            }

        monkeypatch.setattr("routes.strategy.PortfolioSimulator.run_simulation", _mock_run_simulation)
        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
            "commission_pct": 0.15,
            "slippage_pct": 0.10,
            "params": {
                "MIN_SIGNAL_SCORE": 6.5,
                "MIN_SIGNAL_CONFIDENCE": 72.0,
                "MAX_DAILY_TRADES": 4.0,
                "MAX_PORTFOLIO_HEAT": 7.0,
                "PENDING_ENTRY_MAX_GAP_PCT": 1.2,
                "MAX_PER_SECTOR": 3.0,
            },
        })
        assert response.status_code == 200
        params = captured_kwargs.get("params") or {}
        assert params["MIN_SIGNAL_SCORE"] == 6.5
        assert params["MIN_SIGNAL_CONFIDENCE"] == 72.0
        assert params["MAX_DAILY_TRADES"] == 4
        assert params["MAX_PORTFOLIO_HEAT"] == 7.0
        assert params["PENDING_ENTRY_MAX_GAP_PCT"] == 1.2
        assert params["MAX_PER_SECTOR"] == 3

    def test_backtest_simulation_returns_cost_assumptions(self, monkeypatch):
        """POST /api/strategy/backtest should expose execution cost assumptions."""
        mock_result = {
            "total_return": 10.0,
            "final_value": 110000,
            "trades": [],
            "daily_values": [],
        }
        monkeypatch.setattr(
            "routes.strategy.PortfolioSimulator.run_simulation",
            lambda **kwargs: mock_result,
        )
        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
            "params": {"SL_PCT": 2.0},
        })
        assert response.status_code == 200
        data = response.json()
        assert "assumptions" in data
        assert "commission_pct" in data["assumptions"]
        assert "slippage_pct" in data["assumptions"]

    def test_backtest_simulation_passes_cost_assumptions_to_engine(self, monkeypatch):
        """POST /api/strategy/backtest should pass execution costs into simulator params."""
        captured_kwargs = {}

        def _mock_run_simulation(**kwargs):
            captured_kwargs.update(kwargs)
            return {
                "total_return": 0.0,
                "final_value": 100000,
                "trades": [],
                "daily_values": [],
            }

        monkeypatch.setattr("routes.strategy.PortfolioSimulator.run_simulation", _mock_run_simulation)
        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
            "commission_pct": 0.07,
            "slippage_pct": 0.25,
            "params": {"SL_PCT": 2.0},
        })

        assert response.status_code == 200
        params = captured_kwargs.get("params") or {}
        assert params["COMMISSION_PCT"] == 0.07
        assert params["SLIPPAGE_PCT"] == 0.25

    def test_backtest_simulation_uses_stable_default_date_window(self, monkeypatch):
        """POST /api/strategy/backtest should default to simulator baseline start and latest data day."""
        captured_kwargs = {}

        def _mock_run_simulation(**kwargs):
            captured_kwargs.update(kwargs)
            return {
                "total_return": 0.0,
                "final_value": 100000,
                "trades": [],
                "daily_values": [],
            }

        monkeypatch.setattr("routes.strategy.PortfolioSimulator.run_simulation", _mock_run_simulation)
        monkeypatch.setattr("routes.strategy.TimeUtils.now", lambda: datetime.datetime(2026, 5, 17, 12, 0, 0))
        monkeypatch.setattr(
            "routes.strategy.DataManager.get_data_status",
            lambda: {"last_updated": "2026-04-30T16:00:00", "status": "FRESH"},
        )

        response = client.post("/api/v1/strategy/backtest", json={
            "index": "EGX30",
            "capital": 100000,
            "params": {"SL_PCT": 2.0},
        })

        assert response.status_code == 200
        data = response.json()
        assert captured_kwargs["start_date"] == "2025-01-01"
        assert captured_kwargs["end_date"] == "2026-04-30"
        assert data["config"]["start_date"] == "2025-01-01"
        assert data["config"]["end_date"] == "2026-04-30"


# =============================================================================
# SYSTEM STATUS ENDPOINTS
# =============================================================================

class TestSystemEndpoints:
    """Tests for system health and status."""

    def test_system_status(self):
        """GET /api/system/status should return readiness state."""
        response = client.get("/api/v1/system/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_confirm_holiday_revokes_stale_override(self, monkeypatch):
        from routes.shared import is_stale_overridden, set_stale_override

        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {"pipeline_state": "DEGRADED"},
        )
        set_stale_override(True)

        response = client.post(
            "/api/v1/system/confirm-holiday",
            json={"date": "2026-05-28", "description": "Exchange holiday"},
        )

        assert response.status_code == 200
        assert Holiday.select().where(Holiday.date == datetime.date(2026, 5, 28)).exists()
        assert is_stale_overridden() is False

    def test_holiday_admin_bulk_list_and_delete(self, monkeypatch):
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {"pipeline_state": "DEGRADED"},
        )

        save_response = client.post(
            "/api/v1/system/holidays",
            json={
                "holidays": [
                    {"date": "2026-06-16", "description": "Eid al-Adha"},
                    {"date": "2026-07-23", "description": "Revolution Day"},
                ],
            },
        )
        assert save_response.status_code == 200
        assert save_response.json()["count"] == 2

        list_response = client.get("/api/v1/system/holidays?start_date=2026-01-01&end_date=2026-12-31")
        assert list_response.status_code == 200
        listed = list_response.json()["holidays"]
        assert [row["date"] for row in listed] == ["2026-06-16", "2026-07-23"]

        delete_response = client.delete("/api/v1/system/holidays/2026-06-16")
        assert delete_response.status_code == 200
        assert delete_response.json()["deleted"] == 1
        assert not Holiday.select().where(Holiday.date == datetime.date(2026, 6, 16)).exists()

    def test_boot_system_status_returns_lightweight_startup_payload(self, monkeypatch):
        """GET /api/system/boot-status should avoid heavyweight full-status diagnostics."""
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "Pipeline warm and ready.",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "stale_mode": False,
                "freshness": {
                    "overall_ok": True,
                    "market_open": True,
                    "checked_at": "2026-03-31T12:00:00",
                },
                "sync_worker": {
                    "enabled": True,
                    "running": True,
                    "syncing": False,
                    "pipeline_state": "FRESH",
                },
            },
        )
        monkeypatch.setattr(
            "routes.system.get_durable_provisioning_state",
            lambda: {"provisioning_status": "IDLE"},
        )
        monkeypatch.setattr(
            "routes.system.db",
            MagicMock(connect=lambda reuse_if_open=True: None),
            raising=False,
        )
        monkeypatch.setattr(
            "routes.system.scheduler",
            type("FakeScheduler", (), {"running": True})(),
            raising=False,
        )
        monkeypatch.setattr(
            "routes.system.get_data_status_logic",
            lambda: (_ for _ in ()).throw(AssertionError("boot-status should not call get_data_status_logic")),
            raising=False,
        )

        response = client.get("/api/v1/system/boot-status")

        assert response.status_code == 200
        data = response.json()
        assert data["system_ready"] is True
        assert data["pipeline_state"] == "FRESH"
        assert data["db_connected"] is True
        assert data["scheduler"] == {"running": True}
        assert data["telegram"]["enabled"] == bool(data["telegram"]["enabled"])
        assert "data_status" not in data
        assert "metrics" not in data

    def test_full_system_status(self):
        """GET /api/system/full-status should return comprehensive report."""
        response = client.get("/api/v1/system/full-status")
        assert response.status_code == 200
        data = response.json()
        # Validate structure
        assert "system_ready" in data
        assert "db_connected" in data
        assert "scheduler" in data
        assert "telegram" in data
        assert "signal_desk" in data
        assert "metrics" in data
        assert "timestamp" in data

    def test_boot_system_status_includes_signal_desk_summary(self):
        intraday_run = SignalRun.create(status="COMPLETED", scan_type="INTRADAY")
        daily_run = SignalRun.create(status="COMPLETED", scan_type="DAILY")
        SignalRecommendation.create(
            run=intraday_run,
            ticker="COMI",
            side="BUY",
            entry_price=82,
            stop_loss=79,
            target_price=87,
            score=8,
            confidence=81,
            horizon_days=1,
            state="ACTIVE",
        )
        SignalRecommendation.create(
            run=daily_run,
            ticker="HRHO",
            side="BUY",
            entry_price=24,
            stop_loss=22,
            target_price=28,
            score=7,
            confidence=73,
            horizon_days=5,
            state="ACTIVE",
        )
        SignalDeskState.create(
            name="PRIMARY",
            operating_mode="AUTOPILOT",
            autopilot_armed=True,
            autopilot_status="COMPLETED",
            last_autopilot_run_id=77,
            last_autopilot_error=None,
            manual_queue_json='{"position":[{"ticker":"SWDY"}]}',
        )

        response = client.get("/api/v1/system/boot-status")

        assert response.status_code == 200
        data = response.json()
        assert data["signal_desk"]["configured"] is True
        assert data["signal_desk"]["operating_mode"] == "AUTOPILOT"
        assert data["signal_desk"]["autopilot_armed"] is True
        assert data["signal_desk"]["autopilot_status"] == "COMPLETED"
        assert data["signal_desk"]["last_autopilot_run_id"] == 77
        assert data["signal_desk"]["queued_candidate_count"] == 3
        assert data["signal_desk"]["lanes"] == {"intraday": 1, "swing": 1, "position": 1}

    def test_system_status_exposes_sync_worker_runtime_fields(self, monkeypatch):
        """GET /api/system/status should expose the worker state used for diagnostics."""
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "System Operational",
                "bootstrap_complete": True,
                "pipeline_state": "SYNCING",
                "stale_mode": True,
                "freshness": {"overall_ok": False},
                "sync_worker": {
                    "enabled": True,
                    "running": True,
                    "syncing": True,
                    "pipeline_state": "SYNCING",
                    "last_heartbeat_at": "2026-03-16T12:00:00",
                    "last_attempt_at": "2026-03-16T11:59:00",
                    "last_success_at": "2026-03-16T11:55:00",
                    "last_failure_at": None,
                    "last_error": None,
                    "fail_count": 1,
                    "next_retry_seconds": 15,
                    "backoff_seconds": 30,
                },
            },
        )

        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_state"] == "SYNCING"
        assert data["stale_mode"] is True
        assert data["sync_worker"]["pipeline_state"] == "SYNCING"
        assert data["sync_worker"]["syncing"] is True
        assert data["sync_worker"]["last_heartbeat_at"] == "2026-03-16T12:00:00"

    def test_full_system_status_includes_sync_worker_runtime_fields(self, monkeypatch):
        """GET /api/system/full-status should include the diagnostic worker fields."""
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "System Operational",
                "bootstrap_complete": True,
                "pipeline_state": "SYNCING",
                "stale_mode": True,
                "freshness": {"overall_ok": False},
                "sync_worker": {
                    "enabled": True,
                    "running": True,
                    "syncing": True,
                    "pipeline_state": "SYNCING",
                    "last_heartbeat_at": "2026-03-16T12:00:00",
                    "last_attempt_at": "2026-03-16T11:59:00",
                    "last_success_at": "2026-03-16T11:55:00",
                    "last_failure_at": None,
                    "last_error": None,
                    "fail_count": 1,
                    "next_retry_seconds": 15,
                    "backoff_seconds": 30,
                },
            },
        )
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

        response = client.get("/api/v1/system/full-status")

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_state"] == "SYNCING"
        assert data["stale_mode"] is True
        assert data["sync_worker"]["pipeline_state"] == "SYNCING"
        assert data["sync_worker"]["syncing"] is True
        assert data["sync_worker"]["last_heartbeat_at"] == "2026-03-16T12:00:00"

    def test_full_system_status_exposes_durable_provisioning_metadata(self, monkeypatch):
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
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "System Operational",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "stale_mode": False,
                "provisioning_status": "COMPLETED_WITH_WARNINGS",
                "provisioning_target_trading_days": 252,
                "provisioning_completed_trading_days": 200,
                "freshness": {"overall_ok": True},
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": "FRESH",
                },
            },
        )
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

        response = client.get("/api/v1/system/full-status")

        assert response.status_code == 200
        data = response.json()
        assert data["provisioning_status"] == "COMPLETED_WITH_WARNINGS"
        assert data["last_backfill_status"] == "COMPLETED_WITH_WARNINGS"
        assert data["last_backfill_error"] == "Provisioning completed with limited historical coverage."
        assert data["last_backfill_mode"] == "AUTOMATIC"
        assert data["last_backfill_started_at"] == "2026-03-20T08:00:00"
        assert data["last_backfill_completed_at"] == "2026-03-24T09:30:00"

    def test_full_system_status_separates_runtime_provisioning_from_last_manual_backfill(self, monkeypatch):
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
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "System Operational",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "stale_mode": False,
                "provisioning_status": "IDLE",
                "provisioning_target_trading_days": 0,
                "provisioning_completed_trading_days": 0,
                "provisioning_error": None,
                "freshness": {"overall_ok": True},
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": "FRESH",
                },
            },
        )
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

        response = client.get("/api/v1/system/full-status")

        assert response.status_code == 200
        data = response.json()
        assert data["provisioning_status"] == "IDLE"
        assert data["provisioning_target_trading_days"] == 0
        assert data["provisioning_completed_trading_days"] == 0
        assert data["last_backfill_status"] == "COMPLETED"
        assert data["last_backfill_mode"] == "MANUAL"
        assert data["last_backfill_started_at"] == "2026-03-20T08:00:00"
        assert data["last_backfill_completed_at"] == "2026-03-24T09:30:00"

    def test_full_system_status_preserves_runtime_provisioning_error_without_durable_row(self, monkeypatch):
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "ERROR",
                "message": "Startup Failed: Historical provisioning failed.",
                "bootstrap_complete": False,
                "pipeline_state": "STARTING",
                "stale_mode": False,
                "provisioning_status": "ERROR",
                "provisioning_target_trading_days": 252,
                "provisioning_completed_trading_days": 10,
                "provisioning_error": "Provisioning failed for all 10 replay day(s).",
                "freshness": {"overall_ok": False},
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": "STARTING",
                },
            },
        )
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

        response = client.get("/api/v1/system/full-status")

        assert response.status_code == 200
        data = response.json()
        assert data["system_ready"] is False
        assert data["pipeline_state"] == "STARTING"
        assert data["provisioning_status"] == "ERROR"
        assert data["provisioning_target_trading_days"] == 252
        assert data["provisioning_completed_trading_days"] == 10
        assert data["provisioning_error"] == "Provisioning failed for all 10 replay day(s)."

    def test_system_status_defaults_sync_worker_enabled_when_worker_mode_active(self, monkeypatch):
        """GET /api/system/status should use the canonical default sync-worker payload."""
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "System Operational",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "freshness": {"overall_ok": True},
                "stale_mode": False,
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": None,
                },
            },
        )

        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_state"] == "FRESH"
        assert data["stale_mode"] is False
        assert data["sync_worker"]["enabled"] is True
        assert data["sync_worker"]["running"] is False
        assert data["sync_worker"]["syncing"] is False
        assert data["sync_worker"]["pipeline_state"] is None

    def test_system_status_preserves_runtime_provisioning_error_without_durable_row(self, monkeypatch):
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "ERROR",
                "message": "Startup Failed: Historical provisioning failed.",
                "bootstrap_complete": False,
                "pipeline_state": "STARTING",
                "stale_mode": False,
                "provisioning_status": "ERROR",
                "provisioning_target_trading_days": 252,
                "provisioning_completed_trading_days": 10,
                "provisioning_error": "Provisioning failed for all 10 replay day(s).",
                "freshness": {"overall_ok": False},
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": "STARTING",
                },
            },
        )

        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ERROR"
        assert data["pipeline_state"] == "STARTING"
        assert data["provisioning_status"] == "ERROR"
        assert data["provisioning_target_trading_days"] == 252
        assert data["provisioning_completed_trading_days"] == 10
        assert data["provisioning_error"] == "Provisioning failed for all 10 replay day(s)."

    def test_full_system_status_defaults_sync_worker_enabled_when_worker_mode_active(self, monkeypatch):
        """GET /api/system/full-status should preserve the canonical default sync-worker payload."""
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "System Operational",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "freshness": {"overall_ok": True},
                "stale_mode": False,
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": None,
                },
            },
        )
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

        response = client.get("/api/v1/system/full-status")

        assert response.status_code == 200
        data = response.json()
        assert data["pipeline_state"] == "FRESH"
        assert data["stale_mode"] is False
        assert data["sync_worker"]["enabled"] is True
        assert data["sync_worker"]["running"] is False
        assert data["sync_worker"]["syncing"] is False
        assert data["sync_worker"]["pipeline_state"] is None

    def test_system_status_uses_canonical_pipeline_snapshot(self, monkeypatch):
        """GET /api/system/status should reuse the canonical pipeline snapshot."""
        monkeypatch.setattr(
            "routes.system.get_system_state_snapshot",
            lambda: {
                "status": "READY",
                "message": "Raw state",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "freshness": {"overall_ok": True},
            },
            raising=False,
        )
        monkeypatch.setattr("routes.system.read_worker_state", lambda: {}, raising=False)
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "Canonical state",
                "bootstrap_complete": True,
                "pipeline_state": "DEGRADED",
                "stale_mode": True,
                "freshness": {"overall_ok": False},
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": "DEGRADED",
                    "next_retry_seconds": 30,
                },
            },
            raising=False,
        )

        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Canonical state"
        assert data["pipeline_state"] == "DEGRADED"
        assert data["stale_mode"] is True
        assert data["sync_worker"]["pipeline_state"] == "DEGRADED"

    def test_full_system_status_uses_canonical_pipeline_snapshot(self, monkeypatch):
        """GET /api/system/full-status should reuse the canonical pipeline snapshot."""
        monkeypatch.setattr(
            "routes.system.get_system_state_snapshot",
            lambda: {
                "status": "READY",
                "message": "Raw state",
                "bootstrap_complete": True,
                "pipeline_state": "FRESH",
                "freshness": {"overall_ok": True},
            },
            raising=False,
        )
        monkeypatch.setattr("routes.system.read_worker_state", lambda: {}, raising=False)
        monkeypatch.setattr(
            "routes.system.refresh_pipeline_state",
            lambda force=False: {
                "status": "READY",
                "message": "Canonical state",
                "bootstrap_complete": True,
                "pipeline_state": "DEGRADED",
                "stale_mode": True,
                "freshness": {"overall_ok": False},
                "sync_worker": {
                    "enabled": True,
                    "running": False,
                    "syncing": False,
                    "pipeline_state": "DEGRADED",
                    "next_retry_seconds": 30,
                },
            },
            raising=False,
        )
        monkeypatch.setattr("routes.data.evaluate_freshness", lambda **kw: {"status": "OK"})
        monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

        response = client.get("/api/v1/system/full-status")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Canonical state"
        assert data["pipeline_state"] == "DEGRADED"
        assert data["stale_mode"] is True
        assert data["sync_worker"]["pipeline_state"] == "DEGRADED"
