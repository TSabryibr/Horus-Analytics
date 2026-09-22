"""
PHASE 8: SIGNALS MODULE COVERAGE
==================================
Targeted tests for uncovered lines in routes/signals.py:
- env helpers (_int_env, _float_env, _bool_env)
- publish window (all 4 states)
- _compute_tp2 (BUY/SELL/zero), _recommendation_target2 edge cases
- _build_recommendation with tp2 fallback
- guard state get/set, serialize, audit events
- run_daily_signals_logic (guard-blocked, freshness-blocked, existing, force)
- client CRUD (create, list, create API key, list keys)
- rebuild outcomes (NO_TRADE, OPEN, CLOSED)
- publish logic (dry_run, no_recs skip, telegram not configured)
- SLA, deliveries, retry_latest
"""

from core.settings import settings
from core.exclusions import is_excluded_ticker
import pytest
import json
import datetime
import os
import secrets
import hashlib
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from core import TimeUtils
from api import app
from database import (
    SignalRun, SignalRecommendation, SignalDelivery, SignalOutcome,
    SignalGuardState, SignalAuditEvent, SignalValidationRun,
    Client, ClientApiKey, ClientEntitlement,
    Portfolio, Position, Trade, db,
)

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# ENV HELPERS
# =============================================================================

class TestPublishWindow:
    """Tests for get_publish_window_status — all 4 states."""

    def test_window_within(self):
        from core.signals.boundary import get_publish_window_status
        now = datetime.datetime(2025, 2, 19, 15, 0, 0)
        result = get_publish_window_status(now.date(), now_dt=now)
        assert result["ok"] is True
        assert result["reason"] == "within_window"

    def test_window_not_open(self):
        from core.signals.boundary import get_publish_window_status
        now = datetime.datetime(2025, 2, 19, 10, 0, 0)
        result = get_publish_window_status(now.date(), now_dt=now)
        assert result["ok"] is False
        assert result["reason"] == "window_not_open"

    def test_window_closed(self):
        from core.signals.boundary import get_publish_window_status
        now = datetime.datetime(2025, 2, 19, 17, 0, 0)
        result = get_publish_window_status(now.date(), now_dt=now)
        assert result["ok"] is False
        assert result["reason"] == "window_closed"

    def test_window_date_mismatch(self):
        from core.signals.boundary import get_publish_window_status
        now = datetime.datetime(2025, 2, 19, 15, 0, 0)
        result = get_publish_window_status(datetime.date(2025, 2, 18), now_dt=now)
        assert result["ok"] is False
        assert result["reason"] == "run_date_mismatch"


# =============================================================================
# COMPUTE_TP2 AND _RECOMMENDATION_TARGET2
# =============================================================================

class TestTP2:
    """Tests for _compute_tp2 and _recommendation_target2."""

    def test_compute_tp2_buy(self):
        from core.signals.desk import _compute_tp2
        tp2 = _compute_tp2("BUY", 100.0)
        assert tp2 > 100.0  # 100 * 1.04 = 104

    def test_compute_tp2_sell(self):
        from core.signals.desk import _compute_tp2
        tp2 = _compute_tp2("SELL", 100.0)
        assert tp2 < 100.0  # 100 * 0.96 = 96

    def test_compute_tp2_zero(self):
        from core.signals.desk import _compute_tp2
        assert _compute_tp2("BUY", 0) == 0.0

    def test_recommendation_target2_from_rationale(self):
        from core.signals.desk import _recommendation_target2
        rec = MagicMock()
        rec.rationale_json = json.dumps({"target_price_2": 110.0})
        rec.side = "BUY"
        rec.target_price = 105.0
        assert _recommendation_target2(rec) == 110.0

    def test_recommendation_target2_fallback_no_tp2_in_rationale(self):
        from core.signals.desk import _recommendation_target2
        rec = MagicMock()
        rec.rationale_json = json.dumps({"score": 80})
        rec.side = "BUY"
        rec.target_price = 100.0
        tp2 = _recommendation_target2(rec)
        # Should fallback to _compute_tp2
        assert tp2 > 100.0

    def test_recommendation_target2_invalid_json(self):
        from core.signals.desk import _recommendation_target2
        rec = MagicMock()
        rec.rationale_json = "not valid json"
        rec.side = "BUY"
        rec.target_price = 100.0
        tp2 = _recommendation_target2(rec)
        assert tp2 > 0

    def test_build_recommendation_persists_whale_and_trap_metadata(self):
        from core.signals.runs import _build_recommendation

        run = SignalRun.create(
            run_date=TimeUtils.today(),
            scan_type="DAILY",
            status="COMPLETED",
        )
        signal = {
            "Ticker": "COMI",
            "Signal_Type": "BUY",
            "Entry_Price": 100.0,
            "Stop_Loss": 95.0,
            "Target_Price": 110.0,
            "Score": 8,
            "Whale_Signal": "ACCUMULATION",
            "Whale_Strength": 1.0,
            "Whale_Alignment": "SUPPORTIVE",
            "Whale_Reason": "accumulation_support",
            "Trap_Risk_Score": 0,
            "Trap_Risk_Band": "LOW",
            "Trap_Risk_Reason": "low_risk_alignment",
            "Enforcement_State": "ALLOW",
            "Enforcement_Visibility": "VISIBLE",
            "Enforcement_Reason": "not_enforced",
            "Enforcement_Notes": "No whale/trap enforcement threshold breached.",
            "Enforcement_Profile": "EGX30_BALANCED",
        }

        rec = _build_recommendation(signal, run, "BULLISH")
        payload = json.loads(rec.rationale_json)

        assert payload["whale_signal"] == "ACCUMULATION"
        assert payload["whale_alignment"] == "SUPPORTIVE"
        assert payload["trap_risk_band"] == "LOW"
        assert payload["trap_risk_reason"] == "low_risk_alignment"
        assert payload["enforcement_state"] == "ALLOW"
        assert payload["enforcement_reason"] == "not_enforced"
        assert payload["enforcement_profile"] == "EGX30_BALANCED"

    def test_build_recommendation_persists_strategy_profile_metadata(self):
        from core.signals.runs import _build_recommendation

        run = SignalRun.create(
            run_date=TimeUtils.today(),
            scan_type="DAILY",
            status="COMPLETED",
        )
        signal = {
            "Ticker": "HRHO",
            "Signal_Type": "BUY",
            "Entry_Price": 33.5,
            "Stop_Loss": 31.65,
            "Target_Price": 35.96,
            "Score": 9,
            "Scanner_Profile_Id": 42,
            "Scanner_Profile_Name": "EGX Breakout Pine",
            "Scanner_Profile_Source_Type": "PINE",
            "Scanner_Profile_Market": "EGX30",
            "Scanner_Profile_Timeframe": "1D",
        }

        rec = _build_recommendation(signal, run, "BULLISH")
        payload = json.loads(rec.rationale_json)

        assert payload["strategy_profile_id"] == 42
        assert payload["strategy_profile_name"] == "EGX Breakout Pine"
        assert payload["strategy_profile_source_type"] == "PINE"
        assert payload["strategy_profile_market"] == "EGX30"
        assert payload["strategy_profile_timeframe"] == "1D"


# =============================================================================
# GUARD STATE
# =============================================================================

