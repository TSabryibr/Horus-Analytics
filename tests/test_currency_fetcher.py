import pytest
import datetime
from utils.currency_fetcher import get_parallel_usd_egp_rate, get_historical_usd_egp_rate

def test_get_parallel_usd_egp_rate():
    rate = get_parallel_usd_egp_rate()
    assert isinstance(rate, float)
    assert rate > 0.0
    print(f"Verified current rate: {rate}")

def test_get_historical_usd_egp_rate():
    # Test recent date uses current rate
    now = datetime.datetime.now()
    rate_now = get_historical_usd_egp_rate(now)
    assert rate_now == get_parallel_usd_egp_rate()
    
    # Test historical lookup
    rate_peak = get_historical_usd_egp_rate(datetime.datetime(2024, 2, 1))
    assert rate_peak == 65.0
    
    rate_stabilized = get_historical_usd_egp_rate(datetime.datetime(2024, 6, 1))
    assert rate_stabilized == 48.0
    
    rate_2025 = get_historical_usd_egp_rate(datetime.datetime(2025, 6, 1))
    assert rate_2025 == 50.0
    
    rate_2026 = get_historical_usd_egp_rate(datetime.datetime(2026, 6, 1))
    assert rate_2026 == 52.0
