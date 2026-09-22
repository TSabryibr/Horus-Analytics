import os
import datetime
from core import TimeUtils
from core.ai_report.boundary import (
    normalize_source_module,
    int_env,
    float_env,
    bool_env,
    cache_is_fresh,
    error_context,
    module_issue,
    dedupe_report_sections,
)

def test_normalize_source_module():
    assert normalize_source_module("OLLAMA") == "OLLAMA"
    assert normalize_source_module("local") == "LOCAL"
    assert normalize_source_module("rule_based") == "LOCAL"
    assert normalize_source_module(None) == "LOCAL"
    assert normalize_source_module("ollama:qwen") == "OLLAMA"
    assert normalize_source_module("remote") == "LOCAL"

def test_env_helpers(monkeypatch):
    monkeypatch.setenv("TEST_INT", "123")
    monkeypatch.setenv("TEST_FLOAT", "123.45")
    monkeypatch.setenv("TEST_BOOL", "true")
    
    assert int_env("TEST_INT", 0) == 123
    assert int_env("MISSING", 456) == 456
    assert float_env("TEST_FLOAT", 0.0) == 123.45
    assert bool_env("TEST_BOOL", False) is True
    assert bool_env("MISSING", True) is True

def test_cache_is_fresh():
    now = TimeUtils.now()
    fresh = {"generated_at": now - datetime.timedelta(seconds=10)}
    stale = {"generated_at": now - datetime.timedelta(seconds=1000)}
    
    assert cache_is_fresh(fresh) is True
    assert cache_is_fresh(stale) is False
    assert cache_is_fresh(None) is False

def test_error_context_shape():
    ctx = error_context("test_type", "test_reason", "test message", extra="info")
    assert ctx["error_type"] == "test_type"
    assert ctx["error_reason"] == "test_reason"
    assert ctx["message"] == "test message"
    assert ctx["extra"] == "info"

def test_module_issue_shape():
    issue = module_issue("test_module", "test_reason", "test message", status="degraded")
    assert issue["module"] == "test_module"
    assert issue["reason"] == "test_reason"
    assert issue["message"] == "test message"
    assert issue["status"] == "degraded"

def test_dedupe_report_sections_logic():
    report = {
        "daily_report": {
            "summary": ["A", "A", "B"],
            "cross_tab_findings": ["B", "C", "C"]
        },
        "market_direction": {
            "reasoning": ["A", "D"]
        },
        "recommendations": [
            {"ticker": "AAPL", "action": "BUY"},
            {"ticker": "AAPL", "action": "BUY"}
        ],
        "risk_warnings": ["W1", "W1"],
        "next_checklist": ["S1", "S1"]
    }
    deduped = dedupe_report_sections(report)
    
    assert deduped["daily_report"]["summary"] == ["A", "B"]
    assert deduped["daily_report"]["cross_tab_findings"] == ["C"]
    assert deduped["market_direction"]["reasoning"] == ["D"]
    assert len(deduped["recommendations"]) == 1
    assert deduped["risk_warnings"] == ["W1"]
    assert deduped["next_checklist"] == ["S1"]
