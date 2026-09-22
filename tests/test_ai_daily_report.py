from core.settings import settings
from fastapi.testclient import TestClient
import copy

from api import app
from routes import ai_report
from core.ai_report.transport import build_ai_report_telegram_message

client = TestClient(app, raise_server_exceptions=False)


class _ReadyOllamaManager:
    def __init__(self, base_url: str = "http://ollama.internal:11434"):
        self.base_url = base_url

    def ensure_service_running(self, async_start=True):
        return True

    def wait_until_ready(self, timeout_sec):
        return True

    def stop_service(self, timeout_sec=10.0):
        return True

    def uses_local_service(self):
        return False


def _patch_ready_ollama_manager(monkeypatch):
    monkeypatch.setattr(
        "routes.ai_report._build_ollama_manager",
        lambda base_url=None: _ReadyOllamaManager(base_url or "http://ollama.internal:11434"),
        raising=False,
    )


def _snapshot_fixture():
    return {
        "as_of": "2026-02-27T10:00:00",
        "news": {"count": 4, "sentiment_score": 61, "sentiment_regime": "EUXUBERANT GREED", "headlines": []},
        "sectors": {"count": 10, "leading": [{"sector": "Banks", "x": 1.2, "y": 2.4}], "lagging": []},
        "whales": {
            "count": 2,
            "accumulation_count": 2,
            "distribution_count": 0,
            "top_accumulation": [{"Ticker": "COMI", "Signal": "ACCUMULATION"}],
            "top_distribution": [],
        },
        "traps": {"bull_trap_count": 0, "bear_trap_count": 1, "recent_bull_traps": [], "recent_bear_traps": []},
        "arbitrage": {"count": 1, "top_mirrors": []},
        "strategy": {"regime": "BULLISH", "regime_score": 7, "volatility": "NORMAL", "reasoning": "Test", "changes": []},
        "oracle": {"macro_signal": "HEALTHY UPTREND", "macro_message": "Test", "macro_correlation": 0.7, "squeeze_count": 0, "top_squeezes": []},
        "signals": {
            "latest_run": {"run_id": 1, "run_date": "2026-02-27", "scan_type": "DAILY", "signals_count": 3},
            "active_recommendations": [
                {
                    "ticker": "COMI",
                    "side": "BUY",
                    "entry_price": 100.0,
                    "stop_loss": 95.0,
                    "target_price": 108.0,
                    "score": 8.0,
                    "confidence": 81.0,
                    "regime": "BULLISH",
                    "whale_signal": "ACCUMULATION",
                    "whale_strength": 1.0,
                    "whale_alignment": "SUPPORTIVE",
                    "whale_reason": "accumulation_support",
                    "trap_risk_score": 0,
                    "trap_risk_band": "LOW",
                    "trap_risk_reason": "low_risk_alignment",
                    "enforcement_state": "ALLOW",
                    "enforcement_visibility": "VISIBLE",
                    "enforcement_reason": "not_enforced",
                    "enforcement_notes": "No whale/trap enforcement threshold breached.",
                    "enforcement_profile": "EGX30_GUARDED",
                },
                {
                    "ticker": "FWRY",
                    "side": "BUY",
                    "entry_price": 20.0,
                    "stop_loss": 18.5,
                    "target_price": 23.0,
                    "score": 7.0,
                    "confidence": 73.0,
                    "regime": "BULLISH",
                    "whale_signal": "UNKNOWN",
                    "whale_strength": 0.82,
                    "whale_alignment": "NEUTRAL",
                    "whale_reason": "neutral_alignment",
                    "trap_risk_score": 78,
                    "trap_risk_band": "HIGH",
                    "trap_risk_reason": "distribution_against_breakout",
                    "enforcement_state": "BLOCK_EXECUTION",
                    "enforcement_visibility": "VISIBLE",
                    "enforcement_reason": "severe_trap_risk",
                    "enforcement_notes": "Blocked for execution because severe trap risk breached the shadow threshold.",
                    "enforcement_profile": "EGX70_HARDENED",
                }
            ],
            "latest_scanner_signals": [],
            "buy_count": 2,
            "sell_count": 0,
            "avg_score": 7.5,
            "avg_confidence": 77.0,
            "whale_trap_summary": {
                "rollout_mode": "shadow",
                "supportive_whale_alignments": 1,
                "whale_conflicts": 1,
                "high_trap_risk_count": 0,
                "severe_trap_risk_count": 1,
                "top_trap_risk_reasons": {"distribution_against_breakout": 1},
                "threshold_analysis": {
                    "rollout_mode": "shadow",
                    "would_review_count": 1,
                    "would_block_count": 1,
                    "top_block_reasons": {"distribution_against_breakout": 1},
                },
                "top_supportive_names": [{"ticker": "COMI", "whale_signal": "ACCUMULATION", "whale_strength": 1.0, "score": 8.0, "trap_risk_band": "LOW"}],
                "top_conflicted_or_high_risk_names": [{"ticker": "FWRY", "trap_risk_band": "SEVERE", "trap_risk_score": 78, "trap_risk_reason": "distribution_against_breakout", "whale_alignment": "CONFLICT", "score": 7.0}],
            },
            "enforcement_summary": {
                "rollout_mode": "visible_but_blocked",
                "allow_count": 1,
                "watch_only_count": 0,
                "block_count": 1,
                "counts_by_reason": {"severe_trap_risk": 1},
                "counts_by_profile": {
                    "EGX30_GUARDED": {"allow_count": 1, "watch_only_count": 0, "block_count": 0},
                    "EGX70_HARDENED": {"allow_count": 0, "watch_only_count": 0, "block_count": 1},
                },
                "counts_by_market_segment": {
                    "EGX30": {"allow_count": 1, "watch_only_count": 0, "block_count": 0},
                    "EGX70": {"allow_count": 0, "watch_only_count": 0, "block_count": 1},
                },
            },
            "calibration_summary": {
                "rollout_mode": "compare_only",
                "market_segments": {
                    "EGX30": {
                        "active_enforcement_profile": "EGX30_GUARDED",
                        "rollback_profile": "EGX30_BALANCED",
                        "candidate_calibration_profiles": ["EGX30_BALANCED"],
                        "calibration_summary": {
                            "baseline_counts": {"allow_count": 1, "watch_only_count": 0, "block_count": 0},
                            "candidates": {
                                "EGX30_BALANCED": {
                                    "counts": {"allow_count": 1, "watch_only_count": 0, "block_count": 0},
                                    "deltas": {"allow_delta": 0, "watch_only_delta": 0, "block_delta": 0, "reason_deltas": {}},
                                    "top_delta_reasons": [],
                                    "top_reclassified_names": [],
                                }
                            },
                        },
                    },
                    "EGX70": {
                        "active_enforcement_profile": "EGX70_HARDENED",
                        "rollback_profile": "EGX70_STRICT",
                        "candidate_calibration_profiles": ["EGX70_STRICT"],
                        "calibration_summary": {
                            "baseline_counts": {"allow_count": 0, "watch_only_count": 0, "block_count": 1},
                            "candidates": {
                                "EGX70_STRICT": {
                                    "counts": {"allow_count": 0, "watch_only_count": 1, "block_count": 0},
                                    "deltas": {
                                        "allow_delta": 0,
                                        "watch_only_delta": 1,
                                        "block_delta": -1,
                                        "reason_deltas": {"high_trap_risk": 1},
                                    },
                                    "top_delta_reasons": [{"reason": "high_trap_risk", "delta": 1}],
                                    "top_reclassified_names": [
                                        {
                                            "ticker": "FWRY",
                                            "baseline_state": "BLOCK_EXECUTION",
                                            "candidate_state": "WATCH_ONLY",
                                            "baseline_reason": "severe_trap_risk",
                                            "candidate_reason": "high_trap_risk",
                                            "market_segment": "EGX70",
                                        }
                                    ],
                                }
                            },
                        },
                    },
                },
                "top_delta_reasons": [{"reason": "high_trap_risk", "delta": 1}],
                "top_reclassified_names": [
                    {
                        "ticker": "FWRY",
                        "baseline_state": "BLOCK_EXECUTION",
                        "candidate_state": "WATCH_ONLY",
                        "baseline_reason": "severe_trap_risk",
                        "candidate_reason": "high_trap_risk",
                        "market_segment": "EGX70",
                    }
                ],
            },
        },
        "portfolio": {
            "portfolio_id": 1,
            "portfolio_name": "My Portfolio",
            "open_positions": 2,
            "realized_pnl": 1000.0,
            "unrealized_pnl": 200.0,
            "total_pnl": 1200.0,
            "top_positions": [],
            "warnings": [],
        },
    }


