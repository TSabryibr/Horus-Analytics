from core.settings import settings, settings as GlobalSettings
from core.exclusions import get_all_exclusions
import datetime
from pathlib import Path

import pandas as pd

from core import Heimdall
from data_engine import intraday_store
from data_engine import freshness as freshness_mod
from routes.data import evaluate_data_freshness_logic, get_data_status_logic, reset_data_status_cache


def test_status_and_freshness_gate_use_same_policy(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Heimdall, "CURRENT_REALM", "TESTREALM", raising=False)

    today = datetime.date.today()
    expected_day = settings.get_last_completed_market_day(
        datetime.datetime.combine(today, datetime.time.max)
    )

    history_path = Path("data/TESTREALM/history")
    history_path.mkdir(parents=True, exist_ok=True)
    hist_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp(expected_day), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    hist_df.to_parquet(history_path / "COMI.parquet")

    now_bar = datetime.datetime.now().replace(second=0, microsecond=0)
    intraday_store.upsert_intraday(
        "COMI",
        pd.DataFrame(
            [{"timestamp": now_bar, "open": 10, "high": 11, "low": 9.8, "close": 10.8, "volume": 50}]
        ),
        realm="TESTREALM",
    )

    status = get_data_status_logic()
    gate = evaluate_data_freshness_logic(run_date=today.strftime("%Y-%m-%d"), scan_type="DAILY")

    assert status["history"]["ok"] == gate["history"]["ok"]
    assert status["history"]["expected_last_working_day"] == gate["history"]["expected_last_working_day"]
    assert status["history"]["last_updated"] == gate["history"]["last_updated"]


def test_status_exposes_provider_decision_details(monkeypatch):
    report = {
        "recommended_provider": "MUBASHER_DB",
        "recommended_history_provider": "MUBASHER_DB",
        "recommended_intraday_provider": "CSV",
        "recommended_history_details": {
            "provider": "MUBASHER_DB",
            "reason": "most_recent_history",
            "fallback_from": None,
            "evidence": {"history_latest": "20260211", "history_symbols": 536},
        },
        "recommended_intraday_details": {
            "provider": "CSV",
            "reason": "stale_db_fallback",
            "fallback_from": "MUBASHER_DB",
            "evidence": {
                "csv_intraday_latest": "20260212134100",
                "db_intraday_latest": "20260211142900",
                "stale_minutes": 20,
            },
        },
    }

    monkeypatch.setattr(
        "routes.data.evaluate_freshness",
        lambda **kw: {
            "history": {"ok": True},
            "intraday": {"ok": False},
            "overall_ok": False,
        },
    )
    monkeypatch.setattr(
        "routes.data.resolve_timeframe_provider",
        lambda timeframe: ("MUBASHER_DB", report) if timeframe == "history" else ("CSV", report),
    )
    monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)

    status = get_data_status_logic()

    assert status["source"]["history_provider"] == "MUBASHER_DB"
    assert status["source"]["intraday_provider"] == "CSV"
    assert status["source"]["history_decision"]["reason"] == "most_recent_history"
    assert status["source"]["intraday_decision"]["reason"] == "stale_db_fallback"
    assert status["source"]["intraday_decision"]["fallback_from"] == "MUBASHER_DB"


def test_data_status_exposes_active_realtime_overlay(monkeypatch):
    reset_data_status_cache()
    report = {
        "recommended_provider": "MUBASHER_DB",
        "recommended_history_provider": "MUBASHER_DB",
        "recommended_intraday_provider": "MUBASHER_DB",
        "recommended_intraday_details": {
            "provider": "MUBASHER_DB",
            "reason": "upstream_intraday_stale",
            "fallback_from": None,
            "evidence": {
                "intraday_latest": "20260525142900",
                "expected_intraday_date": "20260601",
                "market_open": True,
            },
        },
    }

    monkeypatch.setattr(
        "routes.data.evaluate_freshness",
        lambda **kw: {
            "history": {"ok": True},
            "intraday": {"ok": True, "status": "LIVE", "last_bar": "2026-06-01 14:26"},
            "overall_ok": True,
        },
    )
    monkeypatch.setattr(
        "routes.data.resolve_timeframe_provider",
        lambda timeframe: ("MUBASHER_DB", report),
    )
    monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)

    status = get_data_status_logic()

    assert status["source"]["realtime_overlay"] == {
        "enabled": True,
        "active": True,
        "status": "ACTIVE",
        "provider": "MUBASHER_REALTIME",
        "price_field": "55",
        "guard": "session_range",
        "reason": "upstream_intraday_stale",
        "last_bar": "2026-06-01 14:26",
    }


