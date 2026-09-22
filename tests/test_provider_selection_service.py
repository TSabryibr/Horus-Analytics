
from core.settings import settings
from data_engine import ingest_history, ingest_intraday, provider_selection, sync
from data_engine.provider_selection import (
    format_quality_report,
    resolved_provider_context,
    stage_provider_context,
)
from routes import data as data_routes


def test_stage_provider_context_merges_without_mutating_inputs():
    provider_context = {"provider": "CSV", "reason": "stale_db_fallback"}
    ingest_summary = {"status": "completed_with_fallback", "used_provider": "CSV"}

    merged = stage_provider_context(provider_context, ingest_summary)

    assert merged == {
        "provider": "CSV",
        "reason": "stale_db_fallback",
        "ingest_summary": {
            "status": "completed_with_fallback",
            "used_provider": "CSV",
        },
    }
    assert "ingest_summary" not in provider_context


def test_resolved_provider_context_uses_selection_report_details(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_HISTORY_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)
    report = {
        "recommended_history_details": {
            "provider": "MUBASHER_DB",
            "reason": "most_recent_history",
            "fallback_from": None,
            "evidence": {"history_latest": "20260212"},
        }
    }

    context = resolved_provider_context(
        timeframe="history",
        selected_provider="MUBASHER_DB",
        selection_report=report,
    )

    assert context["provider"] == "MUBASHER_DB"
    assert context["reason"] == "most_recent_history"
    assert context["evidence"]["history_latest"] == "20260212"


def test_format_quality_report_includes_decision_reasons():
    report = {
        "csv": {
            "score": 1,
            "history_symbols": 307,
            "history_latest": "20260211",
            "intraday_symbols": 260,
            "intraday_latest": "20260212134100",
        },
        "mubasher_db": {
            "score": 4,
            "history_symbols": 536,
            "history_latest": "20260211",
            "intraday_symbols": 260,
            "intraday_latest": "20260211142900",
        },
        "directfn": {
            "score": 0,
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
        },
        "metastock_dat": {
            "score": 0,
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
        },
        "recommended_provider": "MUBASHER_DB",
        "recommended_history_provider": "MUBASHER_DB",
        "recommended_intraday_provider": "CSV",
        "recommended_history_details": {
            "provider": "MUBASHER_DB",
            "reason": "most_recent_history",
            "evidence": {"history_latest": "20260211"},
        },
        "recommended_intraday_details": {
            "provider": "CSV",
            "reason": "stale_db_fallback",
            "fallback_from": "MUBASHER_DB",
            "evidence": {"stale_minutes": 20},
        },
    }

    rendered = format_quality_report(report)

    assert "History decision: MUBASHER_DB (most_recent_history)" in rendered
    assert "Intraday decision: CSV (stale_db_fallback from MUBASHER_DB)" in rendered


def test_runtime_consumers_bind_to_provider_selection_service():
    assert ingest_history.resolve_timeframe_provider is provider_selection.resolve_timeframe_provider
    assert ingest_intraday.resolve_timeframe_provider is provider_selection.resolve_timeframe_provider
    assert sync.resolve_timeframe_provider is provider_selection.resolve_timeframe_provider
    assert data_routes.resolve_timeframe_provider is provider_selection.resolve_timeframe_provider
    assert data_routes.normalize_provider is provider_selection.normalize_provider
    assert data_routes.resolved_provider_context is provider_selection.resolved_provider_context


def test_explicit_intraday_provider_returns_stale_source_report(monkeypatch):
    stale_report = {
        "recommended_intraday_provider": "MUBASHER_DB",
        "recommended_intraday_details": {
            "timeframe": "intraday",
            "provider": "MUBASHER_DB",
            "reason": "upstream_intraday_stale",
            "fallback_from": None,
            "evidence": {
                "intraday_latest": "20260525142900",
                "expected_intraday_date": "20260601",
            },
        },
    }

    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_ALLOW_STALE_FALLBACK", False, raising=False)
    monkeypatch.setattr("data_engine.local_feed_selector.compare_local_sources", lambda: stale_report)

    selected_provider, report = provider_selection.resolve_timeframe_provider("intraday")

    assert selected_provider == "MUBASHER_DB"
    assert report is stale_report
