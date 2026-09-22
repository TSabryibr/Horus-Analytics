from core.settings import settings
import datetime

from data_engine.observability import _LOGGER, maybe_emit_freshness_alerts, snapshot_metrics
from data_engine.run_metadata import list_runs
from data_engine import sync as sync_mod
from unittest.mock import patch

def test_freshness_alerts_emit_when_ratios_drop(monkeypatch):
    monkeypatch.setenv("FRESHNESS_MIN_HISTORY_RATIO", "0.95")
    monkeypatch.setenv("FRESHNESS_MIN_INTRADAY_RATIO", "0.90")
    monkeypatch.setenv("ALERT_COOLDOWN_SEC", "0")
    monkeypatch.setenv("FRESHNESS_ALERT_STARTUP_GRACE_SEC", "0")
    monkeypatch.setenv("FRESHNESS_INTRADAY_ALERT_GRACE_MINUTES", "0")
    monkeypatch.setenv("FRESHNESS_INTRADAY_ALERT_THRESHOLD_EPSILON", "0")
    
    with patch("data_engine.observability.settings.is_market_open", return_value=True):
        freshness = {
            "history": {"kpis": {"fresh_ratio": 0.40}},
            "intraday": {"kpis": {"live_ratio": 0.50}},
        }
        alerts = maybe_emit_freshness_alerts(freshness)
        assert len(alerts) >= 2


def test_history_freshness_alert_includes_stale_symbol_sample(monkeypatch):
    monkeypatch.setenv("FRESHNESS_MIN_HISTORY_RATIO", "0.95")
    monkeypatch.setenv("ALERT_COOLDOWN_SEC", "0")
    monkeypatch.setenv("FRESHNESS_ALERT_STARTUP_GRACE_SEC", "0")

    with patch("data_engine.observability.settings.is_market_open", return_value=False):
        freshness = {
            "history": {
                "kpis": {"fresh_ratio": 0.40},
                "stale_sample": ["ACRO", "ALEX", "ESRS", "NBKE"],
            },
            "intraday": {"kpis": {"live_ratio": 1.0}},
        }
        alerts = maybe_emit_freshness_alerts(freshness)

    history_alert = next(msg for msg in alerts if msg.startswith("history_fresh_ratio_low"))
    assert "stale_sample=ACRO,ALEX,ESRS,NBKE" in history_alert


def test_intraday_alert_suppressed_during_market_open_grace_window(monkeypatch):
    monkeypatch.setenv("FRESHNESS_MIN_HISTORY_RATIO", "0.95")
    monkeypatch.setenv("FRESHNESS_MIN_INTRADAY_RATIO", "0.65")
    monkeypatch.setenv("ALERT_COOLDOWN_SEC", "0")
    monkeypatch.setenv("FRESHNESS_ALERT_STARTUP_GRACE_SEC", "0")
    monkeypatch.setenv("FRESHNESS_INTRADAY_ALERT_GRACE_MINUTES", "20")
    monkeypatch.setenv("FRESHNESS_INTRADAY_ALERT_THRESHOLD_EPSILON", "0")
    monkeypatch.setattr("data_engine.observability._PROCESS_START_TS", 0.0, raising=False)
    monkeypatch.setattr("data_engine.observability.time.time", lambda: 10_000.0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 5, 17, 10, 5, 0))
    monkeypatch.setattr(settings, "MARKET_START_TIME", "10:00", raising=False)

    with patch("data_engine.observability.settings.is_market_open", return_value=True):
        freshness = {
            "history": {"kpis": {"fresh_ratio": 1.0}},
            "intraday": {"kpis": {"live_ratio": 0.0}},
        }
        alerts = maybe_emit_freshness_alerts(freshness)

    assert alerts == []