def test_ai_daily_report_rule_based(monkeypatch):
    snapshot = _snapshot_fixture()
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", lambda snapshot, fallback_report: (None, None))

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=false")
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "success"
    assert body["source"] == "rule_based"
    assert body["source_module"] == "LOCAL"
    assert body["reasoning_profile"] == "gpt-5.3-codex"
    assert "Think exactly like GPT-5.3-codex" in body["rule_engine_instruction"]
    assert "cache_ttl_sec" in body
    assert "cache_age_sec" in body
    assert "data_freshness" in body
    assert body["cached"] is False
    assert body["market_direction"]["label"] in {"BULLISH", "BEARISH", "NEUTRAL"}
    assert body["market_direction"]["execution_mode"] in {"CAPITAL_PRESERVATION", "DEFENSIVE", "RISK_OFF", "BALANCED", "TREND_FOLLOWING"}
    assert body["market_direction"]["trade_selectivity"] in {"VERY_HIGH", "HIGH", "MEDIUM"}
    assert isinstance(body["daily_report"]["summary"], list)
    assert isinstance(body["recommendations"], list)
    assert isinstance(body["execution_profile"], dict)
    assert body["enforcement_context"]["block_count"] == 1
    assert body["enforcement_context"]["counts_by_reason"]["severe_trap_risk"] == 1
    assert body["calibration_context"]["rollout_mode"] == "compare_only"
    assert body["calibration_context"]["top_delta_reasons"][0]["reason"] == "high_trap_risk"
    assert body["promotion_context"]["market_segments"]["EGX30"]["new_active_profile"] == "EGX30_GUARDED"
    assert body["promotion_context"]["market_segments"]["EGX70"]["rollback_profile"] == "EGX70_STRICT"


