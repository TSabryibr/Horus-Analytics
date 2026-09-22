"""
TEST SUITE: PHASE 5 COMPUTE OFFLOADING, UNIVERSE SYMBOL CACHE & SLA HISTOGRAM
=============================================================================
Verifies:
  1. Offloading heavy simulation compute to dedicated worker pool (_SIM_COMPUTE_EXECUTOR).
  2. Universe symbol cache mtime tracking, thread-safety, and copy semantics in MarketLists.
  3. Live delivery SLA latency histogram distribution buckets and full-status integration.
"""

import concurrent.futures
import threading
import time
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api import app
from core import TimeUtils
from core.market import MarketLists
from core.signals.sla import (
    LATENCY_HISTOGRAM_BUCKETS,
    compute_delivery_sla_metrics,
    compute_latency_histogram,
)
from database import SignalDelivery, SignalRun
from routes.analytics.simulations import _SIM_COMPUTE_EXECUTOR, get_sim_executor_stats

client = TestClient(app)


# --------------------------------------------------------------------------
# 1. Compute Offloading & Worker Pool Tests
# --------------------------------------------------------------------------

def test_sim_compute_executor_configuration():
    """Verify compute executor is bounded and configured with dedicated worker threads."""
    stats = get_sim_executor_stats()
    assert stats["max_workers"] == 2
    assert _SIM_COMPUTE_EXECUTOR._max_workers == 2


