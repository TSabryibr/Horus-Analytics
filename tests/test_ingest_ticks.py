from core.settings import settings
import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

from data_engine.ingest_ticks import ingest_ticks


def _setup_trade_db(root: Path, trade_date: str) -> None:
    base = root / "UserData" / "847857994" / "HistoricalTrade" / "CASE"
    base.mkdir(parents=True, exist_ok=True)
    db_file = base / f"{trade_date}.db"
    with closing(sqlite3.connect(db_file)) as conn, conn:
        conn.execute(
            "CREATE TABLE TRADES ("
            "SEQUENCE INTEGER, SYMBOL TEXT, TRADETIME TEXT, TRADEPRICE REAL, TRADEQUANTITY REAL, "
            "VWAP REAL, NETCHANGE REAL, PERCENTCHANGE REAL, MARKETID INTEGER, "
            "TRANSACTIONTYPE TEXT, INSTRUMENTTYPE TEXT, ISODDLOTTRADE INTEGER)"
        )
        conn.execute(
            "INSERT INTO TRADES VALUES (1,'COMI','100000',90.5,100,90.4,0.5,0.55,1,'N','E',0)"
        )
        conn.execute(
            "INSERT INTO TRADES VALUES (2,'COMI','100100',90.7,150,90.5,0.7,0.78,1,'N','E',0)"
        )
        conn.commit()


def test_ingest_ticks_writes_parquet(tmp_path, monkeypatch):
    trade_date = "20260212"
    mubasher_root = tmp_path / "PRO Egypt"
    _setup_trade_db(mubasher_root, trade_date)

    monkeypatch.setattr(settings, "MUBASHER_ROOT_DIR", str(mubasher_root), raising=False)
    monkeypatch.setattr(settings, "MUBASHER_USER_ID", "847857994", raising=False)
    monkeypatch.setattr("core.Heimdall.CURRENT_REALM", "TESTREALM", raising=False)
    monkeypatch.chdir(tmp_path)

    stats = ingest_ticks(trade_date=trade_date)
    out_file = tmp_path / "data" / "TESTREALM" / "ticks" / trade_date / "COMI.parquet"

    assert stats["status"] == "ok"
    assert stats["symbols_touched"] == 1
    assert stats["rows_added"] == 2
    assert out_file.exists()

    df = pd.read_parquet(out_file)
    assert len(df) == 2
    assert list(df["sequence"]) == [1, 2]
