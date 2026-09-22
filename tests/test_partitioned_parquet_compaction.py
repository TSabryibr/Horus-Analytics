from pathlib import Path

import pandas as pd

from data_engine import api as data_api
from data_engine import parquet_writer
from data_engine.compaction import compact_folder
from data_engine.history_watermarks import cached_flat_date, load_index as load_history_watermark_index


def test_legacy_partitioned_compaction_flow(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df1 = pd.DataFrame(
        [
            {"timestamp": "2026-02-16 10:00:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
        ]
    )
    df1['timestamp'] = pd.to_datetime(df1['timestamp'])
    df1 = df1.set_index('timestamp')

    df2 = pd.DataFrame(
        [
            {"timestamp": "2026-02-17 10:00:00", "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 150},
        ]
    )
    df2['timestamp'] = pd.to_datetime(df2['timestamp'])
    df2 = df2.set_index('timestamp')

    # Mock legacy partitions
    p1 = Path("data/TEST/history/by_date/2026-02-16")
    p1.mkdir(parents=True, exist_ok=True)
    df1.to_parquet(p1 / "COMI.parquet")

    p2 = Path("data/TEST/history/by_date/2026-02-17")
    p2.mkdir(parents=True, exist_ok=True)
    df2.to_parquet(p2 / "COMI.parquet")

    stats = compact_folder(realm="TEST", folder="history", max_tickers=10)
    assert stats["compacted"] >= 1

    compacted = Path("data/TEST/history/COMI.parquet")
    assert compacted.exists()
    
    out_after = data_api.get_data("COMI", timeframe="history", realm="TEST")
    assert len(out_after) == 2

def test_flat_parquet_writer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"timestamp": "2026-02-18 10:00:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
        ]
    )
    # Testing parquet_writer.save_stream which now writes flat.
    parquet_writer.save_stream("COMI", df, folder="history", realm="TEST")

    flat = Path("data/TEST/history/COMI.parquet")
    assert flat.exists()
    watermark_index = load_history_watermark_index(flat.parent)
    assert cached_flat_date(watermark_index, "COMI", flat).isoformat() == "2026-02-18"

    out = data_api.get_data("COMI", timeframe="history", realm="TEST")
    assert len(out) == 1


def test_history_delta_writer_uses_partition_over_existing_flat(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    data_api.clear_data_cache()

    flat_dir = Path("data/TEST/history")
    flat_dir.mkdir(parents=True, exist_ok=True)
    flat_df = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-02-18"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
        ]
    ).set_index("timestamp")
    flat_df.to_parquet(flat_dir / "COMI.parquet")

    corrected_df = pd.DataFrame(
        [
            {"timestamp": "2026-02-18", "open": 10, "high": 11.2, "low": 9, "close": 10.9, "volume": 150},
        ]
    )
    parquet_writer.save_stream("COMI", corrected_df, folder="history", realm="TEST")

    partition = Path("data/TEST/history/by_date/2026-02-18/COMI.parquet")
    assert partition.exists()

    out = data_api.get_data("COMI", timeframe="history", realm="TEST")
    assert len(out) == 1
    assert float(out["close"].iloc[-1]) == 10.9


def test_compaction_merges_existing_flat_and_incremental_partitions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    flat_dir = Path("data/TEST/history")
    flat_dir.mkdir(parents=True, exist_ok=True)
    flat_df = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-02-16"), "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
        ]
    ).set_index("timestamp")
    flat_df.to_parquet(flat_dir / "COMI.parquet")

    part_dir = Path("data/TEST/history/by_date/2026-02-17")
    part_dir.mkdir(parents=True, exist_ok=True)
    part_df = pd.DataFrame(
        [
            {"timestamp": pd.Timestamp("2026-02-17"), "open": 11, "high": 12, "low": 10, "close": 11.5, "volume": 120},
        ]
    ).set_index("timestamp")
    part_df.to_parquet(part_dir / "COMI.parquet")

    stats = compact_folder(realm="TEST", folder="history", max_tickers=10)
    assert stats["compacted"] == 1

    compacted = pd.read_parquet(flat_dir / "COMI.parquet")
    assert len(compacted) == 2
    assert float(compacted["close"].iloc[-1]) == 11.5
    watermark_index = load_history_watermark_index(flat_dir)
    assert cached_flat_date(watermark_index, "COMI", flat_dir / "COMI.parquet").isoformat() == "2026-02-17"
