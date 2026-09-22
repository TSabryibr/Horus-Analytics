from core.settings import settings
import pandas as pd
from core import TimeUtils


def test_eye_analyze_stock_uses_live_data_when_market_is_open(monkeypatch):
    from core.analyzers import MomentumBreakoutScanner

    calls = []

    def fake_get_stock_data(ticker, include_live=True, **kwargs):
        calls.append({"ticker": ticker, "include_live": include_live})
        return pd.DataFrame()

    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)
    monkeypatch.setattr(MomentumBreakoutScanner, "analyze_stock_frame", lambda ticker, df: {"Ticker": ticker})

    result = MomentumBreakoutScanner.analyze_stock("COMI")

    assert result == {"Ticker": "COMI"}
    assert calls == [{"ticker": "COMI", "include_live": True}]


def test_eye_analyze_stock_uses_history_only_when_market_is_closed(monkeypatch):
    from core.analyzers import MomentumBreakoutScanner

    calls = []

    def fake_get_stock_data(ticker, include_live=True, **kwargs):
        calls.append({"ticker": ticker, "include_live": include_live})
        return pd.DataFrame()

    monkeypatch.setattr(settings, "is_market_open", lambda: False)
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", fake_get_stock_data)
    monkeypatch.setattr(MomentumBreakoutScanner, "analyze_stock_frame", lambda ticker, df: {"Ticker": ticker})

    result = MomentumBreakoutScanner.analyze_stock("COMI")

    assert result == {"Ticker": "COMI"}
    assert calls == [{"ticker": "COMI", "include_live": False}]


def test_liquidity_guard_blocks_illiquid_buys():
    from core.analyzers import MomentumBreakoutScanner
    import numpy as np

    dates = pd.date_range(end=TimeUtils.now(), periods=105)
    prices = [10.0] * 100 + [12.0, 12.5, 13.0, 13.5, 14.0]
    
    df_low_turnover = pd.DataFrame({
        "Open": prices,
        "High": [p + 0.1 for p in prices],
        "Low": [p - 0.1 for p in prices],
        "Close": prices,
        "Volume": [1000] * 105  # 1000 shares * 14 EGP = 14k EGP turnover (far below 2M EGP)
    }, index=dates)
    
    result = MomentumBreakoutScanner.analyze_stock_frame("TEST_TICKER", df_low_turnover)
    
    assert result is not None
    assert "ILLIQUID" in result["Status"] or "LIQUIDITY TRAP" in result["Status"]
    assert "TURNOVER" in result["Status"]
    assert result["Signal_Score"] == 0


def test_liquidity_guard_allows_liquid_buys():
    from core.analyzers import MomentumBreakoutScanner
    import numpy as np

    dates = pd.date_range(end=TimeUtils.now(), periods=105)
    prices = np.linspace(10.0, 15.0, 105)
    
    df_liquid = pd.DataFrame({
        "Open": prices - 0.1,
        "High": prices + 0.2,
        "Low": prices - 0.2,
        "Close": prices,
        "Volume": [500000] * 105  # 500k shares * 10+ EGP = 5M+ EGP daily turnover
    }, index=dates)
    
    result = MomentumBreakoutScanner.analyze_stock_frame("TEST_LIQUID", df_liquid)
    
    assert result is not None
    assert "LIQUIDITY TRAP" not in result["Status"]
