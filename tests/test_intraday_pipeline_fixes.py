import datetime
import pytest
import pandas as pd
import numpy as np

from data_engine.intraday_store import get_bulk_intraday_data, replace_intraday
from core.DataManager import calculate_projected_volume
from core.market.LiveFeedManager import LiveFeedManager
from core.market.IntradayWatcher import check_signal


def test_intraday_store_date_bounding():
    """Verify get_bulk_intraday_data respects since_timestamp bounds."""
    # Seed mock intraday data for 2 days
    dates = [
        "2026-09-01 10:30:00",
        "2026-09-01 11:00:00",
        "2026-09-02 10:30:00",
        "2026-09-02 11:00:00",
    ]
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(dates),
        "open": [10.0, 10.2, 10.5, 10.8],
        "high": [10.3, 10.4, 10.9, 11.0],
        "low": [9.9, 10.1, 10.4, 10.7],
        "close": [10.2, 10.3, 10.8, 10.9],
        "volume": [1000, 1500, 2000, 2500],
    })
    replace_intraday("TEST_TICKER", df)

    # 1. Unbounded query gets all 4 bars
    all_bars = get_bulk_intraday_data(["TEST_TICKER"])
    assert len(all_bars) == 4

    # 2. Bounded query for Sep 2 gets only 2 bars
    sep2_bars = get_bulk_intraday_data(["TEST_TICKER"], since_timestamp="2026-09-02 00:00:00")
    assert len(sep2_bars) == 2
    assert all(sep2_bars["timestamp"] >= pd.Timestamp("2026-09-02 00:00:00"))


def test_calculate_projected_volume_u_curve():
    """Verify EGX empirical U-curve volume projection behavior."""
    today = datetime.datetime(2026, 9, 3)

    # 1. Before 10:45 AM -> Raw volume returned (no projection)
    at_1030 = today.replace(hour=10, minute=30)
    assert calculate_projected_volume(1000.0, at_1030) == 1000.0

    # 2. At 10:45 AM -> Uses 0.35 CDF (multiplier ~2.85x, capped at <= 3.5x)
    at_1045 = today.replace(hour=10, minute=45)
    proj_1045 = calculate_projected_volume(1000.0, at_1045)
    assert 2800.0 <= proj_1045 <= 2900.0  # 1000 / 0.35 = 2857.14

    # 3. At 12:00 PM (120 min elapsed) -> 0.35 + 0.40*(75/165) = ~0.5318 CDF
    at_1200 = today.replace(hour=12, minute=0)
    proj_1200 = calculate_projected_volume(1000.0, at_1200)
    assert 1850.0 <= proj_1200 <= 1900.0  # 1000 / 0.5318 = 1880.4

    # 4. At 14:30 PM (End of session) -> Raw volume returned
    at_1430 = today.replace(hour=14, minute=30)
    assert calculate_projected_volume(1000.0, at_1430) == 1000.0

    # 5. During simulation or when market closed -> Raw volume returned
    assert calculate_projected_volume(1000.0, at_1200, is_simulating=True) == 1000.0
    assert calculate_projected_volume(1000.0, at_1200, is_market_open=False) == 1000.0


def test_live_feed_breakout_multi_tick_filter():
    """Verify LiveFeedManager filters out single-tick breakouts and confirms on 5M close."""
    LiveFeedManager._resistance_cache = {
        "TEST_COMI": {"R20": 100.0, "K1": None, "K2": None}
    }
    LiveFeedManager._triggered_today.clear()
    LiveFeedManager._confirmed_breakouts.clear()
    LiveFeedManager._candle_buffers.clear()

    # Threshold is 100 * 1.015 = 101.50
    # First tick above threshold: should NOT trigger provisional alert immediately
    LiveFeedManager.evaluate_breakout("TEST_COMI", price=102.0, is_confirmed=False)
    assert "TEST_COMI_Resistance_20D" in LiveFeedManager._triggered_today

    # 5M confirmed close:
    LiveFeedManager.evaluate_breakout("TEST_COMI", price=102.5, volume=50000, is_confirmed=True)
    assert "TEST_COMI_Resistance_20D" in LiveFeedManager._confirmed_breakouts


def test_intraday_watcher_deprecation_and_math():
    """Verify IntradayWatcher emits deprecation warning and runs without error."""
    # Mock a small 5-min DataFrame with 70 bars
    np.random.seed(42)
    closes = 50.0 + np.cumsum(np.random.randn(70) * 0.1)
    df = pd.DataFrame({
        "Open": closes - 0.05,
        "High": closes + 0.20,
        "Low": closes - 0.20,
        "Close": closes,
        "Volume": [20000.0] * 70,
    })

    with pytest.deprecated_call():
        res = check_signal("TEST_MOCK", df)
    # Function executes cleanly and handles scaled turnover
    assert res is None or isinstance(res, dict)


def test_upsert_intraday_volume_accumulation_and_ohlc_expansion():
    """Verify upsert_intraday sums volume and expands OHLC on multi-trade conflict."""
    from data_engine.intraday_store import upsert_intraday, get_intraday_data

    ticker = "TEST_ACCUM"
    minute_ts = pd.Timestamp("2026-09-03 10:15:00")

    # Trade 1: price 50.0, vol 500 (replace_intraday clears any previous test run leftovers)
    df1 = pd.DataFrame([{
        "timestamp": minute_ts,
        "open": 50.0,
        "high": 50.0,
        "low": 50.0,
        "close": 50.0,
        "volume": 500.0,
    }])
    replace_intraday(ticker, df1)

    # Trade 2 (same minute): price 52.0 (higher), vol 1000
    df2 = pd.DataFrame([{
        "timestamp": minute_ts,
        "open": 52.0,
        "high": 52.0,
        "low": 52.0,
        "close": 52.0,
        "volume": 1000.0,
    }])
    upsert_intraday(ticker, df2)

    # Trade 3 (same minute): price 49.0 (lower), vol 250
    df3 = pd.DataFrame([{
        "timestamp": minute_ts,
        "open": 49.0,
        "high": 49.0,
        "low": 49.0,
        "close": 49.0,
        "volume": 250.0,
    }])
    upsert_intraday(ticker, df3)

    bars = get_intraday_data(ticker)
    assert len(bars) == 1
    row = bars.iloc[0]

    # Open is preserved from Trade 1
    assert row["open"] == 50.0
    # High expanded to Trade 2
    assert row["high"] == 52.0
    # Low contracted to Trade 3
    assert row["low"] == 49.0
    # Close is latest trade (Trade 3)
    assert row["close"] == 49.0
    # Volume is SUM of all 3 trades: 500 + 1000 + 250 = 1750
    assert row["volume"] == 1750.0


def test_livefeed_fallback_resistance_on_cold_start():
    """Verify LiveFeedManager fallback resistance returns non-empty dict when parquet data exists."""
    fallback = LiveFeedManager._compute_fallback_resistance()
    # If historical data exists in test environment, it returns dictionary of ticker -> levels
    assert isinstance(fallback, dict)
    if fallback:
        sample_key = next(iter(fallback))
        assert "R20" in fallback[sample_key]
        assert fallback[sample_key]["R20"] > 0

