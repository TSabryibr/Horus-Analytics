"""
PORTFOLIO REMAINING PATHS TESTS
================================
Tests for routes/portfolio.py — genesis protocol, portfolio analysis,
report generation, and additional edge cases not covered in Phase 3.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from api import app
from database import Portfolio, Position, Trade, HorusExecution, SignalExecutionAttribution, SignalRun, SignalRecommendation

client = TestClient(app, raise_server_exceptions=False)


# =============================================================================
# GENESIS PROTOCOL
# =============================================================================

class TestGenesisProtocol:
    """Tests for portfolio initialization (Genesis)."""

    def test_genesis_initialize(self):
        """POST /api/portfolio/genesis should set up a portfolio."""
        p = Portfolio.create(name="Genesis Test", type="USER")
        response = client.post("/api/v1/portfolio/genesis", json={
            "portfolio_id": p.id,
            "egp_balance": 100000,
            "usd_balance": 5000,
            "holdings": [],
        })
        assert response.status_code == 200

    def test_genesis_with_holdings(self, monkeypatch):
        """POST /api/portfolio/genesis with holdings should create positions."""
        monkeypatch.setattr(
            "routes.portfolio.WalkForwardValidation.get_trade_permission",
            lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
        )
        p = Portfolio.create(name="Genesis Holdings Test", type="USER")
        response = client.post("/api/v1/portfolio/genesis", json={
            "portfolio_id": p.id,
            "egp_balance": 50000,
            "usd_balance": 0,
            "holdings": [
                {"ticker": "COMI", "shares": 100, "price": 50.0},
                {"ticker": "FWRY", "shares": 200, "price": 5.0},
            ],
        })
        assert response.status_code == 200

    def test_genesis_rejects_non_positive_portfolio_id(self):
        """POST /api/portfolio/genesis should reject zero/negative portfolio IDs."""
        zero_response = client.post("/api/v1/portfolio/genesis", json={
            "portfolio_id": 0,
            "egp_balance": 100000,
            "usd_balance": 5000,
            "holdings": [],
        })
        negative_response = client.post("/api/v1/portfolio/genesis", json={
            "portfolio_id": -1,
            "egp_balance": 100000,
            "usd_balance": 5000,
            "holdings": [],
        })

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422


# =============================================================================
# PORTFOLIO REPORT
# =============================================================================

class TestPortfolioReport:
    """Tests for portfolio management report generation."""

    def test_get_management_report(self):
        """GET /api/portfolio/management/report should return report."""
        p = Portfolio.create(name="Report Test", type="USER")
        Position.create(
            portfolio=p.id, ticker="COMI", shares=100,
            entry_price=50.0, stop_loss=47.0, target_price=55.0,
            current_price=51.0, status="OPEN", currency="EGP",
        )
        response = client.get(f"/api/v1/portfolio/management/report?portfolio_id={p.id}")
        assert response.status_code == 200
        data = response.json()
        assert "portfolio" in data
        assert "positions" in data

    def test_export_portfolio_report(self):
        """GET /api/portfolio/export should return CSV export when trades exist."""
        p = Portfolio.select().first()
        Trade.create(
            ticker="COMI", shares=100, entry_price=10.0, exit_price=11.0,
            entry_date="2025-01-01", exit_date="2025-01-05",
            pnl=100.0, pnl_pct=10.0, portfolio=p,
        )
        response = client.get("/api/v1/portfolio/export")
        assert response.status_code == 200

    def test_download_portfolio_excel_without_xlsxwriter_dependency(self):
        """GET /api/v1/reports/portfolio/excel should still succeed without xlsxwriter."""
        p = Portfolio.create(name="Excel Report Test", type="USER")
        Position.create(
            portfolio=p.id,
            ticker="COMI",
            shares=100,
            entry_price=50.0,
            stop_loss=47.0,
            target_price=55.0,
            current_price=51.0,
            status="OPEN",
            currency="EGP",
        )
        Trade.create(
            ticker="COMI",
            shares=100,
            entry_price=50.0,
            exit_price=52.0,
            entry_date="2025-01-01",
            exit_date="2025-01-05",
            pnl=200.0,
            pnl_pct=4.0,
            portfolio=p,
        )

        response = client.get(f"/api/v1/reports/portfolio/excel?portfolio_id={p.id}")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert response.content[:2] == b"PK"


# =============================================================================
# PORTFOLIO ANALYSIS
# =============================================================================

class TestPortfolioAnalysis:
    """Tests for portfolio analysis endpoint."""

    def test_get_portfolio_analysis(self):
        """GET /api/portfolio/analysis should return analysis data."""
        response = client.get("/api/v1/portfolio/analysis")
        assert response.status_code == 200

    def test_get_portfolio_analysis_uses_existing_portfolio_when_default_id_missing(self, monkeypatch):
        """GET /api/portfolio/analysis should not hardcode portfolio ID 1."""
        Portfolio.delete().where(Portfolio.id == 1).execute()

        captured = {}

        def fake_analyze_portfolio(portfolio_id):
            captured["portfolio_id"] = portfolio_id
            return {"portfolio_id": portfolio_id, "status": "ok"}

        monkeypatch.setattr("routes.portfolio.PositionTracker.update_live_prices", lambda: None)
        monkeypatch.setattr("routes.portfolio.RiskManager.analyze_portfolio", fake_analyze_portfolio)

        response = client.get("/api/v1/portfolio/analysis")

        assert response.status_code == 200
        assert response.json()["portfolio_id"] == 2
        assert captured["portfolio_id"] == 2

    def test_get_portfolio_balance(self):
        """GET /api/portfolio/balance should return balance data."""
        response = client.get("/api/v1/portfolio/balance")
        assert response.status_code == 200

    def test_get_system_portfolio_comparison_api_alias(self):
        """GET /api/v1/portfolio/system-comparison should expose the frontend route shape."""
        response = client.get("/api/v1/portfolio/system-comparison")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 3
        assert isinstance(data["portfolios"], list)

    def test_get_portfolio_performance_api_alias(self):
        """GET /api/v1/portfolio/performance/{id} should return system performance payload."""
        portfolio = Portfolio.create(name="Perf Alias Test", type="SYSTEM")
        Trade.create(
            ticker="COMI",
            shares=100,
            entry_price=10.0,
            exit_price=11.0,
            entry_date="2025-01-01",
            exit_date="2025-01-03",
            pnl=100.0,
            pnl_pct=10.0,
            portfolio=portfolio,
        )

        response = client.get(f"/api/v1/portfolio/performance/{portfolio.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["portfolio"]["id"] == portfolio.id
        assert data["metrics"]["total_trades"] == 1

    def test_get_execution_history_api_alias(self):
        """GET /api/v1/portfolio/execution-history/{id} should return execution history items."""
        portfolio = Portfolio.create(name="Execution Alias Test", type="SYSTEM")
        execution = HorusExecution.create(
            portfolio=portfolio,
            ticker="COMI",
            state="OPEN",
            trigger_source="INTRADAY",
            planned_entry_price=10.5,
            actual_entry_price=10.6,
            gap_pct=0.95,
            active_stop_loss=9.8,
            active_target_price=11.5,
            details_json='{"note":"ok"}',
            trailing_state='{"armed":true}',
        )

        response = client.get(f"/api/v1/portfolio/execution-history/{portfolio.id}?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == execution.id
        assert data[0]["ticker"] == "COMI"
        assert data[0]["details"]["note"] == "ok"
        assert data[0]["trailing"]["armed"] is True

    def test_list_strategy_portfolios_returns_attached_active_profiles(self):
        strategy_portfolio = Portfolio.create(name="Strategy Atlas", type="STRATEGY", auto_manage=True)
        SignalRun.create(run_date="2026-05-01", scan_type="INTRADAY", run_key="2026-05-01:INTRADAY")
        from database import ScannerStrategyProfile
        ScannerStrategyProfile.create(
            profile_name="Strategy Atlas",
            source_type="PINE",
            script_source='{"plan":"ok"}',
            script_hash="strategy-atlas-hash",
            market="EGX30",
            timeframe="1D",
            profile_state="ACTIVE",
        )

        response = client.get("/api/v1/portfolio/strategies")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] >= 1
        hit = next((row for row in payload["portfolios"] if row["id"] == strategy_portfolio.id), None)
        assert hit is not None
        assert hit["type"] == "STRATEGY"
        assert hit["attached_profiles"][0]["profile_name"] == "Strategy Atlas"

    def test_strategy_performance_and_history_use_attribution(self):
        lane_portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
        strategy_portfolio = Portfolio.create(name="Dual Attribution Strategy", type="STRATEGY", auto_manage=True)
        run = SignalRun.create(run_date="2026-05-02", scan_type="INTRADAY", run_key="2026-05-02:INTRADAY")
        rec = SignalRecommendation.create(
            run=run,
            ticker="COMI",
            side="BUY",
            entry_price=100.0,
            stop_loss=95.0,
            target_price=110.0,
            score=8.0,
            confidence=80.0,
            state="ACTIVE",
        )
        trade = Trade.create(
            portfolio=lane_portfolio,
            ticker="COMI",
            shares=100,
            entry_price=100.0,
            exit_price=110.0,
            entry_date="2026-05-02",
            exit_date="2026-05-03",
            pnl=1000.0,
            pnl_pct=10.0,
            reason="TARGET_1",
        )
        execution = HorusExecution.create(
            portfolio=lane_portfolio,
            run=run,
            recommendation=rec,
            ticker="COMI",
            state="CLOSED",
            trigger_source="INTRADAY",
            planned_entry_price=100.0,
            actual_entry_price=100.2,
            active_stop_loss=95.0,
            active_target_price=110.0,
            trade_id=trade.id,
            details_json='{"note":"attributed"}',
        )
        SignalExecutionAttribution.create(
            execution=execution,
            execution_portfolio=lane_portfolio,
            strategy_portfolio=strategy_portfolio,
            recommendation=rec,
            run=run,
            lane="INTRADAY",
            scan_type="INTRADAY",
            strategy_profile_name="Dual Attribution Strategy",
            strategy_source_type="PINE",
            signal_side="BUY",
            signal_state="CLOSED",
            details_json="{}",
        )

        performance_response = client.get(f"/api/v1/portfolio/strategy-performance/{strategy_portfolio.id}")
        history_response = client.get(f"/api/v1/portfolio/execution-history/{strategy_portfolio.id}?limit=10")

        assert performance_response.status_code == 200
        perf = performance_response.json()
        assert perf["scope"] == "STRATEGY_ATTRIBUTION"
        assert perf["metrics"]["total_trades"] == 1
        assert perf["signal_quality"]["generated_count"] == 1
        assert perf["signal_quality"]["filled_count"] == 1

        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history) == 1
        assert history[0]["execution_portfolio_id"] == lane_portfolio.id
        assert history[0]["strategy_portfolio_id"] == strategy_portfolio.id
        assert history[0]["lane"] == "INTRADAY"

    @pytest.mark.parametrize(("method", "path"), [
        ("GET", "/api/v1/portfolio/export"),
        ("GET", "/api/v1/portfolio/management/report"),
        ("GET", "/api/v1/portfolio/rebalance"),
        ("POST", "/api/v1/portfolio/snapshot"),
        ("GET", "/api/v1/portfolio/analysis"),
        ("GET", "/api/v1/reports/portfolio/excel"),
        ("GET", "/api/v1/reports/portfolio/summary"),
    ])
    def test_endpoints_reject_non_positive_portfolio_id(self, method, path):
        """Portfolio query-style endpoints should reject zero or negative portfolio IDs."""
        zero_response = client.request(method, f"{path}?portfolio_id=0")
        negative_response = client.request(method, f"{path}?portfolio_id=-1")

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422


# =============================================================================
# EDGE CASES
# =============================================================================

class TestPortfolioEdgeCases:
    """Edge cases in portfolio operations."""

    def test_add_trade_missing_ticker_validation(self):
        """POST /api/portfolio/add with missing fields should fail."""
        response = client.post("/api/v1/portfolio/add", json={
            "shares": 100,
            "price": 50.0,
        })
        # FastAPI validation error (422) for missing required field 'ticker'
        assert response.status_code == 422

    def test_add_trade_blank_ticker_validation(self, monkeypatch):
        """POST /api/portfolio/add with blank ticker should fail at request validation."""
        monkeypatch.setattr(
            "routes.portfolio.WalkForwardValidation.get_trade_permission",
            lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("WFA should not be called")),
        )

        response = client.post("/api/v1/portfolio/add", json={
            "ticker": "   ",
            "shares": 100,
            "price": 50.0,
        })

        assert response.status_code == 422

    def test_close_trade_missing_price(self):
        """POST /api/portfolio/close without price should return 400."""
        response = client.post("/api/v1/portfolio/close", json={
            "ticker": "COMI",
        })
        assert response.status_code == 422

    def test_close_trade_negative_price(self):
        """POST /api/portfolio/close with price <= 0 should return 400."""
        response = client.post("/api/v1/portfolio/close", json={
            "ticker": "COMI",
            "price": -1,
        })
        assert response.status_code == 422

    def test_seed_demo_portfolio(self):
        """POST /api/portfolio/seed should seed demo data."""
        p = Portfolio.create(name="Demo Test", type="USER")
        response = client.post(f"/api/v1/portfolio/seed?portfolio_id={p.id}")
        assert response.status_code == 200

    def test_seed_demo_portfolio_rejects_non_positive_portfolio_id(self):
        """POST /api/portfolio/seed should reject zero/negative portfolio IDs."""
        zero_response = client.post("/api/v1/portfolio/seed?portfolio_id=0")
        negative_response = client.post("/api/v1/portfolio/seed?portfolio_id=-1")

        assert zero_response.status_code == 422
        assert negative_response.status_code == 422

    def test_seed_demo_portfolio_missing_portfolio_returns_404(self):
        """POST /api/portfolio/seed should preserve 404 for unknown portfolios."""
        response = client.post("/api/v1/portfolio/seed?portfolio_id=999999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
