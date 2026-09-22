from __future__ import annotations

import sys
import time
import pandas as pd

from .pivots import (
    MANIP_ABSORB_PRICE_MAX,
    MANIP_ABSORB_VOL_THRESHOLD,
    MANIP_LOW_VOL_PRICE_MIN,
    MANIP_LOW_VOL_THRESHOLD,
    MIN_TURNOVER_EGP,
)

_RECENT_BREAKOUT_TIMESTAMPS: list[float] = []


def _get_active_timestamps() -> list[float]:
    mod = sys.modules.get("core.analyzers.MomentumBreakoutScanner")
    if mod is not None and hasattr(mod, "_RECENT_BREAKOUT_TIMESTAMPS"):
        return getattr(mod, "_RECENT_BREAKOUT_TIMESTAMPS")
    return _RECENT_BREAKOUT_TIMESTAMPS


def estimate_bid_ask_spread(df: pd.DataFrame, avg_turnover: float) -> float:
    """
    Estimates or extracts the bid-ask spread percentage.
    If 'Bid' and 'Ask' columns are in the dataframe, it uses them.
    Otherwise, it estimates based on average turnover and high-low volatility.
    """
    if 'Bid' in df.columns and 'Ask' in df.columns:
        last_bid = df['Bid'].iloc[-1]
        last_ask = df['Ask'].iloc[-1]
        if last_bid > 0 and last_ask > 0:
            return (last_ask - last_bid) / ((last_ask + last_bid) / 2)

    price = df['Close'].iloc[-1]
    atr = df['ATR'].iloc[-1] if 'ATR' in df.columns else (df['High'] - df['Low']).rolling(14).mean().iloc[-1]
    atr_pct = (atr / price) if price > 0 else 0.02

    if avg_turnover > 10000000:
        base_spread = 0.001  # 0.1%
    elif avg_turnover > 2000000:
        base_spread = 0.003  # 0.3%
    elif avg_turnover > 500000:
        base_spread = 0.008  # 0.8%
    else:
        base_spread = 0.02   # 2.0%

    estimated_spread = base_spread * (1 + atr_pct * 5)
    return min(estimated_spread, 0.10)  # cap at 10%


def detect_manipulation(
    rel_volume: float,
    price_move_pct: float,
    breakout: bool,
    avg_turnover: float,
    ticker: str | None = None,
    bid_depth_shares: int = 0,
    tick_volume: int = 0,
    sector_trend_pct: float = 0.0,
) -> tuple[bool, str, str]:
    """
    ManipulationSentry — detects fake-out breakouts on the EGX.

    Returns (is_manipulation: bool, tag: str, reason: str).
    """
    low_vol_threshold = MANIP_LOW_VOL_THRESHOLD
    if ticker:
        try:
            from database import LegacySignalOutcome
            total_history = LegacySignalOutcome.select().where(LegacySignalOutcome.ticker == ticker).count()
            loss_history = LegacySignalOutcome.select().where(
                (LegacySignalOutcome.ticker == ticker) &
                ((LegacySignalOutcome.stop_loss_hit == True) | (LegacySignalOutcome.outcome_status == "LOSS_SL"))
            ).count()
            if total_history >= 2 and (loss_history / total_history) >= 0.5:
                low_vol_threshold = 1.2
        except Exception:
            pass

    # Mode 1: Tape Painting / Dynamic Telemetry Trap — breakout on below-average volume
    if (breakout
            and rel_volume < low_vol_threshold
            and abs(price_move_pct) > MANIP_LOW_VOL_PRICE_MIN):
        tag = "⚠️ DYNAMIC_TELEMETRY_TRAP" if low_vol_threshold > MANIP_LOW_VOL_THRESHOLD else "⚠️ LOW_VOL_BREAKOUT"
        reason = (f"Breakout on Rel_Vol={rel_volume:.2f} "
                  f"(< {low_vol_threshold:.2f} dynamic threshold), "
                  f"Price_Move={price_move_pct:.2f}%")
        return True, tag, reason

    # Mode 2: Absorption Wall — massive volume, no price movement
    if (rel_volume > MANIP_ABSORB_VOL_THRESHOLD
            and abs(price_move_pct) < MANIP_ABSORB_PRICE_MAX):
        reason = (f"Rel_Vol={rel_volume:.2f} "
                  f"(> {MANIP_ABSORB_VOL_THRESHOLD}) but "
                  f"|Price_Move|={abs(price_move_pct):.2f}% "
                  f"(< {MANIP_ABSORB_PRICE_MAX}%)")
        return True, "⚠️ ABSORPTION_DETECTED", reason

    # Mode 3: Low-liquidity pump
    if rel_volume > 5.0 and avg_turnover < (MIN_TURNOVER_EGP * 2):
        reason = (f"Rel_Vol={rel_volume:.2f} (> 5.0) "
                  f"in thin stock (turnover={avg_turnover/1e6:.2f}M)")
        return True, "⚠️ POTENTIAL MANIPULATION", reason

    # Mode 4: Hard Turnover Floor — suppress breakouts on illiquid micro-caps (< 1.5M EGP turnover)
    MANIP_HARD_TURNOVER_FLOOR_EGP = 1500000.0
    if breakout and avg_turnover < MANIP_HARD_TURNOVER_FLOOR_EGP:
        reason = (f"Turnover {avg_turnover/1e6:.2f}M EGP below hard liquidity floor "
                  f"({MANIP_HARD_TURNOVER_FLOOR_EGP/1e6:.2f}M EGP)")
        return True, "⚠️ ILLIQUID_TURNOVER_TRAP", reason

    # Mode 6: Level 2 Bid Depth Gate — suppress breakouts where bid depth cannot absorb volume
    if breakout and tick_volume > 0 and bid_depth_shares > 0:
        if bid_depth_shares < (3 * tick_volume):
            reason = (f"L2 Bid Depth ({bid_depth_shares} shares) < 3x tick volume ({tick_volume} shares)")
            return True, "⚠️ L2_BID_DEPTH_TRAP", reason

    # Mode 8: Sector Contagion Gate — suppress single-stock breakout if sector trend is dropping < -1.5%
    if breakout and sector_trend_pct and sector_trend_pct < -1.5:
        reason = f"Single-stock breakout diverges from negative sector trend ({sector_trend_pct:.2f}%)"
        return True, "⚠️ SECTOR_DIVERGENCE_TRAP", reason

    # Mode 7: Cross-Ticker Systemic Currency Rally Gate — suppress simultaneous macro breakouts
    if breakout:
        now_ts = time.time()
        active_list = _get_active_timestamps()
        # Clean older timestamps in-place (> 60s)
        active_list[:] = [t for t in active_list if (now_ts - t) < 60.0]

        if len(active_list) >= 4:
            reason = f"Macro currency devaluation burst: {len(active_list)} simultaneous breakouts in 60s"
            return True, "⚠️ SYSTEMIC_CURRENCY_RALLY", reason

        active_list.append(now_ts)

    return False, "", ""
