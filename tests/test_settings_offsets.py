from core.settings import settings
import pytest
from core.scheduling import reschedule_market_jobs
from routes.shared import scheduler

@pytest.fixture(autouse=True)
def setup_teardown():
    # Store original settings
    orig_pre_close = getattr(settings, "PRE_CLOSE_OFFSET_MINS", 20)
    orig_daily_signal = getattr(settings, "DAILY_SIGNAL_OFFSET_MINS", 30)
    orig_intraday = getattr(settings, "INTRADAY_INTERVAL_MINS", 5)

    # Make sure scheduler is started for the test
    if not scheduler.running:
        scheduler.start()
        
    # Add dummy jobs to avoid JobLookupError during reschedule
    try:
        scheduler.add_job(lambda: None, 'cron', hour=12, minute=0, id='pre_close_scan')
    except Exception:
        pass
    try:
        scheduler.add_job(lambda: None, 'cron', hour=12, minute=0, id='daily_signal_scan')
    except Exception:
        pass
    try:
        scheduler.add_job(lambda: None, 'interval', minutes=5, id='intraday_scan')
    except Exception:
        pass

    yield

    # Restore
    settings.PRE_CLOSE_OFFSET_MINS = orig_pre_close
    settings.DAILY_SIGNAL_OFFSET_MINS = orig_daily_signal
    settings.INTRADAY_INTERVAL_MINS = orig_intraday

def test_offset_variables_can_be_updated():
    payload = {
        "PRE_CLOSE_OFFSET_MINS": 15,
        "DAILY_SIGNAL_OFFSET_MINS": 45,
        "INTRADAY_INTERVAL_MINS": 10
    }
    settings.update(payload)
    
    assert settings.PRE_CLOSE_OFFSET_MINS == 15
    assert settings.DAILY_SIGNAL_OFFSET_MINS == 45
    assert settings.INTRADAY_INTERVAL_MINS == 10

def test_api_reschedule_market_jobs():
    payload = {
        "PRE_CLOSE_OFFSET_MINS": 12,
        "DAILY_SIGNAL_OFFSET_MINS": 22,
        "INTRADAY_INTERVAL_MINS": 7
    }
    settings.update(payload)
    
    # Actually call the reschedule logic
    reschedule_market_jobs(scheduler)
    
    # Check if the jobs are correctly updated in the scheduler
    pre_close_job = scheduler.get_job('pre_close_scan')
    daily_signal_job = scheduler.get_job('daily_signal_scan')
    intraday_job = scheduler.get_job('intraday_scan')
    
    assert pre_close_job is not None
    assert daily_signal_job is not None
    assert intraday_job is not None
    
    # Calculate expected times
    import datetime as dt
    close_h, close_m = settings.get_market_close_hour_minute()
    close_dt = dt.datetime(2000, 1, 1, close_h, close_m)
    expected_pre_close = close_dt - dt.timedelta(minutes=12)
    expected_daily = close_dt + dt.timedelta(minutes=22)
    
    # For cron triggers, fields are objects. We get the exact string representation to compare.
    pre_close_fields = {f.name: str(f) for f in pre_close_job.trigger.fields}
    assert pre_close_fields['hour'] == str(expected_pre_close.hour)
    assert pre_close_fields['minute'] == str(expected_pre_close.minute)
    
    daily_fields = {f.name: str(f) for f in daily_signal_job.trigger.fields}
    assert daily_fields['hour'] == str(expected_daily.hour)
    assert daily_fields['minute'] == str(expected_daily.minute)
    
    # Check interval
    assert intraday_job.trigger.interval == dt.timedelta(minutes=7)
