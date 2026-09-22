from core.settings import settings
import time
import pytest
from unittest.mock import MagicMock, patch
from data_engine.sync import sync_all, _sync_ticks

def test_sync_all_runs_parallel(monkeypatch):
    # We want to verify that _sync_intraday, _sync_history, and _sync_ticks run concurrently.
    timing = {}
    
    def mocked_sync_intraday(*args, **kwargs):
        timing['intraday_start'] = time.time()
        time.sleep(1)
        timing['intraday_end'] = time.time()

    def mocked_sync_history(*args, **kwargs):
        timing['history_start'] = time.time()
        time.sleep(1)
        timing['history_end'] = time.time()

    def mocked_sync_ticks(*args, **kwargs):
        timing['ticks_start'] = time.time()
        time.sleep(1)
        timing['ticks_end'] = time.time()

    monkeypatch.setattr("data_engine.sync._sync_intraday", mocked_sync_intraday)
    monkeypatch.setattr("data_engine.sync._sync_history", mocked_sync_history)
    monkeypatch.setattr("data_engine.sync._sync_ticks", mocked_sync_ticks)
    
    # Mock GlobalSettings and other parts needed
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    
    # Mock resolving provider to avoid disk I/O
    monkeypatch.setattr("data_engine.sync.resolve_timeframe_provider", MagicMock(return_value=("TEST_PROVIDER", None)))
    
    # Mock evaluate_freshness to avoid disk I/O
    monkeypatch.setattr("data_engine.sync.evaluate_freshness", MagicMock(return_value={}))
    
    # Mock compaction to avoid actual work
    monkeypatch.setattr("data_engine.sync.compact_folder", MagicMock(return_value={"compacted": 0}))
    
    # Mock observability to avoid side effects
    monkeypatch.setattr("data_engine.sync.emit_event", MagicMock())
    monkeypatch.setattr("data_engine.sync.set_gauge", MagicMock())
    monkeypatch.setattr("data_engine.sync.maybe_emit_freshness_alerts", MagicMock(return_value=[]))
    monkeypatch.setattr("data_engine.sync.snapshot_metrics", MagicMock(return_value={}))

    # Mock DataManager to avoid imports
    monkeypatch.setattr("data_engine.sync.os.getenv", lambda k, d=None: "0" if k == "PARQUET_COMPACTION_ENABLED" else d)

    start_time = time.time()
    sync_all()
    end_time = time.time()
    
    total_duration = end_time - start_time
    
    assert total_duration < 2.5, f"Sync stages appeared to run sequentially. Total duration: {total_duration:.2f}s"
    assert 'intraday_start' in timing
    assert 'history_start' in timing
    assert 'ticks_start' in timing
    
    first_end = min(timing['intraday_end'], timing['history_end'], timing['ticks_end'])
    assert timing['intraday_start'] < first_end
    assert timing['history_start'] < first_end
    assert timing['ticks_start'] < first_end

def test_sync_all_handles_partial_failure(monkeypatch):
    def mocked_fail(*args, **kwargs):
        raise RuntimeError("Stage failed")

    success_mock = MagicMock()
    
    monkeypatch.setattr("data_engine.sync._sync_intraday", mocked_fail)
    monkeypatch.setattr("data_engine.sync._sync_history", success_mock)
    monkeypatch.setattr("data_engine.sync._sync_ticks", success_mock)
    
    # Mock GlobalSettings and other parts needed
    monkeypatch.setattr(settings, "is_market_open", lambda: True)
    monkeypatch.setattr("data_engine.sync.resolve_timeframe_provider", MagicMock(return_value=("TEST_PROVIDER", None)))
    monkeypatch.setattr("data_engine.sync.compact_folder", MagicMock(return_value={"compacted": 0}))
    monkeypatch.setattr("data_engine.sync.emit_event", MagicMock())
    monkeypatch.setattr("data_engine.sync.set_gauge", MagicMock())
    monkeypatch.setattr("data_engine.sync.maybe_emit_freshness_alerts", MagicMock(return_value=[]))

    # Should not raise exception
    sync_all()
    
    # Verify history and ticks still ran
    assert success_mock.call_count == 2


def test_sync_ticks_skips_when_market_is_closed(monkeypatch):
    ingest_ticks_mock = MagicMock()
    monkeypatch.setattr("data_engine.sync.ingest_ticks", ingest_ticks_mock)
    monkeypatch.setattr("data_engine.sync.settings.is_market_open", lambda: False)
    monkeypatch.setattr("data_engine.sync.start_run", MagicMock())
    monkeypatch.setattr("data_engine.sync.finish_run", MagicMock())

    _sync_ticks("EGX", "TEST_PROVIDER", {})

    ingest_ticks_mock.assert_not_called()
