import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from data_engine.mubasher_sqlite_source import (
    build_paths,
    epoch_minute_to_local_naive,
    get_history_last_dates,
    get_intraday_latest_bars,
    list_history_symbols,
    list_intraday_symbols,
    local_naive_to_epoch_minute,
    load_history_dataframe,
    load_intraday_dataframe,
)


def _setup_mubasher_tree(tmp_path: Path) -> Path:
    root = tmp_path / "PRO Egypt"
    base = root / "UserData" / "847857994"
    (base / "History" / "CASE").mkdir(parents=True, exist_ok=True)
    (base / "Intraday" / "CASE").mkdir(parents=True, exist_ok=True)
    return root


def test_load_history_dataframe_normalizes_schema(tmp_path):
    root = _setup_mubasher_tree(tmp_path)
    paths = build_paths(root)

    with closing(sqlite3.connect(paths.history_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (DATE TEXT, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute('INSERT INTO "_COMI" VALUES ("20260210", 10, 12, 9, 11, 1000)')
        conn.execute('INSERT INTO "_COMI" VALUES ("20260211", 11, 13, 10, 12, 1200)')
        conn.commit()

    df = load_history_dataframe(paths, "COMI")

    assert list_history_symbols(paths) == ["COMI"]
    assert not df.empty
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert df["timestamp"].iloc[-1].strftime("%Y%m%d") == "20260211"
    assert float(df["close"].iloc[-1]) == 12.0


def test_get_history_last_dates_uses_source_signature_cache(tmp_path, monkeypatch):
    root = _setup_mubasher_tree(tmp_path)
    paths = build_paths(root)
    monkeypatch.setattr("data_engine.mubasher_sqlite_source._SOURCE_CACHE_DIR", tmp_path / "source_cache")

    with closing(sqlite3.connect(paths.history_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (DATE TEXT, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute('INSERT INTO "_COMI" VALUES ("20260211", 10, 12, 9, 11, 1000)')
        conn.commit()

    assert get_history_last_dates(paths) == {"COMI": "20260211"}

    def _fail_open(*args, **kwargs):
        raise AssertionError("matching source cache should avoid opening history DB")

    monkeypatch.setattr("data_engine.mubasher_sqlite_source._open_sqlite_ro", _fail_open)

    assert get_history_last_dates(paths) == {"COMI": "20260211"}


def test_load_intraday_dataframe_converts_epoch_minutes_to_local(tmp_path):
    root = _setup_mubasher_tree(tmp_path)
    paths = build_paths(root)

    utc_minute = int(pd.Timestamp("2026-02-12 09:00:00", tz="UTC").timestamp() // 60)
    expected_local = epoch_minute_to_local_naive(pd.Series([utc_minute])).iloc[0]

    with closing(sqlite3.connect(paths.intraday_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute('INSERT INTO "_COMI" VALUES (?, 20, 22, 19, 21, 500)', (utc_minute,))
        conn.commit()

    df = load_intraday_dataframe(paths, "COMI")

    assert list_intraday_symbols(paths) == ["COMI"]
    assert not df.empty
    assert list(df.columns) == ["timestamp", "open", "high", "low", "close", "volume"]
    assert df["timestamp"].iloc[0] == expected_local
    assert float(df["close"].iloc[0]) == 21.0


def test_load_intraday_dataframe_supports_min_tmin_delta_filter(tmp_path):
    root = _setup_mubasher_tree(tmp_path)
    paths = build_paths(root)

    minute_1 = int(pd.Timestamp("2026-02-12 09:00:00", tz="UTC").timestamp() // 60)
    minute_2 = int(pd.Timestamp("2026-02-12 09:01:00", tz="UTC").timestamp() // 60)

    with closing(sqlite3.connect(paths.intraday_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute("INSERT INTO \"_COMI\" VALUES (?, 20, 22, 19, 21, 500)", (minute_1,))
        conn.execute("INSERT INTO \"_COMI\" VALUES (?, 21, 23, 20, 22, 600)", (minute_2,))
        conn.commit()

    full_df = load_intraday_dataframe(paths, "COMI")
    assert len(full_df) == 2

    watermark = local_naive_to_epoch_minute(full_df["timestamp"].iloc[0])
    delta_df = load_intraday_dataframe(paths, "COMI", min_tmin=watermark)

    assert len(delta_df) == 1
    assert float(delta_df["close"].iloc[0]) == 22.0


def test_get_intraday_latest_bars_returns_latest_ohlcv_per_symbol(tmp_path):
    root = _setup_mubasher_tree(tmp_path)
    paths = build_paths(root)

    minute_1 = int(pd.Timestamp("2026-02-12 09:00:00", tz="UTC").timestamp() // 60)
    minute_2 = int(pd.Timestamp("2026-02-12 09:01:00", tz="UTC").timestamp() // 60)

    with closing(sqlite3.connect(paths.intraday_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute("INSERT INTO \"_COMI\" VALUES (?, 20, 22, 19, 21, 500)", (minute_1,))
        conn.execute("INSERT INTO \"_COMI\" VALUES (?, 21, 23, 20, 22, 600)", (minute_2,))
        conn.commit()

    latest = get_intraday_latest_bars(paths)

    assert latest["COMI"]["tmin"] == minute_2
    assert latest["COMI"]["timestamp"] == epoch_minute_to_local_naive(pd.Series([minute_2])).iloc[0]
    assert float(latest["COMI"]["close"]) == 22.0
    assert float(latest["COMI"]["volume"]) == 600.0


def test_get_intraday_latest_bars_uses_source_signature_cache(tmp_path, monkeypatch):
    root = _setup_mubasher_tree(tmp_path)
    paths = build_paths(root)
    monkeypatch.setattr("data_engine.mubasher_sqlite_source._SOURCE_CACHE_DIR", tmp_path / "source_cache")

    minute = int(pd.Timestamp("2026-02-12 09:01:00", tz="UTC").timestamp() // 60)
    with closing(sqlite3.connect(paths.intraday_db)) as conn, conn:
        conn.execute('CREATE TABLE "_COMI" (TMIN INTEGER, OP REAL, HIG REAL, LOW REAL, CLS REAL, VOL REAL)')
        conn.execute("INSERT INTO \"_COMI\" VALUES (?, 21, 23, 20, 22, 600)", (minute,))
        conn.commit()

    first = get_intraday_latest_bars(paths)
    assert first["COMI"]["tmin"] == minute

    def _fail_open(*args, **kwargs):
        raise AssertionError("matching source cache should avoid opening intraday DB")

    monkeypatch.setattr("data_engine.mubasher_sqlite_source._open_sqlite_ro", _fail_open)

    cached = get_intraday_latest_bars(paths)
    assert cached["COMI"]["tmin"] == minute
    assert cached["COMI"]["timestamp"] == first["COMI"]["timestamp"]
    assert float(cached["COMI"]["close"]) == 22.0


def test_build_paths_resolves_empty_or_whitespace_user_id(tmp_path):
    root = _setup_mubasher_tree(tmp_path)
    paths_empty = build_paths(root, user_id="")
    assert "847857994" in str(paths_empty.history_db)
    assert paths_empty.history_db.parent.exists()

    paths_space = build_paths(root, user_id="   ")
    assert "847857994" in str(paths_space.history_db)
    assert paths_space.history_db.parent.exists()


