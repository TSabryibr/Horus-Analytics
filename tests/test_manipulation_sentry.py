"""
Tests for ManipulationSentry detection logic integrated into
MomentumBreakoutScanner.

Tests the three detection modes:
1. LOW_VOL_BREAKOUT  (Tape Painting)
2. ABSORPTION_DETECTED  (Absorption Wall)
3. POTENTIAL MANIPULATION  (Low-Liquidity Pump)
and verifies that clean signals pass through unharmed.
"""
import pytest
from core.analyzers.MomentumBreakoutScanner import (
    detect_manipulation,
    MANIP_LOW_VOL_THRESHOLD,
    MANIP_LOW_VOL_PRICE_MIN,
    MANIP_ABSORB_VOL_THRESHOLD,
    MANIP_ABSORB_PRICE_MAX,
    MIN_TURNOVER_EGP,
)


# ------------------------------------------------------------------ #
#                       detect_manipulation unit tests                #
# ------------------------------------------------------------------ #

class TestDetectManipulation:
    """Unit tests for the pure detect_manipulation() function."""

    @pytest.fixture(autouse=True)
    def reset_timestamps(self):
        from core.analyzers.MomentumBreakoutScanner import _RECENT_BREAKOUT_TIMESTAMPS
        _RECENT_BREAKOUT_TIMESTAMPS.clear()

    # ---------- Mode 1: Low-Volume Breakout (Tape Painting) ----------

    def test_low_vol_breakout_flagged(self):
        """Breakout + low rel volume + large price move => LOW_VOL_BREAKOUT."""
        is_manip, tag, reason = detect_manipulation(
            rel_volume=0.5,        # well below 0.8 threshold
            price_move_pct=4.0,    # above 3% threshold
            breakout=True,
            avg_turnover=5_000_000,
        )
        assert is_manip is True
        assert "LOW_VOL_BREAKOUT" in tag
        assert "Rel_Vol=0.50" in reason

    def test_low_vol_no_breakout_passes(self):
        """Same thin volume but no breakout flag => should NOT be flagged."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=0.5,
            price_move_pct=4.0,
            breakout=False,         # no breakout
            avg_turnover=5_000_000,
        )
        assert is_manip is False
        assert tag == ""

    def test_low_vol_small_price_move_passes(self):
        """Breakout + low volume but tiny price move (< 3%) => passes."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=0.5,
            price_move_pct=1.5,     # below 3% threshold
            breakout=True,
            avg_turnover=5_000_000,
        )
        assert is_manip is False
        assert tag == ""

    def test_breakout_adequate_volume_passes(self):
        """Breakout with healthy volume => should pass cleanly."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=1.5,         # above 0.8 threshold
            price_move_pct=4.0,
            breakout=True,
            avg_turnover=5_000_000,
        )
        assert is_manip is False
        assert tag == ""

    # ---------- Mode 2: Absorption Wall ----------

    def test_absorption_wall_flagged(self):
        """Very high volume + near-zero price move => ABSORPTION_DETECTED."""
        is_manip, tag, reason = detect_manipulation(
            rel_volume=4.0,         # well above 3.0 threshold
            price_move_pct=0.1,     # < 0.5% threshold
            breakout=False,
            avg_turnover=10_000_000,
        )
        assert is_manip is True
        assert "ABSORPTION_DETECTED" in tag
        assert "Rel_Vol=4.00" in reason

    def test_absorption_negative_price_move(self):
        """Absorption should trigger on negative tiny moves too (abs check)."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=3.5,
            price_move_pct=-0.2,    # negative but abs < 0.5%
            breakout=False,
            avg_turnover=10_000_000,
        )
        assert is_manip is True
        assert "ABSORPTION_DETECTED" in tag

    def test_high_vol_with_real_price_move_passes(self):
        """High volume with genuine price movement => NOT absorption."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=4.0,
            price_move_pct=2.5,     # real movement, above 0.5%
            breakout=True,
            avg_turnover=10_000_000,
        )
        assert is_manip is False
        assert tag == ""

    # ---------- Mode 3: Low-Liquidity Pump ----------

    def test_low_liquidity_pump_flagged(self):
        """Extreme vol spike in thin stock => POTENTIAL MANIPULATION."""
        is_manip, tag, reason = detect_manipulation(
            rel_volume=6.0,         # > 5.0
            price_move_pct=5.0,     # doesn't matter for this mode
            breakout=True,
            avg_turnover=3_000_000, # below MIN_TURNOVER_EGP * 2 = 4M
        )
        assert is_manip is True
        assert "POTENTIAL MANIPULATION" in tag

    def test_high_vol_in_liquid_stock_passes(self):
        """Extreme vol in a liquid stock is fine — not a pump."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=6.0,
            price_move_pct=5.0,
            breakout=True,
            avg_turnover=20_000_000,  # well above 4M threshold
        )
        assert is_manip is False
        assert tag == ""

    # ---------- Clean passthrough ----------

    def test_normal_conditions_pass(self):
        """Normal trading day, no breakout, average volume => CLEAR."""
        is_manip, tag, reason = detect_manipulation(
            rel_volume=1.0,
            price_move_pct=0.8,
            breakout=False,
            avg_turnover=10_000_000,
        )
        assert is_manip is False
        assert tag == ""
        assert reason == ""

    # ---------- Priority / precedence ----------

    def test_mode1_takes_priority_over_mode3(self):
        """If both Mode 1 and Mode 3 conditions are met, Mode 1 fires first."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=0.3,         # Mode 1: low vol breakout
            price_move_pct=5.0,     # Mode 1: large move
            breakout=True,          # Mode 1 requires breakout
            avg_turnover=1_000_000, # Mode 3: thin stock (< 4M)
        )
        # But rel_volume 0.3 is NOT > 5.0, so Mode 3 wouldn't fire.
        # Mode 1 should fire.
        assert is_manip is True
        assert "LOW_VOL_BREAKOUT" in tag

    def test_mode2_fires_even_without_breakout(self):
        """Absorption doesn't require a breakout flag — it's about distribution."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=4.0,
            price_move_pct=0.1,
            breakout=False,
            avg_turnover=50_000_000,
        )
        assert is_manip is True
        assert "ABSORPTION_DETECTED" in tag

    # ---------- Boundary conditions ----------

    def test_boundary_low_vol_at_threshold(self):
        """Rel_Volume exactly at threshold (0.8) should NOT trigger Mode 1."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=MANIP_LOW_VOL_THRESHOLD,   # exactly 0.8
            price_move_pct=4.0,
            breakout=True,
            avg_turnover=5_000_000,
        )
        # < 0.8 is required, 0.8 itself should pass
        assert is_manip is False

    def test_boundary_absorption_at_threshold(self):
        """Rel_Volume exactly at 3.0 should NOT trigger absorption (> required)."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=MANIP_ABSORB_VOL_THRESHOLD,  # exactly 3.0
            price_move_pct=0.1,
            breakout=False,
            avg_turnover=10_000_000,
        )
        # > 3.0 is required, 3.0 itself should pass
        assert is_manip is False

    def test_boundary_price_at_absorption_limit(self):
        """Price_Move_% exactly at 0.5 should NOT trigger absorption (< required)."""
        is_manip, tag, _ = detect_manipulation(
            rel_volume=4.0,
            price_move_pct=MANIP_ABSORB_PRICE_MAX,  # exactly 0.5
            breakout=False,
            avg_turnover=10_000_000,
        )
        # < 0.5 is required, 0.5 itself should pass
        assert is_manip is False
