"""
PERFORMANCE METRICS MODULE
==========================
Quantitative library for calculating institutional-grade trading metrics.
"""

import numpy as np
import logging

logger = logging.getLogger('PerformanceMetrics')

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """
    Calculates the Sharpe Ratio of a series of returns.
    returns: list or np.array of float (decimal, e.g., 0.05 for 5%)
    risk_free_rate: Annual risk-free rate (decimal)
    """
    if not returns or len(returns) < 2:
        return 0.0
    
    returns_array = np.array(returns)
    # Convert annual risk-free rate to per-trade (approximation)
    # Assuming ~250 trading days or trades
    rf_per_trade = risk_free_rate / 252 
    
    excess_returns = returns_array - rf_per_trade
    std_dev = np.std(returns_array)
    
    if std_dev == 0:
        return 0.0
        
    return float(np.mean(excess_returns) / std_dev * np.sqrt(252))

def calculate_max_drawdown(pnl_pcts):
    """
    Calculates the Maximum Drawdown from a list of P&L percentages.
    pnl_pcts: list of float (e.g., 2.5 for 2.5%)
    """
    if not pnl_pcts:
        return 0.0
    
    # Convert to multipliers (1 + 0.025)
    multipliers = [1 + (x/100.0) for x in pnl_pcts]
    
    # Generate Equity Curve
    equity_curve = np.cumprod(multipliers)
    
    # Calculate Max Drawdown
    peak = equity_curve[0]
    max_dd = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        dd = (peak - value) / peak
        if dd > max_dd:
            max_dd = dd
            
    return float(max_dd * 100.0)

def calculate_expectancy(win_rate_pct, avg_win_pct, avg_loss_pct):
    """
    Calculates the Expectancy of the strategy.
    Expectancy = (Win% * AvgWin) - (Loss% * AvgLoss)
    """
    wr = win_rate_pct / 100.0
    lr = 1.0 - wr
    
    # Ensure average win/loss are absolute
    aw = abs(avg_win_pct)
    al = abs(avg_loss_pct)
    
    expectancy = (wr * aw) - (lr * al)
    return float(expectancy)

def get_advanced_metrics(signals):
    """
    Aggregates all advanced metrics for a set of signals.
    signals: list of dict with 'pnl_pct'
    """
    if not signals:
        return {
            "sharpe": 0.0,
            "max_dd": 0.0,
            "expectancy": 0.0
        }
    
    pnls = [s.get('pnl_pct', 0.0) for s in signals]
    returns_decimal = [x/100.0 for x in pnls]
    
    wins = [x for x in pnls if x > 0]
    losses = [x for x in pnls if x <= 0]
    
    avg_win = np.mean(wins) if wins else 0.0
    avg_loss = np.mean(losses) if losses else 0.0
    win_rate = (len(wins) / len(pnls) * 100.0)
    
    return {
        "sharpe": round(calculate_sharpe_ratio(returns_decimal), 2),
        "max_dd": round(calculate_max_drawdown(pnls), 2),
        "expectancy": round(calculate_expectancy(win_rate, avg_win, avg_loss), 2)
    }
