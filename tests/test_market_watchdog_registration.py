from core.settings import settings
import datetime


class RecordingScheduler:
    def __init__(self):
        self.jobs = []

    def add_job(self, func, trigger, **kwargs):
        self.jobs.append({"func": func, "trigger": trigger, **kwargs})


def test_market_watchdog_has_interval_and_exact_open_cron():
    import api

    scheduler = RecordingScheduler()

    def callback():
        return None

    api._register_market_watchdog_jobs(
        scheduler,
        callback,
        market_open_time=datetime.time(10, 0),
    )

    interval_jobs = [j for j in scheduler.jobs if j["id"] == "market_watchdog"]
    open_jobs = [j for j in scheduler.jobs if j["id"] == "market_watchdog_open"]

    assert interval_jobs == [
        {
            "func": callback,
            "trigger": "interval",
            "minutes": 5,
            "id": "market_watchdog",
            "coalesce": True,
            "max_instances": 1,
            "misfire_grace_time": 60,
        }
    ]
    assert open_jobs == [
        {
            "func": callback,
            "trigger": "cron",
            "hour": 10,
            "minute": 0,
            "id": "market_watchdog_open",
            "misfire_grace_time": 300,
            "coalesce": True,
            "max_instances": 1,
        }
    ]


def test_signal_scan_jobs_register_from_active_settings(monkeypatch):
    import api

    scheduler = RecordingScheduler()
    monkeypatch.setattr(api.settings, "get_market_close_hour_minute", lambda: (14, 30))
    monkeypatch.setattr(api.settings, "PRE_CLOSE_OFFSET_MINS", 12, raising=False)
    monkeypatch.setattr(api.settings, "DAILY_SIGNAL_OFFSET_MINS", 22, raising=False)
    monkeypatch.setattr(api.settings, "INTRADAY_INTERVAL_MINS", 7, raising=False)

    schedule = api._register_signal_scan_jobs(scheduler)
    jobs = {job["id"]: job for job in scheduler.jobs}

    assert jobs["intraday_scan"]["trigger"] == "interval"
    assert jobs["intraday_scan"]["minutes"] == 7
    assert jobs["pre_close_scan"]["trigger"] == "cron"
    assert jobs["pre_close_scan"]["hour"] == 14
    assert jobs["pre_close_scan"]["minute"] == 18
    assert jobs["daily_signal_scan"]["trigger"] == "cron"
    assert jobs["daily_signal_scan"]["hour"] == 14
    assert jobs["daily_signal_scan"]["minute"] == 52
    assert schedule["pre_close_offset_mins"] == 12
    assert schedule["daily_signal_offset_mins"] == 22
    assert schedule["intraday_interval_mins"] == 7
