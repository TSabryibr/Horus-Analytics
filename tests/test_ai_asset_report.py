import asyncio
import json

import pandas as pd

from core.ai_report import asset
from fastapi.testclient import TestClient
import api

client = TestClient(api.app, raise_server_exceptions=False)


class _FakeQuery:
    def __init__(self, result=None):
        self._result = result
        self._rows = result if isinstance(result, list) else ([] if result is None else [result])

    def where(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def first(self):
        return self._result

    def __iter__(self):
        return iter(self._rows)


def test_collect_asset_snapshot_supports_async_news_gatherer(monkeypatch):
    monkeypatch.setattr(
        "core.ai_report.asset.safe_call_with_error",
        asset.safe_call_with_error,
    )
    monkeypatch.setattr(
        "core.ai_report.asset.MarketPredictor.check_macro_health",
        lambda *_args, **_kwargs: {"signal": "BULLISH"},
    )
    monkeypatch.setattr(
        "core.ai_report.asset.Vanaheim.hunt_whales",
        lambda: {"candidates": [{"Ticker": "EGX30", "Signal": "ACCUMULATION"}]},
    )
    monkeypatch.setattr(
        "core.ai_report.asset.Svartalfheim.hunt_traps",
        lambda: {"bull_traps": [], "bear_traps": []},
    )

    async def _fake_async_gather_gossip():
        return {
            "stories": [
                {
                    "title": "EGX30 momentum improves",
                    "summary": "Breadth is improving.",
                    "tickers": ["EGX30"],
                    "gossip_score": 4,
                }
            ]
        }

    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.async_gather_gossip",
        _fake_async_gather_gossip,
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.gather_gossip",
        lambda: {
            "stories": [
                {
                    "title": "EGX30 momentum improves",
                    "summary": "Breadth is improving.",
                    "tickers": ["EGX30"],
                    "gossip_score": 4,
                }
            ]
        },
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.get_bifrost_sentiment",
        lambda stories: {"score": 64.0, "regime": "POSITIVE", "story_count": len(stories)},
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SandboxRegistry.get_lagged_correlations",
        lambda: {"mirrors": [{"symbol": "EGX30", "lagged_symbol": "COMI"}]},
    )
    monkeypatch.setattr("core.ai_report.asset.SignalRecommendation.select", lambda: _FakeQuery())

    snapshot = asset.collect_asset_snapshot("egx30")

    assert snapshot["ticker"] == "EGX30"
    assert snapshot["technical_context"]["macro_regime"] == "BULLISH"
    assert snapshot["news_mentions"][0]["title"] == "EGX30 momentum improves"
    assert snapshot["sentiment"]["regime"] == "POSITIVE"
    assert snapshot["arbitrage"]["symbol"] == "EGX30"


def test_generate_asset_report_derives_meaningful_copy_and_normalizes_sentiment(monkeypatch):
    monkeypatch.setattr(
        "core.ai_report.asset.collect_asset_snapshot",
        lambda _ticker, caches=None: {
            "ticker": "COMI",
            "as_of": "2026-04-13T21:00:00",
            "scope": None,
            "lead_ticker": None,
            "scope_levels": None,
            "lead_ticker_levels": None,
            "technical_context": {
                "macro_regime": "BULLISH",
                "is_bull_trap": False,
                "is_bear_trap": False,
            },
            "whale_flow": [{"Ticker": "COMI", "Signal": "ACCUMULATION"}],
            "sentiment": {"score": 50.0, "regime": "BORING MORTALS"},
            "news_mentions": [
                {
                    "title": "COMI expands digital banking footprint",
                    "source": "MUBASHER",
                    "gossip_score": 4,
                }
            ],
            "scope_news_mentions": [],
            "lead_ticker_news_mentions": [],
            "arbitrage": {"symbol": "COMI", "correlation": 0.84},
            "recommendation": {
                "side": None,
                "score": 0.0,
                "confidence": 0.0,
                "entry": 82.5,
                "stop": 78.0,
                "target": 89.0,
                "rationale": None,
            },
        },
    )

    created_rows = []
    monkeypatch.setattr(
        "core.ai_report.asset.AssetAiReport.create",
        lambda **kwargs: created_rows.append(kwargs),
    )

    report = asset.generate_asset_report("comi", save=True)

    assert report["ticker"] == "COMI"
    assert report["snapshot"]["sentiment"]["regime"] == "NEUTRAL"
    assert report["confidence"] > 0
    assert report["analysis"]["short_term"] != "Assessing price action..."
    assert report["analysis"]["tactical_edge"] != "Monitoring whale flow..."
    assert report["analysis"]["risk_profile"] != "Evaluating traps..."
    assert "BORING MORTALS" not in json.dumps(report)
    assert created_rows and created_rows[0]["confidence_score"] == report["confidence"]


