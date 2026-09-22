import pytest
import time
from core.data.ParallelUSDFeed import ParallelUSDFeed

def test_usd_parallel_feed_heartbeat():
    feed = ParallelUSDFeed(fallback_rate=50.0, max_stale_seconds=5.0)

    rate, is_fresh = feed.get_live_rvu_rate()
    assert rate == 50.0
    assert is_fresh is True

    feed.update_rate(52.5)
    rate_updated, is_fresh_updated = feed.get_live_rvu_rate()
    assert rate_updated == 52.5
    assert is_fresh_updated is True
