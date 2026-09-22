from unittest.mock import patch

from core.ai_report import snapshot as snapshot_service
from core.ai_report.snapshot import (
    _collect_signal_snapshot,
    _collect_cross_tab_snapshot,
    _collect_portfolio_snapshot,
    _compute_data_freshness,
    _extract_sector_leaders,
    _score_market_direction,
)
from database import SignalRecommendation, SignalRun

def test_extract_sector_leaders():
    sectors = [
        {"Sector": "Tech", "Status": "LEADING", "x": 1.0, "y": 2.0},
        {"Sector": "Energy", "Status": "LAGGING", "x": 0.5, "y": 1.0},
        {"Sector": "Finance", "Status": "LEADING", "x": 0.7, "y": 3.0},
    ]
    assert _extract_sector_leaders(sectors, "LEADING") == [
        {"sector": "Finance", "x": 0.7, "y": 3.0},
        {"sector": "Tech", "x": 1.0, "y": 2.0},
    ]
    assert _extract_sector_leaders(sectors, "LAGGING") == [{"sector": "Energy", "x": 0.5, "y": 1.0}]
    assert _extract_sector_leaders([], "LEADING") == []

def test_score_market_direction_logic():
    snapshot = {
        "oracle": {"macro_signal": "BULLISH", "macro_correlation": 0.8},
        "strategy": {"regime": "BULLISH", "regime_score": 85},
        "whales": {"accumulation_count": 10, "distribution_count": 2},
        "news": {"sentiment_score": 75, "sentiment_regime": "BULLISH"},
        "sectors": {"leading": ["Tech", "Energy"], "lagging": []},
        "traps": {"bear_trap_count": 5, "bull_trap_count": 0},
        "signals": {"buy_count": 8, "sell_count": 1, "avg_score": 8.0, "avg_confidence": 75},
        "portfolio": {"open_positions": 2, "total_pnl": 5000}
    }
    score, reasons = _score_market_direction(snapshot)
    assert score > 10  # Very bullish
    assert any("Oracle macro signal is BULLISH" in r for r in reasons)
    assert any("Strong whale accumulation" in r for r in reasons)


def test_score_market_direction_treats_full_bull_as_bullish():
    snapshot = {
        "oracle": {"macro_signal": "NEUTRAL", "macro_correlation": 0.0},
        "strategy": {"regime": "FULL BULL", "regime_score": 85},
        "whales": {"accumulation_count": 0, "distribution_count": 0},
        "news": {"sentiment_score": 50, "sentiment_regime": "NEUTRAL"},
        "sectors": {"leading": [], "lagging": []},
        "traps": {"bear_trap_count": 0, "bull_trap_count": 0},
        "signals": {"buy_count": 0, "sell_count": 0, "avg_score": 0.0, "avg_confidence": 0.0},
        "portfolio": {"open_positions": 0, "total_pnl": 0.0},
    }

    score, reasons = _score_market_direction(snapshot)

    assert score == 2
    assert any("Strategy engine regime is BULLISH" in r for r in reasons)

def test_compute_data_freshness_logic():
    caches = {
        "NEWS_CACHE": {"timestamp": "2024-01-01T12:00:00"},
        "SECTOR_CACHE": {"timestamp": "2024-01-01T12:00:00"},
        "WHALE_CACHE": {"timestamp": "2024-01-01T12:00:00"},
        "TRAP_CACHE": {"timestamp": "2024-01-01T12:00:00"},
        "ARBITRAGE_CACHE": {"timestamp": "2024-01-01T12:00:00"},
        "STRATEGY_CACHE": {"timestamp": "2024-01-01T12:00:00"},
        "ORACLE_CACHE": {"timestamp": "2024-01-01T12:00:00"},
    }
    # Mocking TimeUtils.now to be close to the cache timestamps
    with patch("core.TimeUtils.now") as mock_now:
        import datetime
        mock_now.return_value = datetime.datetime.fromisoformat("2024-01-01T12:05:00")
        freshness = _compute_data_freshness(caches)
        assert freshness["label"] == "FRESH"
        assert freshness["degraded"] is False
        assert 80.0 <= freshness["score"] <= 84.0


def test_collect_portfolio_snapshot_missing_user_portfolio_degrades():
    snapshot = _collect_portfolio_snapshot(None)

    assert snapshot["degraded"] is True
    assert snapshot["degradation_reason"] == "user_portfolio_missing"
    assert snapshot["portfolio_id"] is None
    assert snapshot["issues"][0]["module"] == "portfolio"


