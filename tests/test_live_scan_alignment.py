import datetime
import pytest
import pandas as pd
from core import TimeUtils
from core.settings import settings
from core.DataManager import calculate_projected_volume


def test_is_recent_trading_day_weekend_and_holidays(monkeypatch):
    # Sunday 2026-07-26 (EGX trading day)
    sunday = datetime.date(2026, 7, 26)
    thursday = datetime.date(2026, 7, 23)
    friday = datetime.date(2026, 7, 24)
    saturday = datetime.date(2026, 7, 25)

    ref_dt = datetime.datetime(2026, 7, 26, 11, 0, 0)

    # Thursday should be recent (1 trading day prior, skipping Fri & Sat)
    assert settings.is_recent_trading_day(thursday, max_trading_days=1, ref_dt=ref_dt) is True
    # Sunday itself is today, so recent
    assert settings.is_recent_trading_day(sunday, max_trading_days=1, ref_dt=ref_dt) is True


def test_volume_projection_logic():
    # 10:15 AM (Before 10:45 threshold) -> No projection
    dt_1015 = datetime.datetime(2026, 7, 28, 10, 15, 0)
    vol_1015 = calculate_projected_volume(1000.0, dt_1015, is_market_open=True, is_simulating=False)
    assert vol_1015 == 1000.0

    # 10:45 AM -> Projection starts at threshold (45m elapsed -> 35% of volume -> 1000 / 0.35 ≈ 2857.14)
    dt_1045 = datetime.datetime(2026, 7, 28, 10, 45, 0)
    vol_1045 = calculate_projected_volume(1000.0, dt_1045, is_market_open=True, is_simulating=False)
    assert pytest.approx(vol_1045, rel=1e-2) == 1000.0 / 0.35

    # Midday 12:15 PM -> (135m elapsed: 35% + 40% * (90/165) ≈ 56.82% -> 1000 / 0.5682 ≈ 1760)
    dt_midday = datetime.datetime(2026, 7, 28, 12, 15, 0)
    vol_midday = calculate_projected_volume(1000.0, dt_midday, is_market_open=True, is_simulating=False)
    assert pytest.approx(vol_midday, rel=1e-2) == 1000.0 / (0.35 + 0.40 * (90.0 / 165.0))

    # Market close 14:30 -> No projection
    dt_close = datetime.datetime(2026, 7, 28, 14, 30, 0)
    vol_close = calculate_projected_volume(1000.0, dt_close, is_market_open=True, is_simulating=False)
    assert vol_close == 1000.0

    # Replay / Simulation mode -> Must NEVER project
    dt_sim = datetime.datetime(2026, 7, 28, 12, 0, 0)
    vol_sim = calculate_projected_volume(1000.0, dt_sim, is_market_open=True, is_simulating=True)
    assert vol_sim == 1000.0

    # Market closed -> Must NEVER project
    dt_off = datetime.datetime(2026, 7, 28, 12, 0, 0)
    vol_off = calculate_projected_volume(1000.0, dt_off, is_market_open=False, is_simulating=False)
    assert vol_off == 1000.0

    # Zero / Negative volume -> Safe return
    vol_zero = calculate_projected_volume(0.0, dt_midday, is_market_open=True, is_simulating=False)
    assert vol_zero == 0.0


def test_mubasher_quote_snapshot_creates_incremental_minute_bar():
    from data_engine.mubasher_realtime_source import MubasherQuoteSnapshot
    snapshot = MubasherQuoteSnapshot(
        symbol="COMI",
        timestamp=pd.Timestamp("2026-07-28 12:30:00"),
        last=141.78,
        last_quantity=127.0,
        session_volume=481665.0,
        session_open=141.86,
        session_high=142.00,
        session_low=139.71,
        previous_close=140.0,
    )
    frame = snapshot.to_intraday_frame()
    assert not frame.empty
    row = frame.iloc[0]

    # Incremental minute bar contract: open = high = low = close = last price, volume = last_quantity
    assert float(row["open"]) == 141.78
    assert float(row["high"]) == 141.78
    assert float(row["low"]) == 141.78
    assert float(row["close"]) == 141.78
    assert float(row["volume"]) == 127.0

    # Session metadata is preserved on snapshot object without corrupting incremental bar
    assert snapshot.session_open == 141.86
    assert snapshot.session_high == 142.00
    assert snapshot.session_low == 139.71
    assert snapshot.session_volume == 481665.0
