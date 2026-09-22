from core.settings import settings
from core.exclusions import get_all_exclusions
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from data_engine import api as data_engine_api
from data_engine.history_watermarks import (
    cached_flat_date,
    load_index as load_history_watermark_index,
    save_index as save_history_watermark_index,
    update_flat_date as update_history_flat_date,
)
from data_engine.mubasher_sqlite_source import (
    build_paths,
    get_history_last_dates,
    load_history_dataframe,
    open_history_connection,
)
from data_engine.ingest_history import (
    _get_last_parquet_dates,
    _get_last_parquet_date,
    _ingest_history_from_mubasher_db,
    get_last_ingest_history_summary,
    ingest_history,
)


def _setup_history_db(root: Path) -> Path:
    base = root / "UserData" / "847857994" / "History" / "CASE"
    base.mkdir(parents=True, exist_ok=True)
    db_path = base / "history.db"
    with closing(sqlite3.connect(db_path)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (DATE TEXT, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute("INSERT INTO \"_COMI\" VALUES (?,?,?,?,?,?)", ("20260210", 10, 11, 9, 10.5, 100))
        conn.execute("INSERT INTO \"_COMI\" VALUES (?,?,?,?,?,?)", ("20260211", 10.5, 11.5, 10, 11.0, 120))
        conn.commit()
    return db_path


def test_ingest_history_mubasher_db_runs_incremental(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_history_db(mubasher_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)

    history_dir = tmp_path / "data" / "EGX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    pre_existing = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-10"), "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0}]
    ).set_index("timestamp")
    pre_existing.to_parquet(history_dir / "COMI.parquet")

    updated_first = _ingest_history_from_mubasher_db()
    assert updated_first == 1

    result = data_engine_api.get_data("COMI", timeframe="history", realm="EGX")
    assert len(result) == 2

    updated_second = _ingest_history_from_mubasher_db()
    assert updated_second == 0


def test_last_parquet_date_reads_incremental_partition(tmp_path, monkeypatch):
    monkeypatch.setattr(data_engine_api, "DATA_ROOT", tmp_path / "data")

    history_dir = tmp_path / "data" / "EGX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    flat_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-10"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    flat_df.to_parquet(history_dir / "COMI.parquet")

    part_dir = history_dir / "by_date" / "2026-02-11"
    part_dir.mkdir(parents=True, exist_ok=True)
    part_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-11"), "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 120}]
    ).set_index("timestamp")
    part_df.to_parquet(part_dir / "COMI.parquet")

    assert _get_last_parquet_date("COMI").isoformat() == "2026-02-11"


def test_last_parquet_dates_batch_reads_flat_and_incremental_partitions(tmp_path, monkeypatch):
    monkeypatch.setattr(data_engine_api, "DATA_ROOT", tmp_path / "data")

    history_dir = tmp_path / "data" / "EGX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    flat_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-10"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    flat_df.to_parquet(history_dir / "COMI.parquet")
    flat_df.to_parquet(history_dir / "FWRY.parquet")

    part_dir = history_dir / "by_date" / "2026-02-11"
    part_dir.mkdir(parents=True, exist_ok=True)
    part_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-11"), "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 120}]
    ).set_index("timestamp")
    part_df.to_parquet(part_dir / "COMI.parquet")

    dates = _get_last_parquet_dates(["COMI", "FWRY"], realm="EGX")

    assert dates["COMI"].isoformat() == "2026-02-11"
    assert dates["FWRY"].isoformat() == "2026-02-10"


def test_last_parquet_dates_uses_cached_flat_watermark(tmp_path, monkeypatch):
    monkeypatch.setattr(data_engine_api, "DATA_ROOT", tmp_path / "data")

    history_dir = tmp_path / "data" / "EGX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    flat_path = history_dir / "COMI.parquet"
    flat_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-11"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    flat_df.to_parquet(flat_path)

    watermark_index = load_history_watermark_index(history_dir)
    assert update_history_flat_date(watermark_index, "COMI", flat_path, pd.Timestamp("2026-02-11").date()) is True
    save_history_watermark_index(history_dir, watermark_index)

    def _fail_metadata_read(*args, **kwargs):
        raise AssertionError("cached watermark should avoid parquet metadata reads")

    monkeypatch.setattr("data_engine.ingest_history._read_parquet_max_timestamp", _fail_metadata_read)

    dates = _get_last_parquet_dates(["COMI"], realm="EGX")

    assert dates["COMI"].isoformat() == "2026-02-11"


