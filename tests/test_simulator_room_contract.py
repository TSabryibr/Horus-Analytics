from core.settings import settings
import datetime

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from api import app

client = TestClient(app, raise_server_exceptions=False)


def test_stress_endpoint_forwards_ref_date_capital_and_windows(monkeypatch):
    captured = {}

    def _fake_run(index, ref_date=None, initial_capital=None, lookback_days=365, simulation_days=5):
        captured.update(
            {
                "index": index,
                "ref_date": ref_date,
                "initial_capital": initial_capital,
                "lookback_days": lookback_days,
                "simulation_days": simulation_days,
            }
        )
        return {
            "crash_date": "2026-01-02",
            "market_impact": -5.0,
            "worst_affected": [],
            "least_affected": [],
            "full_data": [],
            "estimated_loss_egp": 5000.0,
            "ending_capital": 95000.0,
            "initial_capital": initial_capital,
            "lookback_days": lookback_days,
            "simulation_days": simulation_days,
            "ref_date": ref_date,
        }

    monkeypatch.setattr("routes.analytics.StressTest.run_stress_test", _fake_run)

    res = client.post(
        "/api/v1/stress-test",
        json={
            "index": "EGX70",
            "ref_date": "2026-01-10",
            "initial_capital": 100000,
            "lookback_days": 180,
            "simulation_days": 7,
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert captured == {
        "index": "EGX70",
        "ref_date": "2026-01-10",
        "initial_capital": 100000.0,
        "lookback_days": 180,
        "simulation_days": 7,
    }


def test_stress_test_uses_ref_date_snapshot_and_returns_capital_impact(monkeypatch):
    from core.simulation import StressTest

    dates = pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"])
    prices = pd.DataFrame({"Close": [100.0, 110.0, 120.0, 130.0]}, index=dates)
    returns = pd.DataFrame(
        {
            "AAA": [0.0, -0.05, -0.02, 0.01],
            "AVG_CHANGE": [0.0, -0.05, -0.02, 0.01],
        },
        index=dates,
    )
    captured = {}

    def _fake_find_worst_day(tickers, name="Index", ref_date=None, lookback_days=365):
        captured["lookback_days"] = lookback_days
        captured["ref_date"] = ref_date
        return pd.Timestamp("2026-01-02"), returns

    monkeypatch.setattr("StressTest.find_worst_day", _fake_find_worst_day)
    monkeypatch.setattr("StressTest.MarketLists.get_market_list", lambda _: {"AAA"})
    monkeypatch.setattr("StressTest.DataManager.DataManager.get_stock_data", lambda ticker, include_live=False: prices)

    result = StressTest.run_stress_test(
        "EGX30",
        ref_date="2026-01-03",
        initial_capital=200000,
        lookback_days=120,
        simulation_days=2,
    )

    assert result is not None
    assert result["ref_date"] == "2026-01-03"
    assert result["lookback_days"] == 120
    assert result["simulation_days"] == 2
    assert result["initial_capital"] == 200000.0
    assert result["estimated_loss_egp"] >= 0
    assert result["ending_capital"] <= 200000.0
    assert result["full_data"][0]["Current_Price"] == 120.0  # snapshot at ref_date
    assert result["full_data"][0]["Current_Price_Date"] == "2026-01-03"
    assert captured["lookback_days"] == 120
    assert captured["ref_date"] == datetime.date(2026, 1, 3)


def test_ragnarok_separates_loss_probability_from_threshold_ruin(monkeypatch):
    import core.RagnarokSimulator as ragnarok

    fake_returns = pd.DataFrame({"AAA": [0.01, -0.01, 0.02, -0.03, 0.01, -0.02]})
    monkeypatch.setattr(ragnarok, "_prepare_returns", lambda tickers: fake_returns)

    outcomes = np.zeros((100, 1, 1), dtype=float)
    outcomes[:50, 0, 0] = 0.10   # final = 110
    outcomes[50:80, 0, 0] = -0.20  # final = 80
    outcomes[80:, 0, 0] = -0.60  # final = 40
    monkeypatch.setattr(ragnarok.np.random, "multivariate_normal", lambda mean, cov, size: outcomes)

    result = ragnarok.run_ragnarok_simulation(
        portfolio_tickers=["AAA"],
        iterations=100,
        days=1,
        starting_value=100.0,
        ruin_threshold_pct=50.0,
    )

    assert round(result["loss_probability"], 2) == 50.0
    assert round(result["ruin_probability"], 2) == 20.0
    assert result["ruin_floor"] == 50.0


def test_replay_risk_sizing_caps_shares_by_cash(monkeypatch):
    import core.replay_engine as replay_engine

    class _Portfolio:
        cash_egp = 1000.0

    monkeypatch.setattr(replay_engine, "_get_simulation_portfolio", lambda: _Portfolio())
    monkeypatch.setattr(settings, "calculate_position_size", lambda **kwargs: {"shares": 500})

    trade, reason = replay_engine._build_risk_sized_replay_trade(
        {
            "Ticker": "AAA",
            "Entry_Price": 10,
            "Stop_Loss": 9,
            "Target_Price": 11,
            "Target_Price_2": 12,
        },
        entry_at="2026-05-01T10:00:00",
    )

    assert reason is None
    assert trade is not None
    assert trade["shares"] < 500
    assert trade["shares"] > 0


def test_replay_skips_invalid_entry_stop_geometry():
    import core.replay_engine as replay_engine

    trade, reason = replay_engine._build_risk_sized_replay_trade(
        {
            "Ticker": "AAA",
            "Entry_Price": 10,
            "Stop_Loss": 10.5,
            "Target_Price": 11,
        },
        entry_at="2026-05-01T10:00:00",
    )

    assert trade is None
    assert "geometry" in str(reason)


def test_simulation_backtest_endpoint_returns_metrics_shape(monkeypatch):
    monkeypatch.setattr("routes.analytics.get_price_action_strategy", lambda strategy_id: {"strategy_id": strategy_id})
    monkeypatch.setattr(
        "routes.analytics.run_price_action_backtest",
        lambda **kwargs: {
            "equity_curve": [100000.0, 101500.0],
            "trades": [{"ticker": "AAA", "pnl": 1500.0}],
            "metrics": {
                "total_return": 1.5,
                "max_drawdown": 2.1,
                "profit_factor": 1.3,
                "expectancy": 100.0,
                "win_rate": 60.0,
                "trade_count": 1,
            },
        },
    )

    res = client.post(
        "/api/v1/simulation/backtest",
        json={
            "strategy_id": "ascending_triangle_breakout",
            "market": "EGX30",
            "start_date": "2025-01-01",
            "end_date": "2025-03-01",
            "capital": 100000,
            "commission": 0.05,
            "slippage": 0.1,
        },
    )

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["data"]["strategy_id"] == "ascending_triangle_breakout"
    assert body["data"]["total_return"] == 1.5
    assert body["data"]["trade_count"] == 1
