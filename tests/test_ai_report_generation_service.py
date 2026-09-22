from core.settings import settings
from unittest.mock import patch
from core.ai_report.generation import (
    _strip_code_fences,
    _normalize_llm_report,
    _build_llm_prompts,
    _maybe_generate_llm_report,
)

def test_strip_code_fences():
    assert _strip_code_fences("```json\n{\"a\":1}\n```") == "{\"a\":1}"
    assert _strip_code_fences("{\"a\":1}") == "{\"a\":1}"
    assert _strip_code_fences("```\n{\"a\":1}\n```") == "{\"a\":1}"

def test_normalize_llm_report():
    fallback = {
        "headline": "FB",
        "market_direction": {"label": "NEUTRAL", "confidence": 50.0, "reasoning": []},
        "daily_report": {"summary": [], "cross_tab_findings": []},
        "recommendations": [],
        "risk_warnings": [],
        "next_checklist": []
    }
    parsed = {
        "headline": "NEW",
        "market_direction": {"label": "BULLISH", "confidence": 80.0, "reasoning": ["Test"], "time_horizon": "1-3d"},
        "daily_report": {"summary": ["Item 1"]},
        "recommendations": [{"ticker": "AAPL"}]
    }
    norm = _normalize_llm_report(parsed, fallback)
    assert norm["headline"] == "NEW"
    assert norm["market_direction"]["label"] == "BULLISH"
    assert norm["daily_report"]["summary"] == ["Item 1"]
    assert norm["recommendations"][0]["ticker"] == "AAPL"
    assert norm["recommendations"][0]["action"] == "WATCH"
    # Ensure next_checklist is still from fallback (empty list)
    assert norm["next_checklist"] == []

def test_build_llm_prompts():
    snapshot = {"as_of": "2026-03-17T00:00:00", "data_freshness": {"label": "FRESH"}}
    fallback = {
        "market_direction": {"composite_score": 4, "bias_description": "constructive"},
        "execution_profile": {"mode": "BALANCED", "selectivity": "MEDIUM", "max_risk_per_trade_pct": 1.0},
    }
    with patch("core.ai_report.generation.rule_engine_instruction_text", return_value="SYSTEM"):
        system, user = _build_llm_prompts(snapshot, fallback)
        assert "9-Module Cross-Correlation Framework" in system
        assert "SYSTEM" in system
        assert user["snapshot"] == snapshot
        assert user["rule_based_reference"] == fallback
        assert user["context"]["data_freshness"] == "FRESH"
        assert "analytical_instructions" in user
        assert "required_schema" in user


def test_maybe_generate_llm_report_returns_source_and_fallback_reason(monkeypatch):
    fallback = {
        "headline": "FB",
        "market_direction": {"label": "NEUTRAL", "confidence": 50.0, "reasoning": [], "composite_score": 0, "bias_description": "flat"},
        "daily_report": {"summary": [], "cross_tab_findings": []},
        "recommendations": [],
        "risk_warnings": [],
        "next_checklist": [],
        "execution_profile": {"mode": "BALANCED", "selectivity": "MEDIUM", "max_risk_per_trade_pct": 1.0},
    }

    monkeypatch.setattr("core.ai_report.generation.bool_env", lambda *args, **kwargs: True)
    monkeypatch.setattr("core.ai_report.generation.float_env", lambda *args, **kwargs: 180.0)
    monkeypatch.setenv("AI_REPORT_OLLAMA_FALLBACK_MODELS", "qwen2.5:latest")

    class _Settings:
        OLLAMA_API_KEY = ""
        OLLAMA_BASE_URL = "http://127.0.0.1:11434"
        AI_REPORT_PROVIDER = "OLLAMA"
        AI_REPORT_OLLAMA_MODEL = "qwen3.5:latest"
        AI_REPORT_OLLAMA_NUM_CTX = 8192
        AI_REPORT_OLLAMA_TIMEOUT_SEC = 300.0

    monkeypatch.setattr("core.ai_report.generation.settings", _Settings(), raising=False)

    calls = []

    def _fake_ollama_report(**kwargs):
        calls.append((kwargs["model"], kwargs["timeout_sec"]))
        if kwargs["model"] == "qwen3.5:latest":
            return None, "timeout"
        return fallback, None

    report, err, source_module, fallback_reason = _maybe_generate_llm_report(
        {},
        fallback,
        call_ollama_report=_fake_ollama_report,
    )

    assert err is None
    assert report == fallback
    assert source_module == "OLLAMA"
    assert fallback_reason == "ollama:qwen3.5:latest -> timeout"
    assert calls[0][0] == "qwen3.5:latest"
    assert calls[1][0] == "qwen2.5:latest"
