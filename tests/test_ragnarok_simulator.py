from core.settings import settings
import pytest
import pandas as pd
import numpy as np

from core import RagnarokSimulator
def test_run_simulation_returns_expected_keys(monkeypatch):
    dates = pd.date_range("2024-01-01", periods=120, freq="B")

    def fake_get_stock_data(ticker, include_live=False):
        np.random.seed(42)
        prices = 100 + np.cumsum(np.random.randn(120) * 0.5)
        return pd.DataFrame(
            {"Close": prices, "Open": prices, "High": prices + 1, "Low": prices - 1, "Volume": [1000] * 120},
            index=dates,
        )

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)
    monkeypatch.setattr(settings, "ACCOUNT_BALANCE", 100_000, raising=False)

    result = RagnarokSimulator.run_ragnarok_simulation(
        portfolio_tickers=["COMI", "FWRY"],
        iterations=100,
        days=10,
    )

    expected_keys = {
        "expected_value",
        "var_95",
        "loss_probability",
        "ruin_probability",
        "ruin_threshold_pct",
        "ruin_floor",
        "starting_value",
        "iterations",
        "days",
        "assets_count",
        "assets_used",
        "weights_used",
    }
    assert expected_keys.issubset(set(result.keys()))
    assert result["iterations"] == 100
    assert result["days"] == 10


def test_run_simulation_raises_on_empty_tickers():
    with pytest.raises(ValueError, match="No tickers"):
        RagnarokSimulator.run_ragnarok_simulation(portfolio_tickers=[], iterations=100, days=10)


def test_run_simulation_raises_on_low_iterations():
    with pytest.raises(ValueError, match="at least 100"):
        RagnarokSimulator.run_ragnarok_simulation(portfolio_tickers=["COMI"], iterations=10, days=10)


def test_prepare_returns_filters_short_series(monkeypatch):
    dates = pd.date_range("2024-01-01", periods=3, freq="B")

    def fake_get_stock_data(ticker, include_live=False):
        return pd.DataFrame(
            {"Close": [10, 11, 12], "Open": [10, 10, 11], "High": [11, 12, 13], "Low": [9, 10, 11], "Volume": [100, 100, 100]},
            index=dates,
        )

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)

    result = RagnarokSimulator._prepare_returns(["COMI"])
    # Only 3 rows → 2 returns after pct_change → <5 threshold → should be empty
    assert result.empty
