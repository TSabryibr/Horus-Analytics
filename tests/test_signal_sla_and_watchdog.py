"""
TESTS FOR PHASE 2: SIGNAL SLA TELEMETRY & MARKET FEED WATCHDOG
==============================================================
Verifies:
  1. SignalDelivery latency tracking & serialization
  2. SLA metric computation (averages, percentiles, breach rates, breakdown)
  3. API endpoint /api/v1/signals/sla and /api/v1/signals/ops/sla
  4. MarketFeedWatchdog heartbeat detection (market closed, healthy, stalled)
  5. Watchdog self-healing flow (cache invalidation, sync retry, admin alert cooldown)
  6. API endpoint /api/v1/live/watchdog
"""
from __future__ import annotations

import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api import app
from core import TimeUtils
from core.market.feed_watchdog import MarketFeedWatchdog
from core.settings import settings
from core.signals.publishing import serialize_delivery
from core.signals.sla import compute_delivery_sla_metrics, record_delivery_telemetry
from database import (
    Portfolio,
    SignalDelivery,
    SignalRecommendation,
    SignalRun,
    db,
)


@pytest.fixture(autouse=True)
def setup_db():
    """Ensure clean test state for each test."""
    MarketFeedWatchdog.reset_state()
    yield
    MarketFeedWatchdog.reset_state()


@pytest.fixture
def client():
    return TestClient(app)


# --------------------------------------------------------------------------
# 1. Model & Telemetry Tests
# --------------------------------------------------------------------------

def test_signaldelivery_latency_field_and_serialization():
    """Test that SignalDelivery stores latency_ms and serialize_delivery includes it."""
    run = SignalRun.create(
        run_date=TimeUtils.today(),
        scan_type="DAILY",
        status="COMPLETED",
    )
    delivery = SignalDelivery.create(
        run=run,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="CHANNEL",
        destination_id="main",
        status="SENT",
        sent_at=TimeUtils.now(),
        latency_ms=142.5,
    )

    retrieved = SignalDelivery.get_by_id(delivery.id)
    assert retrieved.latency_ms == 142.5

    serialized = serialize_delivery(retrieved)
    assert "latency_ms" in serialized
    assert serialized["latency_ms"] == 142.5


def test_record_delivery_telemetry():
    """Test record_delivery_telemetry helper updates and persists latency."""
    run = SignalRun.create(
        run_date=TimeUtils.today(),
        scan_type="DAILY",
        status="COMPLETED",
    )
    delivery = SignalDelivery.create(
        run=run,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="PORTFOLIO",
        status="SENT",
    )
    assert delivery.latency_ms is None

    record_delivery_telemetry(delivery, 235.876)
    refreshed = SignalDelivery.get_by_id(delivery.id)
    assert refreshed.latency_ms == 235.88


# --------------------------------------------------------------------------
# 2. SLA Metrics Computation Tests
# --------------------------------------------------------------------------

def test_compute_delivery_sla_metrics_empty():
    """Test SLA metrics with no deliveries in window."""
    metrics = compute_delivery_sla_metrics(days=1)
    assert metrics["window_days"] == 1
    assert metrics["total_deliveries"] == 0
    assert metrics["success_rate_pct"] == 100.0
    assert metrics["sla_compliant"] is True
    assert metrics["latency_stats"]["count"] == 0
    assert metrics["latency_stats"]["avg_ms"] is None
    assert metrics["latency_stats"]["p95_ms"] is None


def test_compute_delivery_sla_metrics_distribution():
    """Test SLA metrics with multiple dispatches, failures, and latency distributions."""
    run = SignalRun.create(
        run_date=TimeUtils.today(),
        scan_type="DAILY",
        status="COMPLETED",
    )

    # 4 SENT deliveries with varied latencies
    latencies = [100.0, 200.0, 300.0, 6000.0]  # 6000.0 breaches 5000ms threshold
    for lat in latencies:
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

    # 1 FAILED delivery
    SignalDelivery.create(
        run=run,
        channel="TELEGRAM",
        service_tier="MANAGED_EXECUTION",
        destination_type="PORTFOLIO",
        status="FAILED",
        last_error="Network timeout",
        created_at=TimeUtils.now(),
    )

    # 1 SKIPPED delivery
    SignalDelivery.create(
        run=run,
        channel="TELEGRAM",
        service_tier="SIGNALS_ONLY",
        destination_type="CHANNEL",
        status="SKIPPED",
        created_at=TimeUtils.now(),
    )

    metrics = compute_delivery_sla_metrics(days=7, target_latency_ms=5000.0)

    assert metrics["total_deliveries"] >= 6
    assert metrics["sent_count"] >= 4
    assert metrics["failed_count"] >= 1
    assert metrics["skipped_count"] >= 1

    # Sent / (Sent + Failed) = 4 / 5 = 80.0%
    assert metrics["success_rate_pct"] <= 85.0

    stats = metrics["latency_stats"]
    assert stats["count"] >= 4
    assert stats["min_ms"] <= 100.0
    assert stats["max_ms"] >= 6000.0
    assert stats["breached_count"] >= 1
    assert stats["breach_rate_pct"] > 0.0

    # Breakdowns
    assert "TELEGRAM" in metrics["by_channel"]
    assert "SIGNALS_ONLY" in metrics["by_tier"]
    assert "SUBSCRIBER" in metrics["by_destination_type"]