def test_generate_asset_report_stays_neutral_when_single_ticker_has_no_specific_evidence(monkeypatch):
    monkeypatch.setattr(
        "core.ai_report.asset.collect_asset_snapshot",
        lambda _ticker, caches=None: {
            "ticker": "ACAP",
            "as_of": "2026-05-20T16:40:00",
            "scope": None,
            "lead_ticker": None,
            "scope_levels": None,
            "lead_ticker_levels": None,
            "technical_context": {
                "macro_regime": "HEALTHY UPTREND",
                "is_bull_trap": False,
                "is_bear_trap": False,
            },
            "whale_flow": [],
            "sentiment": {"score": 50.0, "regime": "NEUTRAL"},
            "news_mentions": [],
            "scope_news_mentions": [],
            "lead_ticker_news_mentions": [],
            "arbitrage": None,
            "recommendation": {
                "ticker": "ACAP",
                "side": None,
                "score": 0.0,
                "confidence": 0.0,
                "entry": None,
                "stop": None,
                "target": None,
                "rationale": None,
            },
        },
    )

    report = asset.generate_asset_report("acap", save=False)

    assert report["ticker"] == "ACAP"
    assert report["verdict"] == "NEUTRAL"
    assert report["confidence"] <= 40
    assert "No ACAP-specific signal" in report["analysis"]["short_term"]
    assert report["snapshot"]["asset_evidence"]["has_specific_signal"] is False


def test_asset_report_requires_refresh_detects_legacy_placeholder_payload():
    assert asset.asset_report_requires_refresh(
        {
            "analysis": {
                "short_term": "Assessing price action...",
                "tactical_edge": "Monitoring whale flow...",
                "risk_profile": "Evaluating traps...",
            },
            "snapshot": {
                "sentiment": {"regime": "BORING MORTALS"},
            },
        }
    )

    assert not asset.asset_report_requires_refresh(
        {
            "analysis": {
                "short_term": "COMI is constructive with improving breadth.",
                "tactical_edge": "Whale flow is supportive and sentiment is neutral.",
                "risk_profile": "Failed follow-through remains the main risk.",
            },
            "snapshot": {
                "sentiment": {"regime": "NEUTRAL"},
                "price_levels": {"current_price": 82.5, "supports": [], "resistances": []},
            },
        }
    )


def test_asset_report_requires_refresh_detects_macro_only_directional_asset_payload():
    assert asset.asset_report_requires_refresh(
        {
            "ticker": "ACAP",
            "verdict": "BULLISH",
            "confidence": 60.0,
            "analysis": {
                "short_term": "ACAP is tilting constructive with healthy uptrend macro pressure and 60% tactical conviction.",
                "tactical_edge": "Cross-module confirmation is light.",
                "risk_profile": "Confirmation is still shallow.",
            },
            "snapshot": {
                "ticker": "ACAP",
                "scope": None,
                "technical_context": {
                    "macro_regime": "HEALTHY UPTREND",
                    "is_bull_trap": False,
                    "is_bear_trap": False,
                },
                "whale_flow": [],
                "sentiment": {"score": 50.0, "regime": "NEUTRAL"},
                "news_mentions": [],
                "arbitrage": None,
                "recommendation": {
                    "ticker": "ACAP",
                    "side": None,
                    "score": 0.0,
                    "confidence": 0.0,
                    "entry": None,
                    "stop": None,
                    "target": None,
                },
            },
        }
    )


