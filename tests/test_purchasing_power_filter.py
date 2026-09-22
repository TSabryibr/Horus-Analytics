import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from core.settings import settings
from core.analyzers.MomentumBreakoutScanner import analyze_stock_frame

@pytest.fixture
def base_stock_dataframe():
    # Construct a valid dataframe with enough bars
    # Using high volume/turnover to pass LiquidityGuard checks
    from core import TimeUtils
    dates = pd.date_range(end=TimeUtils.now(), periods=150)
    data = {
        "Open": [10.0] * 150,
        "High": [10.5] * 150,
        "Low": [9.8] * 150,
        "Close": [10.2] * 150,
        "Volume": [500000] * 150
    }
    df = pd.DataFrame(data, index=dates)
    # Ensure there's a strong breakout setup
    df.iloc[149, df.columns.get_loc("Close")] = 12.0 # price spike
    df.iloc[149, df.columns.get_loc("High")] = 12.5
    df.iloc[149, df.columns.get_loc("Volume")] = 800000 # modest volume spike to not trigger manipulation (>5x)
    return df

@patch("core.analyzers.MomentumBreakoutScanner.estimate_bid_ask_spread", return_value=0.005)
def test_ppf_fails_on_low_projected_return(mock_spread, base_stock_dataframe, monkeypatch):
    # Set hurdle to be higher than potential return
    monkeypatch.setattr(settings, "USD_DEVALUATION_DAILY_SLOPE", 5.0) # 5% daily devaluation
    monkeypatch.setattr(settings, "PPP_MIN_ALPHA_PREMIUM", 10.0) # 10% minimum premium
    # Projected return will be around (Target 2 - 12) / 12 * 100
    # Hurdle rate = 5.0 * 10 + 10.0 = 60%
    
    result = analyze_stock_frame("TEST_EGP", base_stock_dataframe)
    
    assert result is not None
    assert result["Status"] == "⚠️ NOMINAL TRAP (PPP_FAILURE)"
    assert result["Signal_Score"] == 0
    assert "PPP_Failure" in result["Signal_Reasons"]
    assert result["PPP_Hurdle_%"] == 60.0

@patch("core.analyzers.MomentumBreakoutScanner.estimate_bid_ask_spread", return_value=0.005)
def test_ppf_passes_on_high_projected_return(mock_spread, base_stock_dataframe, monkeypatch):
    # Set very low hurdle rate
    monkeypatch.setattr(settings, "USD_DEVALUATION_DAILY_SLOPE", 0.01) # 0.1% daily
    monkeypatch.setattr(settings, "PPP_MIN_ALPHA_PREMIUM", 0.0) # 0% minimum premium
    
    result = analyze_stock_frame("TEST_EGP", base_stock_dataframe)
    
    assert result is not None
    # Since it passes PPP, the status will be breakout or buy signal
    assert result["Status"] != "⚠️ NOMINAL TRAP (PPP_FAILURE)"
    assert result["Signal_Score"] > 0
    assert "PPP_Failure" not in result["Signal_Reasons"]

@patch("core.analyzers.MomentumBreakoutScanner.estimate_bid_ask_spread", return_value=0.005)
def test_ppf_bypassed_for_usd_denominated_ticker(mock_spread, base_stock_dataframe, monkeypatch):
    # Set high hurdle rate that would normally fail EGP
    monkeypatch.setattr(settings, "USD_DEVALUATION_DAILY_SLOPE", 2.0)
    monkeypatch.setattr(settings, "PPP_MIN_ALPHA_PREMIUM", 10.0)
    
    # We patch USD_STOCKS to treat this ticker as USD-denominated
    with patch("core.analyzers.MomentumBreakoutScanner.USD_STOCKS", ["TEST_USD"]):
        result = analyze_stock_frame("TEST_USD", base_stock_dataframe)
        
        assert result is not None
        # Bypassed because it's USD, so no PPP failure status
        assert result["Status"] != "⚠️ NOMINAL TRAP (PPP_FAILURE)"
        assert result["Currency"] == "USD"