# --------------------------------------------------------------------------
# 3. API Route Tests
# --------------------------------------------------------------------------

def test_api_signals_sla_endpoint(client):
    """Test GET /api/v1/signals/sla returns comprehensive metrics."""
    response = client.get("/api/v1/signals/sla?days=7&target_latency_ms=5000.0")
    assert response.status_code == 200
    data = response.json()
    assert "window_days" in data
    assert "total_deliveries" in data
    assert "latency_stats" in data
    assert "by_channel" in data
    assert "by_tier" in data


def test_api_signals_ops_sla_backward_compatibility(client):
    """Test existing GET /api/v1/signals/ops/sla maintains backward compatibility."""
    response = client.get("/api/v1/signals/ops/sla?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert "deliveries" in data
    assert "success_rate_pct" in data["deliveries"]
    assert "avg_latency_ms" in data["deliveries"]


def test_api_live_watchdog_endpoint(client, monkeypatch):
    """Test GET /api/v1/live/watchdog returns heartbeat info."""
    monkeypatch.setattr(settings, "is_market_open", lambda: False)
    response = client.get("/api/v1/live/watchdog?max_stall_minutes=5.0")
    assert response.status_code == 200
    data = response.json()
    assert data["is_market_open"] is False
    assert data["stalled"] is False
    assert data["status"] == "MARKET_CLOSED"


# --------------------------------------------------------------------------
# 4. Market Feed Watchdog Heartbeat Tests
# --------------------------------------------------------------------------

def test_watchdog_heartbeat_market_closed(monkeypatch):
    """When market is closed, heartbeat reports not stalled and MARKET_CLOSED."""
    monkeypatch.setattr(settings, "is_market_open", lambda: False)
    status = MarketFeedWatchdog.check_feed_heartbeat()
    assert status["is_market_open"] is False
    assert status["stalled"] is False
    assert status["status"] == "MARKET_CLOSED"


def test_watchdog_heartbeat_no_data(monkeypatch):
    """When market is open but no data exists, heartbeat reports stalled NO_DATA."""
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(
        "data_engine.intraday_store.get_latest_timestamps",
        lambda realm="EGX": {},
    )
    status = MarketFeedWatchdog.check_feed_heartbeat()
    assert status["is_market_open"] is True
    assert status["stalled"] is True
    assert status["status"] == "NO_DATA"


def test_watchdog_heartbeat_healthy(monkeypatch):
    """When market is open and newest bar is fresh (e.g. 1m old), status is HEALTHY."""
    now = TimeUtils.now()
    fresh_ts = pd.Timestamp(now - datetime.timedelta(minutes=1))

    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(
        "data_engine.intraday_store.get_latest_timestamps",
        lambda realm="EGX": {"COMI": fresh_ts, "FWRY": fresh_ts},
    )

    status = MarketFeedWatchdog.check_feed_heartbeat(max_stall_minutes=5.0)
    assert status["is_market_open"] is True
    assert status["stalled"] is False
    assert status["status"] == "HEALTHY"
    assert status["lag_minutes"] <= 2.0
    assert status["tickers_monitored"] == 2


def test_watchdog_heartbeat_stalled(monkeypatch):
    """When newest bar is older than threshold (e.g. 12m old), status is STALLED."""
    now = TimeUtils.now()
    stale_ts = pd.Timestamp(now - datetime.timedelta(minutes=12))

    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr(
        "data_engine.intraday_store.get_latest_timestamps",
        lambda realm="EGX": {"COMI": stale_ts},
    )

    status = MarketFeedWatchdog.check_feed_heartbeat(max_stall_minutes=5.0)
    assert status["is_market_open"] is True
    assert status["stalled"] is True
    assert status["status"] == "STALLED"
    assert status["lag_minutes"] >= 11.0


# --------------------------------------------------------------------------
# 5. Market Feed Watchdog Self-Healing & Alerting Tests
# --------------------------------------------------------------------------

def test_watchdog_check_and_heal_healthy(monkeypatch):
    """When feed is healthy, check_and_heal takes no action."""
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    fresh_ts = pd.Timestamp(TimeUtils.now() - datetime.timedelta(minutes=1))
    monkeypatch.setattr(
        "data_engine.intraday_store.get_latest_timestamps",
        lambda realm="EGX": {"COMI": fresh_ts},
    )

    result = MarketFeedWatchdog.check_and_heal()
    assert result["action"] == "none"
    assert result["healed"] is False
    assert result["status"]["stalled"] is False


def test_watchdog_check_and_heal_sync_recovers_feed(monkeypatch):
    """When feed stalls, self-healing runs sync; if sync brings fresh data, action is sync_healed."""
    monkeypatch.setattr(settings, "is_market_open", lambda: True)

    now = TimeUtils.now()
    stale_ts = pd.Timestamp(now - datetime.timedelta(minutes=10))
    fresh_ts = pd.Timestamp(now - datetime.timedelta(minutes=1))

    # First call returns stale_ts, second call (after sync) returns fresh_ts
    call_count = 0
    def mock_timestamps(realm="EGX"):
        nonlocal call_count
        call_count += 1
        return {"COMI": stale_ts if call_count == 1 else fresh_ts}

    sync_called = []
    def mock_sync(realm, provider):
        sync_called.append((realm, provider))

    cache_invalidated = []
    def mock_invalidate(realm="EGX"):
        cache_invalidated.append(realm)

    monkeypatch.setattr("data_engine.intraday_store.get_latest_timestamps", mock_timestamps)
    monkeypatch.setattr("data_engine.sync._sync_intraday", mock_sync)
    monkeypatch.setattr("data_engine.freshness.invalidate_freshness_cache", mock_invalidate)

    result = MarketFeedWatchdog.check_and_heal(max_stall_minutes=5.0)

    assert len(sync_called) == 1
    assert len(cache_invalidated) >= 1
    assert result["action"] == "sync_healed"
    assert result["healed"] is True
    assert result["status"]["stalled"] is False


def test_watchdog_check_and_heal_alert_and_cooldown(monkeypatch):
    """When feed stalls and sync fails to heal, alert is broadcast; 2nd call enters cooldown."""
    monkeypatch.setattr(settings, "is_market_open", lambda: True)

    now = TimeUtils.now()
    stale_ts = pd.Timestamp(now - datetime.timedelta(minutes=15))

    # Feed remains stale
    monkeypatch.setattr(
        "data_engine.intraday_store.get_latest_timestamps",
        lambda realm="EGX": {"COMI": stale_ts},
    )
    monkeypatch.setattr("data_engine.sync._sync_intraday", lambda realm, provider: None)
    monkeypatch.setattr("data_engine.freshness.invalidate_freshness_cache", lambda realm="EGX": None)

    broadcasted_alerts = []
    monkeypatch.setattr(
        "core.AlertManager.broadcast_alert",
        lambda msg, **kwargs: broadcasted_alerts.append(msg) or {"ok": True},
    )

    # 1. First stall -> alert sent
    res1 = MarketFeedWatchdog.check_and_heal(max_stall_minutes=5.0, alert_cooldown_minutes=15.0)
    assert res1["action"] == "alert_sent"
    assert res1["healed"] is False
    assert len(broadcasted_alerts) == 1
    assert "CRITICAL: MARKET FEED STALLED" in broadcasted_alerts[0]

    # 2. Second tick immediately -> in cooldown, no new alert
    res2 = MarketFeedWatchdog.check_and_heal(max_stall_minutes=5.0, alert_cooldown_minutes=15.0)
    assert res2["action"] == "alert_cooldown"
    assert res2["healed"] is False
    assert len(broadcasted_alerts) == 1  # Alert count remains 1

    # 3. Simulate elapsed cooldown (e.g. 16 minutes later) -> new alert sent
    MarketFeedWatchdog._last_alert_time = now - datetime.timedelta(minutes=16)
    res3 = MarketFeedWatchdog.check_and_heal(max_stall_minutes=5.0, alert_cooldown_minutes=15.0)
    assert res3["action"] == "alert_sent"
    assert len(broadcasted_alerts) == 2
