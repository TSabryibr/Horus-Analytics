"""
WFA VALIDATION SERVICE
======================
Automated background worker that runs SignalAccuracyChecker across the entire universe.
Updates TickerStrategyMetrics table to inform Alpha Intelligence.
"""

import logging
import datetime
from core import SignalAccuracyChecker
from core.simulation import PerformanceMetrics
from database import TickerStrategyMetrics, db

logger = logging.getLogger('WFAService')

def run_weekly_validation(window_days=5, lookback_days=90):
    """
    Runs accuracy check for all tickers over the last N days.
    """
    logger.info(f"Starting WFA Validation (window={window_days}d, lookback={lookback_days}d)")
    
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=lookback_days)
    
    try:
        results = SignalAccuracyChecker.run_accuracy_check(
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            window_days=window_days,
            index_choice="ALL"
        )
        
        if not results or not results.get('signals'):
            logger.warning("No signals found in validation period.")
            return
            
        # Group signals by ticker to calculate per-ticker stats
        ticker_groups = {}
        for sig in results['signals']:
            t = sig['ticker']
            if t not in ticker_groups:
                ticker_groups[t] = []
            ticker_groups[t].append(sig)
            
        logger.info(f"Grouping results for {len(ticker_groups)} tickers...")
        
        with db.atomic():
            for ticker, sigs in ticker_groups.items():
                total = len(sigs)
                tp_hits = sum(1 for s in sigs if s['outcome'] == 'TP_HIT')
                win_rate = (tp_hits / total * 100) if total > 0 else 0
                avg_gain = sum(s['pnl_pct'] for s in sigs) / total if total > 0 else 0
                
                # Advanced Metrics
                metrics_adv = PerformanceMetrics.get_advanced_metrics(sigs)
                
                # Update or Create
                TickerStrategyMetrics.insert(
                    ticker=ticker,
                    window_days=window_days,
                    total_signals=total,
                    win_rate_pct=round(win_rate, 1),
                    avg_gain_pct=round(avg_gain, 2),
                    sharpe_ratio=metrics_adv['sharpe'],
                    max_drawdown=metrics_adv['max_dd'],
                    expectancy=metrics_adv['expectancy'],
                    updated_at=datetime.datetime.now()
                ).on_conflict(
                    conflict_target=[TickerStrategyMetrics.ticker, TickerStrategyMetrics.window_days],
                    preserve=[
                        TickerStrategyMetrics.total_signals, 
                        TickerStrategyMetrics.win_rate_pct, 
                        TickerStrategyMetrics.avg_gain_pct,
                        TickerStrategyMetrics.sharpe_ratio,
                        TickerStrategyMetrics.max_drawdown,
                        TickerStrategyMetrics.expectancy,
                        TickerStrategyMetrics.updated_at
                    ]
                ).execute()
                
        logger.info("WFA Validation Complete. Metrics updated.")
        
    except Exception as e:
        logger.error(f"WFA Service Error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Test Run
    logging.basicConfig(level=logging.INFO)
    run_weekly_validation(window_days=5, lookback_days=30)
