"""
HORUS CONFLUENCE ENGINE
=======================
Multi-Dimensional Signal Synthesizer & Composite Conviction Scoring.

Combines signals across the 5 Institutional Dimensions:
1. Macro Trend & Volatility (Oracle / Squeeze)
2. Sector Rotation & Relative Strength (RRG)
3. Seasonal Probabilities (Cyclicality)
4. Smart Money Flow (Whale Accumulation / Distribution)
5. Technical Structure & False Breakout Traps (Scanner / Traps)
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from core import TimeUtils
from core.market import MarketLists

logger = logging.getLogger(__name__)

class ConfluenceEngine:
    @staticmethod
    def evaluate_ticker(
        ticker: str,
        sector_data: Optional[Dict[str, Any]] = None,
        whale_data: Optional[Dict[str, Any]] = None,
        trap_data: Optional[Dict[str, Any]] = None,
        oracle_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates a 1-to-5 star conviction score and generates confluence tags.
        """
        score = 0.0
        tags: List[str] = []
        warnings: List[str] = []
        sector = MarketLists.get_sector(ticker)
        
        # 1. Macro Regime Check (Oracle)
        macro_bullish = False
        if oracle_data:
            status = str(oracle_data.get("status", "")).upper()
            forecast = str(oracle_data.get("forecast", "")).upper()
            if "BULL" in status or "BULL" in forecast or "UP" in forecast or "ACCUMULATION" in status:
                score += 1.0
                macro_bullish = True
                tags.append("MACRO_TAILWIND")
            else:
                score += 0.5
        else:
            score += 0.5

        # 2. Sector Rotation Check (RRG)
        sector_leading = False
        if sector_data:
            sectors_list = sector_data.get("sectors", []) if isinstance(sector_data, dict) else []
            for sec in sectors_list:
                if sec.get("Sector") == sector:
                    trend = str(sec.get("Trend", "")).upper()
                    rot_score = float(sec.get("Rotation_Score", 0))
                    if "LEADING" in trend or "IMPROVING" in trend or rot_score > 100:
                        score += 1.0
                        sector_leading = True
                        tags.append(f"SECTOR_{trend}")
                    elif "LAGGING" in trend or "WEAKENING" in trend:
                        warnings.append(f"Sector {sector} is {trend}")
                    break
        else:
            score += 0.5

        # 3. Seasonality Check (Current Month Historical Edge)
        current_month = TimeUtils.now().month
        if current_month in [1, 2, 4, 8, 9, 10, 11]:
            score += 1.0
            tags.append("SEASONAL_EDGE")
        else:
            score += 0.5

        # 4. Whale Flow Check (Smart Money Accumulation)
        whale_signal = None
        if whale_data:
            candidates = whale_data.get("candidates", []) if isinstance(whale_data, dict) else []
            for w in candidates:
                if w.get("Ticker") == ticker:
                    whale_signal = w.get("Signal")
                    if whale_signal == "ACCUMULATION":
                        score += 1.0
                        tags.append("WHALE_ACCUMULATION")
                    elif whale_signal == "DISTRIBUTION":
                        score -= 1.0
                        warnings.append("🚨 Heavy Whale Distribution Detected")
                    break

        # 5. Trap Reversals & Technical Structure Check
        if trap_data:
            bull_traps = trap_data.get("bull_traps", []) if isinstance(trap_data, dict) else []
            bear_traps = trap_data.get("bear_traps", []) if isinstance(trap_data, dict) else []
            
            # Check Bear Trap (Springboard Reversal = Highly Bullish Long Alpha)
            for bt in bear_traps:
                if bt.get("Ticker") == ticker:
                    score += 1.0
                    tags.append("SPRING_REVERSAL")
                    break
            
            # Check Bull Trap (Upthrust = Dangerous Exhaustion)
            for ut in bull_traps:
                if ut.get("Ticker") == ticker:
                    score -= 1.5
                    warnings.append("⚠️ Active Bull Trap / Upthrust (Resistance Failure)")
                    break

        # Bound Stars (1 to 5)
        raw_stars = max(1.0, min(5.0, round(score, 1)))
        stars_int = int(round(raw_stars))

        # Rating label
        if raw_stars >= 4.0:
            rating = "HIGH_CONVICTION_BUY"
        elif raw_stars >= 3.0:
            rating = "ACCUMULATE"
        elif raw_stars >= 2.0:
            rating = "NEUTRAL_HOLD"
        else:
            rating = "DEFENSIVE_FADE"

        return {
            "ticker": ticker,
            "sector": sector,
            "stars": stars_int,
            "raw_score": round(score, 2),
            "rating": rating,
            "tags": tags,
            "warnings": warnings,
            "macro_bullish": macro_bullish,
            "sector_leading": sector_leading,
            "whale_signal": whale_signal
        }
