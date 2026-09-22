from __future__ import annotations

import json

import pandas as pd
from fastapi.testclient import TestClient

from api import app
from database import ScannerStrategyProfile

client = TestClient(app, raise_server_exceptions=False)


def _daily_breakout_frame() -> pd.DataFrame:
    index = pd.date_range("2025-01-01", periods=9, freq="D")
    frame = pd.DataFrame(
        [
            {"Open": 10.0, "High": 10.8, "Low": 9.2, "Close": 10.2, "Volume": 1000},
            {"Open": 10.1, "High": 10.9, "Low": 9.4, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 11.0, "Low": 9.6, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.95, "Low": 9.8, "Close": 10.5, "Volume": 1000},
            {"Open": 10.5, "High": 10.98, "Low": 10.0, "Close": 10.6, "Volume": 1000},
            {"Open": 10.6, "High": 11.0, "Low": 10.2, "Close": 10.7, "Volume": 1000},
            {"Open": 10.7, "High": 11.1, "Low": 10.5, "Close": 11.2, "Volume": 2500},
            {"Open": 11.25, "High": 11.4, "Low": 11.1, "Close": 11.3, "Volume": 1800},
            {"Open": 11.3, "High": 13.5, "Low": 11.2, "Close": 13.0, "Volume": 3000},
        ],
        index=index,
    )
    frame.index.name = "Date"
    return frame


def _intraday_reversal_frame() -> pd.DataFrame:
    index = pd.date_range("2026-02-10 10:00", periods=8, freq="5min")
    frame = pd.DataFrame(
        [
            {"Open": 10.5, "High": 10.7, "Low": 10.3, "Close": 10.55, "Volume": 1000},
            {"Open": 10.55, "High": 10.65, "Low": 10.28, "Close": 10.48, "Volume": 1000},
            {"Open": 10.48, "High": 10.58, "Low": 10.24, "Close": 10.4, "Volume": 1000},
            {"Open": 10.4, "High": 10.5, "Low": 10.22, "Close": 10.36, "Volume": 1000},
            {"Open": 10.36, "High": 10.44, "Low": 10.18, "Close": 10.3, "Volume": 1000},
            {"Open": 10.3, "High": 10.48, "Low": 10.26, "Close": 10.46, "Volume": 1700},
            {"Open": 10.46, "High": 10.62, "Low": 10.4, "Close": 10.6, "Volume": 1900},
            {"Open": 10.6, "High": 10.85, "Low": 10.55, "Close": 10.8, "Volume": 2100},
        ],
        index=index,
    )
    frame.index.name = "Date"
    return frame


