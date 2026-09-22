from datetime import datetime

import numpy as np
import pandas as pd

from core.analyzers import Helheim
from core import TimeUtils
def _mock_price_df(rows=320, as_string_index=False):
    idx = pd.date_range("2024-01-01", periods=rows, freq="B")
    close = 100 + np.linspace(0, 20, rows) + np.sin(np.arange(rows) / 8.0)
    df = pd.DataFrame({"Close": close}, index=idx)
    if as_string_index:
        df.index = df.index.strftime("%Y-%m-%d")
    return df


def test_analyze_seasonality_invalid_ticker_returns_error():
    res = Helheim.analyze_seasonality("   ")
    assert res["status"] == "error"
    assert "Invalid ticker" in res["message"]


def test_analyze_seasonality_insufficient_data_returns_error(monkeypatch):
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_stock_data",
        lambda _ticker: _mock_price_df(rows=100),
    )
    res = Helheim.analyze_seasonality("COMI")
    assert res["status"] == "error"
    assert "Insufficient Data" in res["message"]


def test_analyze_seasonality_handles_string_index(monkeypatch):
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_stock_data",
        lambda _ticker: _mock_price_df(rows=320, as_string_index=True),
    )
    res = Helheim.analyze_seasonality("comi")
    assert res["status"] == "success"
    assert res["ticker"] == "COMI"
    assert len(res["months"]) > 0
    assert len(res["weekdays"]) > 0
    assert {"best_month", "worst_month", "summary"}.issubset(set(res["verdict"].keys()))


def test_get_market_seasonality_uses_egx30_and_month_label(monkeypatch):
    monkeypatch.setattr("core.market.MarketLists.get_market_list", lambda choice: {"AAA", "BBB"} if choice == "EGX30" else set())
    monkeypatch.setattr(TimeUtils, "now", lambda: datetime(2026, 2, 3))

    def _fake_analyze(ticker):
        months = [
            {"label": "Jan", "average_return": 1.0, "win_rate": 55.0, "count": 10},
            {"label": "Feb", "average_return": 3.5 if ticker == "AAA" else 1.5, "win_rate": 60.0, "count": 10},
        ]
        return {
            "status": "success",
            "ticker": ticker,
            "months": months,
            "weekdays": [],
            "verdict": {"best_month": "Feb", "worst_month": "Jan", "summary": "mock"},
        }

    monkeypatch.setattr("core.analyzers.Helheim.analyze_seasonality", _fake_analyze)
    res = Helheim.get_market_seasonality()

    assert res["status"] == "success"
    assert res["month"] == 2
    assert res["month_label"] == "Feb"
    assert len(res["top_historical_performers"]) == 1
    assert res["top_historical_performers"][0]["ticker"] == "AAA"


def test_analyze_seasonality_uses_monthly_candle_return_metric(monkeypatch):
    # Build 300 monthly candles (>=250 rows to satisfy minimum-history guard).
    # Jan candles are +10% (100 -> 110), while Dec closes are 150.
    # Old daily-close aggregation would read Jan as negative (~-26.7%),
    # but monthly candle-return aggregation must keep Jan positive at +10%.
    idx = pd.date_range("2000-01-31", periods=300, freq="ME")
    open_vals = np.full(len(idx), 100.0)
    close_vals = np.full(len(idx), 100.0)
    jan_mask = idx.month == 1
    dec_mask = idx.month == 12
    close_vals[jan_mask] = 110.0
    close_vals[dec_mask] = 150.0
    df = pd.DataFrame({"Open": open_vals, "Close": close_vals}, index=idx)

    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda _ticker: df)
    res = Helheim.analyze_seasonality("COMI")

    assert res["status"] == "success"
    jan = next(m for m in res["months"] if m["label"] == "Jan")
    assert jan["average_return"] == 10.0
    assert jan["win_rate"] == 100.0
    assert jan["count"] == 25
