import pytest
import pandas as pd
from core.data.DataFeedCrossCheck import data_feed_cross_check
from core.signals.HumanSlippageModel import human_slippage_model
from core.analyzers.MomentumBreakoutScanner import detect_manipulation

def test_data_feed_cross_check():
    # 20-day mean of 10.0 EGP
    df = pd.DataFrame({"Close": [10.0] * 20})

    # Normal tick (11.0 EGP) -> Valid
    is_valid, msg = data_feed_cross_check.verify_tick("SWDY", 11.0, df)
    assert is_valid is True
    assert msg == "VERIFIED"

    # Dirty tick (15.0 EGP, 50% deviation) -> Intercepted
    is_valid_dirty, msg_dirty = data_feed_cross_check.verify_tick("SWDY", 15.0, df)
    assert is_valid_dirty is False
    assert "UNVERIFIED_DATA_FEED" in msg_dirty

def test_human_slippage_model():
    res = human_slippage_model.calculate_adjusted_targets(
        entry_price=100.0,
        target_1=110.0,
        target_2=120.0,
        stop_loss=95.0,
        slippage_bps=25
    )
    assert res["raw_entry"] == 100.0
    assert res["adjusted_entry"] == 100.25
    assert res["adjusted_target_1"] == 110.0

def test_sector_contagion_gate():
    # Breakout on stock where sector is dropping -2.0% (< -1.5%)
    is_manip, tag, reason = detect_manipulation(
        rel_volume=2.0,
        price_move_pct=4.0,
        breakout=True,
        avg_turnover=5000000.0,
        sector_trend_pct=-2.0
    )
    assert is_manip is True
    assert tag == "⚠️ SECTOR_DIVERGENCE_TRAP"
    assert "negative sector trend" in reason
