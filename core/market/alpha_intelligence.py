"""
ALPHA INTELLIGENCE ENGINE
=========================
Unifies disparate signals into a single Composite Confidence Score.
Integrates:
1. Technical Score (DailyScanner)
2. Whale Activity (Heimdall)
3. Volatility Regime (Heimdall)
4. Historical Win-Rate (TickerStrategyMetrics)

Author: Horus Analytics
"""

import logging
from database import TickerStrategyMetrics
from core import Heimdall
from core.analyzers import SentimentCrawler

# Simple cache for gossip per session/loop
_gossip_cache = None
_gossip_lookup = None # Optimized lookup map { ticker: [gossip_items] }

logger = logging.getLogger('AlphaIntelligence')

def get_composite_score(ticker, base_score, window_days=5):
    """
    Calculates a 0-100 intelligence-weighted confidence score.
    Returns:
        dict: {
            "score": float,
            "rationale": list[str],
            "ticker": str
        }
    """
    # Normalize base score (assuming max base score is around 10-20)
    # We want base technical components to represent ~50% of weight
    composite = float(base_score) * 4.0 
    rationale = [f"Base Technical Score: {base_score}"]
    
    # 1. Integrate Heimdall Diagnostics (Guardians of Alpha)
    try:
        diag = Heimdall.diagnose_stock(ticker)
        if diag.get("status") != "error":
            # Whale Activity (Smart Money Divergence)
            whale = diag.get("whale_activity", "NEUTRAL")
            if whale == "ACCUMULATION":
                composite += 15
                rationale.append("Whale Accumulation (OBV Divergence) (+15)")
            elif whale == "DISTRIBUTION":
                composite -= 20
                rationale.append("Whale Distribution (OBV Divergence) (-20)")
                
            # Squeeze status (Volatility Coil)
            if diag.get("volatility_status") == "SQUEEZE":
                composite += 10
                rationale.append("Volatility Squeeze (BB Coil) (+10)")
                
            # Trap status (The Deadbolt)
            trap = diag.get("trap_status", "NONE")
            if trap == "BULL_TRAP":
                composite -= 50
                rationale.append("CRITICAL: Bull Trap Detected (-50)")
            elif trap == "BEAR_TRAP":
                composite += 25
                rationale.append("Bear Trap Reversal (+25)")
    except Exception as e:
        logger.error(f"Heimdall integration error for {ticker}: {e}")

    # 2. Integrate Historical performance (WFA Logic)
    try:
        metrics = TickerStrategyMetrics.get_or_none(
            TickerStrategyMetrics.ticker == ticker,
            TickerStrategyMetrics.window_days == window_days
        )
        if metrics:
            wr = metrics.win_rate_pct
            if wr >= 70:
                composite += 12
                rationale.append(f"Historical Success Rate {wr}% (+12)")
            elif wr <= 35:
                composite -= 15
                rationale.append(f"Low Historical Accuracy {wr}% (-15)")
            
            # Sharpe Ratio Integration
            sharpe = getattr(metrics, 'sharpe_ratio', 0.0)
            if sharpe >= 1.5:
                composite += 10
                rationale.append(f"Institutional Grade Sharpe ({sharpe}) (+10)")
            elif sharpe >= 0.8:
                composite += 5
                rationale.append(f"Solid Risk-Adjusted Return (Sharpe {sharpe}) (+5)")
    except Exception as e:
        logger.error(f"Strategy Metrics integration error for {ticker}: {e}")

    # 3. Integrate Sentiment (SentimentCrawler)
    global _gossip_cache, _gossip_lookup
    try:
        if _gossip_cache is None:
            _gossip_cache = SentimentCrawler.gather_gossip()
            # Build an optimized lookup map once per session/loop
            _gossip_lookup = {}
            for item in _gossip_cache:
                for t in item.get('tickers', []):
                    _gossip_lookup.setdefault(t, []).append(item)
            
        ticker_gossip = _gossip_lookup.get(ticker, [])
        if ticker_gossip:
            avg_gossip = sum(item.get('gossip_score', 0) for item in ticker_gossip) / len(ticker_gossip)
            
            # Impact: Map -10 to +10 into roughly -15 to +15 composite weight
            sentiment_impact = avg_gossip * 1.5
            composite += sentiment_impact
            
            direction = "Positive" if avg_gossip > 0 else "Negative"
            rationale.append(f"Gossip Sentiment: {direction} ({avg_gossip:+.1f}) impact({sentiment_impact:+.1f})")
    except Exception as e:
        logger.error(f"Sentiment integration error for {ticker}: {e}")

    # Clamp 0-100
    final_score = max(0.0, min(100.0, composite))
    
    return {
        "score": float(round(final_score, 1)),
        "rationale": list(rationale),
        "ticker": ticker
    }

if __name__ == "__main__":
    # Quick Test
    test_res = get_composite_score("COMI", base_score=10)
    print(f"\n--- Alpha Intel: {test_res['ticker']} ---")
    print(f"Final Score: {test_res['score']}")
    print("Rationale:")
    for r in test_res['rationale']:
        print(f"  - {r}")
