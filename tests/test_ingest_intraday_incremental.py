from core.settings import settings
from core.exclusions import get_all_exclusions
import sqlite3
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path

import pandas as pd

from data_engine import intraday_store
from data_engine.ingest_intraday import (
    _ingest_intraday_from_mubasher_db,
    _source_archive_lags_live_day,
    get_last_ingest_intraday_summary,
    ingest_intraday,
)
from data_engine.mubasher_realtime_source import MubasherQuoteSnapshot
from data_engine.mubasher_sqlite_source import epoch_minute_to_local_naive, local_naive_to_epoch_minute


def _setup_intraday_db(root: Path) -> Path:
    base = root / "UserData" / "847857994" / "Intraday" / "CASE"
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / "INTRADAY_MASTER.db"
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute("INSERT INTO \"_COMI\" VALUES (?,?, ?, ?, ?, ?)", (1000, 10, 11, 9, 10.5, 100))
        conn.execute("INSERT INTO \"_COMI\" VALUES (?,?, ?, ?, ?, ?)", (1001, 10.5, 11.5, 10, 11, 120))
        conn.commit()
    return db_path


def test_ingest_intraday_mubasher_db_runs_incremental(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_intraday_db(mubasher_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)
    monkeypatch.setattr(settings, "INTRADAY_PARQUET_MIRROR", False, raising=False)

    ts_1000 = epoch_minute_to_local_naive(pd.Series([1000])).iloc[0]
    pre_existing = pd.DataFrame(
        [{"timestamp": ts_1000, "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    )
    intraday_store.upsert_intraday("COMI", pre_existing, realm="EGX")

    updated_first = _ingest_intraday_from_mubasher_db()
    assert updated_first == 1

    result = intraday_store.get_intraday_data("COMI", realm="EGX")
    assert len(result) == 2

    updated_second = _ingest_intraday_from_mubasher_db()
    assert updated_second == 0


def test_ingest_intraday_mubasher_db_skips_tail_load_when_latest_bar_unchanged(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_intraday_db(mubasher_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)
    monkeypatch.setattr(settings, "INTRADAY_PARQUET_MIRROR", False, raising=False)
    monkeypatch.setattr(settings, "INTRADAY_REFRESH_EQUAL_MINUTE", True, raising=False)

    pre_existing = pd.DataFrame(
        [
            {"timestamp": epoch_minute_to_local_naive(pd.Series([1000])).iloc[0], "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": epoch_minute_to_local_naive(pd.Series([1001])).iloc[0], "open": 10.5, "high": 11.5, "low": 10, "close": 11, "volume": 120},
        ]
    )
    intraday_store.upsert_intraday("COMI", pre_existing, realm="EGX")

    def _fail_tail_load(*args, **kwargs):
        raise AssertionError("unchanged latest bar should not load a per-symbol source tail")

    monkeypatch.setattr("data_engine.ingest_intraday.load_intraday_dataframe", _fail_tail_load)

    updated = _ingest_intraday_from_mubasher_db()

    assert updated == 0


def test_ingest_intraday_mubasher_db_refreshes_same_minute_correction(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_intraday_db(mubasher_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)
    monkeypatch.setattr(settings, "INTRADAY_PARQUET_MIRROR", False, raising=False)

    ts_1000 = epoch_minute_to_local_naive(pd.Series([1000])).iloc[0]
    ts_1001 = epoch_minute_to_local_naive(pd.Series([1001])).iloc[0]
    stale_store = pd.DataFrame(
        [
            {"timestamp": ts_1000, "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0},
            {"timestamp": ts_1001, "open": 10.5, "high": 11.5, "low": 10.0, "close": 10.8, "volume": 110.0},
        ]
    )
    intraday_store.upsert_intraday("COMI", stale_store, realm="EGX")

    updated = _ingest_intraday_from_mubasher_db()
    assert updated == 1

    result = intraday_store.get_intraday_data("COMI", realm="EGX")
    assert len(result) == 2
    assert float(result["close"].iloc[-1]) == 11.0
    assert float(result["volume"].iloc[-1]) == 120.0


def test_ingest_intraday_mubasher_realtime_overlay_when_archive_lags(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    base = mubasher_root / "UserData" / "847857994" / "Intraday" / "CASE"
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / "INTRADAY_MASTER.db"
    stale_tmin = local_naive_to_epoch_minute(pd.Timestamp("2026-05-25 14:29:00"))
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute(
            'INSERT INTO "_COMI" VALUES (?, ?, ?, ?, ?, ?)',
            (stale_tmin, 10.0, 10.0, 10.0, 10.0, 100.0),
        )
        conn.commit()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True, raising=False)
    monkeypatch.setattr(settings, "MUBASHER_REALTIME_OVERLAY_ENABLED", True, raising=False)
    monkeypatch.setattr("data_engine.ingest_intraday.TimeUtils.today", lambda: date(2026, 6, 1))
    monkeypatch.setattr(settings, "INTRADAY_PARQUET_MIRROR", False, raising=False)
    monkeypatch.setattr(
        "data_engine.ingest_intraday.fetch_realtime_snapshots",
        lambda symbols, root, user_id=None: {
            "COMI": MubasherQuoteSnapshot(
                symbol="COMI",
                timestamp=pd.Timestamp("2026-06-01 10:39:05"),
                last=11.0,
                last_quantity=50.0,
            )
        },
    )

    updated = _ingest_intraday_from_mubasher_db()

    assert updated == 2
    result = intraday_store.get_intraday_data("COMI", realm="EGX")
    assert result.index.max() == pd.Timestamp("2026-06-01 10:39:00")
    assert float(result["close"].iloc[-1]) == 11.0
    assert float(result["volume"].iloc[-1]) == 50.0


def test_mubasher_realtime_overlay_activates_when_archive_is_stale_same_day(monkeypatch):
    stale_tmin = local_naive_to_epoch_minute(pd.Timestamp("2026-06-01 10:30:00"))

    monkeypatch.setattr(settings, "is_market_open", lambda: True, raising=False)
    monkeypatch.setattr("data_engine.ingest_intraday.TimeUtils.today", lambda: date(2026, 6, 1))
    monkeypatch.setattr(
        "data_engine.ingest_intraday.TimeUtils.now",
        lambda: pd.Timestamp("2026-06-01 10:55:00").to_pydatetime(),
    )
    monkeypatch.setattr(settings, "LOCAL_INTRADAY_DB_STALE_MINUTES", 20, raising=False)

    assert _source_archive_lags_live_day({"COMI": stale_tmin}) is True


def test_ingest_intraday_mubasher_realtime_keeps_live_cache_when_archive_lags(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_intraday_db(mubasher_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)
    monkeypatch.setattr(settings, "is_market_open", lambda: True, raising=False)
    monkeypatch.setattr(settings, "MUBASHER_REALTIME_OVERLAY_ENABLED", True, raising=False)
    monkeypatch.setattr("data_engine.ingest_intraday.TimeUtils.today", lambda: date(2026, 6, 1))
    monkeypatch.setattr(settings, "INTRADAY_PARQUET_MIRROR", False, raising=False)
    intraday_store.upsert_intraday(
        "COMI",
        pd.DataFrame(
            [
                {
                    "timestamp": pd.Timestamp("2026-06-01 10:35:00"),
                    "open": 12.0,
                    "high": 12.0,
                    "low": 12.0,
                    "close": 12.0,
                    "volume": 20.0,
                }
            ]
        ),
        realm="EGX",
    )
    monkeypatch.setattr(
        "data_engine.ingest_intraday.fetch_realtime_snapshots",
        lambda symbols, root, user_id=None: {
            "COMI": MubasherQuoteSnapshot(
                symbol="COMI",
                timestamp=pd.Timestamp("2026-06-01 10:40:15"),
                last=13.0,
                last_quantity=30.0,
            )
        },
    )

    _ingest_intraday_from_mubasher_db()

    result = intraday_store.get_intraday_data("COMI", realm="EGX")
    assert pd.Timestamp("2026-06-01 10:35:00") in result.index
    assert result.index.max() == pd.Timestamp("2026-06-01 10:40:00")
    assert float(result["close"].iloc[-1]) == 13.0


def test_ingest_intraday_emits_structured_fallback_summary(monkeypatch):
    emitted = []

    @contextmanager
    def _fake_lock():
        yield True

    monkeypatch.setattr("data_engine.ingest_intraday._ingestion_lock", _fake_lock)
    monkeypatch.setattr(
        "data_engine.ingest_intraday.resolve_timeframe_provider",
        lambda timeframe, provider=None: ("MUBASHER_DB", None),
    )
    monkeypatch.setattr("data_engine.ingest_intraday._ingest_intraday_from_mubasher_db", lambda: -1)
    monkeypatch.setattr("data_engine.ingest_intraday._ingest_intraday_from_csv", lambda: 7)
    monkeypatch.setattr(
        "data_engine.ingest_intraday.emit_event",
        lambda event, level="info", **fields: emitted.append((event, level, fields)),
    )

    updated = ingest_intraday(provider="MUBASHER_DB")

    assert updated == 7
    assert emitted
    event, level, fields = emitted[-1]
    assert event == "pipeline.ingest_intraday.provider_fallback"
    assert level == "warning"
    assert fields["requested_provider"] == "MUBASHER_DB"
    assert fields["fallback_provider"] == "CSV"
    assert fields["failure_mode"] == "source_unavailable"
    assert fields["updated"] == 7

    summary = get_last_ingest_intraday_summary()
    assert summary["requested_provider"] == "MUBASHER_DB"
    assert summary["used_provider"] == "CSV"
    assert summary["fallback_from"] == "MUBASHER_DB"
    assert summary["failure_mode"] == "source_unavailable"
    assert summary["updated"] == 7