def test_data_status_reuses_short_lived_cache(monkeypatch):
    reset_data_status_cache()
    monkeypatch.setenv("DATA_STATUS_CACHE_TTL_SEC", "60")
    monkeypatch.setattr("routes.data.get_system_state_snapshot", lambda: {"data_version": 7})
    monkeypatch.setattr("routes.data.resolve_timeframe_provider", lambda timeframe: ("CSV", None))
    monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

    calls = {"count": 0}

    def fake_evaluate(**kwargs):
        calls["count"] += 1
        return {
            "history": {"ok": True},
            "intraday": {"ok": True},
            "overall_ok": True,
        }

    monkeypatch.setattr("routes.data.evaluate_freshness", fake_evaluate)

    first = get_data_status_logic()
    second = get_data_status_logic()

    assert calls["count"] == 1
    assert first == second


def test_data_status_cache_invalidates_when_data_version_changes(monkeypatch):
    reset_data_status_cache()
    monkeypatch.setenv("DATA_STATUS_CACHE_TTL_SEC", "60")
    version = {"value": 11}
    monkeypatch.setattr("routes.data.get_system_state_snapshot", lambda: {"data_version": version["value"]})
    monkeypatch.setattr("routes.data.resolve_timeframe_provider", lambda timeframe: ("CSV", None))
    monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

    calls = {"count": 0}

    def fake_evaluate(**kwargs):
        calls["count"] += 1
        return {
            "history": {"ok": True},
            "intraday": {"ok": True},
            "overall_ok": True,
        }

    monkeypatch.setattr("routes.data.evaluate_freshness", fake_evaluate)

    get_data_status_logic()
    version["value"] = 12
    get_data_status_logic()

    assert calls["count"] == 2


def test_data_status_cache_ttl_starts_after_payload_is_built(monkeypatch):
    reset_data_status_cache()
    monkeypatch.setenv("DATA_STATUS_CACHE_TTL_SEC", "5")
    current_time = {"value": 100.0}

    monkeypatch.setattr("routes.data.time.time", lambda: current_time["value"])
    monkeypatch.setattr("routes.data.get_system_state_snapshot", lambda: {"data_version": 9})
    monkeypatch.setattr("routes.data.resolve_timeframe_provider", lambda timeframe: ("CSV", None))
    monkeypatch.setattr("routes.data.maybe_emit_freshness_alerts", lambda status: None)

    calls = {"count": 0}

    def fake_evaluate(**kwargs):
        calls["count"] += 1
        current_time["value"] += 6.0
        return {
            "history": {"ok": True},
            "intraday": {"ok": True},
            "overall_ok": True,
        }

    monkeypatch.setattr("routes.data.evaluate_freshness", fake_evaluate)

    get_data_status_logic()
    get_data_status_logic()

    assert calls["count"] == 1


def test_freshness_ignores_excluded_history_symbols_in_ratio(tmp_path, monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 2, 17)
    history_path = tmp_path / "data" / realm / "history"
    history_path.mkdir(parents=True, exist_ok=True)

    fresh_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp(expected_day), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    stale_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp(expected_day - datetime.timedelta(days=1)), "open": 5, "high": 6, "low": 4, "close": 5.5, "volume": 50}]
    ).set_index("timestamp")
    fresh_df.to_parquet(history_path / "COMI.parquet")
    stale_df.to_parquet(history_path / "SIMO.parquet")

    freshness_mod._HISTORY_CACHE.clear()
    monkeypatch.setattr(freshness_mod, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: expected_day)
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: False)
    monkeypatch.setattr(GlobalSettings, "get_all_exclusions", lambda: {"SIMO"}, raising=False)
    monkeypatch.setattr(freshness_mod, "_canonical_runtime_symbols", lambda realm: set())

    status = freshness_mod.evaluate_freshness(realm=realm, run_date=expected_day, scan_type="DAILY")

    assert status["history"]["kpis"]["symbol_count"] == 1
    assert status["history"]["kpis"]["fresh_symbols"] == 1
    assert status["history"]["kpis"]["stale_symbols"] == 0
    assert status["history"]["kpis"]["fresh_ratio"] == 1.0