class TestPriceActionRoutes:
    def test_price_action_catalog_lists_seeded_strategies(self):
        response = client.get("/api/v1/strategy/price-action/catalog")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["count"] >= 1
        assert any(item["strategy_id"] == "ascending_triangle_breakout" for item in body["strategies"])

    def test_price_action_evaluate_returns_signal_preview(self, monkeypatch):
        monkeypatch.setattr("routes.strategy.DataManager.get_stock_data", lambda ticker, include_live=False: _daily_breakout_frame().copy())

        response = client.post(
            "/api/v1/strategy/price-action/evaluate",
            json={
                "ticker": "COMI",
                "family": "SWING",
                "include_warning_only": False,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["ticker"] == "COMI"
        assert body["signal_count"] >= 1
        assert any(signal["strategy_id"] == "ascending_triangle_breakout" for signal in body["signals"])

    def test_price_action_backtest_returns_metrics_and_trades(self, monkeypatch):
        tickers = {"COMI", "HRHO", "ETEL"}
        monkeypatch.setattr("core.price_action.backtest.MarketLists.get_market_list", lambda market: tickers)
        monkeypatch.setattr("core.price_action.backtest.DataManager.get_stock_data", lambda ticker, include_live=False: _daily_breakout_frame().copy())

        response = client.post(
            "/api/v1/strategy/price-action/backtest",
            json={
                "strategy_id": "ascending_triangle_breakout",
                "market": "EGX30",
                "date_from": "2025-01-01",
                "date_to": "2025-01-09",
                "capital": 100000,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["config"]["strategy_id"] == "ascending_triangle_breakout"
        assert body["metrics"]["trade_count"] == 3
        assert body["metrics"]["profit_factor"] > 1.0
        assert len(body["trades"]) == 3

    def test_price_action_backtest_rejects_zero_cost_assumptions(self):
        response = client.post(
            "/api/v1/strategy/price-action/backtest",
            json={
                "strategy_id": "ascending_triangle_breakout",
                "market": "EGX30",
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "capital": 100000,
                "commission_pct": 0.0,
                "slippage_pct": 0.1,
            },
        )

        assert response.status_code == 400
        assert "commission_pct must be > 0" in response.json()["detail"]

    def test_price_action_promote_persists_ready_profile(self, monkeypatch):
        tickers = {f"T{i:03d}" for i in range(35)}
        monkeypatch.setattr("core.price_action.backtest.MarketLists.get_market_list", lambda market: tickers)
        monkeypatch.setattr("core.price_action.backtest.DataManager.get_stock_data", lambda ticker, include_live=False: _daily_breakout_frame().copy())

        response = client.post(
            "/api/v1/strategy/price-action/promote",
            json={
                "profile_name": "EGX Ascending Triangle Pack",
                "strategy_id": "ascending_triangle_breakout",
                "market": "EGX30",
                "date_from": "2025-01-01",
                "date_to": "2025-01-09",
                "capital": 100000,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["source_type"] == "PRICE_ACTION"
        profile = ScannerStrategyProfile.get_by_id(body["profile_id"])
        assert profile.source_type == "PRICE_ACTION"
        saved_payload = json.loads(profile.script_source)
        assert saved_payload["strategy_id"] == "ascending_triangle_breakout"

    def test_price_action_activate_promoted_profile(self, monkeypatch):
        tickers = {f"T{i:03d}" for i in range(35)}
        monkeypatch.setattr("core.price_action.backtest.MarketLists.get_market_list", lambda market: tickers)
        monkeypatch.setattr("core.price_action.backtest.DataManager.get_stock_data", lambda ticker, include_live=False: _daily_breakout_frame().copy())

        promoted = client.post(
            "/api/v1/strategy/price-action/promote",
            json={
                "profile_name": "EGX Ascending Triangle Active",
                "strategy_id": "ascending_triangle_breakout",
                "market": "EGX30",
                "date_from": "2025-01-01",
                "date_to": "2025-01-09",
                "capital": 100000,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
        ).json()

        response = client.post(
            "/api/v1/strategy/price-action/activate-profile",
            json={"profile_id": promoted["profile_id"]},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["profile_state"] == "ACTIVE"
        assert body["source_type"] == "PRICE_ACTION"
        assert body["portfolio"]["name"] == "EGX Ascending Triangle Active"
        assert body["portfolio"]["type"] == "STRATEGY"

    def test_price_action_promote_rejects_profiles_that_fail_gates(self, monkeypatch):
        monkeypatch.setattr("core.price_action.backtest.MarketLists.get_market_list", lambda market: {"COMI"})
        monkeypatch.setattr("core.price_action.backtest.DataManager.get_stock_data", lambda ticker, include_live=False: _daily_breakout_frame().copy())

        response = client.post(
            "/api/v1/strategy/price-action/promote",
            json={
                "profile_name": "Failing EGX Ascending Triangle Pack",
                "strategy_id": "ascending_triangle_breakout",
                "market": "EGX30",
                "date_from": "2025-01-01",
                "date_to": "2025-12-31",
                "capital": 100000,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
        )

        assert response.status_code == 400
        assert "promotion gates" in response.json()["detail"]

    def test_price_action_intraday_backtest_supports_sampled_execution(self, monkeypatch):
        monkeypatch.setattr("core.price_action.backtest.MarketLists.get_market_list", lambda market: {"COMI", "HRHO"})
        monkeypatch.setattr(
            "core.price_action.backtest.DataManager.get_intraday_data",
            lambda ticker, refresh_if_stale=False: _intraday_reversal_frame().copy(),
        )

        response = client.post(
            "/api/v1/strategy/price-action/backtest",
            json={
                "strategy_id": "intraday_trendline_break_reversal",
                "market": "EGX30",
                "date_from": "2026-02-10",
                "date_to": "2026-02-11",
                "capital": 100000,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
                "ticker_limit": 1,
                "max_bars_per_ticker": 8,
                "max_trades": 1,
                "recent_sessions_only": 1,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["execution"]["mode"] == "SAMPLED_INTRADAY"
        assert body["execution"]["ticker_limit"] == 1
        assert body["execution"]["recent_sessions_only"] == 1
        assert body["execution"]["scanned_tickers"] == 1

    def test_price_action_promote_rejects_sampled_intraday_backtests(self, monkeypatch):
        monkeypatch.setattr("core.price_action.backtest.MarketLists.get_market_list", lambda market: {"COMI", "HRHO"})
        monkeypatch.setattr(
            "core.price_action.backtest.DataManager.get_intraday_data",
            lambda ticker, refresh_if_stale=False: _intraday_reversal_frame().copy(),
        )

        response = client.post(
            "/api/v1/strategy/price-action/promote",
            json={
                "profile_name": "Sampled Intraday Trendline Profile",
                "strategy_id": "intraday_trendline_break_reversal",
                "market": "EGX30",
                "date_from": "2026-02-10",
                "date_to": "2026-02-11",
                "capital": 100000,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
                "ticker_limit": 1,
                "max_bars_per_ticker": 8,
                "max_trades": 1,
                "recent_sessions_only": 1,
            },
        )

        assert response.status_code == 400
        assert "Sampled intraday backtests cannot be promoted" in response.json()["detail"]
