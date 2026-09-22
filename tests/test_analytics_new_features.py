from fastapi.testclient import TestClient
from unittest.mock import patch

from api import app
from routes.shared import NEWS_CACHE
from core import TimeUtils


client = TestClient(app, raise_server_exceptions=False)


def test_news_endpoint_includes_bifrost_payload(monkeypatch):
    NEWS_CACHE["data"] = []
    mock_news = [
        {
            "source": "MockWire",
            "title": "Rocket breakout buy signal",
            "summary": "Green tape and profit up",
            "link": "https://example.com/a",
            "tickers": ["COMI"],
            "gossip_score": 3,
        },
        {
            "source": "MockWire",
            "title": "Crash sell dump",
            "summary": "Red loss down day",
            "link": "https://example.com/b",
            "tickers": ["FWRY"],
            "gossip_score": -3,
        },
    ]

    async def _fake_gather_gossip():
        return {"stories": mock_news, "macro_correlation": 0.1}

    monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _fake_gather_gossip)

    res = client.get("/api/v1/news")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert "bifrost" in body
    assert {"score", "regime", "bull_count", "bear_count", "total_hits", "sample_size"}.issubset(
        set(body["bifrost"].keys())
    )


def test_news_endpoint_cache_path_also_computes_bifrost():
    from routes.shared import SYSTEM_STATE

    NEWS_CACHE["data"] = [
        {"source": "Cache", "title": "buy rocket", "summary": "green", "link": "#", "tickers": [], "gossip_score": 1}
    ]
    NEWS_CACHE["timestamp"] = TimeUtils.now()
    NEWS_CACHE["version"] = SYSTEM_STATE.get("data_version", 0)
    NEWS_CACHE["cache_source"] = "memory"
    res = client.get("/api/v1/news")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "cache"
    assert "bifrost" in body


def test_news_endpoint_filters_saudi_items_from_cache():
    from routes.shared import SYSTEM_STATE

    NEWS_CACHE["data"] = {
        "stories": [
            {
                "source": "Argaam",
                "title": "AlJazira Capital reviews ADES Holding Q1 results, sets rating, TP",
                "summary": "Saudi Market Intelligence",
                "link": "https://www.argaam.com/en/article/example",
                "tickers": ["ACAP"],
                "gossip_score": 0,
            },
            {
                "source": "Enterprise",
                "title": "EGX closes higher as banks lead the session",
                "summary": "Egyptian equities improved.",
                "link": "https://enterpriseam.com/egypt/example",
                "tickers": [],
                "gossip_score": 1,
            },
        ],
        "macro_correlation": 0.0,
    }
    NEWS_CACHE["timestamp"] = TimeUtils.now()
    NEWS_CACHE["version"] = SYSTEM_STATE.get("data_version", 0)
    NEWS_CACHE["cache_source"] = "memory"

    res = client.get("/api/v1/news")

    assert res.status_code == 200
    body = res.json()
    assert body["count"] == 1
    assert body["data"][0]["source"] == "Enterprise"


def test_news_endpoint_uses_persisted_disk_cache_on_cold_start(monkeypatch, tmp_path):
    from routes.analytics import _persist_news_cache_to_disk, _load_news_cache_from_disk
    from routes.shared import SYSTEM_STATE

    cache_file = tmp_path / "news_cache.json"
    monkeypatch.setattr("routes.analytics.NEWS_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("NEWS_CACHE_TTL_SEC", "300")

    NEWS_CACHE["data"] = []
    NEWS_CACHE["timestamp"] = None
    NEWS_CACHE["version"] = -1

    current_version = SYSTEM_STATE.get("data_version", 0)
    cached_payload = {
        "stories": [
            {
                "source": "DiskCache",
                "title": "Cached market pulse",
                "summary": "Green tape holding up",
                "link": "#",
                "tickers": ["COMI"],
                "gossip_score": 2,
            }
        ],
        "macro_correlation": 0.42,
    }
    now = TimeUtils.now()
    _persist_news_cache_to_disk(cached_payload, now, current_version)

    NEWS_CACHE["data"] = []
    NEWS_CACHE["timestamp"] = None
    NEWS_CACHE["version"] = -1
    _load_news_cache_from_disk()

    async def _should_not_run():
        raise AssertionError("should use disk cache before refetching")

    monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _should_not_run)

    res = client.get("/api/v1/news")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "cache"
    assert body["count"] == 1
    assert body["macro_correlation"] == 0.42


