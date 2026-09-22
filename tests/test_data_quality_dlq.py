from pathlib import Path

import pandas as pd

from data_engine import intraday_store, parquet_writer
from data_engine.data_quality import validate_ohlcv_and_quarantine
from core.settings import settings


def test_parquet_writer_quarantines_invalid_ohlcv_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"timestamp": "2026-02-17 10:00:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": "2026-02-17 10:01:00", "open": 10, "high": 9, "low": 10, "close": 10.2, "volume": -5},
        ]
    )

    parquet_writer.save_stream("COMI", df, folder="history", realm="TEST")
    data_root = Path(settings.DATA_ROOT)
    out_file = data_root / "TEST" / "history" / "COMI.parquet"
    dlq_file = data_root / "TEST" / "dlq" / "history" / "COMI.parquet"
    assert out_file.exists()
    assert dlq_file.exists()

    out_df = pd.read_parquet(out_file)
    dlq_df = pd.read_parquet(dlq_file)
    assert len(out_df) == 1
    assert len(dlq_df) >= 1
    assert "_dlq_reason" in dlq_df.columns


def test_intraday_store_quarantines_invalid_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"timestamp": "2026-02-17 10:00:00", "open": 20, "high": 21, "low": 19, "close": 20.5, "volume": 100},
            {"timestamp": "2026-02-17 10:01:00", "open": -5, "high": 19, "low": 18, "close": 20.5, "volume": 20},
        ]
    )
    inserted = intraday_store.upsert_intraday("COMI", df, realm="TEST2")
    out = intraday_store.get_intraday_data("COMI", realm="TEST2")

    data_root = Path(settings.DATA_ROOT)
    dlq_file = data_root / "TEST2" / "dlq" / "intraday_store" / "COMI.parquet"
    assert inserted == 1
    assert len(out) == 1
    assert dlq_file.exists()


def test_validate_ohlcv_returns_rejection_reason_counts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"timestamp": "2026-02-17 10:00:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": "not-a-date", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": "2026-02-17 10:01:00", "open": -5, "high": 19, "low": 18, "close": 20.5, "volume": 20},
            {"timestamp": "2026-02-17 10:02:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": -1},
        ]
    )

    cleaned, dq = validate_ohlcv_and_quarantine("COMI", df, realm="TEST3", stream="intraday")

    assert len(cleaned) == 1
    assert dq["rejected_rows"] == 3
    assert dq["rejection_reason_counts"]["invalid_timestamp"] == 1
    assert dq["rejection_reason_counts"]["invalid_price"] == 1
    assert dq["rejection_reason_counts"]["negative_volume"] == 1
    assert dq["dlq_path"]


def test_validate_ohlcv_emits_rejection_reason_counts_in_event(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    emitted = []
    monkeypatch.setattr("data_engine.data_quality.emit_event", lambda event, level="info", **fields: emitted.append((event, level, fields)))

    df = pd.DataFrame(
        [
            {"timestamp": "2026-02-17 10:00:00", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": "2026-02-17 10:01:00", "open": -5, "high": 19, "low": 18, "close": 20.5, "volume": 20},
            {"timestamp": "2026-02-17 10:02:00", "open": -4, "high": 18, "low": 17, "close": 19.5, "volume": 10},
            {"timestamp": "2026-02-17 10:03:00", "open": -3, "high": 17, "low": 16, "close": 18.5, "volume": 5},
            {"timestamp": "2026-02-17 10:04:00", "open": -2, "high": 16, "low": 15, "close": 17.5, "volume": 1},
            {"timestamp": "2026-02-17 10:05:00", "open": -1, "high": 15, "low": 14, "close": 16.5, "volume": 1},
        ]
    )

    _, dq = validate_ohlcv_and_quarantine("COMI", df, realm="TEST4", stream="intraday")

    assert dq["rejected_rows"] == 5
    assert emitted
    event, level, fields = emitted[-1]
    assert event == "pipeline.data_quality.rejected_rows"
    assert level == "info"
    assert fields["rejection_reason_counts"]["invalid_price"] == 5


def test_validate_ohlcv_emits_source_note_for_legacy_zero_price_history_rows(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    emitted = []
    monkeypatch.setattr("data_engine.data_quality.emit_event", lambda event, level="info", **fields: emitted.append((event, level, fields)))

    df = pd.DataFrame(
        [
            {"timestamp": "2003-11-03", "open": 0.01, "high": 0.01, "low": 0.00, "close": 0.01, "volume": 2167265},
            {"timestamp": "2003-11-04", "open": 0.01, "high": 0.01, "low": 0.00, "close": 0.00, "volume": 2858800},
            {"timestamp": "2003-11-05", "open": 0.01, "high": 0.01, "low": 0.01, "close": 0.01, "volume": 13831345},
        ]
    )

    _, dq = validate_ohlcv_and_quarantine("GGCC", df, realm="TEST5", stream="history")

    assert dq["rejected_rows"] == 2
    assert emitted
    event, level, fields = emitted[-1]
    assert event == "pipeline.data_quality.rejected_rows"
    assert level == "info"
    assert fields["rejection_reason_counts"]["invalid_price"] == 2
    assert fields["source_note"] == "Legacy vendor source contains zero-price OHLC rows; quarantined as expected."