def test_history_symbol_scan_reads_last_date_from_flat_parquet(tmp_path, monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 4, 2)
    history_path = tmp_path / "data" / realm / "history"
    history_path.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp(expected_day - datetime.timedelta(days=1)), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": pd.Timestamp(expected_day), "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 110},
        ]
    ).set_index("timestamp")
    df.to_parquet(history_path / "COMI.parquet")

    freshness_mod._HISTORY_CACHE.clear()
    monkeypatch.setattr(freshness_mod, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(GlobalSettings, "get_all_exclusions", lambda: set(), raising=False)

    history_dates = freshness_mod._history_symbol_dates_raw(realm)

    assert history_dates == {"COMI": expected_day}


def test_history_symbol_scan_merges_flat_symbols_with_partitions(tmp_path, monkeypatch):
    realm = "TESTREALM"
    older_day = datetime.date(2026, 4, 1)
    newer_day = datetime.date(2026, 4, 2)
    history_path = tmp_path / "data" / realm / "history"
    history_path.mkdir(parents=True, exist_ok=True)

    flat_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp(older_day), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    flat_df.to_parquet(history_path / "FWRY.parquet")

    part_dir = history_path / "by_date" / newer_day.isoformat()
    part_dir.mkdir(parents=True, exist_ok=True)
    part_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp(newer_day), "open": 20, "high": 21, "low": 19, "close": 20.5, "volume": 200}]
    ).set_index("timestamp")
    part_df.to_parquet(part_dir / "COMI.parquet")

    freshness_mod._HISTORY_CACHE.clear()
    monkeypatch.setattr(freshness_mod, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(GlobalSettings, "get_all_exclusions", lambda: set(), raising=False)

    history_dates = freshness_mod._history_symbol_dates_raw(realm)

    assert history_dates == {"COMI": newer_day, "FWRY": older_day}


def test_freshness_filters_runtime_quarantined_symbols_but_keeps_source_stale_candidates(tmp_path, monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 4, 1)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(Heimdall, "CURRENT_REALM", realm, raising=False)
    monkeypatch.setattr(freshness_mod, "DATA_ROOT", tmp_path / "data")
    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: expected_day)
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: False)
    monkeypatch.setattr(settings, "MARKET_WEEKEND", [4, 5], raising=False)
    monkeypatch.setattr(settings, "_is_db_holiday", lambda day: False, raising=False)
    monkeypatch.setattr(GlobalSettings, "get_all_exclusions", lambda: set(), raising=False)
    monkeypatch.setattr(freshness_mod, "_canonical_runtime_symbols", lambda realm: set())
    freshness_mod._HISTORY_CACHE.clear()

    history_path = tmp_path / "data" / realm / "history"
    history_path.mkdir(parents=True, exist_ok=True)

    def _write_history(symbol: str, bar_day: datetime.date) -> None:
        df = pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp(bar_day),
                    "open": 10,
                    "high": 11,
                    "low": 9,
                    "close": 10.5,
                    "volume": 100,
                }
            ]
        ).set_index("timestamp")
        df.to_parquet(history_path / f"{symbol}.parquet")

    _write_history("COMI", expected_day)
    _write_history("ADIB_R3", expected_day - datetime.timedelta(days=40))
    _write_history("MEGM", datetime.date(2025, 10, 1))
    _write_history("TRTO", expected_day - datetime.timedelta(days=1))

    intraday_store.upsert_intraday(
        "TRTO",
        pd.DataFrame(
            [
                {
                    "timestamp": datetime.datetime(2026, 3, 31, 11, 57, 0),
                    "open": 12,
                    "high": 13,
                    "low": 11.5,
                    "close": 12.7,
                    "volume": 75,
                }
            ]
        ),
        realm=realm,
    )

    status = freshness_mod.evaluate_freshness(realm=realm, run_date=expected_day, scan_type="DAILY")

    assert status["history"]["kpis"]["symbol_count"] == 2
    assert status["history"]["kpis"]["fresh_symbols"] == 1
    assert status["history"]["kpis"]["stale_symbols"] == 1
    assert status["history"]["kpis"]["fresh_ratio"] == 0.5
    assert status["history"]["stale_sample"] == ["TRTO"]