def test_collect_asset_snapshot_builds_price_history_levels_without_promoting_to_signal(monkeypatch):
    monkeypatch.setattr("core.ai_report.asset.SignalRecommendation.select", lambda: _FakeQuery())
    monkeypatch.setattr(
        "core.DataManager.DataManager.get_stock_data",
        lambda ticker, limit=90: pd.DataFrame(
            {
                "Open": [7.62, 7.57, 7.60, 7.61, 7.59, 7.74, 7.91, 8.28, 8.84, 8.61],
                "High": [7.75, 7.69, 7.75, 7.68, 7.75, 8.20, 8.35, 9.47, 9.10, 8.75],
                "Low": [7.56, 7.57, 7.60, 7.53, 7.55, 7.74, 7.91, 8.28, 8.48, 8.28],
                "Close": [7.57, 7.60, 7.61, 7.59, 7.74, 7.91, 8.28, 8.84, 8.61, 8.31],
                "Volume": [510246, 271234, 362879, 531345, 497406, 1851258, 2438110, 4591283, 1342213, 1277016],
            },
            index=pd.date_range("2026-05-06", periods=10),
        ),
    )

    snapshot = asset.collect_asset_snapshot(
        "acap",
        caches={
            "ORACLE_CACHE": {"data": {"EGX30": {"signal": "HEALTHY UPTREND"}}, "timestamp": "2026-05-20T17:00:00"},
            "WHALE_CACHE": {"data": {"candidates": []}, "timestamp": "2026-05-20T17:00:00"},
            "TRAP_CACHE": {"data": {"bull_traps": [], "bear_traps": []}, "timestamp": "2026-05-20T17:00:00"},
            "NEWS_CACHE": {"data": [], "timestamp": "2026-05-20T17:00:00"},
            "ARBITRAGE_CACHE": {"data": {"mirrors": []}, "timestamp": "2026-05-20T17:00:00"},
        },
    )

    assert snapshot["ticker"] == "ACAP"
    assert snapshot["asset_evidence"]["has_specific_signal"] is False
    assert snapshot["price_levels"]["current_price"] == 8.31
    assert snapshot["price_levels"]["supports"]
    assert snapshot["price_levels"]["resistances"]
    assert snapshot["price_levels"]["supports"][0]["price"] <= 8.31
    assert snapshot["price_levels"]["resistances"][0]["price"] >= 8.31


