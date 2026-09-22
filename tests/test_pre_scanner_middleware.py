import pytest
import pandas as pd
import numpy as np
import datetime
from core.pre_scanner_middleware import PreScannerMiddleware, DataValidationError
from core.analyzers import MomentumBreakoutScanner
from database import SignalStateArchive, db
from core import TimeUtils

@pytest.fixture(autouse=True)
def transaction():
    with db.transaction() as txn:
        yield
        txn.rollback()

def test_pre_scanner_validation_catches_empty_df():
    with pytest.raises(DataValidationError, match="empty or None"):
        PreScannerMiddleware.process("EGX_STOCK", None)
        
    with pytest.raises(DataValidationError, match="empty or None"):
        PreScannerMiddleware.process("EGX_STOCK", pd.DataFrame())

def test_pre_scanner_validation_catches_missing_columns():
    dates = pd.date_range(start="2026-07-01", periods=105)
    df = pd.DataFrame({
        "Open": [10.0] * 105,
        "High": [11.0] * 105,
        "Low": [9.0] * 105,
        # Missing Close
        "Volume": [1000] * 105
    }, index=dates)
    
    with pytest.raises(DataValidationError, match="Missing required columns"):
        PreScannerMiddleware.process("EGX_STOCK", df)

def test_pre_scanner_validation_catches_stale_data(monkeypatch):
    dates = pd.date_range(start="2026-07-01", periods=105)
    df = pd.DataFrame({
        "Open": [10.0] * 105,
        "High": [11.0] * 105,
        "Low": [9.0] * 105,
        "Close": [10.0] * 105,
        "Volume": [1000] * 105
    }, index=dates)
    
    # Force system time to be 10 days ahead of the latest data index
    latest_dt = df.index[-1].to_pydatetime()
    mock_now = latest_dt + datetime.timedelta(days=10)
    monkeypatch.setattr(TimeUtils, "now", lambda: mock_now)
    
    with pytest.raises(DataValidationError, match="stale"):
        PreScannerMiddleware.process("EGX_STOCK", df)

def test_pre_scanner_conversion_egp_to_usd(monkeypatch):
    # Set up some dates
    dates = pd.date_range(start="2026-07-10", periods=105)
    df = pd.DataFrame({
        "Open": [50.0] * 105,
        "High": [55.0] * 105,
        "Low": [45.0] * 105,
        "Close": [50.0] * 105,
        "Volume": [1000] * 105
    }, index=dates)
    
    # Mock parallel USD-EGP rate to return 50.0
    monkeypatch.setattr("core.pre_scanner_middleware.get_parallel_usd_egp_rate", lambda: 50.0)
    monkeypatch.setattr("core.pre_scanner_middleware.get_historical_usd_egp_rate", lambda dt: 50.0)
    # Ensure current time is fresh
    monkeypatch.setattr(TimeUtils, "now", lambda: datetime.datetime(2026, 7, 10))
    
    # EGP Stock
    df_processed, signal_id, snapshot = PreScannerMiddleware.process("COMI", df)
    
    # Prices divided by 50.0 should be 1.0
    assert float(df_processed["Close"].iloc[-1]) == 1.0
    assert float(df_processed["Open"].iloc[-1]) == 1.0
    assert snapshot["currency"] == "EGP"
    assert snapshot["raw_close_egp"] == 50.0
    assert snapshot["raw_close_usd"] == 1.0
    
    # USD Stock (should not be modified)
    df_processed_usd, _, snapshot_usd = PreScannerMiddleware.process("EGBE", df)
    assert float(df_processed_usd["Close"].iloc[-1]) == 50.0
    assert snapshot_usd["currency"] == "USD"
    assert snapshot_usd["raw_close_usd"] == 50.0

def test_provenance_log_created_on_scan(monkeypatch):
    dates = pd.date_range(start="2026-07-10", periods=105)
    # Generate mock liquid breakout data
    prices = [10.0] * 100 + [12.0, 12.5, 13.0, 13.5, 14.0]
    df = pd.DataFrame({
        "Open": prices,
        "High": [p + 0.1 for p in prices],
        "Low": [p - 0.1 for p in prices],
        "Close": prices,
        "Volume": [50000] * 105
    }, index=dates)
    
    # Mock current parallel FX rate to 50.0
    monkeypatch.setattr("core.pre_scanner_middleware.get_parallel_usd_egp_rate", lambda: 50.0)
    monkeypatch.setattr("core.pre_scanner_middleware.get_historical_usd_egp_rate", lambda dt: 50.0)
    monkeypatch.setattr("core.analyzers.MomentumBreakoutScanner.get_parallel_usd_egp_rate", lambda: 50.0)
    monkeypatch.setattr(TimeUtils, "now", lambda: datetime.datetime(2026, 7, 10))
    
    # Count archives before
    initial_count = SignalStateArchive.select().count()
    
    res = MomentumBreakoutScanner.analyze_stock_frame("COMI", df)
    
    assert res is not None
    assert "Signal_Id" in res
    assert "Price_USD" in res
    # EGP price remains 14.0
    assert res["Price"] == 14.0
    # Price in USD should be 14.0 / 50.0 = 0.28
    assert res["Price_USD"] == 0.28
    
    # Check that a SignalStateArchive record was created
    new_count = SignalStateArchive.select().count()
    assert new_count == initial_count + 1
    
    archive = SignalStateArchive.select().order_by(SignalStateArchive.id.desc()).first()
    assert archive.ticker == "COMI"
    assert archive.signal_id == res["Signal_Id"]
    assert archive.final_status == res["Status"]
    assert archive.signal_score == res["Signal_Score"]
    assert archive.kill_reason is None or len(archive.kill_reason) > 0

def test_provenance_log_corrupted_data(monkeypatch):
    # Pass empty df to trigger DataValidationError
    initial_count = SignalStateArchive.select().count()
    
    res = MomentumBreakoutScanner.analyze_stock_frame("COMI", None)
    assert res is None
    
    # Check that a SignalStateArchive record with CORRUPTED was created
    new_count = SignalStateArchive.select().count()
    assert new_count == initial_count + 1
    
    archive = SignalStateArchive.select().order_by(SignalStateArchive.id.desc()).first()
    assert archive.ticker == "COMI"
    assert "DATA_CORRUPTED" in archive.final_status
    assert "empty or None" in archive.kill_reason