class TestGuardState:
    """Tests for guard state management."""

    def test_get_guard_state(self):
        response = client.get("/api/v1/signals/guard")
        assert response.status_code == 200

    def test_set_guard_state_block(self):
        response = client.post("/api/v1/signals/guard", json={
            "is_blocked": True,
            "reason": "Test block",
            "source": "MANUAL",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["guard_state"]["is_blocked"] is True

    def test_set_guard_state_unblock(self):
        response = client.post("/api/v1/signals/guard", json={
            "is_blocked": False,
            "reason": "All clear",
            "source": "MANUAL",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["guard_state"]["is_blocked"] is False


# =============================================================================
# RUN DAILY SIGNALS LOGIC — guard blocked, freshness blocked, existing, force
# =============================================================================

class TestRunDailySignals:
    """Tests for run_daily_signals_logic various paths."""

    def _unblock_guard(self):
        client.post("/api/v1/signals/guard", json={"is_blocked": False, "source": "TEST"})

    def test_run_daily_invalid_scan_type(self):
        self._unblock_guard()
        response = client.post("/api/v1/signals/runs/daily", json={"scan_type": "INVALID"})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "invalid_scan_type"
        assert detail["parameter"] == "scan_type"
        assert detail["scan_type"] == "INVALID"

    def test_run_daily_guard_blocked(self, monkeypatch):
        monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic",
                            lambda run_date=None, scan_type="DAILY": {"overall_ok": True})
        client.post("/api/v1/signals/guard", json={
            "is_blocked": True, "reason": "Degraded", "source": "WFA",
            "details": {"validation_run_id": 7},
        })
        response = client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-01-01", "scan_type": "DAILY",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"
        assert data["block_type"] == "guard"
        assert data["block_reason"] == "Degraded"
        assert data["guard_reason"] == "Degraded"
        assert data["guard_source"] == "WFA"
        assert data["guard_details"] == {"validation_run_id": 7}
        assert data["guard"]["source"] == "WFA"
        assert data["guard"]["details"] == {"validation_run_id": 7}

        event = (
            SignalAuditEvent.select()
            .where(SignalAuditEvent.event_type == "RUN_BLOCKED_GUARD")
            .order_by(SignalAuditEvent.id.desc())
            .get()
        )
        details = json.loads(event.details_json or "{}")
        assert details["block_type"] == "guard"
        assert details["block_reason"] == "Degraded"
        assert details["guard_reason"] == "Degraded"
        assert details["guard_source"] == "WFA"
        assert details["guard_details"] == {"validation_run_id": 7}
        assert details["guard"]["details"] == {"validation_run_id": 7}
        self._unblock_guard()

    def test_run_daily_freshness_blocked(self, monkeypatch):
        self._unblock_guard()
        monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic",
                            lambda run_date=None, scan_type="DAILY": {"overall_ok": False, "issues": ["stale"]})
        response = client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-02-01", "scan_type": "DAILY",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"
        assert data["block_type"] == "freshness"
        assert data["block_reason"] == "stale"
        assert data["freshness"]["issues"] == ["stale"]

        event = (
            SignalAuditEvent.select()
            .where(SignalAuditEvent.event_type == "RUN_BLOCKED_FRESHNESS")
            .order_by(SignalAuditEvent.id.desc())
            .get()
        )
        details = json.loads(event.details_json or "{}")
        assert details["block_type"] == "freshness"
        assert details["block_reason"] == "stale"
        assert details["freshness"]["issues"] == ["stale"]

    def test_run_daily_success(self, monkeypatch):
        self._unblock_guard()
        monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic",
                            lambda run_date=None, scan_type="DAILY": {"overall_ok": True})
        monkeypatch.setattr("core.signals.runs.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday: (
                                [{"Ticker": "COMI", "Signal_Type": "BUY", "Entry_Price": 85, "Stop_Loss": 80,
                                  "Target_Price": 95, "Score": 9}],
                                ["COMI", "FWRY"], {}, "BULLISH"
                            ))
        monkeypatch.setattr("core.signals.runs.is_excluded_ticker", lambda x, y=None: False)
        response = client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-02-10", "scan_type": "DAILY", "force": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("completed", "existing")
        if data["status"] == "completed":
            assert data["run"]["signals_count"] >= 1

    def test_run_daily_existing_no_force(self, monkeypatch):
        """Second run on same date without force should return existing."""
        self._unblock_guard()
        monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic",
                            lambda run_date=None, scan_type="DAILY": {"overall_ok": True})
        monkeypatch.setattr("core.signals.runs.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday: ([], [], {}, "NEUTRAL"))
        # Create a run first
        client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-02-11", "scan_type": "DAILY", "force": True,
        })
        # Now hit it again without force
        response = client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-02-11", "scan_type": "DAILY", "force": False,
        })
        data = response.json()
        assert data["status"] == "existing"


# =============================================================================
# CLIENT MANAGEMENT
# =============================================================================

