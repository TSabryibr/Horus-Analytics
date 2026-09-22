import pytest
import pandas as pd
import numpy as np
import datetime
import json
from database import Trade, SignalStateArchive, db
from core.analyzers.SlippageReconciler import SlippageReconciler
from core.analyzers import MomentumBreakoutScanner
from core import TimeUtils

@pytest.fixture(autouse=True)
def transaction():
    with db.transaction() as txn:
        yield
        txn.rollback()

def test_slippage_and_decay_calculation():
    # Setup theoretical signal state snapshot
    signal_id = "SIG-TEST-SLIPPAGE-123"
    snapshot = {
        "raw_close_egp": 10.0,
        "raw_close_usd": 0.20,
        "currency": "EGP"
    }
    
    SignalStateArchive.create(
        ticker="COMI",
        timestamp=TimeUtils.now(),
        final_status="🐋 HIGH CONVICTION BUY",
        signal_score=8,
        filter_snapshot_json=json.dumps(snapshot),
        kill_reason=None,
        signal_id=signal_id
    )
    
    # Create corresponding Trade record
    Trade.create(
        portfolio=1,
        ticker="COMI",
        shares=1000,
        entry_price=10.5,  # Actual entry is 10.5, theoretical was 10.0 -> +5% slippage
        exit_price=9.5,    # Actual exit is 9.5, theoretical was 10.0 -> -5% decay
        entry_date=TimeUtils.now() - datetime.timedelta(days=2),
        exit_date=TimeUtils.now(),
        pnl=-1000.0,
        pnl_pct=-9.5,
        currency="EGP",
        entry_usd_rate=50.0,
        exit_usd_rate=50.0,
        reason="STOP_LOSS",
        signal_id=signal_id
    )
    
    # Run reconciler report
    report = SlippageReconciler.generate_reconciliation_report(limit=10)
    
    assert report["reconciled_trades_count"] == 1
    assert report["average_slippage_pct"] == 5.0
    
    trade_detail = report["trades"][0]
    assert trade_detail["ticker"] == "COMI"
    assert trade_detail["actual_entry"] == 10.5
    assert trade_detail["theoretical_entry"] == 10.0
    assert trade_detail["slippage_nominal"] == 0.5
    assert trade_detail["slippage_pct"] == 5.0
    assert trade_detail["actual_exit"] == 9.5
    assert trade_detail["decay_pct"] == -5.0

def test_dynamic_calibration_metrics():
    ticker = "COMI"
    
    # Scenario A: Fewer than 3 trades -> should return 0.0 (not enough metrics)
    metrics_few = SlippageReconciler.get_dynamic_calibration_metrics(ticker, lookback_days=10)
    assert metrics_few == 0.0
    
    # Scenario B: 3 trades with different slippages: 2%, 4%, 6% (average should be 4%)
    slippages = [2.0, 4.0, 6.0]
    for i, slippage_pct in enumerate(slippages):
        sig_id = f"SIG-TEST-CALIB-{i}"
        theoretical = 100.0
        actual = theoretical * (1.0 + (slippage_pct / 100.0))
        
        snapshot = {
            "raw_close_egp": theoretical,
            "currency": "EGP"
        }
        
        SignalStateArchive.create(
            ticker=ticker,
            timestamp=TimeUtils.now(),
            final_status="🐋 HIGH CONVICTION BUY",
            signal_score=8,
            filter_snapshot_json=json.dumps(snapshot),
            kill_reason=None,
            signal_id=sig_id
        )
        
        Trade.create(
            portfolio=1,
            ticker=ticker,
            shares=100,
            entry_price=actual,
            exit_price=theoretical,
            entry_date=TimeUtils.now() - datetime.timedelta(days=1),
            exit_date=TimeUtils.now(),
            pnl=0.0,
            pnl_pct=0.0,
            currency="EGP",
            entry_usd_rate=50.0,
            exit_usd_rate=50.0,
            reason="MANUAL",
            signal_id=sig_id
        )
        
    metrics_enough = SlippageReconciler.get_dynamic_calibration_metrics(ticker, lookback_days=10)
    assert metrics_enough == 4.0

def test_dynamic_liquidity_guard_tighter_spread(monkeypatch):
    # Mock dynamic slippage calculation to return 1.5%
    monkeypatch.setattr(SlippageReconciler, "get_dynamic_calibration_metrics", lambda ticker: 1.5)
    
    # Mock FX rates
    monkeypatch.setattr("core.pre_scanner_middleware.get_parallel_usd_egp_rate", lambda: 50.0)
    monkeypatch.setattr("core.pre_scanner_middleware.get_historical_usd_egp_rate", lambda dt: 50.0)
    monkeypatch.setattr("core.analyzers.MomentumBreakoutScanner.get_parallel_usd_egp_rate", lambda: 50.0)
    
    # Construct a dataframe with a 1.0% estimated bid-ask spread
    dates = pd.date_range(start="2026-07-01", periods=105)
    # Average turnover = 10M EGP (liquid enough, threshold is 2M EGP)
    # ATR is set to 2.0. With close=200.0, ATR/Close is 1.0%.
    # bid-ask spread estimate is 0.5 * (ATR / Close) = 0.5 * 1.0% = 0.5% (or close to 1.0%)
    # Let's mock estimate_bid_ask_spread to return 0.01 (1.0% spread)
    monkeypatch.setattr("core.analyzers.MomentumBreakoutScanner.estimate_bid_ask_spread", lambda df, avg_turnover: 0.01)
    
    prices = [200.0] * 104 + [210.0]
    df = pd.DataFrame({
        "Open": [200.0] * 104 + [200.0],
        "High": [200.1] * 104 + [211.0],
        "Low": [199.9] * 104 + [199.0],
        "Close": prices,
        "Volume": [50000] * 105
    }, index=dates)
    
    # Scenario: Spread is 1.0%.
    # Default MAX_SPREAD_PCT limit is 2.0% (0.02).
    # Since historical slippage is 1.5%, dynamic spread limit is max(0.5%, 2.0% - 1.5%) = 0.5% (0.005).
    # Since estimated spread 1.0% (0.01) > dynamic spread limit 0.5% (0.005), it should trigger a WIDE_SPREAD liquidity trap!
    
    res = MomentumBreakoutScanner.analyze_stock_frame("COMI", df)
    
    assert res is not None
    assert "LIQUIDITY TRAP" in res["Status"]
    assert "WIDE_SPREAD" in res["Status"]
    assert res["Signal_Score"] == 0