def test_intraday_alert_suppressed_when_only_slightly_below_threshold(monkeypatch):
    monkeypatch.setenv("FRESHNESS_MIN_HISTORY_RATIO", "0.90")
    monkeypatch.setenv("FRESHNESS_MIN_INTRADAY_RATIO", "0.65")
    monkeypatch.setenv("ALERT_COOLDOWN_SEC", "0")
    monkeypatch.setenv("FRESHNESS_ALERT_STARTUP_GRACE_SEC", "0")
    monkeypatch.setenv("FRESHNESS_INTRADAY_ALERT_GRACE_MINUTES", "0")
    monkeypatch.setenv("FRESHNESS_INTRADAY_ALERT_THRESHOLD_EPSILON", "0.01")
    monkeypatch.setattr("data_engine.observability._PROCESS_START_TS", 0.0, raising=False)
    monkeypatch.setattr("data_engine.observability.time.time", lambda: 20_000.0)
    monkeypatch.setattr("core.TimeUtils.now", lambda: datetime.datetime(2026, 5, 17, 11, 0, 0))
    monkeypatch.setattr(settings, "MARKET_START_TIME", "10:00", raising=False)

    with patch("data_engine.observability.settings.is_market_open", return_value=True):
        freshness = {
            "history": {"kpis": {"fresh_ratio": 1.0}},
            "intraday": {"kpis": {"live_ratio": 0.6464}},
        }
        alerts = maybe_emit_freshness_alerts(freshness)

    assert alerts == []


def test_pipeline_observability_logger_does_not_propagate():
    assert _LOGGER.propagate is False


def test_sync_writes_run_metadata(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import concurrent.futures
    OriginalThreadPoolExecutor = concurrent.futures.ThreadPoolExecutor
    monkeypatch.setattr("concurrent.futures.ThreadPoolExecutor", lambda **kw: OriginalThreadPoolExecutor(max_workers=1))
    monkeypatch.setenv("PARQUET_COMPACTION_ENABLED", "0")
    monkeypatch.setattr(sync_mod.settings, "is_market_open", lambda: True, raising=False)
    monkeypatch.setattr(sync_mod.settings, "TICK_SYNC_ENABLED", True, raising=False)

    report = {
        "csv": {
            "score": 1,
            "history_symbols": 300,
            "history_latest": "20260217",
            "intraday_symbols": 260,
            "intraday_latest": "20260217100000",
        },
        "mubasher_db": {
            "score": 4,
            "history_symbols": 536,
            "history_latest": "20260217",
            "intraday_symbols": 260,
            "intraday_latest": "20260217093000",
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
            "fallback_from": None,
            "evidence": {"history_latest": "20260217", "history_symbols": 536},
        },
        "recommended_intraday_details": {
            "provider": "CSV",
            "reason": "stale_db_fallback",
            "fallback_from": "MUBASHER_DB",
            "evidence": {
                "csv_intraday_latest": "20260217100000",
                "db_intraday_latest": "20260217093000",
                "stale_minutes": 20,
            },
        },
    }

    def _fake_resolve(timeframe: str, provider: str = "AUTO"):
        if timeframe == "intraday":
            return "CSV", report
        return "MUBASHER_DB", report

    monkeypatch.setattr(sync_mod, "resolve_timeframe_provider", _fake_resolve)
    monkeypatch.setattr(sync_mod, "ingest_intraday", lambda provider=None: 2)
    monkeypatch.setattr(sync_mod, "ingest_history", lambda provider=None, force_recent_days=-1: 3)
    monkeypatch.setattr(
        sync_mod,
        "ingest_ticks",
        lambda: {"status": "ok", "trade_date": "20260217", "symbols_touched": 4, "rows_added": 12},
    )
    monkeypatch.setattr(
        sync_mod,
        "evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": {
            "history": {"kpis": {"fresh_ratio": 1.0}, "last_updated": "2026-02-17"},
            "intraday": {"kpis": {"live_ratio": 1.0}, "last_bar": "2026-02-17 10:00"},
        },
    )
    monkeypatch.setattr(sync_mod.TimeUtils, "today", lambda: __import__("datetime").date(2026, 2, 17))

    sync_mod.sync_all(force_history_recent_days=0)

    runs = list_runs(realm="EGX", limit=10)
    stages = {r["stage"] for r in runs}
    assert "ingest_history" in stages
    assert "ingest_intraday" in stages
    assert "ingest_ticks" in stages
    intraday_run = next(r for r in runs if r["stage"] == "ingest_intraday")
    history_run = next(r for r in runs if r["stage"] == "ingest_history")
    assert intraday_run["provider_context"]["reason"] == "stale_db_fallback"
    assert intraday_run["provider_context"]["fallback_from"] == "MUBASHER_DB"
    assert history_run["provider_context"]["reason"] == "most_recent_history"
    assert snapshot_metrics().get("gauges") is not None


def test_sync_intraday_persists_execution_fallback_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sync_mod.TimeUtils, "today", lambda: __import__("datetime").date(2026, 2, 17))
    monkeypatch.setattr(
        sync_mod,
        "evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": {
            "history": {"kpis": {"fresh_ratio": 1.0}, "last_updated": "2026-02-17"},
            "intraday": {"kpis": {"live_ratio": 1.0}, "last_bar": "2026-02-17 10:00"},
        },
    )
    monkeypatch.setattr(sync_mod, "ingest_intraday", lambda provider=None: 2)
    monkeypatch.setattr(
        sync_mod,
        "get_last_ingest_intraday_summary",
        lambda: {
            "requested_provider": "MUBASHER_DB",
            "used_provider": "CSV",
            "fallback_from": "MUBASHER_DB",
            "failure_mode": "source_unavailable",
            "status": "completed_with_fallback",
            "updated": 2,
        },
        raising=False,
    )
    emitted = []
    monkeypatch.setattr(
        sync_mod,
        "emit_event",
        lambda event, level="info", **fields: emitted.append((event, level, fields)),
    )

    sync_mod._sync_intraday(
        "EGX",
        "MUBASHER_DB",
        {"provider": "MUBASHER_DB", "reason": "explicit_provider_override", "fallback_from": None},
    )

    intraday_run = next(r for r in list_runs(realm="EGX", limit=10) if r["stage"] == "ingest_intraday")
    assert intraday_run["provider_context"]["provider"] == "MUBASHER_DB"
    assert intraday_run["provider_context"]["ingest_summary"]["used_provider"] == "CSV"
    assert intraday_run["provider_context"]["ingest_summary"]["fallback_from"] == "MUBASHER_DB"
    assert intraday_run["provider_context"]["ingest_summary"]["status"] == "completed_with_fallback"

    stage_complete = next(
        fields for event, _, fields in emitted if event == "pipeline.stage.complete" and fields.get("stage") == "intraday"
    )
    assert stage_complete["provider_context"]["ingest_summary"]["used_provider"] == "CSV"
    assert stage_complete["ingest_summary"]["status"] == "completed_with_fallback"


