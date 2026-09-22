import datetime

import pandas as pd

from core import TimeUtils
def test_now_returns_datetime():
    result = TimeUtils.now()
    assert isinstance(result, datetime.datetime)


def test_today_returns_date():
    result = TimeUtils.today()
    assert isinstance(result, datetime.date)


def test_pd_now_returns_timestamp():
    result = TimeUtils.pd_now()
    assert isinstance(result, pd.Timestamp)


def test_set_simulation_overrides_now():
    target = datetime.datetime(2025, 6, 15, 10, 30, 0)
    TimeUtils.set_simulation(target)
    try:
        assert TimeUtils.now() == target
        assert TimeUtils.today() == target.date()
    finally:
        TimeUtils.clear_simulation()


def test_clear_simulation_restores_live():
    target = datetime.datetime(2025, 1, 1)
    TimeUtils.set_simulation(target)
    TimeUtils.clear_simulation()

    # After clearing, now() should be close to real time, not 2025-01-01
    result = TimeUtils.now()
    assert result.year >= 2026
    assert not TimeUtils.is_simulating()


def test_is_simulating_lifecycle():
    assert TimeUtils.is_simulating() is False

    TimeUtils.set_simulation(datetime.datetime(2025, 3, 1))
    assert TimeUtils.is_simulating() is True
    assert TimeUtils.get_simulation_date() == datetime.datetime(2025, 3, 1)

    TimeUtils.clear_simulation()
    assert TimeUtils.is_simulating() is False
    assert TimeUtils.get_simulation_date() is None


def test_simulation_status_output_is_ascii_clean(capsys):
    target = datetime.datetime(2025, 3, 1, 9, 30, 0)

    try:
        TimeUtils.set_simulation(target)
        activated = capsys.readouterr().out
        assert activated == "[Time Travel] Activated: 2025-03-01\n"
    finally:
        TimeUtils.clear_simulation()

    deactivated = capsys.readouterr().out
    assert deactivated == "[Time Travel] Deactivated: Back to Live\n"
