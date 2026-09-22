from pathlib import Path

import pandas as pd

from data_engine import api as data_api


def _write_parquet(path: Path, rows: list[tuple[str, float]]) -> None:
    df = pd.DataFrame(rows, columns=["timestamp", "close"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.set_index("timestamp")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)


def test_get_data_uses_cache_until_file_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    parquet_path = tmp_path / "data" / "EGX" / "history" / "COMI.parquet"
    _write_parquet(parquet_path, [("2026-02-12 10:00:00", 100.0)])

    data_api.clear_data_cache()
    
    # DuckDB objects are read-only, so we wrap it in a proxy to spy on execute
    class DuckDBProxy:
        def __init__(self, real_db):
            self.real_db = real_db
            self.calls = 0

        def execute(self, query, *args, **kwargs):
            if "SELECT" in query.upper() and "read_parquet" in query:
                self.calls += 1
            return self.real_db.execute(query, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.real_db, name)

    proxy = DuckDBProxy(data_api._DB)
    monkeypatch.setattr(data_api, "_DB", proxy)

    # First call: hits DB
    df_1 = data_api.get_data("COMI", timeframe="history", realm="EGX")
    # Second call: hits cache
    df_2 = data_api.get_data("COMI", timeframe="history", realm="EGX")

    assert not df_1.empty
    assert len(df_1) == 1
    assert len(df_2) == 1
    # 1 schema call + 1 data call = 2
    assert proxy.calls == 2

    # Modify file -> stamp changes
    _write_parquet(
        parquet_path,
        [("2026-02-12 10:00:00", 100.0), ("2026-02-12 10:01:00", 101.0)],
    )
    # Third call: hits DB again because stamp changed
    df_3 = data_api.get_data("COMI", timeframe="history", realm="EGX")

    assert len(df_3) == 2
    # 2 more calls = 4
    assert proxy.calls == 4


def test_get_bulk_data_scopes_partition_globs_to_requested_tickers(tmp_path, monkeypatch):
    monkeypatch.setattr(data_api, "DATA_ROOT", tmp_path / "data")
    data_api.clear_data_cache()

    _write_parquet(
        tmp_path / "data" / "EGX" / "history" / "by_date" / "2026-02-12" / "COMI.parquet",
        [("2026-02-12 10:00:00", 100.0)],
    )
    _write_parquet(
        tmp_path / "data" / "EGX" / "history" / "by_date" / "2026-02-12" / "FWRY.parquet",
        [("2026-02-12 10:00:00", 25.0)],
    )

    df = data_api.get_bulk_data(["COMI"], timeframe="history", realm="EGX")

    assert not df.empty
    assert set(df["ticker"]) == {"COMI"}


def test_get_bulk_data_prefers_partition_rows_over_flat_duplicates(tmp_path, monkeypatch):
    monkeypatch.setattr(data_api, "DATA_ROOT", tmp_path / "data")
    data_api.clear_data_cache()

    _write_parquet(
        tmp_path / "data" / "EGX" / "history" / "COMI.parquet",
        [("2026-02-12 10:00:00", 100.0)],
    )
    _write_parquet(
        tmp_path / "data" / "EGX" / "history" / "by_date" / "2026-02-12" / "COMI.parquet",
        [("2026-02-12 10:00:00", 101.0)],
    )

    df = data_api.get_bulk_data(["COMI"], timeframe="history", realm="EGX", limit=10)

    assert len(df) == 1
    assert float(df["close"].iloc[0]) == 101.0


def test_list_tickers_does_not_cache_empty_cold_start_result(tmp_path, monkeypatch):
    monkeypatch.setattr(data_api, "DATA_ROOT", tmp_path / "data")
    data_api.clear_data_cache()

    assert data_api.list_tickers(timeframe="history", realm="EGX") == []

    _write_parquet(
        tmp_path / "data" / "EGX" / "history" / "COMI.parquet",
        [("2026-02-12 10:00:00", 100.0)],
    )

    assert data_api.list_tickers(timeframe="history", realm="EGX") == ["COMI"]