def test_collect_asset_snapshot_aggregates_market_scope_inputs(monkeypatch):
    macro_calls = []

    def _fake_macro(index_choice):
        macro_calls.append(index_choice)
        return {"signal": "BULLISH"}

    monkeypatch.setattr(
        "core.ai_report.asset.MarketPredictor.check_macro_health",
        _fake_macro,
    )
    monkeypatch.setattr(
        "core.ai_report.asset.MarketLists.get_market_list",
        lambda choice: {"COMI", "MFPC"} if str(choice).upper() == "EGX70" else set(),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.Vanaheim.hunt_whales",
        lambda: {
            "candidates": [
                {"Ticker": "COMI", "Signal": "ACCUMULATION", "Volume_Ratio": 2.3},
                {"Ticker": "TMGH", "Signal": "ACCUMULATION", "Volume_Ratio": 3.1},
            ]
        },
    )
    monkeypatch.setattr(
        "core.ai_report.asset.Svartalfheim.hunt_traps",
        lambda: {
            "bull_traps": [{"ticker": "COMI"}],
            "bear_traps": [{"ticker": "MFPC"}],
        },
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.gather_gossip",
        lambda: {
            "stories": [
                {"title": "COMI expands lending book", "tickers": ["COMI"], "gossip_score": 3},
                {"title": "Elsewhere", "tickers": ["TMGH"], "gossip_score": 1},
            ]
        },
    )
    async def _fake_async_scope_gossip():
        return {
            "stories": [
                {"title": "COMI expands lending book", "tickers": ["COMI"], "gossip_score": 3},
                {"title": "Elsewhere", "tickers": ["TMGH"], "gossip_score": 1},
            ]
        }

    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.async_gather_gossip",
        _fake_async_scope_gossip,
        raising=False,
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.get_bifrost_sentiment",
        lambda stories: {"score": 61.0, "regime": "POSITIVE", "sample_size": len(stories)},
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SandboxRegistry.get_lagged_correlations",
        lambda: {
            "mirrors": [
                {"symbol": "COMI", "leader": "MFPC", "correlation": 0.84},
                {"symbol": "TMGH", "leader": "HRHO", "correlation": 0.93},
            ]
        },
    )

    LatestRec = type(
        "LatestRec",
        (),
        {},
    )
    top_rec = LatestRec()
    top_rec.ticker = "COMI"
    top_rec.side = "BUY"
    top_rec.score = 8.4
    top_rec.confidence = 76.0
    top_rec.entry_price = 82.5
    top_rec.stop_loss = 79.0
    top_rec.target_price = 89.0
    top_rec.rationale_json = None
    second_rec = LatestRec()
    second_rec.ticker = "MFPC"
    second_rec.side = "BUY"
    second_rec.score = 7.1
    second_rec.confidence = 68.0
    second_rec.entry_price = 77.8
    second_rec.stop_loss = 74.9
    second_rec.target_price = 84.2
    second_rec.rationale_json = None
    monkeypatch.setattr(
        "core.ai_report.asset.SignalRecommendation.select",
        lambda: _FakeQuery([top_rec, second_rec]),
    )

    snapshot = asset.collect_asset_snapshot("egx70")

    assert macro_calls == ["EGX70"]
    assert snapshot["ticker"] == "EGX70"
    assert snapshot["technical_context"]["macro_regime"] == "BULLISH"
    assert snapshot["technical_context"]["bull_trap_count"] == 1
    assert snapshot["technical_context"]["bear_trap_count"] == 1
    assert snapshot["news_mentions"][0]["title"] == "COMI expands lending book"
    assert snapshot["scope"] == "EGX70"
    assert snapshot["lead_ticker"] == "COMI"
    assert snapshot["scope_news_mentions"][0]["title"] == "COMI expands lending book"
    assert snapshot["lead_ticker_news_mentions"][0]["title"] == "COMI expands lending book"
    assert snapshot["lead_ticker_levels"]["ticker"] == "COMI"
    assert snapshot["lead_ticker_levels"]["entry"] == 82.5
    assert snapshot["scope_levels"]["supports"][0]["members"] >= 1
    assert snapshot["scope_levels"]["resistances"][0]["members"] >= 1
    assert snapshot["recommendation"]["entry"] == 82.5
    assert snapshot["arbitrage"]["symbol"] == "COMI"


def test_collect_asset_snapshot_prefers_warm_shared_caches(monkeypatch):
    monkeypatch.setattr(
        "core.ai_report.asset.MarketLists.get_market_list",
        lambda choice: {"COMI", "MFPC"} if str(choice).upper() == "EGX70" else set(),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.MarketPredictor.check_macro_health",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("macro should come from cache")),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.Vanaheim.hunt_whales",
        lambda: (_ for _ in ()).throw(AssertionError("whales should come from cache")),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.Svartalfheim.hunt_traps",
        lambda: (_ for _ in ()).throw(AssertionError("traps should come from cache")),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.gather_gossip",
        lambda: (_ for _ in ()).throw(AssertionError("news should come from cache")),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.async_gather_gossip",
        lambda: (_ for _ in ()).throw(AssertionError("async news should come from cache")),
        raising=False,
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SandboxRegistry.get_lagged_correlations",
        lambda: (_ for _ in ()).throw(AssertionError("arbitrage should come from cache")),
    )
    monkeypatch.setattr(
        "core.ai_report.asset.SentimentCrawler.get_bifrost_sentiment",
        lambda stories: {"score": 57.0, "regime": "NEUTRAL", "sample_size": len(stories)},
    )

    LatestRec = type("LatestRec", (), {})
    rec = LatestRec()
    rec.ticker = "COMI"
    rec.side = "BUY"
    rec.score = 8.1
    rec.confidence = 74.0
    rec.entry_price = 82.0
    rec.stop_loss = 79.2
    rec.target_price = 88.4
    rec.rationale_json = None
    monkeypatch.setattr(
        "core.ai_report.asset.SignalRecommendation.select",
        lambda: _FakeQuery([rec]),
    )

    snapshot = asset.collect_asset_snapshot(
        "EGX70",
        caches={
            "ORACLE_CACHE": {"data": {"EGX70": {"signal": "BULLISH"}}, "timestamp": "2026-04-14T09:00:00"},
            "WHALE_CACHE": {
                "data": {"candidates": [{"Ticker": "COMI", "Signal": "ACCUMULATION", "Volume_Ratio": 2.2}]},
                "timestamp": "2026-04-14T09:00:00",
            },
            "TRAP_CACHE": {
                "data": {"bull_traps": [{"ticker": "COMI"}], "bear_traps": []},
                "timestamp": "2026-04-14T09:00:00",
            },
            "NEWS_CACHE": {
                "data": [{"title": "COMI leads EGX70 breadth", "tickers": ["COMI"], "gossip_score": 4}],
                "timestamp": "2026-04-14T09:00:00",
            },
            "ARBITRAGE_CACHE": {
                "data": {"mirrors": [{"symbol": "COMI", "leader": "MFPC", "correlation": 0.81}]},
                "timestamp": "2026-04-14T09:00:00",
            },
        },
    )

    assert snapshot["technical_context"]["macro_regime"] == "BULLISH"
    assert snapshot["whale_flow"][0]["Ticker"] == "COMI"
    assert snapshot["technical_context"]["bull_trap_count"] == 1
    assert snapshot["news_mentions"][0]["title"] == "COMI leads EGX70 breadth"
    assert snapshot["arbitrage"]["symbol"] == "COMI"
    assert snapshot["lead_ticker"] == "COMI"