def test_last_parquet_dates_refreshes_stale_flat_watermark(tmp_path, monkeypatch):
    monkeypatch.setattr(data_engine_api, "DATA_ROOT", tmp_path / "data")

    history_dir = tmp_path / "data" / "EGX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    flat_path = history_dir / "COMI.parquet"
    old_df = pd.DataFrame(
        [{"timestamp": pd.Timestamp("2026-02-10"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100}]
    ).set_index("timestamp")
    old_df.to_parquet(flat_path)

    watermark_index = load_history_watermark_index(history_dir)
    update_history_flat_date(watermark_index, "COMI", flat_path, pd.Timestamp("2026-02-10").date())
    save_history_watermark_index(history_dir, watermark_index)

    new_df = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-02-10"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": pd.Timestamp("2026-02-12"), "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 120},
        ]
    ).set_index("timestamp")
    new_df.to_parquet(flat_path)

    dates = _get_last_parquet_dates(["COMI"], realm="EGX")
    refreshed_index = load_history_watermark_index(history_dir)

    assert dates["COMI"].isoformat() == "2026-02-12"
    assert cached_flat_date(refreshed_index, "COMI", flat_path).isoformat() == "2026-02-12"


def test_ingest_history_mubasher_db_uses_batched_local_watermarks(tmp_path, monkeypatch):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_history_db(mubasher_root)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.exclusions.get_all_exclusions", lambda: [], raising=False)

    history_dir = tmp_path / "data" / "EGX" / "history"
    history_dir.mkdir(parents=True, exist_ok=True)
    pre_existing = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-02-10"), "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.5, "volume": 100.0},
            {"timestamp": pd.Timestamp("2026-02-11"), "open": 10.5, "high": 11.5, "low": 10.0, "close": 11.0, "volume": 120.0},
        ]
    ).set_index("timestamp")
    pre_existing.to_parquet(history_dir / "COMI.parquet")

    def _fail_single_lookup(*args, **kwargs):
        raise AssertionError("Mubasher history ingest should use batched local watermarks")

    monkeypatch.setattr("data_engine.ingest_history._get_last_parquet_date", _fail_single_lookup)

    updated = _ingest_history_from_mubasher_db()

    assert updated == 0


def test_mubasher_history_loader_accepts_shared_connection(tmp_path):
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_history_db(mubasher_root)
    paths = build_paths(mubasher_root, user_id="847857994")

    with closing(open_history_connection(paths)) as conn:
        source_last_dates = get_history_last_dates(paths, conn=conn)
        df = load_history_dataframe(paths, "COMI", min_date=pd.Timestamp("2026-02-10"), conn=conn)

    assert source_last_dates["COMI"] == "20260211"
    assert len(df) == 1
    assert df["timestamp"].iloc[0] == pd.Timestamp("2026-02-11")


def test_ingest_history_emits_structured_fallback_summary(monkeypatch):
    emitted = []

    monkeypatch.setattr(
        "data_engine.ingest_history.resolve_timeframe_provider",
        lambda timeframe, provider=None: ("MUBASHER_DB", None),
    )
    monkeypatch.setattr("data_engine.ingest_history._ingest_history_from_mubasher_db", lambda force_recent_days=0: -1)
    monkeypatch.setattr("data_engine.ingest_history._ingest_history_from_csv", lambda force_recent_days=0: 5)
    monkeypatch.setattr(
        "data_engine.ingest_history.emit_event",
        lambda event, level="info", **fields: emitted.append((event, level, fields)),
    )

    updated = ingest_history(provider="MUBASHER_DB", force_recent_days=0)

    assert updated == 5
    assert emitted
    event, level, fields = emitted[-1]
    assert event == "pipeline.ingest_history.provider_fallback"
    assert level == "warning"
    assert fields["requested_provider"] == "MUBASHER_DB"
    assert fields["fallback_provider"] == "CSV"
    assert fields["failure_mode"] == "source_unavailable"
    assert fields["updated"] == 5

    summary = get_last_ingest_history_summary()
    assert summary["requested_provider"] == "MUBASHER_DB"
    assert summary["used_provider"] == "CSV"
    assert summary["fallback_from"] == "MUBASHER_DB"
    assert summary["failure_mode"] == "source_unavailable"
    assert summary["updated"] == 5
