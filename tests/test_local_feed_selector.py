from core.settings import settings
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from data_engine.local_feed_selector import compare_local_sources, resolve_local_feed_provider
from data_engine.local_feed_selector import (
    apply_startup_recommended_provider,
    format_quality_report,
    provider_decision_for_timeframe,
    recommend_provider_for_timeframe,
    resolve_timeframe_provider,
)


def _write_csv_history(path: Path, rows: list[str]) -> None:
    path.write_text("<DATE>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n" + "\n".join(rows) + "\n", encoding="utf-8")


def _write_csv_intraday(path: Path, rows: list[str]) -> None:
    path.write_text("<DTYYYYMMDD>,<HHMMSS>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>\n" + "\n".join(rows) + "\n", encoding="utf-8")


def _setup_mubasher_db(root: Path) -> None:
    base = root / "UserData" / "847857994"
    (base / "History" / "CASE").mkdir(parents=True, exist_ok=True)
    (base / "Intraday" / "CASE").mkdir(parents=True, exist_ok=True)
    history_db = base / "History" / "CASE" / "history.db"
    intraday_db = base / "Intraday" / "CASE" / "INTRADAY_MASTER.db"

    with closing(sqlite3.connect(history_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (DATE TEXT)')
        conn.execute('CREATE TABLE "_FWRY" (DATE TEXT)')
        conn.execute('INSERT INTO "_COMI" VALUES ("20260212")')
        conn.execute('INSERT INTO "_FWRY" VALUES ("20260212")')
        conn.commit()

    with closing(sqlite3.connect(intraday_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER)')
        conn.execute('CREATE TABLE "_FWRY" (TMIN INTEGER)')
        conn.execute('INSERT INTO "_COMI" VALUES (29400480)')  # 2026+ range minute marker
        conn.execute('INSERT INTO "_FWRY" VALUES (29400480)')
        conn.commit()


def test_resolve_provider_auto_prefers_mubasher_when_more_complete(tmp_path, monkeypatch):
    csv_history = tmp_path / "csv_history"
    csv_intraday = tmp_path / "csv_intraday"
    csv_history.mkdir(parents=True, exist_ok=True)
    csv_intraday.mkdir(parents=True, exist_ok=True)

    _write_csv_history(csv_history / "COMI.csv", ["20260210,10,12,9,11,100"])
    _write_csv_intraday(csv_intraday / "COMI.csv", ["20260210,100000,10,12,9,11,100"])

    mubasher_root = tmp_path / "PRO Egypt"
    _setup_mubasher_db(mubasher_root)

    monkeypatch.setattr(settings, "METASTOCK_HISTORY_FOLDER", str(csv_history), raising=False)
    monkeypatch.setattr(settings, "METASTOCK_INTRADAY_FOLDER", str(csv_intraday), raising=False)
    monkeypatch.setattr(settings, "METASTOCK_DAT_HISTORY_FOLDER", str(tmp_path / "missing_dat_history"), raising=False)
    monkeypatch.setattr(settings, "METASTOCK_DAT_INTRADAY_FOLDER", str(tmp_path / "missing_dat_intraday"), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)

    report = compare_local_sources()
    provider, _ = resolve_local_feed_provider()

    assert report["recommended_provider"] == "MUBASHER_DB"
    assert provider == "MUBASHER_DB"


def test_timeframe_policy_override(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_HISTORY_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "CSV", raising=False)

    history_provider, report_h = resolve_timeframe_provider("history")
    intraday_provider, report_i = resolve_timeframe_provider("intraday")

    assert history_provider == "MUBASHER_DB"
    assert intraday_provider == "CSV"
    assert report_h is None
    assert report_i is None


def test_timeframe_policy_overrides_legacy_unified_provider(monkeypatch):
    report = {
        "db_available": True,
        "csv": {
            "history_symbols": 300,
            "history_latest": "20260212",
            "intraday_symbols": 260,
            "intraday_latest": "20260212120000",
            "available": True,
        },
        "mubasher_db": {
            "history_symbols": 536,
            "history_latest": "20260212",
            "intraday_symbols": 536,
            "intraday_latest": "20260212130000",
            "available": True,
        },
        "directfn": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
        "metastock_dat": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
    }

    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "CSV", raising=False)
    monkeypatch.setattr(settings, "LOCAL_HISTORY_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr("data_engine.local_feed_selector.compare_local_sources", lambda: report)

    history_provider, _ = resolve_timeframe_provider("history")
    intraday_provider, _ = resolve_timeframe_provider("intraday")

    assert history_provider == "MUBASHER_DB"
    assert intraday_provider == "MUBASHER_DB"


def test_intraday_recommendation_prefers_csv_when_db_stale(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20, raising=False)
    report = {
        "db_available": True,
        "csv": {
            "history_symbols": 300,
            "history_latest": "20260212",
            "intraday_symbols": 260,
            "intraday_latest": "20260212140000",
        },
        "mubasher_db": {
            "history_symbols": 500,
            "history_latest": "20260212",
            "intraday_symbols": 260,
            "intraday_latest": "20260212130000",
        },
        "directfn": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
        },
    }
    selected = recommend_provider_for_timeframe(report, timeframe="intraday")
    assert selected == "CSV"


def test_intraday_provider_decision_explains_stale_db_fallback(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20, raising=False)
    report = {
        "db_available": True,
        "csv": {
            "history_symbols": 300,
            "history_latest": "20260212",
            "intraday_symbols": 260,
            "intraday_latest": "20260212140000",
            "available": True,
        },
        "mubasher_db": {
            "history_symbols": 500,
            "history_latest": "20260212",
            "intraday_symbols": 260,
            "intraday_latest": "20260212130000",
            "available": True,
        },
        "directfn": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
        "metastock_dat": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
    }

    decision = provider_decision_for_timeframe(report, timeframe="intraday")

    assert decision["provider"] == "CSV"
    assert decision["reason"] == "stale_db_fallback"
    assert decision["fallback_from"] == "MUBASHER_DB"
    assert decision["evidence"]["csv_intraday_latest"] == "20260212140000"
    assert decision["evidence"]["db_intraday_latest"] == "20260212130000"
    assert decision["evidence"]["stale_minutes"] == 20


def test_intraday_recommendation_prefers_mubasher_precision_when_latest_ties(monkeypatch):
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20, raising=False)
    monkeypatch.setattr("data_engine.local_feed_selector.settings.is_market_open", lambda: False)
    report = {
        "db_available": True,
        "csv": {
            "history_symbols": 312,
            "history_latest": "20260525",
            "intraday_symbols": 270,
            "intraday_latest": "20260525142900",
            "available": True,
        },
        "mubasher_db": {
            "history_symbols": 546,
            "history_latest": "20260525",
            "intraday_symbols": 265,
            "intraday_latest": "20260525142900",
            "available": True,
        },
        "directfn": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
        "metastock_dat": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
    }

    decision = provider_decision_for_timeframe(report, timeframe="intraday")

    assert decision["provider"] == "MUBASHER_DB"
    assert decision["reason"] == "freshest_intraday_precision_tiebreak"
    assert decision["evidence"]["intraday_latest"] == "20260525142900"


def test_intraday_provider_decision_flags_only_stale_live_source(monkeypatch):
    monkeypatch.setattr("data_engine.local_feed_selector.TimeUtils.today", lambda: date(2026, 6, 1))
    monkeypatch.setattr("data_engine.local_feed_selector.settings.is_market_open", lambda: True)
    report = {
        "db_available": True,
        "csv": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
        "mubasher_db": {
            "history_symbols": 546,
            "history_latest": "20260525",
            "intraday_symbols": 265,
            "intraday_latest": "20260525142900",
            "available": True,
        },
        "directfn": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
        "metastock_dat": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "available": False,
        },
    }

    decision = provider_decision_for_timeframe(report, timeframe="intraday")

    assert decision["provider"] == "MUBASHER_DB"
    assert decision["reason"] == "upstream_intraday_stale"
    assert decision["fallback_from"] is None
    assert decision["evidence"]["intraday_latest"] == "20260525142900"
    assert decision["evidence"]["expected_intraday_date"] == "20260601"
    assert decision["evidence"]["market_open"] is True