def test_ragnarok_runs_on_dedicated_worker_thread(monkeypatch):
    """Verify /api/v1/ragnarok simulation executes on HorusComputeWorker thread pool."""
    execution_thread_names = []

    def mock_run_ragnarok(*args, **kwargs):
        current_thread = threading.current_thread()
        execution_thread_names.append(current_thread.name)
        return {
            "status": "success",
            "simulations": kwargs.get("iterations", 10),
            "ruin_probability": 0.02,
        }

    monkeypatch.setattr("core.RagnarokSimulator.run_ragnarok_simulation", mock_run_ragnarok)
    monkeypatch.setattr("routes.analytics.simulations.RagnarokSimulator.run_ragnarok_simulation", mock_run_ragnarok)

    res = client.post(
        "/api/v1/ragnarok",
        json={
            "tickers": ["COMI", "EAST"],
            "iterations": 50,
            "days": 10,
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(execution_thread_names) == 1
    # Verify execution ran inside the dedicated worker pool
    assert "HorusComputeWorker" in execution_thread_names[0]


def test_monte_carlo_runs_on_worker_thread(monkeypatch):
    """Verify /api/v1/montecarlo executes asynchronously on worker pool."""
    execution_threads = []

    def mock_run_mc(*args, **kwargs):
        execution_threads.append(threading.current_thread().name)
        return {
            "simulations": 100,
            "median_final_capital": 120000.0,
            "ruin_probability": 0.01,
        }

    monkeypatch.setattr("core.MonteCarlo.run_monte_carlo", mock_run_mc)
    monkeypatch.setattr("routes.analytics.MonteCarlo.run_monte_carlo", mock_run_mc)
    monkeypatch.setattr("routes.analytics.simulations.MonteCarlo.run_monte_carlo", mock_run_mc)

    # Mock Trade query returning closed trades
    mock_trade_model = MagicMock()
    mock_trade_model.exit_date = MagicMock()
    mock_trade_model.exit_date.__le__ = MagicMock(return_value=True)
    mock_query = MagicMock()
    mock_query.dicts.return_value.iterator.return_value = [
        {"pnl": 500, "entry_price": 100, "shares": 10, "pnl_pct": 5.0},
        {"pnl": -200, "entry_price": 100, "shares": 10, "pnl_pct": -2.0},
    ]
    mock_trade_model.select.return_value.where.return_value = mock_query
    monkeypatch.setattr("routes.analytics.Trade", mock_trade_model)
    monkeypatch.setattr("routes.analytics.simulations.Trade", mock_trade_model)

    res = client.post(
        "/api/v1/montecarlo",
        json={"initial_capital": 100000, "simulations": 100},
    )

    assert res.status_code == 200
    assert len(execution_threads) == 1
    assert "HorusComputeWorker" in execution_threads[0]


def test_simulation_backtest_runs_on_worker_thread(monkeypatch):
    """Verify /api/v1/simulation/backtest executes on worker pool."""
    execution_threads = []

    def mock_backtest(**kwargs):
        execution_threads.append(threading.current_thread().name)
        return {
            "metrics": {"total_return": 15.5, "win_rate": 60.0, "max_drawdown": 4.2},
            "equity_curve": [100000, 115500],
            "trades": [],
        }

    monkeypatch.setattr("routes.analytics.run_price_action_backtest", mock_backtest)
    monkeypatch.setattr("routes.analytics.simulations.run_price_action_backtest", mock_backtest)
    monkeypatch.setattr("core.price_action.backtest.run_price_action_backtest", mock_backtest)
    monkeypatch.setattr("routes.analytics.get_price_action_strategy", lambda s: {"id": s})
    monkeypatch.setattr("routes.analytics.simulations.get_price_action_strategy", lambda s: {"id": s})

    res = client.post(
        "/api/v1/simulation/backtest",
        json={
            "strategy_id": "ascending_triangle_breakout",
            "market": "EGX30",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "capital": 100000,
            "commission": 0.002,
            "slippage": 0.001,
        },
    )

    assert res.status_code == 200
    assert len(execution_threads) == 1
    assert "HorusComputeWorker" in execution_threads[0]



# --------------------------------------------------------------------------
# 2. Universe Symbol Cache & Thread-Safety Tests
# --------------------------------------------------------------------------

def test_market_lists_mtime_cache_and_stats():
    """Verify MarketLists avoids disk re-reads when file modification time hasn't changed."""
    # Force reload
    reloaded = MarketLists.load_metadata(force=True)
    stats = MarketLists.get_universe_cache_stats()
    assert stats["reloads"] >= 1

    # Second call without force must be a cache hit
    hit = MarketLists.load_metadata(force=False)
    assert hit is False  # False indicates served from cache, no disk read
    new_stats = MarketLists.get_universe_cache_stats()
    assert new_stats["hits"] >= stats["hits"] + 1


def test_market_lists_copy_semantics_prevent_cache_corruption():
    """Verify get_market_list returns a copy so caller mutations don't corrupt the cache."""
    list_30 = MarketLists.get_market_list("30")
    original_len = len(list_30)

    # Mutate the returned set
    list_30.add("POISON_TICKER")
    assert "POISON_TICKER" in list_30

    # Fetch again from cache
    fresh_30 = MarketLists.get_market_list("30")
    assert "POISON_TICKER" not in fresh_30
    assert len(fresh_30) == original_len


def test_market_lists_concurrent_thread_safety():
    """Verify concurrent reads across multiple threads execute without race conditions."""
    results = []

    def worker():
        for _ in range(50):
            s30 = MarketLists.get_market_list("30")
            s70 = MarketLists.get_market_list("70")
            s_all = MarketLists.get_market_list("ALL")
            sec = MarketLists.get_sector("COMI")
            name = MarketLists.get_company_name("COMI")
            results.append((len(s30), len(s70), len(s_all), sec, name))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 8 * 50
    first_result = results[0]
    # All threads should read consistent lengths
    for r in results:
        assert r[0] == first_result[0]
        assert r[1] == first_result[1]
        assert r[2] == first_result[2]


def test_market_lists_invalidate_cache():
    """Verify invalidate_cache resets the mtime timestamp."""
    MarketLists.load_metadata()
    MarketLists.invalidate_cache()
    stats = MarketLists.get_universe_cache_stats()
    assert stats["mtime"] == -1.0


# --------------------------------------------------------------------------
# 3. Live Telegram Delivery Latency Histogram Tests
# --------------------------------------------------------------------------

def test_compute_latency_histogram_distribution():
    """Verify compute_latency_histogram correctly buckets varied latency values."""
    latencies = [
        120.0,   # <250ms
        249.9,   # <250ms
        250.0,   # 250-500ms (boundary)
        499.0,   # 250-500ms
        500.0,   # 500-1000ms (boundary)
        999.0,   # 500-1000ms
        1000.0,  # 1-2.5s (boundary)
        2499.0,  # 1-2.5s
        2500.0,  # 2.5-5s (boundary)
        4999.0,  # 2.5-5s
        5000.0,  # >5s (boundary)
        7500.0,  # >5s
    ]

    hist = compute_latency_histogram(latencies)
    assert len(hist) == 6

    bucket_map = {item["bucket"]: item for item in hist}

    assert bucket_map["<250ms"]["count"] == 2
    assert bucket_map["250-500ms"]["count"] == 2
    assert bucket_map["500-1000ms"]["count"] == 2
    assert bucket_map["1-2.5s"]["count"] == 2
    assert bucket_map["2.5-5s"]["count"] == 2
    assert bucket_map[">5s"]["count"] == 2

    # Verify percentages
    total_pct = sum(item["pct"] for item in hist)
    assert abs(total_pct - 100.0) < 0.1
    for item in hist:
        assert item["pct"] == round((2 / 12) * 100.0, 2)


def test_compute_latency_histogram_empty():
    """Verify compute_latency_histogram handles empty input without error."""
    hist = compute_latency_histogram([])
    assert len(hist) == 6
    for item in hist:
        assert item["count"] == 0
        assert item["pct"] == 0.0


def test_compute_delivery_sla_metrics_includes_histogram():
    """Verify compute_delivery_sla_metrics returns histogram in latency_stats."""
    run = SignalRun.create(
        run_date=TimeUtils.today(),
        scan_type="DAILY",
        status="COMPLETED",
    )

    test_latencies = [150.0, 350.0, 750.0, 1500.0, 3500.0, 6000.0]
    for lat in test_latencies:
        SignalDelivery.create(
            run=run,
            channel="TELEGRAM",
            service_tier="SIGNALS_ONLY",
            destination_type="SUBSCRIBER",
            status="SENT",
            sent_at=TimeUtils.now(),
            latency_ms=lat,
            created_at=TimeUtils.now(),
        )

    metrics = compute_delivery_sla_metrics(days=1, target_latency_ms=5000.0)

    stats = metrics["latency_stats"]
    assert "histogram" in stats
    hist = stats["histogram"]
    assert len(hist) == 6

    # Verify each bucket has at least 1 record
    bucket_map = {b["bucket"]: b for b in hist}
    assert bucket_map["<250ms"]["count"] >= 1
    assert bucket_map["250-500ms"]["count"] >= 1
    assert bucket_map["500-1000ms"]["count"] >= 1
    assert bucket_map["1-2.5s"]["count"] >= 1
    assert bucket_map["2.5-5s"]["count"] >= 1
    assert bucket_map[">5s"]["count"] >= 1


def test_system_full_status_includes_delivery_sla_histogram():
    """Verify GET /api/v1/system/full-status returns delivery_sla with histogram."""
    res = client.get("/api/v1/system/full-status")
    assert res.status_code == 200
    data = res.json()

    assert "delivery_sla" in data
    delivery_sla = data["delivery_sla"]
    assert "latency_stats" in delivery_sla
    assert "histogram" in delivery_sla["latency_stats"]
    assert len(delivery_sla["latency_stats"]["histogram"]) == 6


def test_signals_sla_endpoint_returns_histogram():
    """Verify GET /api/v1/signals/sla returns delivery SLA with histogram."""
    res = client.get("/api/v1/signals/sla?days=7&target_latency_ms=5000.0")
    assert res.status_code == 200
    data = res.json()

    assert "latency_stats" in data
    assert "histogram" in data["latency_stats"]
    assert len(data["latency_stats"]["histogram"]) == 6
