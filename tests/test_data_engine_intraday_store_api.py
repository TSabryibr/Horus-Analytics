import pandas as pd

from data_engine import api as data_api
from data_engine import intraday_store


def test_intraday_get_data_prefers_sqlite_store(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    df = pd.DataFrame(
        [
            {"timestamp": "2026-02-12 10:00:00", "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 100},
            {"timestamp": "2026-02-12 10:01:00", "open": 10.5, "high": 11.2, "low": 10.2, "close": 11.0, "volume": 120},
        ]
    )
    intraday_store.upsert_intraday("COMI", df, realm="EGX")

    def _boom(*args, **kwargs):
        raise AssertionError("read_parquet should not be used when intraday store has data")

    monkeypatch.setattr(data_api.pd, "read_parquet", _boom)

    out = data_api.get_data("COMI", timeframe="intraday", realm="EGX", limit=1)
    assert len(out) == 1
    assert float(out["close"].iloc[-1]) == 11.0


def test_intraday_store_get_latest_timestamps_returns_max_per_ticker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    intraday_store.upsert_intraday(
        "COMI",
        pd.DataFrame(
            [
                {"timestamp": "2026-02-12 10:00:00", "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 100},
                {"timestamp": "2026-02-12 10:05:00", "open": 10.5, "high": 11.2, "low": 10.2, "close": 11.0, "volume": 120},
            ]
        ),
        realm="EGX",
    )
    intraday_store.upsert_intraday(
        "FWRY",
        pd.DataFrame(
            [
                {"timestamp": "2026-02-12 09:55:00", "open": 20.0, "high": 20.5, "low": 19.9, "close": 20.3, "volume": 80},
            ]
        ),
        realm="EGX",
    )

    latest = intraday_store.get_latest_timestamps(realm="EGX")

    assert latest["COMI"] == pd.Timestamp("2026-02-12 10:05:00")
    assert latest["FWRY"] == pd.Timestamp("2026-02-12 09:55:00")


def test_intraday_store_get_latest_bars_returns_latest_ohlcv_per_ticker(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    intraday_store.upsert_intraday(
        "COMI",
        pd.DataFrame(
            [
                {"timestamp": "2026-02-12 10:00:00", "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 100},
                {"timestamp": "2026-02-12 10:05:00", "open": 10.5, "high": 11.2, "low": 10.2, "close": 11.0, "volume": 120},
            ]
        ),
        realm="EGX",
    )
    intraday_store.upsert_intraday(
        "FWRY",
        pd.DataFrame(
            [
                {"timestamp": "2026-02-12 09:55:00", "open": 20.0, "high": 20.5, "low": 19.9, "close": 20.3, "volume": 80},
            ]
        ),
        realm="EGX",
    )

    latest = intraday_store.get_latest_bars(["COMI"], realm="EGX")

    assert list(latest["ticker"]) == ["COMI"]
    assert latest["timestamp"].iloc[0] == pd.Timestamp("2026-02-12 10:05:00")
    assert float(latest["close"].iloc[0]) == 11.0
    assert float(latest["volume"].iloc[0]) == 120.0


def test_intraday_store_returns_available_date_counts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    intraday_store.upsert_intraday(
        "COMI",
        pd.DataFrame(
            [
                {"timestamp": "2026-02-11 10:00:00", "open": 10.0, "high": 11.0, "low": 9.5, "close": 10.5, "volume": 100},
                {"timestamp": "2026-02-12 10:05:00", "open": 10.5, "high": 11.2, "low": 10.2, "close": 11.0, "volume": 120},
            ]
        ),
        realm="EGX",
    )
    intraday_store.upsert_intraday(
        "FWRY",
        pd.DataFrame(
            [
                {"timestamp": "2026-02-12 09:55:00", "open": 20.0, "high": 20.5, "low": 19.9, "close": 20.3, "volume": 80},
            ]
        ),
        realm="EGX",
    )

    dates = intraday_store.get_intraday_date_counts(realm="EGX")

    assert dates == [
        {"date": "2026-02-11", "records": 1, "tickers": 1},
        {"date": "2026-02-12", "records": 2, "tickers": 2},
    ]
