"""
MONTE CARLO SIMULATOR
=====================
Performs non-deterministic stress testing on a sequence of trades.
Shuffles the trade sequence 1,000+ times to estimate:
1. Probability of Drawdown > X%
2. Probability of Ruin (Account < 0)
3. Median expected equity vs Worst case
"""

import numpy as np
import pandas as pd
import random

def run_monte_carlo(trades_list, initial_equity, simulations=1000, ruin_threshold_pct=100.0):
    """
    Runs Monte Carlo simulation on a list of trade P&L values (percentage or absolute).
    
    Args:
        trades_list (list): List of dictionaries, each containing 'pnl_pct' or 'pnl'. 
                            Ideally 'pnl_pct' (e.g. 5.5 for 5.5%) is better for compounding.
        initial_equity (float): Starting capital
        simulations (int): Number of shuffles to perform
        
    Returns:
        dict: Statistics and simulation paths
    """
    if not trades_list:
        return None
        
    # Extract P&L percentages (as multipliers, e.g., 5% -> 1.05)
    # If using fixed fractional position sizing, the return % is consistent regardless of account size
    # We assume 'pnl_pct' is percent gain on *account* per trade OR percent gain on *risk unit*.
    # For simplicity in this app's context, let's assume 'pnl' is absolute EGP amount for fixed lot,
    # OR 'pnl_pct' is applied to current equity if compounding.
    
    # Strategy: Use Simple Compounding per trade based on PnL % 
    # (Assuming position size scales with equity)
    
    # Extract returns series
    returns = []
    for t in trades_list:
        if 'pnl_pct' in t:
            returns.append(t['pnl_pct'] / 100) # 5.0 -> 0.05
        elif 'pnl' in t:
            returns.append(t['pnl'] / initial_equity)
            
    if not returns:
        return None

    returns = np.array(returns)
    num_trades = len(returns)
    
    # 1. Vectorized Path Generation
    # We create a matrix of indices and shuffle each row independently
    # Note: random.shuffle is slow for matrix, we use np.random.choice for sampling if replacement or 
    # to maintain exactly 1:1 shuffle per path, we generate permutations.
    # For large simulations, permutation indices are faster.
    indices = np.tile(np.arange(num_trades), (simulations, 1))
    for i in range(simulations):
        np.random.shuffle(indices[i])
    
    shuffled_rets = returns[indices] # (simulations, num_trades)
    
    # 2. Vectorized Equity Walk
    # Compounding: Equity = Initial * Cumprod(1 + returns)
    paths = np.ones((simulations, num_trades + 1)) * initial_equity
    paths[:, 1:] = initial_equity * np.cumprod(1 + shuffled_rets, axis=1)
    
    # 3. Vectorized Drawdown Calculation
    # Peak at each point
    peaks = np.maximum.accumulate(paths, axis=1)
    # Drawdown percentage matrix
    drawdowns = (peaks - paths) / peaks * 100
    max_drawdowns = np.max(drawdowns, axis=1)
    
    final_equities = paths[:, -1]
    try:
        ruin_threshold_pct = float(ruin_threshold_pct)
    except Exception:
        ruin_threshold_pct = 100.0
    ruin_threshold_pct = min(100.0, max(0.0, ruin_threshold_pct))
    ruin_floor = float(initial_equity) * (1.0 - ruin_threshold_pct / 100.0)
    
    # Stats
    results = {
        'simulations': simulations,
        'median_equity': float(np.median(final_equities)),
        'worst_case_equity': float(np.min(final_equities)),
        'best_case_equity': float(np.max(final_equities)),
        'avg_max_drawdown': float(np.mean(max_drawdowns)),
        'median_max_drawdown': float(np.median(max_drawdowns)),
        'worst_max_drawdown': float(np.max(max_drawdowns)),
        'loss_probability': float(np.sum(final_equities < initial_equity) / simulations * 100.0),
        'ruin_probability': float(np.sum(final_equities <= ruin_floor) / simulations * 100.0),
        'ruin_threshold_pct': float(ruin_threshold_pct),
        'ruin_floor': float(ruin_floor),
        'drawdown_probability_20': float(np.sum(max_drawdowns >= 20) / simulations * 100.0),
        'drawdown_probability_50': float(np.sum(max_drawdowns >= 50) / simulations * 100.0),
        # Return a subset of paths for plotting (e.g., first 50)
        'plot_paths': paths[:50].tolist() 
    }
    
    return results

if __name__ == "__main__":
    # Test Data
    test_trades = [{'pnl_pct': 2.0}, {'pnl_pct': -1.0}, {'pnl_pct': 5.0}, {'pnl_pct': -2.0}] * 10
    res = run_monte_carlo(test_trades, 100000)
    print("Monte Carlo Test Reuslts:")
    print(f"Median Eq: {res['median_equity']}")
    print(f"Worst DD: {res['worst_max_drawdown']}%")