def test_news_endpoint_uses_stale_disk_cache_within_grace_window(monkeypatch, tmp_path):
    from routes.analytics import _persist_news_cache_to_disk
    from routes.shared import SYSTEM_STATE

    cache_file = tmp_path / "news_cache.json"
    monkeypatch.setattr("routes.analytics.NEWS_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("NEWS_CACHE_TTL_SEC", "5")
    monkeypatch.setenv("NEWS_DISK_GRACE_TTL_SEC", "600")
    monkeypatch.setattr("routes.analytics.TimeUtils.now", lambda: __import__("datetime").datetime.fromisoformat("2026-04-01T12:10:00"))

    NEWS_CACHE["data"] = []
    NEWS_CACHE["timestamp"] = None
    NEWS_CACHE["version"] = -1

    current_version = SYSTEM_STATE.get("data_version", 0)
    cached_payload = {
        "stories": [
            {
                "source": "DiskCache",
                "title": "Cached market pulse",
                "summary": "Green tape holding up",
                "link": "#",
                "tickers": ["COMI"],
                "gossip_score": 2,
            }
        ],
        "macro_correlation": 0.42,
    }
    stale_but_recent = __import__("datetime").datetime.fromisoformat("2026-04-01T12:00:00")
    _persist_news_cache_to_disk(cached_payload, stale_but_recent, current_version)

    async def _should_not_run():
        raise AssertionError("stale disk cache should short-circuit cold-start refetch")

    monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _should_not_run)

    res = client.get("/api/v1/news")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "cache"
    assert body["count"] == 1


def test_news_endpoint_uses_pipeline_refresh_version_for_disk_cache(monkeypatch, tmp_path):
    from routes.analytics import _persist_news_cache_to_disk

    cache_file = tmp_path / "news_cache.json"
    monkeypatch.setattr("routes.analytics.NEWS_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("NEWS_CACHE_TTL_SEC", "5")
    monkeypatch.setenv("NEWS_DISK_GRACE_TTL_SEC", "600")
    monkeypatch.setattr("routes.analytics.get_system_state_snapshot", lambda: {"data_version": 0})
    monkeypatch.setattr("core.pipeline.refresh_pipeline_state", lambda force=False: {"data_version": 8})
    monkeypatch.setattr("routes.analytics.TimeUtils.now", lambda: __import__("datetime").datetime.fromisoformat("2026-04-01T12:10:00"))

    NEWS_CACHE["data"] = []
    NEWS_CACHE["timestamp"] = None
    NEWS_CACHE["version"] = -1
    NEWS_CACHE["cache_source"] = None

    cached_payload = {
        "stories": [
            {
                "source": "DiskCache",
                "title": "Cached market pulse",
                "summary": "Green tape holding up",
                "link": "#",
                "tickers": ["COMI"],
                "gossip_score": 2,
            }
        ],
        "macro_correlation": 0.42,
    }
    _persist_news_cache_to_disk(cached_payload, __import__("datetime").datetime.fromisoformat("2026-04-01T12:00:00"), 8)

    async def _should_not_run():
        raise AssertionError("pipeline-refresh data_version should unlock disk news cache reuse")

    monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _should_not_run)

    res = client.get("/api/v1/news")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "cache"
    assert body["count"] == 1