def test_generate_rule_based_report_uses_whale_trap_shadow_context():
    snapshot = _snapshot_fixture()

    report = ai_report._generate_rule_based_report(snapshot)

    assert report["shadow_context"]["supportive_whale_alignments"] == 1
    assert report["shadow_context"]["severe_trap_risk_count"] == 1
    assert report["shadow_context"]["threshold_analysis"]["would_review_count"] == 1
    assert report["enforcement_context"]["block_count"] == 1
    assert report["calibration_context"]["rollout_mode"] == "compare_only"
    assert report["promotion_context"]["market_segments"]["EGX70"]["new_active_profile"] == "EGX70_HARDENED"
    assert any("SHADOW FLOW:" in line for line in report["daily_report"]["summary"])
    assert any("SHADOW LEADERS:" in line for line in report["daily_report"]["summary"])
    assert any("SHADOW THRESHOLDS:" in line for line in report["daily_report"]["summary"])
    assert any("ENFORCEMENT:" in line for line in report["daily_report"]["summary"])
    assert any("CALIBRATION:" in line for line in report["daily_report"]["summary"])
    assert any("PROMOTION:" in line for line in report["daily_report"]["summary"])
    assert any("whale accumulation support" in rec["rationale"].lower() for rec in report["recommendations"])
    assert any("blocked by whale/trap enforcement" in rec["rationale"].lower() for rec in report["recommendations"])
    assert any("severe trap-risk candidates" in warning.lower() for warning in report["risk_warnings"])
    assert any("shadow thresholds would review" in warning.lower() for warning in report["risk_warnings"])
    assert any("blocked candidates detected" in warning.lower() for warning in report["risk_warnings"])
    assert any("compare-only calibration" in warning.lower() for warning in report["risk_warnings"])
    assert any("rollback remains available" in warning.lower() for warning in report["risk_warnings"])


def test_generate_rule_based_report_clarifies_composite_stance_vs_strategy_module():
    snapshot = copy.deepcopy(_snapshot_fixture())
    snapshot["strategy"]["regime"] = "FULL BULL"
    snapshot["whales"]["accumulation_count"] = 0
    snapshot["whales"]["distribution_count"] = 0
    snapshot["news"]["sentiment_score"] = 35
    snapshot["sectors"]["leading"] = []
    snapshot["sectors"]["lagging"] = [{"sector": "Industrials", "x": -0.8, "y": -1.2}]
    snapshot["traps"]["bear_trap_count"] = 0
    snapshot["traps"]["bull_trap_count"] = 1
    snapshot["signals"]["buy_count"] = 0
    snapshot["signals"]["sell_count"] = 1
    snapshot["signals"]["avg_score"] = 6.0
    snapshot["signals"]["avg_confidence"] = 52.0

    report = ai_report._generate_rule_based_report(snapshot)

    market_structure = report["daily_report"]["summary"][0]
    assert report["market_direction"]["label"] == "NEUTRAL"
    assert "Composite stance is NEUTRAL" in market_structure
    assert "strategy engine is FULL BULL" in market_structure


def test_ai_daily_report_cache_hit(monkeypatch):
    snapshot = _snapshot_fixture()
    calls = {"n": 0}

    def _collect(_portfolio_id=None):
        calls["n"] += 1
        return snapshot

    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", _collect)
    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", lambda snapshot, fallback_report: (None, None))

    first = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=false")
    assert first.status_code == 200

    second = client.get("/api/v1/ai/daily-report?use_llm=false")
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert calls["n"] == 1


