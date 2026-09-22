from datetime import datetime

import pandas as pd

from data_engine.mubasher_realtime_source import (
    MubasherQuoteSnapshot,
    parse_quote_messages,
)


def _field(tag: int, value: str | int | float) -> bytes:
    return int(tag).to_bytes(2, "big") + str(value).encode("ascii")


def test_parse_quote_message_decodes_live_snapshot_fields():
    raw = b"\x03\x0e\x0a\x00\x04CASE\x1c" + b"\x1c".join(
        [
            _field(3, "ACAP"),
            _field(10, "8.71"),
            _field(11, "3500"),
            _field(16, "239505"),
            _field(30, "8.87"),
            _field(31, "8.56"),
            _field(32, "8.49"),
            _field(33, "8.49"),
            _field(75, "242"),
            _field(635, "20260601073905"),
        ]
    )

    snapshots = parse_quote_messages(raw)

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.symbol == "ACAP"
    assert snapshot.last == 8.71
    assert snapshot.last_quantity == 3500
    assert snapshot.session_volume == 239505
    assert snapshot.trades == 242
    assert snapshot.timestamp == pd.Timestamp(datetime(2026, 6, 1, 10, 39, 5))


def test_parse_quote_message_prefers_trade_last_over_daily_limit_field():
    raw = b"\x03\x0e\x0a\x00\x04CASE\x1c" + b"\x1c".join(
        [
            _field(3, "MAAL"),
            _field(10, "4.13"),
            _field(11, "24514"),
            _field(16, "1660157"),
            _field(30, "5.46"),
            _field(31, "5.24"),
            _field(32, "5.34"),
            _field(33, "5.16"),
            _field(55, "5.35"),
            _field(56, "1000"),
            _field(75, "1635"),
            _field(80, "6.19"),
            _field(81, "4.13"),
            _field(635, "20260601112318"),
        ]
    )

    snapshots = parse_quote_messages(raw)

    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.symbol == "MAAL"
    assert snapshot.last == 5.35
    assert snapshot.last_quantity == 1000


def test_quote_snapshot_converts_to_current_minute_bar():
    snapshot = MubasherQuoteSnapshot(
        symbol="ACAP",
        timestamp=pd.Timestamp("2026-06-01 10:39:05"),
        last=8.71,
        last_quantity=3500,
        session_volume=239505,
        session_open=8.49,
        session_high=8.87,
        session_low=8.56,
        trades=242,
    )

    frame = snapshot.to_intraday_frame()

    assert frame.to_dict("records") == [
        {
            "timestamp": pd.Timestamp("2026-06-01 10:39:00"),
            "open": 8.71,
            "high": 8.71,
            "low": 8.71,
            "close": 8.71,
            "volume": 3500.0,
        }
    ]


def test_quote_snapshot_rejects_price_outside_reported_session_range():
    snapshot = MubasherQuoteSnapshot(
        symbol="MAAL",
        timestamp=pd.Timestamp("2026-06-01 14:23:18"),
        last=4.13,
        last_quantity=24514,
        session_open=5.34,
        session_high=5.46,
        session_low=5.24,
        previous_close=5.16,
        trades=1635,
    )

    assert snapshot.to_intraday_frame().empty


def test_fetch_realtime_snapshots_noop_when_disabled(monkeypatch, tmp_path):
    from data_engine.mubasher_realtime_source import fetch_realtime_snapshots
    from core.settings import settings
    monkeypatch.setattr(settings, "MUBASHER_REALTIME_OVERLAY_ENABLED", False)
    assert fetch_realtime_snapshots(["COMI"], tmp_path) == {}