def test_news_endpoint_disk_grace_cache_ignores_cross_process_version_drift(monkeypatch, tmp_path):
    from routes.analytics import _persist_news_cache_to_disk

    cache_file = tmp_path / "news_cache.json"
    monkeypatch.setattr("routes.analytics.NEWS_CACHE_FILE", cache_file, raising=False)
    monkeypatch.setenv("NEWS_CACHE_TTL_SEC", "5")
    monkeypatch.setenv("NEWS_DISK_GRACE_TTL_SEC", "600")
    monkeypatch.setattr("routes.analytics.get_system_state_snapshot", lambda: {"data_version": 0})
    monkeypatch.setattr("core.pipeline.refresh_pipeline_state", lambda force=False: {"data_version": 1})
    monkeypatch.setattr("routes.analytics.TimeUtils.now", lambda: __import__("datetime").datetime.fromisoformat("2026-04-01T12:10:00"))

    NEWS_CACHE["data"] = []
    NEWS_CACHE["timestamp"] = None
    NEWS_CACHE["version"] = -1
    NEWS_CACHE["cache_source"] = None

    cached_payload = {
        "stories": [
            {
                "source": "DiskCache",
                "title": "Cached market pulse",
                "summary": "Green tape holding up",
                "link": "#",
                "tickers": ["COMI"],
                "gossip_score": 2,
            }
        ],
        "macro_correlation": 0.42,
    }
    _persist_news_cache_to_disk(cached_payload, __import__("datetime").datetime.fromisoformat("2026-04-01T12:00:00"), 8)

    async def _should_not_run():
        raise AssertionError("cross-process version drift should not invalidate disk news grace cache")

    monkeypatch.setattr("routes.analytics.SentimentCrawler.async_gather_gossip", _should_not_run)

    res = client.get("/api/v1/news")
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "cache"
    assert body["count"] == 1


def test_ragnarok_endpoint_error_when_no_tickers_and_no_open_positions(monkeypatch):
    class _FakeQuery:
        def where(self, *_args, **_kwargs):
            return self

        def dicts(self):
            return []

    monkeypatch.setattr("routes.analytics.Position.select", lambda *_args, **_kwargs: _FakeQuery())
    res = client.post("/api/v1/ragnarok", json={"iterations": 100, "days": 20})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "error"
    assert "No portfolio tickers found" in body["message"]


def test_ragnarok_endpoint_dedupes_payload_tickers(monkeypatch):
    captured = {}

    def _fake_run(portfolio_tickers, iterations, days):
        captured["tickers"] = portfolio_tickers
        captured["iterations"] = iterations
        captured["days"] = days
        return {
            "expected_value": 123.0,
            "var_95": 100.0,
            "ruin_probability": 11.0,
        }

    monkeypatch.setattr("core.RagnarokSimulator.run_ragnarok_simulation", _fake_run)

    res = client.post(
        "/api/v1/ragnarok",
        json={"iterations": 250, "days": 15, "tickers": [" comi ", "COMI", "FWRY", ""]},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert captured["tickers"] == ["COMI", "FWRY"]
    assert captured["iterations"] == 250
    assert captured["days"] == 15


def test_ragnarok_endpoint_uses_open_positions_when_tickers_not_provided(monkeypatch):
    class _FakeQuery:
        def where(self, *_args, **_kwargs):
            return self

        def dicts(self):
            return [{"ticker": "comi"}, {"ticker": "FWRY"}, {"ticker": "COMI"}]

    captured = {}

    def _fake_run(portfolio_tickers, iterations, days):
        captured["tickers"] = portfolio_tickers
        return {
            "expected_value": 200.0,
            "var_95": 150.0,
            "ruin_probability": 9.0,
        }

    monkeypatch.setattr("routes.analytics.Position.select", lambda *_args, **_kwargs: _FakeQuery())
    monkeypatch.setattr("core.RagnarokSimulator.run_ragnarok_simulation", _fake_run)

    res = client.post("/api/v1/ragnarok", json={"iterations": 100, "days": 20})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert captured["tickers"] == ["COMI", "FWRY"]