def test_collect_cross_tab_snapshot_surfaces_module_failures(monkeypatch):
    caches = {
        "NEWS_CACHE": {},
        "SECTOR_CACHE": {},
        "WHALE_CACHE": {},
        "TRAP_CACHE": {},
        "ARBITRAGE_CACHE": {},
        "STRATEGY_CACHE": {},
        "ORACLE_CACHE": {},
    }

    monkeypatch.setattr(
        snapshot_service.SentimentCrawler,
        "gather_gossip",
        lambda: (_ for _ in ()).throw(RuntimeError("news source down")),
        raising=False,
    )
    monkeypatch.setattr(
        snapshot_service.SentimentCrawler,
        "get_bifrost_sentiment",
        lambda news: (_ for _ in ()).throw(RuntimeError("sentiment source down")),
        raising=False,
    )
    monkeypatch.setattr(
        snapshot_service.SectorRotation,
        "analyze_rotation",
        lambda: (_ for _ in ()).throw(RuntimeError("sector source down")),
        raising=False,
    )
    monkeypatch.setattr(snapshot_service.Vanaheim, "hunt_whales", lambda: {"status": "ok", "count": 0, "candidates": []}, raising=False)
    monkeypatch.setattr(snapshot_service.Svartalfheim, "hunt_traps", lambda: {"status": "ok", "bull_traps": [], "bear_traps": []}, raising=False)
    monkeypatch.setattr(snapshot_service.SandboxRegistry, "get_lagged_correlations", lambda: {"status": "ok", "count": 0, "mirrors": []}, raising=False)
    monkeypatch.setattr(snapshot_service.ExecutionWatchdog, "generate_strategy_proposal", lambda: {}, raising=False)
    monkeypatch.setattr(snapshot_service.MarketPredictor, "check_macro_health", lambda market: {"signal": "NEUTRAL", "message": "ok", "correlation": 0.0}, raising=False)
    monkeypatch.setattr(snapshot_service.MarketPredictor, "hunt_the_coil", lambda: {"status": "ok", "count": 0, "candidates": []}, raising=False)

    snapshot = _collect_cross_tab_snapshot(
        None,
        caches,
        collect_signal_snapshot=lambda: {"active_recommendations": [], "buy_count": 0, "sell_count": 0, "avg_score": 0.0, "avg_confidence": 0.0},
        collect_portfolio_snapshot=lambda portfolio_id=None: {
            "portfolio_id": None,
            "portfolio_name": None,
            "open_positions": 0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_pnl": 0.0,
            "top_positions": [],
            "warnings": [],
            "degraded": False,
            "degradation_reason": None,
            "issues": [],
        },
    )

    assert snapshot["snapshot_degradation"]["degraded"] is True
    modules = {issue["module"] for issue in snapshot["snapshot_degradation"]["issues"]}
    assert "news" in modules
    assert "news_sentiment" in modules
    assert "sectors" in modules