def test_compute_data_freshness_surfaces_missing_and_stale_sources(monkeypatch):
    monkeypatch.setattr(ai_report, "NEWS_CACHE", {"timestamp": None})
    monkeypatch.setattr(ai_report, "SECTOR_CACHE", {"timestamp": "2000-01-01T00:00:00"})
    monkeypatch.setattr(ai_report, "WHALE_CACHE", {"timestamp": "2000-01-01T00:00:00"})
    monkeypatch.setattr(ai_report, "TRAP_CACHE", {"timestamp": "2000-01-01T00:00:00"})
    monkeypatch.setattr(ai_report, "ARBITRAGE_CACHE", {"timestamp": "2000-01-01T00:00:00"})
    monkeypatch.setattr(ai_report, "STRATEGY_CACHE", {"timestamp": "2000-01-01T00:00:00"})
    monkeypatch.setattr(ai_report, "ORACLE_CACHE", {"timestamp": "2000-01-01T00:00:00"})

    freshness = ai_report._compute_data_freshness()

    assert freshness["degraded"] is True
    assert "news" in freshness["missing_sources"]
    assert "sectors" in freshness["stale_sources"]
    assert freshness["source_status"]["news"]["status"] == "missing"
    assert freshness["source_status"]["sectors"]["status"] == "stale"
    assert any(issue["module"] == "news" for issue in freshness["issues"])


def test_collect_portfolio_snapshot_surfaces_missing_user_portfolio_degradation():
    snapshot = ai_report._collect_portfolio_snapshot(None)

    assert snapshot["degraded"] is True
    assert snapshot["degradation_reason"] == "user_portfolio_missing"
    assert snapshot["portfolio_id"] is None
    assert snapshot["issues"][0]["module"] == "portfolio"
    assert "No USER portfolio found." in snapshot["warnings"]