def test_freshness_ratio_excludes_non_actionable_missing_and_inactive_review_symbols(monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 5, 12)
    run_date = datetime.date(2026, 5, 13)

    freshness_mod._EVALUATE_FRESHNESS_CACHE.clear()
    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: expected_day)
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: True)
    monkeypatch.setattr(freshness_mod.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 13, 12, 20, 0))
    monkeypatch.setattr(
        freshness_mod,
        "_build_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: (
            {
                "tracked_symbols": ["COMI", "TRTO", "OLDI", "MISS"],
                "review_candidates": [
                    {
                        "ticker": "TRTO",
                        "reason": "SOURCE_STALE",
                        "history_trading_day_age": 1,
                        "intraday_trading_day_age": 0,
                    },
                    {
                        "ticker": "OLDI",
                        "reason": "SOURCE_STALE",
                        "history_trading_day_age": 8,
                        "intraday_trading_day_age": 8,
                    },
                    {
                        "ticker": "MISS",
                        "reason": "MISSING_SOURCE",
                        "history_trading_day_age": None,
                        "intraday_trading_day_age": None,
                    },
                ],
            },
            {
                "COMI": expected_day,
                "TRTO": expected_day - datetime.timedelta(days=1),
                "OLDI": expected_day - datetime.timedelta(days=8),
            },
            {
                "COMI": pd.Timestamp("2026-05-13 12:20"),
                "TRTO": pd.Timestamp("2026-05-13 12:19"),
                "OLDI": pd.Timestamp("2026-05-03 10:15"),
            },
        ),
    )

    status = freshness_mod.evaluate_freshness(realm=realm, run_date=run_date, scan_type="DAILY")

    assert status["history"]["kpis"]["symbol_count"] == 2
    assert status["history"]["kpis"]["fresh_symbols"] == 1
    assert status["history"]["kpis"]["stale_symbols"] == 1
    assert status["history"]["kpis"]["fresh_ratio"] == 0.5
    assert status["history"]["stale_sample"] == ["TRTO"]


def test_freshness_holds_previous_eod_until_same_day_history_arrives_after_close(monkeypatch):
    realm = "TESTREALM"
    run_date = datetime.date(2026, 5, 13)
    previous_eod = datetime.date(2026, 5, 12)

    freshness_mod._EVALUATE_FRESHNESS_CACHE.clear()
    monkeypatch.setattr(
        GlobalSettings,
        "get_last_completed_market_day",
        lambda moment: run_date if moment.date() == run_date else previous_eod,
    )
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: False)
    monkeypatch.setattr(freshness_mod.TimeUtils, "now", lambda: datetime.datetime(2026, 5, 13, 14, 50, 0))
    monkeypatch.setattr(
        freshness_mod,
        "_build_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: (
            {"tracked_symbols": ["COMI"]},
            {"COMI": previous_eod},
            {"COMI": pd.Timestamp("2026-05-13 14:14")},
        ),
    )

    status = freshness_mod.evaluate_freshness(realm=realm, run_date=run_date, scan_type="DAILY")

    assert status["history"]["expected_last_working_day"] == previous_eod.isoformat()
    assert status["history"]["pending_eod_history"] is True
    assert status["history"]["ok"] is True
    assert status["history"]["kpis"]["fresh_ratio"] == 1.0


def test_freshness_history_ratio_uses_tracked_runtime_universe(monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 4, 1)

    freshness_mod._EVALUATE_FRESHNESS_CACHE.clear()
    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: expected_day)
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: False)
    monkeypatch.setattr(
        freshness_mod,
        "_build_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: (
            {"tracked_symbols": ["COMI", "TRTO", "VALU"]},
            {"COMI": expected_day, "TRTO": expected_day - datetime.timedelta(days=1)},
            {},
        ),
    )

    status = freshness_mod.evaluate_freshness(realm=realm, run_date=expected_day, scan_type="DAILY")

    assert status["history"]["kpis"]["symbol_count"] == 3
    assert status["history"]["kpis"]["fresh_symbols"] == 1
    assert status["history"]["kpis"]["stale_symbols"] == 2
    assert status["history"]["kpis"]["missing_symbols"] == 1
    assert status["history"]["kpis"]["fresh_ratio"] == 0.3333
    assert status["history"]["stale_sample"] == ["TRTO", "VALU"]