def test_intraday_policy_mubasher_can_fallback_to_csv_when_stale(monkeypatch):
    stale_report = {
        "db_available": True,
        "csv": {
            "history_symbols": 307,
            "history_latest": "20260211",
            "intraday_symbols": 260,
            "intraday_latest": "20260212134100",
            "score": 1,
        },
        "mubasher_db": {
            "history_symbols": 536,
            "history_latest": "20260211",
            "intraday_symbols": 260,
            "intraday_latest": "20260211142900",
            "score": 4,
        },
        "directfn": {
            "history_symbols": 0,
            "history_latest": None,
            "intraday_symbols": 0,
            "intraday_latest": None,
            "score": 0,
        },
        "recommended_provider": "MUBASHER_DB",
        "recommended_history_provider": "MUBASHER_DB",
        "recommended_intraday_provider": "CSV",
    }

    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_HISTORY_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "MUBASHER_DB", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_ALLOW_STALE_FALLBACK", True, raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20, raising=False)
    monkeypatch.setattr("data_engine.local_feed_selector.compare_local_sources", lambda: stale_report)

    intraday_provider, report_i = resolve_timeframe_provider("intraday")

    assert intraday_provider == "CSV"
    assert report_i is not None


def test_format_quality_report_includes_provider_decision_reasons():
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
            "evidence": {
                "history_latest": "20260211",
                "history_symbols": 536,
            },
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

    formatted = format_quality_report(report)

    assert "History decision: MUBASHER_DB (most_recent_history)" in formatted
    assert "Intraday decision: CSV (stale_db_fallback from MUBASHER_DB)" in formatted


def test_startup_unified_mode_falls_back_to_timeframe_when_recommendations_differ(monkeypatch):
    report = {
        "recommended_provider": "MUBASHER_DB",
        "recommended_history_provider": "METASTOCK_DAT",
        "recommended_intraday_provider": "CSV",
    }
    monkeypatch.setattr("data_engine.local_feed_selector.compare_local_sources", lambda: report)
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_HISTORY_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "AUTO", raising=False)

    selection = apply_startup_recommended_provider(unified=True)

    assert selection["mode"] == "TIMEFRAME"
    assert selection["history_provider"] == "METASTOCK_DAT"
    assert selection["intraday_provider"] == "CSV"
    assert selection["fallback_from"] == "UNIFIED"
    assert selection["selected_provider"] == "AUTO"


def test_startup_can_force_unified_when_explicitly_requested(monkeypatch):
    report = {
        "recommended_provider": "MUBASHER_DB",
        "recommended_history_provider": "METASTOCK_DAT",
        "recommended_intraday_provider": "CSV",
    }
    monkeypatch.setattr("data_engine.local_feed_selector.compare_local_sources", lambda: report)
    monkeypatch.setattr(settings, "LOCAL_FEED_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_HISTORY_PROVIDER", "AUTO", raising=False)
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_PROVIDER", "AUTO", raising=False)

    selection = apply_startup_recommended_provider(unified=True, force_unified=True)

    assert selection["mode"] == "UNIFIED"
    assert selection["selected_provider"] == "MUBASHER_DB"
    assert selection["history_provider"] == "MUBASHER_DB"
    assert selection["intraday_provider"] == "MUBASHER_DB"