def test_collect_cross_tab_snapshot_surfaces_module_failures(monkeypatch):
    monkeypatch.setattr(ai_report, "NEWS_CACHE", {})
    monkeypatch.setattr(ai_report, "SECTOR_CACHE", {})
    monkeypatch.setattr(ai_report, "WHALE_CACHE", {})
    monkeypatch.setattr(ai_report, "TRAP_CACHE", {})
    monkeypatch.setattr(ai_report, "ARBITRAGE_CACHE", {})
    monkeypatch.setattr(ai_report, "STRATEGY_CACHE", {})
    monkeypatch.setattr(ai_report, "ORACLE_CACHE", {})

    monkeypatch.setattr(
        ai_report.SentimentCrawler,
        "gather_gossip",
        lambda: (_ for _ in ()).throw(RuntimeError("news source down")),
        raising=False,
    )
    monkeypatch.setattr(
        "routes.ai_report.SentimentCrawler.get_bifrost_sentiment",
        lambda news: (_ for _ in ()).throw(RuntimeError("sentiment source down")),
    )
    monkeypatch.setattr(
        "routes.ai_report.SectorRotation.analyze_rotation",
        lambda: (_ for _ in ()).throw(RuntimeError("sector source down")),
    )
    monkeypatch.setattr("routes.ai_report.Vanaheim.hunt_whales", lambda: {"status": "ok", "count": 0, "candidates": []})
    monkeypatch.setattr("routes.ai_report.Svartalfheim.hunt_traps", lambda: {"status": "ok", "bull_traps": [], "bear_traps": []})
    monkeypatch.setattr("routes.ai_report.SandboxRegistry.get_lagged_correlations", lambda: {"status": "ok", "count": 0, "mirrors": []})
    monkeypatch.setattr("routes.ai_report.ExecutionWatchdog.generate_strategy_proposal", lambda: {})
    monkeypatch.setattr("routes.ai_report.MarketPredictor.check_macro_health", lambda market: {"signal": "NEUTRAL", "message": "ok", "correlation": 0.0})
    monkeypatch.setattr("routes.ai_report.MarketPredictor.hunt_the_coil", lambda: {"status": "ok", "count": 0, "candidates": []})
    monkeypatch.setattr("routes.ai_report._collect_signal_snapshot", lambda: _snapshot_fixture()["signals"])
    monkeypatch.setattr(
        "routes.ai_report._collect_portfolio_snapshot",
        lambda portfolio_id=None: {
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

    snapshot = ai_report._collect_cross_tab_snapshot(None)

    assert snapshot["snapshot_degradation"]["degraded"] is True
    assert snapshot["snapshot_degradation"]["module_status"]["news"]["status"] == "degraded"
    assert snapshot["snapshot_degradation"]["module_status"]["sectors"]["status"] == "degraded"
    modules = {issue["module"] for issue in snapshot["snapshot_degradation"]["issues"]}
    assert "news" in modules
    assert "news_sentiment" in modules
    assert "sectors" in modules


def test_llm_generation_uses_ollama_only(monkeypatch):
    fallback_report = {
        "headline": "Fallback",
        "market_direction": {"label": "NEUTRAL", "confidence": 50.0, "time_horizon": "1-3d", "reasoning": []},
        "daily_report": {"summary": [], "cross_tab_findings": []},
        "recommendations": [],
        "risk_warnings": [],
        "next_checklist": [],
    }

    monkeypatch.setattr(settings, "OLLAMA_API_KEY", "", raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_OLLAMA_MODEL", "qwen3-coder:30b", raising=False)

    called = {"ollama": 0}

    def _fake_ollama_report(**kwargs):
        called["ollama"] += 1
        return fallback_report, None

    monkeypatch.setattr("routes.ai_report._call_ollama_report", _fake_ollama_report)

    report, err = ai_report._maybe_generate_llm_report({}, fallback_report)
    assert err is None
    assert report is not None
    assert called["ollama"] == 1
    assert getattr(ai_report._maybe_generate_llm_report, "last_source_module", None) == "OLLAMA"


def test_llm_ollama_timeout_retries_with_fallback_model(monkeypatch):
    fallback_report = {
        "headline": "Fallback",
        "market_direction": {"label": "NEUTRAL", "confidence": 50.0, "time_horizon": "1-3d", "reasoning": []},
        "daily_report": {"summary": [], "cross_tab_findings": []},
        "recommendations": [],
        "risk_warnings": [],
        "next_checklist": [],
    }

    monkeypatch.setattr(settings, "AI_REPORT_PROVIDER", "OLLAMA", raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_OLLAMA_MODEL", "qwen3.5:latest", raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_OLLAMA_TIMEOUT_SEC", 800, raising=False)
    monkeypatch.setenv("AI_REPORT_OLLAMA_FALLBACK_MODELS", "qwen2.5:latest")

    calls = []

    def _fake_ollama_report(**kwargs):
        calls.append((kwargs["model"], kwargs["timeout_sec"]))
        if kwargs["model"] == "qwen3.5:latest":
            return None, "Ollama read timed out after 800.0s. Increase AI_REPORT_OLLAMA_TIMEOUT_SEC or reduce model size."
        return fallback_report, None

    monkeypatch.setattr("routes.ai_report._call_ollama_report", _fake_ollama_report)

    report, err = ai_report._maybe_generate_llm_report({}, fallback_report)
    assert err is None
    assert report is not None
    assert calls[0][0] == "qwen3.5:latest"
    assert calls[1][0] == "qwen2.5:latest"


def test_provider_key_test_endpoint_rejects_non_ollama():
    res = client.post(
        "/api/v1/ai/provider/test",
        json={"provider": "REMOTE", "api_key": "test-key"},
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["error_type"] == "validation"
    assert detail["error_reason"] == "unsupported_provider"
    assert detail["provider"] == "REMOTE"


def test_provider_key_test_endpoint_surfaces_connectivity_failure(monkeypatch):
    monkeypatch.setattr(
        "routes.ai_report._test_ollama_endpoint",
        lambda **kwargs: (False, "Ollama connectivity test failed: refused"),
    )

    res = client.post(
        "/api/v1/ai/provider/test",
        json={
            "provider": "OLLAMA",
            "base_url": "http://127.0.0.1:11434",
            "model": "qwen3-coder:30b",
        },
    )

    assert res.status_code == 400
    detail = res.json()["detail"]
    assert detail["error_type"] == "provider_check"
    assert detail["error_reason"] == "ollama_connectivity_failed"
    assert detail["provider"] == "OLLAMA"
    assert detail["base_url"] == "http://127.0.0.1:11434"
    assert detail["model"] == "qwen3-coder:30b"
    assert detail["provider_detail"] == "Ollama connectivity test failed: refused"


def test_provider_key_test_endpoint_ollama_success(monkeypatch):
    class _FakeResponse:
        status_code = 200
        text = "ok"
        content = b'{"models":[{"name":"qwen3-coder:30b"}]}'

        @staticmethod
        def json():
            return {"models": [{"name": "qwen3-coder:30b"}]}

    monkeypatch.setattr("routes.ai_report.requests.get", lambda *args, **kwargs: _FakeResponse())
    res = client.post(
        "/api/v1/ai/provider/test",
        json={
            "provider": "OLLAMA",
            "base_url": "http://127.0.0.1:11434",
            "model": "qwen3-coder:30b",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["provider"] == "OLLAMA"


def test_ai_daily_report_source_module_from_llm(monkeypatch):
    snapshot = _snapshot_fixture()
    _patch_ready_ollama_manager(monkeypatch)
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)

    def _fake_llm(snapshot, fallback_report):
        setattr(ai_report._maybe_generate_llm_report, "last_source_module", "OLLAMA")
        return fallback_report, None

    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", _fake_llm)
    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "llm"
    assert body["source_module"] == "OLLAMA"


def test_ai_daily_report_provider_local_forces_local_source(monkeypatch):
    snapshot = _snapshot_fixture()
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)

    def _should_not_call_llm(*args, **kwargs):
        raise AssertionError("LLM should not be called when provider=LOCAL")

    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", _should_not_call_llm)

    response = client.get("/api/v1/ai/daily-report?provider=LOCAL")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "rule_based"
    assert body["source_module"] == "LOCAL"


def test_ai_daily_report_llm_failure_degrades_to_rule_based(caplog, monkeypatch):
    snapshot = _snapshot_fixture()
    _patch_ready_ollama_manager(monkeypatch)
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr(
        "routes.ai_report._maybe_generate_llm_report",
        lambda snapshot, fallback_report: (None, "Ollama call failed: timeout"),
    )

    with caplog.at_level("WARNING", logger="horus.ai_report"):
        response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["source"] == "rule_based"
    assert body["source_module"] == "LOCAL"
    assert body["degraded"] is True
    assert body["degradation_stage"] == "llm_generation"
    assert body["degradation_reason"] == "llm_provider_failed"
    assert body["provider_fallback_used"] is False
    assert body["llm_error"] == "Ollama call failed: timeout"
    assert body["fallback_reason"] == "Ollama call failed: timeout"
    assert "degraded to rule-based output" in caplog.text


def test_ai_daily_report_success_after_provider_fallback_is_visible(caplog, monkeypatch):
    snapshot = _snapshot_fixture()
    _patch_ready_ollama_manager(monkeypatch)
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)

    def _fake_llm(snapshot, fallback_report):
        setattr(_fake_llm, "last_source_module", "OLLAMA")
        setattr(_fake_llm, "last_fallback_reason", "ollama:qwen3-coder:30b -> timeout")
        return fallback_report, None

    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", _fake_llm)

    with caplog.at_level("INFO", logger="horus.ai_report"):
        response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["source"] == "llm"
    assert body["source_module"] == "OLLAMA"
    assert body["degraded"] is False
    assert body["degradation_reason"] is None
    assert body["provider_fallback_used"] is True
    assert body["fallback_reason"] == "ollama:qwen3-coder:30b -> timeout"
    assert "used LLM provider fallback" in caplog.text


def test_ai_daily_report_snapshot_degradation_is_visible(caplog, monkeypatch):
    snapshot = _snapshot_fixture()
    snapshot["snapshot_degradation"] = {
        "degraded": True,
        "issues": [
            {"module": "portfolio", "reason": "user_portfolio_missing", "message": "No USER portfolio found."}
        ],
        "module_status": {"portfolio": {"status": "degraded", "source": "database"}},
    }
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", lambda snapshot, fallback_report: (None, None))

    with caplog.at_level("WARNING", logger="horus.ai_report"):
        response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=false")

    assert response.status_code == 200
    body = response.json()
    assert body["degraded"] is False
    assert body["snapshot_degraded"] is True
    assert body["snapshot_degradation"]["issues"][0]["reason"] == "user_portfolio_missing"
    assert "snapshot degraded" in caplog.text


def test_ai_daily_report_invalid_provider_returns_400():
    response = client.get("/api/v1/ai/daily-report?provider=CLAUDE")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["error_type"] == "validation"
    assert detail["error_reason"] == "unsupported_provider"
    assert detail["provider"] == "CLAUDE"


def test_ai_daily_report_unexpected_failure_returns_structured_500(monkeypatch):
    monkeypatch.setattr(
        "routes.ai_report._collect_cross_tab_snapshot",
        lambda portfolio_id=None: (_ for _ in ()).throw(RuntimeError("snapshot exploded")),
    )

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=false&provider=LOCAL")

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail["error_type"] == "generation"
    assert detail["error_reason"] == "ai_daily_report_failed"
    assert detail["portfolio_id"] is None
    assert detail["provider"] == "LOCAL"
    assert "snapshot exploded" in detail["message"]


def test_build_llm_prompts_enhanced_content():
    snapshot = _snapshot_fixture()
    fallback_report = ai_report._generate_rule_based_report(snapshot)
    system_prompt, user_prompt = ai_report._build_llm_prompts(snapshot, fallback_report)

    # System prompt must include the 9-module framework and output rules
    assert "9-Module Cross-Correlation Framework" in system_prompt
    assert "Oracle Macro" in system_prompt
    assert "Whale Flow" in system_prompt
    assert "OUTPUT RULES" in system_prompt
    assert "REASONING CONTRACT" in system_prompt

    # User prompt must have the new structured keys
    assert "analytical_instructions" in user_prompt
    assert "recommendation_quality_rules" in user_prompt
    assert "summary_style_guide" in user_prompt
    assert "context" in user_prompt
    assert len(user_prompt["analytical_instructions"]) >= 9
    assert len(user_prompt["recommendation_quality_rules"]) >= 5

    # Original required keys must still be present
    assert "required_schema" in user_prompt
    assert "snapshot" in user_prompt
    assert "rule_based_reference" in user_prompt
    assert "reasoning_profile" in user_prompt
    assert "reasoning_contract" in user_prompt

    # Thinking contract should have 15 rules now
    assert len(user_prompt["reasoning_contract"]) == 15

    # Context should have execution metadata
    ctx = user_prompt["context"]
    assert "report_timestamp" in ctx
    assert "data_freshness" in ctx
    assert "current_execution_mode" in ctx
    assert "composite_direction_score" in ctx


def test_dedupe_report_sections_removes_duplicates_and_overlaps():
    report = {
        "market_direction": {
            "reasoning": [
                "Module A bullish",
                "Module A bullish",
                "Summary duplicate",
            ]
        },
        "daily_report": {
            "summary": ["Summary duplicate", "Summary duplicate", "Unique summary"],
            "cross_tab_findings": ["Summary duplicate", "Finding 1", "Finding 1"],
        },
        "recommendations": [
            {"ticker": "COMI", "action": "BUY"},
            {"ticker": "COMI", "action": "BUY"},
            {"ticker": "HRHO", "action": "WATCH"},
        ],
        "risk_warnings": ["Warn 1", "Warn 1"],
        "next_checklist": ["Step 1", "Step 1"],
    }

    out = ai_report._dedupe_report_sections(report)

    assert out["daily_report"]["summary"] == ["Summary duplicate", "Unique summary"]
    assert out["daily_report"]["cross_tab_findings"] == ["Finding 1"]
    assert out["market_direction"]["reasoning"] == ["Module A bullish"]
    assert len(out["recommendations"]) == 2
    assert out["risk_warnings"] == ["Warn 1"]
    assert out["next_checklist"] == ["Step 1"]


def test_ai_daily_report_arabic_telegram_copy_is_localized_and_professional():
    payload = {
        "market_direction": {"label": "BULLISH", "confidence": 87.0},
        "execution_profile": {
            "mode": "TREND_FOLLOWING",
            "selectivity": "MEDIUM",
            "max_risk_per_trade_pct": 1.25,
        },
        "daily_report": {
            "summary": [
                "MARKET STRUCTURE: Regime is FULL BULL (Score: 8), Macro is HEALTHY UPTREND, Volatility is NORMAL.",
                "EXECUTION PROFILE: TRENDFOLLOWING | Selectivity: MEDIUM | Risk Cap: 1.25% per trade.",
                "WHALE FLOW: 74% accumulation rate, top institutional targets OIH, ASPI, UNIP.",
                "SQUEEZE ALERT: SDTI and ICFC coiling; bandwidths < 0.055 indicating imminent volatility.",
            ]
        },
        "recommendations": [
            {
                "ticker": "ICID",
                "action": "BUY",
                "confidence": 85,
                "entry_zone": "5.00 - 5.04",
                "stop_loss": 4.89,
                "take_profit": "5.30 (R:R 1.85:1)",
            },
            {
                "ticker": "BONY",
                "action": "WATCH",
                "confidence": 55,
                "entry_zone": "Above 5.65 (Trap break)",
                "stop_loss": 5.40,
                "take_profit": "6.00",
            },
        ],
        "risk_warnings": [
            "DISTRIBUTION RISK: Bull traps (6) exceed bear traps (4); avoid chasing vertical moves without volume confirmation.",
            "CONCENTRATION RISK: Portfolio 'Horus' currently has 0 positions; ensure new entries are diversified across leading sectors (HealthCare, Travel).",
            "SQUEEZE VOLATILITY: SDTI and ICFC may exhibit violent bidirectional moves before trending.",
        ],
    }

    message = build_ai_report_telegram_message(payload, language="AR")

    assert "*تقرير حورس اليومي للسوق بالذكاء الاصطناعي*" in message
    assert "هورس" not in message
    assert "حالة السوق: صعود قوي" in message
    assert "ملف التنفيذ: متابعة الاتجاه" in message
    assert "`ICID` شراء" in message
    assert "`BONY` مراقبة" in message
    assert "حد المخاطرة" in message
    assert "محفظة حورس" in message
    for english_fragment in [
        "MARKET STRUCTURE",
        "EXECUTION PROFILE",
        "BULLISH",
        "TREND",
        "MEDIUM",
        "BUY",
        "WATCH",
        "DISTRIBUTION RISK",
        "Portfolio",
        "risk cap",
        "Trap break",
    ]:
        assert english_fragment not in message


def test_ai_daily_report_broadcast_endpoint_success(monkeypatch):
    snapshot = _snapshot_fixture()
    snapshot["snapshot_degradation"] = {
        "degraded": True,
        "issues": [
            {"module": "portfolio", "reason": "user_portfolio_missing", "message": "No USER portfolio found."}
        ],
        "module_status": {"portfolio": {"status": "degraded", "source": "database"}},
    }
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", lambda snapshot, fallback_report: (None, None))
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token-123", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-100123", raising=False)
    monkeypatch.setattr(settings, "TELEGRAM_REPORT_LANGUAGE", "AR", raising=False)

    sent = {"message": ""}

    def _fake_send(message: str):
        sent["message"] = message
        return {"ok": True, "result": {"message_id": 1}}

    monkeypatch.setattr("routes.ai_report.TelegramBot_Alerts.send_message", _fake_send)

    response = client.post(
        "/api/v1/ai/daily-report/broadcast",
        json={"force_refresh": True, "use_llm": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["snapshot_degraded"] is True
    assert data["snapshot_degradation"]["issues"][0]["reason"] == "user_portfolio_missing"
    assert "*تقرير حورس اليومي للسوق بالذكاء الاصطناعي*" in sent["message"]
    assert "هورس" not in sent["message"]
    assert "*HORUS AI DAILY MARKET REPORT*" not in sent["message"]


def test_ai_daily_report_broadcast_failure_surfaces_delivery_diagnostics(caplog, monkeypatch):
    snapshot = _snapshot_fixture()
    _patch_ready_ollama_manager(monkeypatch)
    snapshot["snapshot_degradation"] = {
        "degraded": True,
        "issues": [
            {"module": "portfolio", "reason": "user_portfolio_missing", "message": "No USER portfolio found."}
        ],
        "module_status": {"portfolio": {"status": "degraded", "source": "database"}},
    }
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr(
        "routes.ai_report._maybe_generate_llm_report",
        lambda snapshot, fallback_report: (None, "Ollama call failed: timeout"),
    )
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token-123", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-100123", raising=False)
    monkeypatch.setattr(
        "routes.ai_report.TelegramBot_Alerts.send_message",
        lambda message: {"ok": False, "description": "bot blocked"},
    )

    with caplog.at_level("WARNING", logger="horus.ai_report"):
        response = client.post(
            "/api/v1/ai/daily-report/broadcast",
            json={"force_refresh": True, "use_llm": True},
        )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["error_type"] == "delivery"
    assert detail["error_reason"] == "telegram_delivery_failed"
    assert detail["telegram_description"] == "bot blocked"
    assert detail["source_module"] == "LOCAL"
    assert detail["degraded"] is True
    assert detail["degradation_reason"] == "llm_provider_failed"
    assert detail["fallback_reason"] == "Ollama call failed: timeout"
    assert detail["snapshot_degraded"] is True
    assert detail["snapshot_degradation"]["issues"][0]["reason"] == "user_portfolio_missing"
    assert "broadcast delivery failed" in caplog.text


def test_high_bull_trap_density_triggers_risk_gate():
    from core.ai_report.generation import _generate_rule_based_report
    snapshot = _snapshot_fixture()
    snapshot["traps"] = {"bull_trap_count": 42, "bear_trap_count": 0, "recent_bull_traps": [], "recent_bear_traps": []}

    report = _generate_rule_based_report(snapshot)
    exec_profile = report["execution_profile"]

    assert exec_profile["mode"] == "PULLBACK_RETEST_ONLY"
    assert exec_profile["selectivity"] == "HIGH"
    assert exec_profile["max_total_new_risk_pct"] <= 2.5
    assert any("Extreme Bull Trap density (42 traps)" in r for r in report["market_direction"]["reasoning"])