def test_runtime_report_tracks_canonical_symbol_missing_from_all_stores(monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 4, 1)

    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: expected_day)
    monkeypatch.setattr(freshness_mod, "_history_symbol_dates_raw", lambda realm: {"COMI": expected_day})
    monkeypatch.setattr(freshness_mod, "_intraday_symbol_timestamps_raw", lambda realm: {})
    monkeypatch.setattr(
        freshness_mod,
        "_canonical_runtime_symbols",
        lambda realm: {"COMI", "VALU"},
        raising=False,
    )

    report, _, _ = freshness_mod._build_runtime_ticker_report(realm=realm, ref_date=expected_day)

    assert report["tracked_symbols"] == ["COMI", "VALU"]
    assert report["summary"]["tracked_count"] == 2
    assert report["summary"]["review_candidate_count"] == 1
    assert report["review_candidates"][0]["ticker"] == "VALU"
    assert report["review_candidates"][0]["reason"] == "MISSING_SOURCE"


def test_pre_close_requires_intraday_freshness_during_market_hours(monkeypatch):
    realm = "TESTREALM"
    expected_day = datetime.date(2026, 4, 30)

    freshness_mod._EVALUATE_FRESHNESS_CACHE.clear()
    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: expected_day)
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: True)
    monkeypatch.setattr(
        freshness_mod,
        "_build_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: (
            {"tracked_symbols": ["COMI"]},
            {"COMI": expected_day},
            {},
        ),
    )
    monkeypatch.setattr(freshness_mod.TimeUtils, "now", lambda: datetime.datetime(2026, 4, 30, 13, 0, 0))

    status = freshness_mod.evaluate_freshness(realm=realm, run_date=expected_day, scan_type="PRE_CLOSE")

    assert status["history"]["ok"] is True
    assert status["intraday"]["ok"] is False
    assert status["overall_ok"] is False


def test_source_history_dates_string_coercion(monkeypatch):
    """
    Ensure string-formatted source_history_dates (e.g., 'YYYYMMDD' from Mubasher SQLite)
    do not cause TypeError ('>=' not supported between instances of 'datetime.date' and 'str')
    in _intraday_kpis_for_day or evaluate_freshness.
    """
    target_day = datetime.date(2026, 9, 15)
    intra_ts = {"DTPP": pd.Timestamp("2026-09-14 14:29:00")}
    source_history_dates = {"DTPP": "20260914"}

    # Must not raise TypeError
    intraday_res = freshness_mod._intraday_kpis_for_day(
        intra_ts=intra_ts,
        target_day=target_day,
        stale_minutes=60,
        market_open=False,
        history_kpis={"fresh_ratio": 0.0},
        source_history_dates=source_history_dates,
    )
    assert intraday_res["live_symbols"] == 1
    assert intraday_res["stale_symbols"] == 0

    history_dates = {"DTPP": datetime.date(2026, 9, 14)}
    history_res = freshness_mod._history_kpis_for_day(
        history_dates=history_dates,
        expected_day=target_day,
        expected_symbols={"DTPP"},
        source_history_dates=source_history_dates,
    )
    assert history_res["fresh_symbols"] == 1

    # Also test evaluate_freshness with mocked runtime report and raw string dates
    freshness_mod._EVALUATE_FRESHNESS_CACHE.clear()
    monkeypatch.setattr(GlobalSettings, "get_last_completed_market_day", lambda dt: target_day)
    monkeypatch.setattr(GlobalSettings, "is_market_open", lambda: False)
    monkeypatch.setattr(
        freshness_mod,
        "_build_runtime_ticker_report",
        lambda realm, ref_date=None, dormant_trading_days=90: (
            {"tracked_symbols": ["DTPP"]},
            history_dates,
            intra_ts,
        ),
    )
    monkeypatch.setattr(freshness_mod.TimeUtils, "now", lambda: datetime.datetime(2026, 9, 15, 9, 30, 0))

    class DummyPaths:
        history_db = Path("nonexistent")

    monkeypatch.setattr("data_engine.mubasher_sqlite_source.build_paths", lambda *args, **kwargs: DummyPaths())
    monkeypatch.setattr("data_engine.mubasher_sqlite_source.get_history_last_dates", lambda *args, **kwargs: {"DTPP": "20260914"})
    # Run evaluation
    status = freshness_mod.evaluate_freshness(realm="TESTREALM", run_date=target_day, scan_type="DAILY")
    assert status["status"] in {"FRESH", "STALE"}