def test_collect_cross_tab_snapshot_marks_live_fallback_sources_fresh(monkeypatch):
    import datetime

    caches = {
        "NEWS_CACHE": {},
        "SECTOR_CACHE": {},
        "WHALE_CACHE": {},
        "TRAP_CACHE": {},
        "ARBITRAGE_CACHE": {},
        "STRATEGY_CACHE": {},
        "ORACLE_CACHE": {},
    }
    fixed_now = datetime.datetime(2026, 5, 4, 15, 0, 0)

    monkeypatch.setattr("core.TimeUtils.now", lambda: fixed_now)
    monkeypatch.setattr(snapshot_service.SentimentCrawler, "gather_gossip", lambda: {"stories": []}, raising=False)
    monkeypatch.setattr(
        snapshot_service.SentimentCrawler,
        "get_bifrost_sentiment",
        lambda news: {"score": 50.0, "regime": "NEUTRAL", "sample_size": 0},
        raising=False,
    )
    monkeypatch.setattr(snapshot_service.SectorRotation, "analyze_rotation", lambda: [], raising=False)
    monkeypatch.setattr(snapshot_service.Vanaheim, "hunt_whales", lambda: {"status": "ok", "count": 0, "candidates": []}, raising=False)
    monkeypatch.setattr(snapshot_service.Svartalfheim, "hunt_traps", lambda: {"status": "ok", "bull_traps": [], "bear_traps": []}, raising=False)
    monkeypatch.setattr(snapshot_service.SandboxRegistry, "get_lagged_correlations", lambda: {"status": "ok", "count": 0, "mirrors": []}, raising=False)
    monkeypatch.setattr(snapshot_service.ExecutionWatchdog, "generate_strategy_proposal", lambda: {}, raising=False)
    monkeypatch.setattr(snapshot_service.MarketPredictor, "check_macro_health", lambda market: {"signal": "NEUTRAL", "message": "ok", "correlation": 0.0}, raising=False)
    monkeypatch.setattr(snapshot_service.MarketPredictor, "hunt_the_coil", lambda: {"status": "ok", "count": 0, "candidates": []}, raising=False)

    snapshot = _collect_cross_tab_snapshot(
        None,
        caches,
        collect_signal_snapshot=lambda: {"active_recommendations": [], "buy_count": 0, "sell_count": 0, "avg_score": 0.0, "avg_confidence": 0.0},
        collect_portfolio_snapshot=lambda portfolio_id=None: {
            "portfolio_id": None,
            "portfolio_name": None,
            "open_positions": 0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_pnl": 0.0,
            "top_positions": [],
            "warnings": [],
            "degraded": False,
            "degradation_reason": None,
            "issues": [],
        },
    )

    freshness = snapshot["data_freshness"]
    assert freshness["label"] == "FRESH"
    assert freshness["missing_sources"] == []
    assert freshness["stale_sources"] == []
    assert all(cache.get("timestamp") == fixed_now for cache in caches.values())


def test_collect_cross_tab_snapshot_aggregates_whale_trap_signal_metadata(monkeypatch):
    caches = {
        "NEWS_CACHE": {},
        "SECTOR_CACHE": {},
        "WHALE_CACHE": {"data": {"status": "ok", "count": 0, "candidates": []}},
        "TRAP_CACHE": {"data": {"status": "ok", "bull_traps": [], "bear_traps": []}},
        "ARBITRAGE_CACHE": {"data": {"status": "ok", "count": 0, "mirrors": []}},
        "STRATEGY_CACHE": {"data": {"regime": "NEUTRAL", "regime_score": 50, "volatility": "NORMAL"}},
        "ORACLE_CACHE": {},
    }

    monkeypatch.setattr(snapshot_service.SentimentCrawler, "gather_gossip", lambda: [], raising=False)
    monkeypatch.setattr(snapshot_service.SentimentCrawler, "get_bifrost_sentiment", lambda news: {"score": 50.0, "regime": "BORING MORTALS", "sample_size": 0}, raising=False)
    monkeypatch.setattr(snapshot_service.SectorRotation, "analyze_rotation", lambda: [], raising=False)
    monkeypatch.setattr(snapshot_service.MarketPredictor, "check_macro_health", lambda market: {"signal": "NEUTRAL", "message": "ok", "correlation": 0.0}, raising=False)
    monkeypatch.setattr(snapshot_service.MarketPredictor, "hunt_the_coil", lambda: {"status": "ok", "count": 0, "candidates": []}, raising=False)

    snapshot = _collect_cross_tab_snapshot(
        None,
        caches,
        collect_signal_snapshot=lambda: {
            "active_recommendations": [
                {
                    "ticker": "COMI",
                    "side": "BUY",
                    "score": 8.0,
                    "enforcement_state": "ALLOW",
                    "enforcement_reason": "not_enforced",
                    "enforcement_profile": "EGX30_GUARDED",
                    "route_profile": "EGX30_TREND_PROFILE",
                    "whale_alignment": "SUPPORTIVE",
                    "whale_signal": "ACCUMULATION",
                    "whale_strength": 1.0,
                    "trap_risk_score": 0,
                    "trap_risk_band": "LOW",
                    "trap_risk_reason": "low_risk_alignment",
                },
                {
                    "ticker": "FWRY",
                    "side": "BUY",
                    "score": 7.0,
                    "enforcement_state": "BLOCK_EXECUTION",
                    "enforcement_reason": "severe_trap_risk",
                    "enforcement_profile": "EGX70_HARDENED",
                    "route_profile": "EGX70_TACTICAL_PROFILE",
                    "whale_alignment": "NEUTRAL",
                    "whale_signal": "UNKNOWN",
                    "whale_strength": 0.8,
                    "trap_risk_score": 68,
                    "trap_risk_band": "HIGH",
                    "trap_risk_reason": "distribution_against_breakout",
                },
                {
                    "ticker": "SWDY",
                    "side": "BUY",
                    "score": 6.0,
                    "enforcement_state": "BLOCK_EXECUTION",
                    "enforcement_reason": "severe_trap_risk",
                    "enforcement_profile": "EGX70_HARDENED",
                    "route_profile": "EGX70_TACTICAL_PROFILE",
                    "whale_alignment": "NEUTRAL",
                    "trap_risk_score": 82,
                    "trap_risk_band": "SEVERE",
                    "trap_risk_reason": "illiquid_breakout",
                },
            ],
            "buy_count": 3,
            "sell_count": 0,
            "avg_score": 7.0,
            "avg_confidence": 70.0,
        },
        collect_portfolio_snapshot=lambda portfolio_id=None: {
            "portfolio_id": None,
            "portfolio_name": None,
            "open_positions": 0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_pnl": 0.0,
            "top_positions": [],
            "warnings": [],
            "degraded": False,
            "degradation_reason": None,
            "issues": [],
        },
    )

    summary = snapshot["signals"]["whale_trap_summary"]
    assert summary["supportive_whale_alignments"] == 1
    assert summary["whale_conflicts"] == 0
    assert summary["high_trap_risk_count"] == 1
    assert summary["severe_trap_risk_count"] == 1
    assert summary["top_trap_risk_reasons"]["distribution_against_breakout"] == 1
    assert summary["top_trap_risk_reasons"]["illiquid_breakout"] == 1
    assert summary["top_supportive_names"][0]["ticker"] == "COMI"
    assert summary["top_conflicted_or_high_risk_names"][0]["ticker"] == "SWDY"
    enforcement = snapshot["signals"]["enforcement_summary"]
    assert enforcement["allow_count"] == 1
    assert enforcement["watch_only_count"] == 0
    assert enforcement["block_count"] == 2
    assert enforcement["counts_by_reason"] == {"severe_trap_risk": 2}
    calibration = snapshot["signals"]["calibration_summary"]
    assert calibration["rollout_mode"] == "compare_only"
    assert calibration["market_segments"]["EGX30"]["active_enforcement_profile"] == "EGX30_GUARDED"
    assert calibration["market_segments"]["EGX30"]["rollback_profile"] == "EGX30_BALANCED"
    assert calibration["market_segments"]["EGX30"]["calibration_summary"]["candidates"]["EGX30_BALANCED"]["deltas"]["watch_only_delta"] == 0
    assert calibration["market_segments"]["EGX70"]["active_enforcement_profile"] == "EGX70_HARDENED"
    assert calibration["market_segments"]["EGX70"]["rollback_profile"] == "EGX70_STRICT"
    assert calibration["market_segments"]["EGX70"]["calibration_summary"]["candidates"]["EGX70_STRICT"]["deltas"]["watch_only_delta"] == 1
    assert calibration["top_delta_reasons"][0] == {"reason": "high_trap_risk", "delta": 1}


