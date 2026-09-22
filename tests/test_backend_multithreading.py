import threading
import time
import pytest
import pandas as pd
from data_engine import api as data_api
from pathlib import Path

def _write_dummy_parquet(path: Path):
    df = pd.DataFrame([{"timestamp": pd.Timestamp.now(), "close": 100.0}])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path)

def test_duckdb_concurrent_reads(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create some dummy data
    for i in range(5):
        _write_dummy_parquet(tmp_path / "data" / "EGX" / "history" / f"TICKER_{i}.parquet")
    
    errors = []
    def worker():
        try:
            for _ in range(20):
                # Randomly read one of the tickers
                import random
                ticker = f"TICKER_{random.randint(0, 4)}"
                df = data_api.get_data(ticker, timeframe="history", realm="EGX")
                assert not df.empty
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Concurrent DuckDB reads failed with errors: {errors}"

def test_duckdb_mixed_load(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_dummy_parquet(tmp_path / "data" / "EGX" / "history" / "STRESS.parquet")
    
    # We want to stress the Lock. DuckDB is in-memory for queries usually but here it reads files.
    # We can also stress the LIST_CACHE and QUERY_CACHE locks.
    
    errors = []
    def reader():
        try:
            for _ in range(50):
                data_api.get_data("STRESS", timeframe="history", realm="EGX")
        except Exception as e:
            errors.append(e)

    def lister():
        try:
            for _ in range(50):
                data_api.list_tickers(timeframe="history", realm="EGX")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=reader) for _ in range(5)] + \
              [threading.Thread(target=lister) for _ in range(5)]
              
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Mixed DuckDB load failed with errors: {errors}"