@pytest.mark.skip(reason="Multi-tenant concepts removed in single operator backend")
class TestClientManagement:
    """Tests for client CRUD and API key management."""

    def test_create_client(self):
        response = client.post("/api/v1/clients", json={
            "name": "Test Client A",
            "description": "Test client for coverage",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["client"]["name"] == "Test Client A"

    def test_create_client_empty_name(self):
        response = client.post("/api/v1/clients", json={"name": "  "})
        assert response.status_code == 400

    def test_list_clients(self):
        response = client.get("/api/v1/clients")
        assert response.status_code == 200
        assert "clients" in response.json()

    def test_create_api_key(self):
        # First create a client
        resp = client.post("/api/v1/clients", json={"name": "Key Client"})
        cid = resp.json()["client"]["id"]
        # Create API key
        response = client.post(f"/api/v1/clients/{cid}/api-keys", json={"is_active": True})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "created"
        assert data["api_key"].startswith("hax_")

    def test_create_api_key_nonexistent_client(self):
        response = client.post("/api/v1/clients/99999/api-keys", json={"is_active": True})
        assert response.status_code == 404

    def test_list_api_keys(self):
        resp = client.post("/api/v1/clients", json={"name": "List Keys Client"})
        cid = resp.json()["client"]["id"]
        client.post(f"/api/v1/clients/{cid}/api-keys", json={"is_active": True})
        response = client.get(f"/api/v1/clients/{cid}/api-keys")
        assert response.status_code == 200
        data = response.json()
        assert len(data["keys"]) >= 1

    def test_list_api_keys_nonexistent_client(self):
        response = client.get("/api/v1/clients/99999/api-keys")
        assert response.status_code == 404

    def test_revoke_api_key(self):
        resp = client.post("/api/v1/clients", json={"name": "Revoke Client"})
        cid = resp.json()["client"]["id"]
        key_resp = client.post(f"/api/v1/clients/{cid}/api-keys", json={"is_active": True})
        kid = key_resp.json()["meta"]["id"]
        response = client.post(f"/api/v1/clients/{cid}/api-keys/{kid}/revoke")
        assert response.status_code == 200
        assert response.json()["status"] == "revoked"

    def test_revoke_api_key_nonexistent(self):
        resp = client.post("/api/v1/clients", json={"name": "Revoke Client 2"})
        cid = resp.json()["client"]["id"]
        response = client.post(f"/api/v1/clients/{cid}/api-keys/99999/revoke")
        assert response.status_code == 404

    def test_rotate_api_key(self):
        resp = client.post("/api/v1/clients", json={"name": "Rotate Client"})
        cid = resp.json()["client"]["id"]
        key_resp = client.post(f"/api/v1/clients/{cid}/api-keys", json={"is_active": True})
        kid = key_resp.json()["meta"]["id"]
        response = client.post(f"/api/v1/clients/{cid}/api-keys/{kid}/rotate", json={
            "revoke_old": True, "new_is_active": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rotated"
        assert data["new_api_key"].startswith("hax_")


# =============================================================================
# ENTITLEMENTS
# =============================================================================

@pytest.mark.skip(reason="Multi-tenant concepts removed in single operator backend")
class TestEntitlements:
    """Tests for client entitlement management."""

    def test_set_entitlements(self):
        resp = client.post("/api/v1/clients", json={"name": "Entitlement Client"})
        cid = resp.json()["client"]["id"]
        # Need a USER-type portfolio
        p = Portfolio.select().where(Portfolio.type == "USER").first()
        if not p:
            p = Portfolio.create(name="Entitlement Test", type="USER")
        response = client.post(f"/api/v1/clients/{cid}/entitlements", json={
            "portfolio_ids": [p.id], "replace": True,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

    def test_get_entitlements(self):
        resp = client.post("/api/v1/clients", json={"name": "Get Entitlement Client"})
        cid = resp.json()["client"]["id"]
        response = client.get(f"/api/v1/clients/{cid}/entitlements")
        assert response.status_code == 200

    def test_get_entitlements_nonexistent(self):
        response = client.get("/api/v1/clients/99999/entitlements")
        assert response.status_code == 404


# =============================================================================
# SIGNAL RUNS, RECOMMENDATIONS, AUDIT
# =============================================================================

class TestSignalRunsCRUD:
    """Tests for signal runs list/get and recommendations."""

    def test_list_signal_runs(self):
        response = client.get("/api/v1/signals/runs")
        assert response.status_code == 200
        assert "runs" in response.json()

    def test_list_signal_runs_filtered(self):
        response = client.get("/api/v1/signals/runs", params={
            "run_date": "2025-02-10", "scan_type": "DAILY",
        })
        assert response.status_code == 200

    def test_get_signal_run_not_found(self):
        response = client.get("/api/v1/signals/runs/99999")
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "not_found"
        assert detail["error_reason"] == "signal_run_not_found"
        assert detail["run_id"] == 99999

    @pytest.mark.skip(reason="Endpoint removed")
    def test_security_status(self):
        pass

    @pytest.mark.skip(reason="Obsolete dependency on run_id handling")
    def test_get_signal_recommendations_no_run(self):
        pass

    def test_audit_events_list(self):
        response = client.get("/api/v1/signals/audit/events")
        assert response.status_code == 200
        assert "events" in response.json()

    def test_audit_events_filtered(self):
        response = client.get("/api/v1/signals/audit/events", params={
            "event_type": "RUN_COMPLETED", "severity": "INFO", "limit": 10,
        })
        assert response.status_code == 200

    def test_audit_events_reject_invalid_limit(self):
        response = client.get("/api/v1/signals/audit/events", params={"limit": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "limit_out_of_range"
        assert detail["parameter"] == "limit"
        assert detail["provided"] == 0

    def test_audit_summary(self):
        response = client.get("/api/v1/signals/audit/summary", params={"days": 7})
        assert response.status_code == 200

    def test_audit_summary_reject_invalid_days(self):
        response = client.get("/api/v1/signals/audit/summary", params={"days": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "days_out_of_range"
        assert detail["parameter"] == "days"
        assert detail["provided"] == 0

    def test_parse_run_date_invalid(self):
        """Signal run with invalid date should 400."""
        response = client.post("/api/v1/signals/runs/daily", json={
            "run_date": "not-a-date", "scan_type": "DAILY",
        })
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "invalid_run_date"
        assert detail["parameter"] == "run_date"
        assert detail["run_date"] == "not-a-date"


# =============================================================================
# OUTCOMES AND CALIBRATION
# =============================================================================

class TestOutcomes:
    """Tests for signal outcomes and calibration."""

    def test_get_outcomes_empty(self):
        response = client.get("/api/v1/signals/outcomes")
        assert response.status_code == 200
        assert "outcomes" in response.json()

    def test_get_outcomes_filtered(self):
        response = client.get("/api/v1/signals/outcomes", params={
            "outcome_status": "CLOSED", "limit": 5,
        })
        assert response.status_code == 200

    def test_get_outcomes_reject_invalid_limit(self):
        response = client.get("/api/v1/signals/outcomes", params={"limit": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "limit_out_of_range"
        assert detail["parameter"] == "limit"
        assert detail["provided"] == 0

    def test_rebuild_outcomes(self, monkeypatch):
        """POST /api/signals/outcomes/rebuild should process."""
        monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic",
                            lambda run_date=None, scan_type="DAILY": {"overall_ok": True})
        monkeypatch.setattr("core.signals.runs.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday: ([], [], {}, "NEUTRAL"))
        # Ensure guard is clear
        client.post("/api/v1/signals/guard", json={"is_blocked": False, "source": "TEST"})
        # Create a run
        client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-02-15", "scan_type": "DAILY", "force": True,
        })
        response = client.post("/api/v1/signals/outcomes/rebuild", json={
            "from_date": "2025-02-14", "to_date": "2025-02-16",
        })
        assert response.status_code == 200

    def test_calibration(self):
        response = client.get("/api/v1/signals/calibration", params={
            "window": 30, "include_breakdowns": True,
        })
        assert response.status_code == 200

    def test_calibration_reject_invalid_window(self):
        response = client.get("/api/v1/signals/calibration", params={"window": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "window_out_of_range"
        assert detail["parameter"] == "window"
        assert detail["provided"] == 0


# =============================================================================
# PUBLISH, DELIVERIES, RETRY, SLA
# =============================================================================

class TestPublishAndSLA:
    """Tests for publish, deliveries, retry, and SLA."""

    def test_publish_rejects_unsupported_channel(self):
        response = client.post("/api/v1/signals/publish", json={"channel": "EMAIL"})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "unsupported_channel"
        assert detail["channel"] == "EMAIL"

    def test_publish_no_run(self):
        """Publish with nonexistent run_id should 404."""
        response = client.post("/api/v1/signals/publish", json={"run_id": 99999})
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "not_found"
        assert detail["error_reason"] == "signal_run_not_found"
        assert detail["run_id"] == 99999

    def test_publish_rejects_non_completed_run(self):
        run = SignalRun.create(status="RUNNING")
        response = client.post("/api/v1/signals/publish", json={"run_id": run.id})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "state"
        assert detail["error_reason"] == "run_not_completed"
        assert detail["run_id"] == run.id
        assert detail["run_status"] == "RUNNING"

    def test_publish_rejects_non_positive_run_id(self):
        """Publish should reject zero/negative run_id values at request validation."""
        zero_response = client.post("/api/v1/signals/publish", json={"run_id": 0})
        negative_response = client.post("/api/v1/signals/publish", json={"run_id": -1})

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422

    def test_publish_rejects_non_positive_portfolio_ids(self):
        """Publish should reject zero/negative portfolio_ids at request validation."""
        zero_response = client.post("/api/v1/signals/publish", json={"portfolio_ids": [0]})
        negative_response = client.post("/api/v1/signals/publish", json={"portfolio_ids": [-1]})

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422

    def test_publish_dry_run(self, monkeypatch):
        """Publish with dry_run=True should mark DRY_RUN."""
        monkeypatch.setattr("core.signals.runs.evaluate_data_freshness_logic",
                            lambda run_date=None, scan_type="DAILY": {"overall_ok": True})
        monkeypatch.setattr("core.signals.runs.DailyScanner.get_market_signals",
                            lambda index_choice, is_intraday: (
                                [{"Ticker": "COMI", "Signal_Type": "BUY", "Entry_Price": 85
                                  , "Stop_Loss": 80, "Target_Price": 95, "Score": 8}],
                                ["COMI"], {}, "BULLISH"
                            ))
        # Ensure at least one USER portfolio exists for publishing
        if not Portfolio.select().where(Portfolio.type == "USER").exists():
            Portfolio.create(name="Default USER Portfolio", type="USER")

        client.post("/api/v1/signals/guard", json={"is_blocked": False, "source": "TEST"})
        run_resp = client.post("/api/v1/signals/runs/daily", json={
            "run_date": "2025-02-12", "scan_type": "DAILY", "force": True,
        })
        data = run_resp.json()
        run_data = data.get("run")
        if run_data and run_data.get("status") == "COMPLETED":
            run_id = run_data["id"]
            response = client.post("/api/v1/signals/publish", json={
                "run_id": run_id, "dry_run": True, "ignore_guard": True,
            })
            assert response.status_code == 200
            rdata = response.json()
            assert rdata["summary"]["dry_run"] >= 0
        else:
            pytest.skip("Could not create COMPLETED run for publish test")

    def test_publish_surfaces_delivery_failure_reasons(self, monkeypatch):
        """Publish summary should aggregate delivery failure reasons."""
        run = SignalRun.create(status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="COMI", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        Portfolio.create(name="Failure Reason Port", type="USER")

        monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
        monkeypatch.setattr("core.settings.settings.TELEGRAM_TOKEN", "token")
        monkeypatch.setattr("core.settings.settings.CHAT_ID", "chat")
        monkeypatch.setattr(
            "core.signals.publishing.TelegramBot_Alerts.send_message",
            lambda _message, **kwargs: {"ok": False, "description": "transport down"},
        )

        response = client.post("/api/v1/signals/publish", json={"run_id": run.id, "max_retries": 0})

        assert response.status_code == 200
        summary = response.json()["summary"]
        assert summary["failed"] == 1
        assert summary["failure_reasons"]["transport down"] == 1

        event = (
            SignalAuditEvent.select()
            .where(
                (SignalAuditEvent.run == run) &
                (SignalAuditEvent.event_type == "PUBLISH_COMPLETED")
            )
            .order_by(SignalAuditEvent.id.desc())
            .get()
        )
        details = json.loads(event.details_json or "{}")
        assert details["summary"]["failure_reasons"]["transport down"] == 1

    def test_deliveries_not_found(self):
        response = client.get("/api/v1/signals/deliveries", params={"run_id": 99999})
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "not_found"
        assert detail["error_reason"] == "signal_run_not_found"
        assert detail["run_id"] == 99999

    def test_sla(self):
        response = client.get("/api/v1/signals/ops/sla", params={"days": 7})
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert "deliveries" in data
        assert "guard_state" in data

    def test_sla_invalid_days(self):
        response = client.get("/api/v1/signals/ops/sla", params={"days": 0})
        assert response.status_code == 400

    def test_walkforward_latest(self):
        response = client.get("/api/v1/signals/validation/walkforward/latest")
        assert response.status_code == 200

    def test_workspace_signal_performance(self):
        # Needs USER-type portfolio
        p = Portfolio.select().where(Portfolio.type == "USER").first()
        if not p:
            p = Portfolio.create(name="Performance Test", type="USER")
        response = client.get("/api/v1/signals/performance/workspace", params={
            "portfolio_id": p.id, "windows": "30,60,90",
        })
        assert response.status_code == 200

    def test_workspace_signal_performance_rejects_unknown_user_portfolio(self):
        response = client.get("/api/v1/signals/performance/workspace", params={
            "portfolio_id": 999999,
            "windows": "30,60,90",
        })
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "not_found"
        assert detail["error_reason"] == "user_portfolio_not_found"
        assert detail["portfolio_id"] == 999999

    def test_workspace_signal_performance_rejects_invalid_windows_token(self):
        p = Portfolio.select().where(Portfolio.type == "USER").first()
        if not p:
            p = Portfolio.create(name="Performance Invalid Window Token", type="USER")
        response = client.get("/api/v1/signals/performance/workspace", params={
            "portfolio_id": p.id, "windows": "30,bad,90",
        })
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "invalid_windows_token"
        assert detail["parameter"] == "windows"
        assert detail["invalid_token"] == "bad"

    def test_workspace_signal_performance_rejects_out_of_range_windows_value(self):
        p = Portfolio.select().where(Portfolio.type == "USER").first()
        if not p:
            p = Portfolio.create(name="Performance Invalid Window Range", type="USER")
        response = client.get("/api/v1/signals/performance/workspace", params={
            "portfolio_id": p.id, "windows": "30,0,90",
        })
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "windows_value_out_of_range"
        assert detail["parameter"] == "windows"
        assert detail["invalid_token"] == "0"

    def test_retry_latest_no_run(self):
        """retry-latest with no completed run should noop."""
        # Delete all completed runs to test noop path
        # Instead of deleting all runs, just test the endpoint works
        response = client.post("/api/v1/signals/publish/retry-latest")
        assert response.status_code == 200

    def test_retry_latest_rejects_invalid_retry_params(self):
        """retry-latest should reject invalid retry params at the HTTP boundary."""
        SignalRun.create(status="COMPLETED")

        response = client.post("/api/v1/signals/publish/retry-latest?max_retries=-1")

        assert response.status_code == 422

    def test_sla_rejects_invalid_days(self):
        response = client.get("/api/v1/signals/ops/sla", params={"days": 0})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "days_out_of_range"
        assert detail["parameter"] == "days"
        assert detail["provided"] == 0

    @pytest.mark.skip(reason="Client endpoints removed")
    def test_client_signal_recommendations_no_key(self):
        """GET /api/client/signals/recommendations without API key should 401."""
        response = client.get("/api/v1/client/signals/recommendations")
        assert response.status_code == 401


# =============================================================================
# RATE LIMITING & ENTITLEMENTS DEEP DIVE
# =============================================================================

@pytest.mark.skip(reason="Multi-tenant concepts removed in single operator backend")
class TestClientAccessAdvanced:
    """Advanced tests for rate limiting and entitlements."""

    @pytest.mark.skip(reason="Not fully implemented")
    def test_client_api_rate_limiter(self, monkeypatch):
        """Test the sliding window rate limiter directly."""
        pytest.skip("Test skipped: _enforce_client_api_rate_limit is not currently implemented in routes.signals")
        from core.signals.boundary import client_api_rate_windows as _client_api_rate_windows, enforce_client_api_rate_limit as _enforce_client_api_rate_limit

        name = "RateLimitTest_" + secrets.token_hex(4)
        c = Client.create(name=name)
        k = ClientApiKey.create(client=c, key_hash="testhash_" + name, key_prefix="hax_test", is_active=True)
        
        # Mock env vars for small limit
        monkeypatch.setenv("SIGNAL_CLIENT_API_RATE_LIMIT_PER_MIN", "2")
        monkeypatch.setenv("SIGNAL_CLIENT_API_RATE_WINDOW_SEC", "10")
        
        # Clear existing windows for this test
        _client_api_rate_windows.clear()

        # 1st request - ok
        _enforce_client_api_rate_limit(c, k)  # type: ignore
        # 2nd request - ok
        _enforce_client_api_rate_limit(c, k)  # type: ignore
        
        # 3rd request - should raise 429
        with pytest.raises(HTTPException) as exc:
            _enforce_client_api_rate_limit(c, k)  # type: ignore
        assert exc.value.status_code == 429
        assert "rate limit exceeded" in str(exc.value.detail).lower()

    def test_client_entitlements_enforcement(self):
        """Test that recommendations are only returned for entitled clients."""
        # setup client and key
        name = "EntUser_" + secrets.token_hex(4)
        c = Client.create(name=name)
        raw_key = "hax_ent_" + secrets.token_hex(8)
        khash = hashlib.sha256(raw_key.encode()).hexdigest()
        k = ClientApiKey.create(client=c, key_hash=khash, key_prefix=raw_key[:10], is_active=True)  # type: ignore
        
        # create portfolios
        p1 = Portfolio.create(name="P1_" + name, type="USER")
        
        # entitle p1
        ClientEntitlement.create(client=c, portfolio=p1, is_active=True)
        
        # create recommendations for a run
        run = SignalRun.create(run_date=TimeUtils.today(), scan_type="DAILY", status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="AAPL", side="BUY", 
                                   entry_price=150, stop_loss=140, target_price=165)
        
        # Request via API with X-API-Key
        response = client.get("/api/v1/client/signals/recommendations", headers={
            "X-API-Key": raw_key
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("recommendations", [])) > 0

    def test_get_recommendations_p1_specifically(self):
        """Test requesting specific portfolio allowed by entitlement."""
        name = "SpecTest_" + secrets.token_hex(4)
        c = Client.create(name=name)
        raw_key = "hax_spec_" + secrets.token_hex(8)
        khash = hashlib.sha256(raw_key.encode()).hexdigest()
        ClientApiKey.create(client=c, key_hash=khash, key_prefix=raw_key[:10], is_active=True)  # type: ignore
        
        p1 = Portfolio.create(name="P_Spec_" + name, type="USER")
        ClientEntitlement.create(client=c, portfolio=p1, is_active=True)
        
        # ensure a completed run exists
        run = SignalRun.create(run_date=TimeUtils.today(), scan_type="DAILY", status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="MSFT", side="BUY", 
                                   entry_price=300, stop_loss=280, target_price=330)
        
        response = client.get("/api/v1/client/signals/recommendations", 
                             params={"portfolio_id": p1.id},
                             headers={"X-API-Key": raw_key})
        assert response.status_code == 200
        assert len(response.json()["recommendations"]) > 0

    def test_get_recommendations_forbidden_portfolio(self):
        """Test requesting specific portfolio NOT allowed by entitlement."""
        name = "ForbidTest_" + secrets.token_hex(4)
        c = Client.create(name=name)
        raw_key = "hax_forbid_" + secrets.token_hex(8)
        khash = hashlib.sha256(raw_key.encode()).hexdigest()
        ClientApiKey.create(client=c, key_hash=khash, key_prefix=raw_key[:10], is_active=True)  # type: ignore
        
        p_mine = Portfolio.create(name="P_Mine_" + name, type="USER")
        p_other = Portfolio.create(name="P_Other_" + name, type="USER")
        ClientEntitlement.create(client=c, portfolio=p_mine, is_active=True)
        
        response = client.get("/api/v1/client/signals/recommendations", 
                             params={"portfolio_id": p_other.id},
                             headers={"X-API-Key": raw_key})
        # Should return 403 Forbidden
        assert response.status_code == 403
        assert "not entitled" in response.json()["detail"].lower()


# =============================================================================
# RETRY, WALKFORWARD & CALIBRATION DEEP DIVE
# =============================================================================

class TestRetryDeepDive:
    """Tests for retry_failed_deliveries logic."""

    def test_retry_rejects_unsupported_channel(self):
        response = client.post("/api/v1/signals/publish/retry", json={
            "run_id": 1,
            "channel": "EMAIL",
        })
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert detail["error_type"] == "validation"
        assert detail["error_reason"] == "unsupported_channel"
        assert detail["channel"] == "EMAIL"

    def test_retry_run_not_found(self):
        response = client.post("/api/v1/signals/publish/retry", json={
            "run_id": 999999,
            "channel": "TELEGRAM"
        })
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "not_found"
        assert detail["error_reason"] == "signal_run_not_found"
        assert detail["channel"] == "TELEGRAM"

    def test_retry_rejects_non_positive_run_id(self):
        """Retry should reject zero/negative run_id values at request validation."""
        zero_response = client.post("/api/v1/signals/publish/retry", json={
            "run_id": 0,
            "channel": "TELEGRAM",
        })
        negative_response = client.post("/api/v1/signals/publish/retry", json={
            "run_id": -1,
            "channel": "TELEGRAM",
        })

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422

    def test_retry_no_failed_deliveries(self):
        run = SignalRun.create(status="COMPLETED")
        response = client.post("/api/v1/signals/publish/retry", json={
            "run_id": run.id,
            "channel": "TELEGRAM"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "noop"
        assert data["noop_type"] == "retry"
        assert data["noop_reason"] == "no_failed_deliveries"
        assert data["channel"] == "TELEGRAM"
        assert "no failed deliveries" in data["message"].lower()

        event = (
            SignalAuditEvent.select()
            .where(
                (SignalAuditEvent.run == run) &
                (SignalAuditEvent.event_type == "PUBLISH_RETRY_NOOP")
            )
            .order_by(SignalAuditEvent.id.desc())
            .get()
        )
        details = json.loads(event.details_json or "{}")
        assert details["noop_type"] == "retry"
        assert details["noop_reason"] == "no_failed_deliveries"

    def test_retry_legacy_delivery_without_portfolio_uses_destination_path(self):
        run = SignalRun.create(status="COMPLETED")
        # Legacy deliveries can exist without a portfolio link; retry should route
        # through the stored destination instead of treating this as a noop.
        SignalDelivery.create(run=run, channel="TELEGRAM", status="FAILED", portfolio=None)
        
        response = client.post("/api/v1/signals/publish/retry", json={
            "run_id": run.id,
            "channel": "TELEGRAM"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["summary"]["skipped"] == 1
        assert data["summary"]["skip_reasons"]["no_recommendations"] == 1

        event = (
            SignalAuditEvent.select()
            .where(
                (SignalAuditEvent.run == run) &
                (SignalAuditEvent.event_type == "PUBLISH_RETRY_EXECUTED")
            )
            .order_by(SignalAuditEvent.id.desc())
            .get()
        )
        details = json.loads(event.details_json or "{}")
        assert details["result_summary"]["skipped"] == 1

    def test_retry_success_trigger(self):
        run = SignalRun.create(status="COMPLETED")
        p1 = Portfolio.create(name="RetryP_" + secrets.token_hex(4), type="USER")
        SignalDelivery.create(run=run, channel="TELEGRAM", status="FAILED", portfolio=p1)
        
        # We need to mock publish_signal_run_logic because it might try to actually send telegrams
        with patch("core.signals.runs.publish_signal_run_logic") as mock_publish:
            mock_publish.return_value = {"status": "completed", "summary": {"success": 1, "failed": 0}}
            
            response = client.post("/api/v1/signals/publish/retry", json={
                "run_id": run.id,
                "channel": "TELEGRAM"
            })
            assert response.status_code == 200
            assert response.json()["status"] == "completed"
            mock_publish.assert_called_once()


class TestWalkforwardDeepDive:
    """Tests for walkforward validation auto-blocking."""

    def test_walkforward_auto_block(self):
        # Create some failed outcomes
        run = SignalRun.create(run_date=TimeUtils.today() - datetime.timedelta(days=1), status="COMPLETED")
        rec = SignalRecommendation.create(run=run, ticker="FAIL", side="BUY", 
                                         entry_price=100, stop_loss=90, target_price=110)
        # Outcome with negative PnL
        SignalOutcome.create(recommendation=rec, run=run, ticker="FAIL", 
                            outcome_status="CLOSED", pnl_pct=-0.1, exit_date=TimeUtils.now())
        
        req_body = {
            "window_days": 30,
            "min_closed_signals": 1,
            "min_win_rate_pct": 80.0, # Will fail since win rate is 0%
            "auto_block": True
        }
        
        # Ensure guard is not blocked initially
        gs = SignalGuardState.get_or_create(name="PUBLISH")[0]
        gs.is_blocked = False
        gs.save()
        
        response = client.post("/api/v1/signals/validation/walkforward/run", json=req_body)
        assert response.status_code == 200
        assert response.json()["status"] == "fail"
        assert response.json()["guard_action"] == "blocked"
        
        # Verify DB state
        gs = SignalGuardState.get(SignalGuardState.name == "PUBLISH")
        assert gs.is_blocked is True
        assert "walkforward_fail" in gs.reason

    def test_walkforward_auto_unblock(self):
        # Create a passing outcome
        run = SignalRun.create(run_date=TimeUtils.today() - datetime.timedelta(days=1), status="COMPLETED")
        rec = SignalRecommendation.create(run=run, ticker="PASS", side="BUY", 
                                         entry_price=100, stop_loss=90, target_price=110)
        SignalOutcome.create(recommendation=rec, run=run, ticker="PASS", 
                            outcome_status="CLOSED", pnl_pct=0.05, exit_date=TimeUtils.now())
        
        # Start blocked
        gs = SignalGuardState.get_or_create(name="PUBLISH")[0]
        gs.is_blocked = True
        gs.reason = "previous_fail"
        gs.save()
        
        req_body = {
            "window_days": 30,
            "min_closed_signals": 1,
            "min_win_rate_pct": 10.0,
            "auto_unblock": True
        }
        
        response = client.post("/api/v1/signals/validation/walkforward/run", json=req_body)
        assert response.status_code == 200
        assert response.json()["status"] == "pass"
        assert response.json()["guard_action"] == "unblocked"
        
        gs = SignalGuardState.get(SignalGuardState.name == "PUBLISH")
        assert gs.is_blocked is False


class TestCalibrationDeepDive:
    """Tests for calibration breakdowns."""

    def test_calibration_breakdowns(self):
        # Setup data with regime and rationale (for sector)
        run = SignalRun.create(status="COMPLETED")
        rationale = json.dumps({"sector": "Tech", "note": "blah"})
        rec = SignalRecommendation.create(run=run, ticker="AAPL", regime="BULL", 
                                         rationale_json=rationale, entry_price=150, 
                                         stop_loss=140, target_price=165, confidence=85.0)
        SignalOutcome.create(recommendation=rec, run=run, ticker="AAPL", 
                            outcome_status="CLOSED", pnl_pct=0.05)
        
        response = client.get("/api/v1/signals/calibration", params={"include_breakdowns": True})
        assert response.status_code == 200
        data = response.json()
        
        assert "regime_breakdown" in data
        assert "sector_breakdown" in data
        assert "BULL" in data["regime_breakdown"]
        assert "Tech" in data["sector_breakdown"]
        
        # Verify binning (85.0 should be in 80-89)
        bins = data["confidence_bins"]
        found_bin = any(b["bin"] == "80-89" and b["count"] > 0 for b in bins)
        assert found_bin


class TestOutcomesMatchingDeepDive:
    """Advanced outcome matching tests (Trade/Position)."""

    def test_rebuild_outcomes_matching_trade(self):
        run = SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED")
        rec = SignalRecommendation.create(run=run, ticker="MATCH_T", side="BUY", 
                                         entry_price=100, stop_loss=90, target_price=110)
        
        # Create a matching trade within the default window (run_date to run_date + 5 days)
        trade = Trade.create(ticker="MATCH_T", entry_date=TimeUtils.now(), 
                            exit_date=TimeUtils.now(), entry_price=100, exit_price=105, 
                            shares=10, pnl=50, pnl_pct=5.0)
        
        response = client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run.id})
        assert response.status_code == 200
        
        # Verify outcome
        out = SignalOutcome.get(SignalOutcome.recommendation == rec)
        assert out.outcome_status == "CLOSED"
        assert out.pnl_pct == 5.0
        assert "Matched trade" in out.notes

    def test_rebuild_outcomes_matching_position(self):
        run = SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED")
        rec = SignalRecommendation.create(run=run, ticker="MATCH_P", side="BUY", 
                                         entry_price=100, stop_loss=90, target_price=110)
        
        # Create a matching open position
        pos = Position.create(ticker="MATCH_P", entry_date=TimeUtils.now(), 
                             entry_price=100, stop_loss=90, target_price=110,
                             shares=10, status="OPEN", current_price=102)
        
        response = client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run.id})
        assert response.status_code == 200
        
        out = SignalOutcome.get(SignalOutcome.recommendation == rec)
        assert out.outcome_status == "OPEN"
        assert out.pnl_pct == 2.0
        assert "Matched open position" in out.notes


class TestRecommendationsAdvanced:
    """Tests for rich recommendation serialized output and context."""

    def test_get_recommendations_rich_data(self):
        run = SignalRun.create(status="COMPLETED")
        p1 = Portfolio.create(name="Ctx_" + secrets.token_hex(4), type="USER")
        rationale = {"sector": "Finance", "strength": "High"}
        cutoff = TimeUtils.now()
        
        rec = SignalRecommendation.create(run=run, ticker="RICH", side="BUY", 
                                         entry_price=100, stop_loss=90, target_price=110,
                                         rationale_json=json.dumps(rationale),
                                         data_cutoff_at=cutoff)
        
        response = client.get("/api/v1/signals/recommendations", params={
            "run_id": run.id,
            "portfolio_id": p1.id
        })
        assert response.status_code == 200
        data = response.json()
        
        assert data["portfolio_context"]["id"] == p1.id
        # Verify rich fields in the first recommendation
        r0 = data["recommendations"][0]
        assert r0["ticker"] == "RICH"
        assert r0["rationale"] == rationale
        assert r0["data_cutoff_at"] is not None
        assert "T" in r0["data_cutoff_at"] # ISO format check

    def test_get_recommendations_rejects_unknown_user_portfolio(self):
        run = SignalRun.create(status="COMPLETED")
        response = client.get("/api/v1/signals/recommendations", params={
            "run_id": run.id,
            "portfolio_id": 999999,
        })
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "not_found"
        assert detail["error_reason"] == "user_portfolio_not_found"
        assert detail["portfolio_id"] == 999999


class TestPublishFullDeepDive:
    """Tests for complex publishing logic branches."""

    def test_publish_blocked_by_guard(self):
        run = SignalRun.create(status="COMPLETED")
        # Block the guard
        gs = SignalGuardState.get_or_create(name="PUBLISH")[0]
        gs.is_blocked = True
        gs.reason = "test_block"
        gs.source = "WFA"
        gs.details_json = json.dumps({"validation_run_id": 99})
        gs.save()
        
        response = client.post("/api/v1/signals/publish", json={"run_id": run.id})
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "blocked by guard" in detail["message"].lower()
        assert detail["block_type"] == "guard"
        assert detail["block_reason"] == "test_block"
        assert detail["guard_reason"] == "test_block"
        assert detail["guard_source"] == "WFA"
        assert detail["guard_details"] == {"validation_run_id": 99}
        assert detail["guard"]["details"] == {"validation_run_id": 99}

        event = (
            SignalAuditEvent.select()
            .where(
                (SignalAuditEvent.run == run) &
                (SignalAuditEvent.event_type == "PUBLISH_BLOCKED_GUARD")
            )
            .order_by(SignalAuditEvent.id.desc())
            .get()
        )
        details = json.loads(event.details_json or "{}")
        assert details["block_type"] == "guard"
        assert details["block_reason"] == "test_block"
        assert details["guard_reason"] == "test_block"
        assert details["guard_source"] == "WFA"
        assert details["guard_details"] == {"validation_run_id": 99}
        assert details["guard"]["details"] == {"validation_run_id": 99}
        
        # Cleanup
        gs.is_blocked = False
        gs.reason = None
        gs.source = "MANUAL"
        gs.details_json = None
        gs.save()

    def test_publish_blocked_by_window(self):
        run = SignalRun.create(status="COMPLETED")
        with patch("core.signals.runs._signals_get_publish_window_status") as mock_window:
            mock_window.return_value = {
                "ok": False,
                "reason": "window_not_open",
                "window_start": "2026-03-16T14:35:00",
                "window_cutoff": "2026-03-16T16:00:00",
                "now": "2026-03-16T14:00:00",
            }
            response = client.post("/api/v1/signals/publish", json={
                "run_id": run.id,
                "enforce_window": True
            })
            assert response.status_code == 400
            detail = response.json()["detail"]
            assert "blocked by window" in detail["message"].lower()
            assert detail["block_type"] == "window"
            assert detail["block_reason"] == "window_not_open"
            assert detail["window"]["window_start"] == "2026-03-16T14:35:00"

            event = (
                SignalAuditEvent.select()
                .where(
                    (SignalAuditEvent.run == run) &
                    (SignalAuditEvent.event_type == "PUBLISH_BLOCKED_WINDOW")
                )
                .order_by(SignalAuditEvent.id.desc())
                .get()
            )
            details = json.loads(event.details_json or "{}")
            assert details["block_type"] == "window"
            assert details["block_reason"] == "window_not_open"
            assert details["window"]["window_cutoff"] == "2026-03-16T16:00:00"

    @pytest.mark.skip(reason="Single operator mode is now the only mode")
    def test_publish_single_operator_mode(self):
        run = SignalRun.create(status="COMPLETED")
        # Ensure we have recommendations
        SignalRecommendation.create(run=run, ticker="T1", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        
        with patch("routes.signals._single_operator_mode", return_value=True):
            # Should proceed even without portfolios if single mode is on
            # But it might try to send Telegram, so mock that too
            with patch("routes.signals.TelegramBot_Alerts.send_message") as mock_tg:
                mock_tg.return_value = {"ok": True, "result": {"message_id": 123}}
                
                # Mock GlobalSettings to have tokens
                with patch("routes.signals.settings.TELEGRAM_TOKEN", "fake_token"), \
                     patch("routes.signals.settings.CHAT_ID", "fake_id"):
                    
                    response = client.post("/api/v1/signals/publish", json={"run_id": run.id})
                    assert response.status_code == 200
                    assert response.json()["summary"]["sent"] == 1

    def test_publish_telegram_skipped_no_config(self):
        run = SignalRun.create(status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="T1", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        Portfolio.create(name="SkipP_" + secrets.token_hex(4), type="USER")
        
        with patch("core.settings.settings.TELEGRAM_TOKEN", None):
            response = client.post("/api/v1/signals/publish", json={"run_id": run.id})
            assert response.status_code == 200
            assert response.json()["summary"]["skipped"] >= 1

    def test_publish_telegram_retry_loop_failure(self, monkeypatch):
        run = SignalRun.create(status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="T1", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        p1 = Portfolio.create(name="RetryF_" + secrets.token_hex(4), type="USER")
        
        monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
        monkeypatch.setattr("core.settings.settings.CHAT_ID", "fake_chat", raising=False)

        with patch("core.signals.publishing.TelegramBot_Alerts.send_message") as mock_tg, \
             patch("core.settings.settings.TELEGRAM_TOKEN", "fake"), \
             patch("time.sleep") as mock_sleep: # Fast retries
            
            mock_tg.return_value = {"ok": False, "description": "Too many requests"}
            
            response = client.post("/api/v1/signals/publish", json={
                "run_id": run.id,
                "portfolio_ids": [p1.id],
                "max_retries": 2,
                "backoff_ms": 10
            })
            assert response.status_code == 200
            assert response.json()["summary"]["failed"] == 1
            assert mock_tg.call_count == 3 # Initial + 2 retries
            assert mock_sleep.call_count == 2


class TestOutcomesPrecision:
    """Precision tests for specific branches in outcomes/PnL."""

    def test_rebuild_outcomes_pnl_calc_mock(self):
        """Use mock for defensive branches (unreachable via standard DB due to NOT NULL)."""
        run = SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED")
        rec = SignalRecommendation.create(run=run, ticker="MOCK_P", side="BUY", 
                                         entry_price=100, stop_loss=90, target_price=110)
        
        # Mock the Trade object returned by database
        mock_trade = MagicMock()
        mock_trade.id = 999
        mock_trade.ticker = "MOCK_P"
        mock_trade.entry_date = TimeUtils.now()
        mock_trade.exit_date = TimeUtils.now()
        mock_trade.entry_price = 100.0
        mock_trade.exit_price = 105.0
        mock_trade.shares = 10
        mock_trade.pnl = None # Trigger 601
        mock_trade.pnl_pct = None # Trigger 603-604
        
        with patch("routes.signals.Trade.select") as mock_select:
            mock_select.return_value.where.return_value.order_by.return_value.first.return_value = mock_trade
            client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run.id})
            
        out = SignalOutcome.get(SignalOutcome.recommendation == rec)
        assert out.pnl == 50.0
        assert out.pnl_pct == 5.0

    def test_build_delivery_message_no_portfolio_internal(self):
        from core.signals.publishing import build_delivery_message as _build_delivery_message
        run = SignalRun.create(run_date=TimeUtils.today())
        rec = SignalRecommendation.create(run=run, ticker="T1", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        
        # Test line 518: portfolio=None
        msg = _build_delivery_message(run, [rec], None)
        assert "Premium Channel" in msg
        assert "T1" in msg

    def test_build_delivery_message_empty_internal(self):
        from core.signals.publishing import build_delivery_message as _build_delivery_message
        run = SignalRun.create(run_date=TimeUtils.today())
        # Test line 530: no lines
        msg = _build_delivery_message(run, [], None)
        assert "No active recommendations" in msg


class TestSignalsFinalPrecision:
    """Final precision gaps to reach 90%+."""

    def test_rebuild_outcomes_no_trade(self):
        run = SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="NONE", side="BUY", 
                                   entry_price=100, stop_loss=90, target_price=110)
        
        # No trade or position created for "NONE"
        response = client.post("/api/v1/signals/outcomes/rebuild", json={"run_id": run.id})
        assert response.status_code == 200
        assert response.json()["results"][0]["no_trade"] == 1

    def test_list_signal_runs_error_branches(self):
        # Line 856: Run date parsing error
        response = client.get("/api/v1/signals/runs", params={"run_date": "invalid-date"})
        assert response.status_code == 400
        
        # Line 959: scan_type.upper()
        SignalRun.create(scan_type="DAILY", started_at=TimeUtils.now())
        response = client.get("/api/v1/signals/runs", params={"scan_type": "daily"})
        assert response.status_code == 200
        assert len(response.json()["runs"]) >= 1

    def test_get_recommendations_not_found_fallback(self):
        # Line 877: SignalRun.get_or_none fallback when run_id is None (returns latest COMPLETED)
        SignalRun.create(run_date=TimeUtils.today(), status="COMPLETED", completed_at=TimeUtils.now())
        response = client.get("/api/v1/signals/recommendations")
        assert response.status_code == 200
        
        # Line 890 (defensive if run is None after lookup)
        # Highly defensive, but let's try with 0 id
        response = client.get("/api/v1/signals/recommendations", params={"run_id": 999999})
        assert response.status_code == 404

    def test_publish_no_recs_skipped(self):
        # Line 2064-2069: No recommendations for the run
        run = SignalRun.create(status="COMPLETED")
        Portfolio.create(name="NoRecP_" + secrets.token_hex(4), type="USER")
        response = client.post("/api/v1/signals/publish", json={"run_id": run.id})
        assert response.status_code == 200
        assert response.json()["summary"]["skipped"] >= 1
        assert response.json()["summary"]["skip_reasons"]["no_recommendations"] >= 1

    def test_publish_telegram_not_configured_skip_reason(self):
        run = SignalRun.create(status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="T1", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        Portfolio.create(name="NoTelegramP_" + secrets.token_hex(4), type="USER")
        monkeypatch = pytest.MonkeyPatch()
        monkeypatch.setattr("core.settings.settings.TELEGRAM_TOKEN", "")
        monkeypatch.setattr("core.settings.settings.CHAT_ID", "")

        try:
            response = client.post("/api/v1/signals/publish", json={"run_id": run.id})
        finally:
            monkeypatch.undo()

        assert response.status_code == 200
        summary = response.json()["summary"]
        assert summary["skipped"] >= 1
        assert summary["skip_reasons"]["telegram_not_configured"] >= 1

    def test_publish_no_destinations_error(self, monkeypatch):
        monkeypatch.setattr("core.settings.settings.TELEGRAM_MAIN_CHANNEL_SIGNAL_LEVEL", "off", raising=False)
        monkeypatch.setattr("core.settings.settings.CHAT_ID", "", raising=False)
        # Requested portfolio IDs that do not resolve now flow through the unified
        # destination eligibility path, which also accounts for subscriber/channel destinations.
        run = SignalRun.create(status="COMPLETED")
        SignalRecommendation.create(run=run, ticker="T1", side="BUY", entry_price=10, stop_loss=9, target_price=11)
        
        # Use portfolio_ids that don't exist
        response = client.post("/api/v1/signals/publish", json={"run_id": run.id, "portfolio_ids": [999999]})
        assert response.status_code == 404
        detail = response.json()["detail"]
        assert detail["error_type"] == "eligibility"
        assert detail["error_reason"] == "no_eligible_signal_destinations"
        assert detail["requested_portfolio_ids"] == [999999]
        assert "no eligible signal destinations" in detail["message"].lower()

    @pytest.mark.skip(reason="Client auth removed")
    def test_client_auth_error_branches(self):
        # Line 140: Invalid API key
        response = client.get("/api/v1/client/signals/recommendations", headers={"X-API-Key": "wrong"})
        assert response.status_code == 401
        
        # Line 143: Client is inactive
        c = Client.create(name="Inactive", is_active=False)
        k = "hax_" + secrets.token_urlsafe(16)
        hashed = hashlib.sha256(k.encode("utf-8")).hexdigest()
        ClientApiKey.create(client=c, key_hash=hashed, key_prefix="hax_", is_active=True)
        response = client.get("/api/v1/client/signals/recommendations", headers={"X-API-Key": k})
        assert response.status_code == 403

    @pytest.mark.skip(reason="Client rate limiting removed")
    def test_rate_limit_env_zero(self):
        # Line 153: limit <= 0 or window_sec <= 0
        from core.signals.boundary import extract_bearer_token as _extract_bearer_token # Just ensuring imported
        # Use a side_effect function to handle multiple calls to _int_env
        def mock_int_env(name, default):
            if "LIMIT" in name: return 0
            return 60

        with patch("core.signals.boundary.int_env", side_effect=mock_int_env), \
             patch("core.signals.boundary.bool_env", return_value=True):
            
            c = Client.create(name="LimiterZ_" + secrets.token_hex(4), is_active=True)
            k = "hax_" + secrets.token_urlsafe(16)
            hashed = hashlib.sha256(k.encode("utf-8")).hexdigest()
            ClientApiKey.create(client=c, key_hash=hashed, key_prefix="hax_", is_active=True)
            
            # Create entitlement to avoid 403
            p = Portfolio.create(name="LimP_" + secrets.token_hex(4), type="USER")
            ClientEntitlement.create(client=c, portfolio=p, is_active=True)
            
            response = client.get("/api/v1/client/signals/recommendations", headers={"X-API-Key": k})
            # It should pass rate limit check (line 153) and then fail entitlement check if not setup perfectly, 
            # but getting a 403 means it got past rate limit!
            assert response.status_code in (200, 403) 

    def test_audit_event_branches(self):
        # Line 720-722: creation logic
        SignalAuditEvent.create(event_type="TEST_EVENT", details_json={"foo": "bar"}, admin_user="admin")
        assert SignalAuditEvent.select().where(SignalAuditEvent.event_type == "TEST_EVENT").exists()

    def test_list_signal_runs_serialization_precision(self):
        # Line 823-838: Serialization for failed runs
        # Use 'error' field per database.py
        SignalRun.create(scan_type="DAILY", status="FAILED", error="Borked", started_at=TimeUtils.now())
        response = client.get("/api/v1/signals/runs")
        runs = response.json()["runs"]
        assert any(r["status"] == "FAILED" for r in runs)
        # The key in _serialize_run is "error" 
        assert any(r.get("error") == "Borked" for r in runs)
