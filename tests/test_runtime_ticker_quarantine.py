from core.settings import settings
import datetime

import pandas as pd
from fastapi.testclient import TestClient

from api import app
from data_engine.freshness import get_runtime_ticker_report

from data_engine.ticker_filters import (
    classify_runtime_ticker_state,
    is_rights_style_ticker,
    is_runtime_quarantined_ticker,
)

client = TestClient(app, raise_server_exceptions=False)


def test_rights_style_ticker_is_detected():
    assert is_rights_style_ticker("ADIB_R3") is True
    assert is_rights_style_ticker("COMI") is False


def test_dormant_symbol_is_runtime_quarantined(monkeypatch):
    monkeypatch.setattr(settings, "MARKET_WEEKEND", [4, 5], raising=False)
    monkeypatch.setattr(settings, "_is_db_holiday", lambda day: False, raising=False)

    state = classify_runtime_ticker_state(
        "MEGM",
        last_history_date=datetime.date(2025, 10, 1),
        last_intraday_timestamp=None,
        ref_date=datetime.date(2026, 4, 1),
        dormant_trading_days=90,
    )

    assert state["reason"] == "DORMANT"
    assert state["quarantined"] is True
    assert is_runtime_quarantined_ticker(
        "MEGM",
        last_history_date=datetime.date(2025, 10, 1),
        last_intraday_timestamp=None,
        ref_date=datetime.date(2026, 4, 1),
        dormant_trading_days=90,
    ) is True


def test_recently_active_source_stale_symbol_is_not_quarantined(monkeypatch):
    monkeypatch.setattr(settings, "MARKET_WEEKEND", [4, 5], raising=False)
    monkeypatch.setattr(settings, "_is_db_holiday", lambda day: False, raising=False)

    state = classify_runtime_ticker_state(
        "TRTO",
        last_history_date=datetime.date(2026, 3, 31),
        last_intraday_timestamp=datetime.datetime(2026, 3, 31, 11, 57, 0),
        ref_date=datetime.date(2026, 4, 1),
        dormant_trading_days=90,
    )

    assert state["reason"] == "SOURCE_STALE"
    assert state["quarantined"] is False
    assert is_runtime_quarantined_ticker(
        "TRTO",
        last_history_date=datetime.date(2026, 3, 31),
        last_intraday_timestamp=datetime.datetime(2026, 3, 31, 11, 57, 0),
        ref_date=datetime.date(2026, 4, 1),
        dormant_trading_days=90,
    ) is False


def test_runtime_universe_report_endpoint_returns_quarantined_and_review_candidates(monkeypatch):
    monkeypatch.setattr(
        "routes.data.get_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: {
            "realm": realm,
            "report_date": "2026-04-02",
            "dormant_trading_days": dormant_trading_days,
            "runtime_quarantined": [
                {
                    "ticker": "ADIB_R3",
                    "reason": "RIGHTS",
                    "quarantined": True,
                    "last_history_date": "2025-11-30",
                    "last_intraday_timestamp": None,
                    "history_trading_day_age": 90,
                    "intraday_trading_day_age": None,
                }
            ],
            "review_candidates": [
                {
                    "ticker": "TRTO",
                    "reason": "SOURCE_STALE",
                    "quarantined": False,
                    "last_history_date": "2026-03-31",
                    "last_intraday_timestamp": "2026-03-31T11:57:00",
                    "history_trading_day_age": 1,
                    "intraday_trading_day_age": 1,
                }
            ],
            "tracked_symbols": ["COMI", "TRTO"],
            "summary": {
                "tracked_count": 2,
                "runtime_quarantined_count": 1,
                "review_candidate_count": 1,
                "counts_by_reason": {"RIGHTS": 1, "SOURCE_STALE": 1},
            },
        },
    )

    response = client.get("/api/v1/data/runtime-universe")

    assert response.status_code == 200
    payload = response.json()
    assert payload["runtime_quarantined"][0]["ticker"] == "ADIB_R3"
    assert payload["review_candidates"][0]["ticker"] == "TRTO"
    assert payload["summary"]["runtime_quarantined_count"] == 1


def test_runtime_universe_report_marks_overlay_backed_source_stale_reviews(monkeypatch):
    monkeypatch.setattr(
        "routes.data.get_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: {
            "realm": realm,
            "report_date": "2026-06-09",
            "runtime_quarantined": [],
            "review_candidates": [
                {"ticker": "TRTO", "reason": "SOURCE_STALE", "quarantined": False},
            ],
            "tracked_symbols": ["TRTO"],
            "summary": {
                "tracked_count": 1,
                "runtime_quarantined_count": 0,
                "review_candidate_count": 1,
                "counts_by_reason": {"SOURCE_STALE": 1},
            },
        },
    )
    monkeypatch.setattr(
        "routes.data.get_data_status_logic",
        lambda: {
            "intraday": {"status": "LIVE"},
            "source": {
                "intraday_decision": {"reason": "upstream_intraday_stale"},
                "realtime_overlay": {"active": True, "status": "ACTIVE"},
            },
        },
    )

    response = client.get("/api/v1/data/runtime-universe")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_context"]["archive_intraday_stale"] is True
    assert payload["source_context"]["realtime_overlay_active"] is True
    assert "archive/source lag" in payload["source_context"]["runtime_review_note"]


def test_runtime_ticker_report_uses_last_completed_market_day_for_source_stale_detection(monkeypatch):
    monkeypatch.setattr("data_engine.freshness._history_symbol_dates_raw", lambda realm: {"COMI": datetime.date(2026, 4, 1)})
    monkeypatch.setattr(
        "data_engine.freshness._intraday_symbol_timestamps_raw",
        lambda realm: {"COMI": pd.Timestamp("2026-04-02 10:35:00")},
    )
    monkeypatch.setattr("data_engine.freshness.TimeUtils.today", lambda: datetime.date(2026, 4, 2))
    monkeypatch.setattr(
        "data_engine.freshness.settings.get_last_completed_market_day",
        lambda moment: datetime.date(2026, 4, 1),
    )
    monkeypatch.setattr("data_engine.freshness._canonical_runtime_symbols", lambda realm: set())

    report = get_runtime_ticker_report("EGX")

    assert report["summary"]["review_candidate_count"] == 0
    assert report["summary"]["counts_by_reason"]["ACTIVE"] == 1