def test_sync_history_persists_execution_fallback_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sync_mod.TimeUtils, "today", lambda: __import__("datetime").date(2026, 2, 17))
    monkeypatch.setattr(
        sync_mod,
        "evaluate_freshness",
        lambda realm, run_date, scan_type="DAILY": {
            "history": {"kpis": {"fresh_ratio": 1.0}, "last_updated": "2026-02-17"},
            "intraday": {"kpis": {"live_ratio": 1.0}, "last_bar": "2026-02-17 10:00"},
        },
    )
    monkeypatch.setattr(sync_mod, "ingest_history", lambda provider=None, force_recent_days=-1: 3)
    monkeypatch.setattr(
        sync_mod,
        "get_last_ingest_history_summary",
        lambda: {
            "requested_provider": "MUBASHER_DB",
            "used_provider": "CSV",
            "fallback_from": "MUBASHER_DB",
            "failure_mode": "source_unavailable",
            "status": "completed_with_fallback",
            "updated": 3,
        },
        raising=False,
    )
    emitted = []
    monkeypatch.setattr(
        sync_mod,
        "emit_event",
        lambda event, level="info", **fields: emitted.append((event, level, fields)),
    )

    sync_mod._sync_history(
        "EGX",
        "MUBASHER_DB",
        0,
        {"provider": "MUBASHER_DB", "reason": "explicit_provider_override", "fallback_from": None},
    )

    history_run = next(r for r in list_runs(realm="EGX", limit=10) if r["stage"] == "ingest_history")
    assert history_run["provider_context"]["provider"] == "MUBASHER_DB"
    assert history_run["provider_context"]["ingest_summary"]["used_provider"] == "CSV"
    assert history_run["provider_context"]["ingest_summary"]["fallback_from"] == "MUBASHER_DB"
    assert history_run["provider_context"]["ingest_summary"]["status"] == "completed_with_fallback"

    stage_complete = next(
        fields for event, _, fields in emitted if event == "pipeline.stage.complete" and fields.get("stage") == "history"
    )
    assert stage_complete["provider_context"]["ingest_summary"]["used_provider"] == "CSV"
    assert stage_complete["ingest_summary"]["status"] == "completed_with_fallback"