def test_collect_signal_snapshot_surfaces_whale_trap_metadata_from_rationale_json():
    run = SignalRun.create(
        run_date=snapshot_service.TimeUtils.today(),
        scan_type="DAILY",
        status="COMPLETED",
        signals_count=1,
    )
    SignalRecommendation.create(
        run=run,
        ticker="COMI",
        side="BUY",
        entry_price=100.0,
        stop_loss=95.0,
        target_price=110.0,
        score=8.0,
        confidence=80.0,
        state="ACTIVE",
        rationale_json='{"whale_signal":"ACCUMULATION","whale_alignment":"SUPPORTIVE","whale_strength":1.0,"whale_reason":"accumulation_support","trap_risk_score":0,"trap_risk_band":"LOW","trap_risk_reason":"low_risk_alignment","enforcement_state":"ALLOW","enforcement_reason":"not_enforced","enforcement_profile":"EGX30_GUARDED"}',
    )

    snapshot = _collect_signal_snapshot()

    rec = next(row for row in snapshot["active_recommendations"] if row["ticker"] == "COMI")
    assert rec["whale_signal"] == "ACCUMULATION"
    assert rec["whale_alignment"] == "SUPPORTIVE"
    assert rec["trap_risk_band"] == "LOW"
    assert rec["trap_risk_reason"] == "low_risk_alignment"
    assert rec["enforcement_state"] == "ALLOW"
    assert rec["enforcement_reason"] == "not_enforced"
    assert rec["enforcement_profile"] == "EGX30_GUARDED"
