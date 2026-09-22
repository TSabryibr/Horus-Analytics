import pytest
import pandas as pd
import numpy as np
from core import MarketPredictor
from unittest.mock import MagicMock

# Helper to create synthetic OHLCV data
def create_synthetic_df(trend="UP", length=100, start_price=10.0, volatility=0.1):
    # Use fixed start date to ensure indices align across different mock calls
    dates = pd.date_range(start="2025-01-01", periods=length, freq='D')
    prices = [start_price]
    
    for i in range(1, length):
        change = volatility if trend == "UP" else -volatility
        if trend == "FLAT": change = np.random.uniform(-0.01, 0.01)
        prices.append(prices[-1] * (1 + change))
        
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices,
        'High': [p * 1.01 for p in prices],
        'Low': [p * 0.99 for p in prices],
        'Close': prices,
        'Volume': [1000000] * length # High volume for liquidity checks
    })
    df.set_index('Date', inplace=True)
    return df

@pytest.fixture
def mock_data_manager(mocker):
    return mocker.patch('core.DataManager.DataManager.get_stock_data')

@pytest.fixture
def mock_market_lists(mocker):
    mocker.patch('core.market.MarketLists.get_sector', return_value="Test Sector")
    return mocker.patch('core.market.MarketLists.get_market_list')

def test_calculate_market_breadth_uptrend(mock_data_manager, mock_market_lists):
    # Setup: 3 stocks, all going UP
    mock_market_lists.return_value = ["A", "B", "C"]
    mock_data_manager.side_effect = lambda t: create_synthetic_df("UP", length=100)
    
    ad_line = MarketPredictor.calculate_market_breadth()
    
    assert ad_line is not None
    assert len(ad_line) > 0
    # Net Advances should be positive and increasing (slope > 0)
    slope = np.polyfit(range(len(ad_line)), ad_line.values, 1)[0]
    assert slope > 0

def test_calculate_market_breadth_downtrend(mock_data_manager, mock_market_lists):
    # Setup: 3 stocks, all going DOWN
    mock_market_lists.return_value = ["A", "B", "C"]
    mock_data_manager.side_effect = lambda t: create_synthetic_df("DOWN", length=100)
    
    ad_line = MarketPredictor.calculate_market_breadth()
    
    assert ad_line is not None
    # Net Advances should be negative and decreasing
    slope = np.polyfit(range(len(ad_line)), ad_line.values, 1)[0]
    assert slope < 0

def test_check_macro_health_bearish_divergence(mock_data_manager, mock_market_lists):
    mock_market_lists.return_value = ["A", "B", "C"]
    
    # Breadth going DOWN (Market weakness), but Index going UP (Fake rally)
    def side_effect(ticker):
        if ticker == "EGX30":
            return create_synthetic_df("UP", length=100) # Index Pumping
        else:
            return create_synthetic_df("DOWN", length=100) # Market Dumping
    
    mock_data_manager.side_effect = side_effect
    
    result = MarketPredictor.check_macro_health("EGX30")
    
    assert result is not None
    assert "BEARISH DIVERGENCE" in result['signal']
    assert result['correlation'] < 0 # Should use negative correlation roughly

def test_check_macro_health_healthy_uptrend(mock_data_manager, mock_market_lists):
    mock_market_lists.return_value = ["A", "B", "C"]
    
    # Everything going UP
    mock_data_manager.side_effect = lambda t: create_synthetic_df("UP", length=100)
    
    result = MarketPredictor.check_macro_health("EGX30")
    
    assert result is not None
    assert "HEALTHY UPTREND" in result['signal']

@pytest.mark.skip(reason="Needs better synthetic data generation for Bollinger Band squeeze")
def test_hunt_the_coil_found(mock_data_manager, mock_market_lists):
    mock_market_lists.return_value = ["COIL_STOCK"]
    
    # Create valid dataframe but inject tight Bollinger Bands at the end
    df = create_synthetic_df("FLAT", length=200)
    
    # Mocking pandas_ta bbands result directly or constructing DF such that TA lib calculates it???
    # Better: Mock pandas_ta extension or ensure synthetic data produces tight bands.
    # Actually, pandas_ta is attached to df. Let's mock DataManager return, and we rely on real pandas_ta.
    # To get a squeeze, we need very low volatility recently vs history.
    
    # Let's manually construct a DF where last 20 days are identical (zero variance) = bandwidth 0
    dates = pd.date_range(end=pd.Timestamp.now(), periods=200, freq='D')
    prices = [10.0] * 100 + [10.0 + (i%2)*0.1 for i in range(80)] + [10.0] * 20 
    # History has some movement, End is flat
    
    df = pd.DataFrame({
        'Date': dates,
        'Close': prices, 
        'Open': prices, 'High': prices, 'Low': prices,
        'Volume': [2000000] * 200
    })
    df.set_index('Date', inplace=True)
    
    mock_data_manager.return_value = df
    
    result = MarketPredictor.hunt_the_coil()
    
    assert result['status'] == 'found', f"Expected found, got {result}"
    assert len(result['candidates']) == 1
    assert result['candidates'][0]['Ticker'] == "COIL_STOCK"

def test_hunt_the_coil_none(mock_data_manager, mock_market_lists):
    mock_market_lists.return_value = ["NO_SQUEEZE"]
    
    # High volatility recently
    df = create_synthetic_df("UP", length=200, volatility=0.1) # 10% daily moves = huge bands
    mock_data_manager.return_value = df
    
    result = MarketPredictor.hunt_the_coil()
    
    assert result['status'] == 'none'


def test_calculate_market_breadth_logs_ascii_status(monkeypatch, capsys):
    monkeypatch.setattr("core.market.MarketLists.get_market_list", lambda *_args, **_kwargs: [])

    result = MarketPredictor.calculate_market_breadth()

    captured = capsys.readouterr().out
    assert result is None
    assert "[THE CANARY] Calculating Market Breadth..." in captured
    assert "No data available for breadth." in captured
    assert "ð" not in captured
    assert "â" not in captured