def test_asset_report_route_returns_scope_payload_when_pipeline_ready(monkeypatch):
    monkeypatch.setattr(
        "api.refresh_pipeline_state",
        lambda force=False: {
            "status": "READY",
            "message": "System Operational",
            "bootstrap_complete": True,
            "pipeline_state": "FRESH",
            "stale_mode": False,
            "freshness": {"overall_ok": True},
        },
    )
    monkeypatch.setattr(
        "routes.ai_report._core_generate_asset_report",
        lambda ticker, save=True, caches=None: {
            "status": "success",
            "ticker": ticker,
            "generated_at": "2026-04-14T08:40:00",
            "verdict": "BULLISH",
            "confidence": 71.0,
            "snapshot": {
                "ticker": ticker,
                "scope": ticker if ticker in {"EGX30", "EGX70", "EGX100", "ALL"} else None,
                "lead_ticker": "COMI",
                "scope_levels": {
                    "supports": [{"price": 79.1, "strength": 0.8, "label": "support_cluster_1", "members": 3}],
                    "resistances": [{"price": 88.6, "strength": 0.75, "label": "resistance_cluster_1", "members": 4}],
                },
                "lead_ticker_levels": {
                    "ticker": "COMI",
                    "entry": 82.5,
                    "stop": 79.0,
                    "target": 88.6,
                },
                "scope_news_mentions": [{"title": "Breadth improves", "gossip_score": 3}],
                "lead_ticker_news_mentions": [{"title": "COMI attracts follow-through", "gossip_score": 5}],
                "sentiment": {"score": 58.0, "regime": "NEUTRAL"},
                "recommendation": {"ticker": "COMI", "entry": 82.5, "stop": 79.0, "target": 88.6},
            },
            "analysis": {
                "short_term": "Constructive scope setup.",
                "tactical_edge": "Basket breadth supports the lead ticker.",
                "risk_profile": "Failed follow-through remains the main risk.",
            },
        },
    )

    for ticker in ("EGX30", "EGX70", "EGX100", "ALL"):
        response = client.get(f"/api/v1/ai/asset-report?ticker={ticker}&force_refresh=true")

        assert response.status_code == 200
        body = response.json()
        assert body["ticker"] == ticker
        assert body["snapshot"]["scope"] == ticker
        assert body["snapshot"]["lead_ticker"] == "COMI"
        assert body["snapshot"]["scope_levels"]["supports"][0]["members"] == 3
        assert body["snapshot"]["lead_ticker_levels"]["entry"] == 82.5
        assert body["snapshot"]["scope_news_mentions"][0]["title"] == "Breadth improves"
        assert body["snapshot"]["lead_ticker_news_mentions"][0]["title"] == "COMI attracts follow-through"
