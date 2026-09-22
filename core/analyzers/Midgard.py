"""
MIDGARD (THE RAVENS)
====================
"Thought and Memory fly over the world."

The Strategy Audit Module.
1. Reads Signal History from database.
2. Checks future price action after each signal.
3. Calculates realized performance metrics.

Refactored from HuginMunin.py.
"""

from core.settings import settings
import datetime
import pandas as pd
import numpy as np
from core import DataManager
import database
from colorama import Fore, Style, init

init(autoreset=True)

EVAL_PERIODS = [1, 3, 5, 10]

def calculate_max_drawdown(pnl_series):
    """Calculates max drawdown from a series of PnL returns."""
    if not pnl_series: return 0.0
    cumulative = np.cumsum(pnl_series)
    peak = -np.inf
    max_dd = 0
    for val in cumulative:
        if val > peak:
            peak = val
        dd = peak - val
        if dd > max_dd:
            max_dd = dd
    return round(float(max_dd), 2)

def audit_strategies(days_limit=None):
    """
    Analyzes the accuracy of past signals stored in the DB.
    Returns structured results for API.
    """
    from core import TimeUtils
    from database import Trade
    
    now_ref = TimeUtils.now()
    query = database.Signal.select()
    
    if days_limit:
        cutoff = TimeUtils.today() - datetime.timedelta(days=days_limit)
        query = query.where(database.Signal.date >= cutoff)
    else:
        query = query.where(database.Signal.date <= TimeUtils.today())

    if not query.exists():
        return {"status": "empty", "message": "No signals found in the memory."}

    results = []
    
    # Pre-fetch all trades for conversion checking
    all_trades = list(Trade.select().dicts())
    
    for sig in query:
        ticker = sig.ticker
        date = pd.to_datetime(sig.date)
        entry_price = sig.price
        strategy = sig.source
        
        df = DataManager.DataManager.get_stock_data(ticker, include_live=False)
        if df is None or df.empty or date not in df.index: continue
        
        idx = df.index.get_loc(date)
        
        # Check if this signal was converted to a trade (Approx match)
        converted = any(
            t['ticker'] == ticker and 
            abs((pd.to_datetime(t['entry_date']) - date).days) <= 1 
            for t in all_trades
        )
        
        outcome = {
            "id": sig.id,
            "ticker": ticker,
            "date": date.strftime('%Y-%m-%d'),
            "strategy": strategy,
            "entry_price": round(float(entry_price), settings.PRICE_PRECISION),
            "pnl_history": {},
            "converted": converted
        }
        
        # Check future returns
        for days in EVAL_PERIODS:
            if idx + days < len(df):
                f_price = df['Close'].iloc[idx + days]
                pnl = ((f_price - entry_price) / entry_price) * 100
                outcome["pnl_history"][f"{days}D"] = round(float(pnl), 2)
        
        if outcome["pnl_history"]:
            results.append(outcome)

    if not results:
        return {"status": "empty", "message": "No signals have reached evaluation age yet."}

    # Summary Stats
    df_res = pd.DataFrame(results)
    # Extract 5D PnL for ranking if available, else 1D
    df_res['score_pnl'] = df_res['pnl_history'].apply(lambda x: x.get('5D', x.get('1D', 0)))
    
    strategy_summary = []
    for strat in df_res['strategy'].unique():
        s_df = df_res[df_res['strategy'] == strat].sort_values('date')
        
        wins = s_df[s_df['score_pnl'] > 0]
        losses = s_df[s_df['score_pnl'] <= 0]
        
        win_rate = (len(wins) / len(s_df)) * 100
        avg_win = wins['score_pnl'].mean() if not wins.empty else 0
        avg_loss = abs(losses['score_pnl'].mean()) if not losses.empty else 0
        
        # Expected Value: (Win% * AvgWin) - (Loss% * AvgLoss)
        ev = (win_rate/100 * avg_win) - ((1 - win_rate/100) * avg_loss)
        
        # Max Drawdown & Equity Curve
        pnl_sequence = s_df['score_pnl'].tolist()
        equity_curve = np.cumsum(pnl_sequence).tolist()
        max_dd = calculate_max_drawdown(pnl_sequence)
        
        # Conversion Rate
        conv_rate = (s_df['converted'].sum() / len(s_df)) * 100
        
        strategy_summary.append({
            "name": strat,
            "count": len(s_df),
            "win_rate": round(float(win_rate), 1),
            "avg_return": round(float(s_df['score_pnl'].mean()), 2),
            "expected_value": round(float(ev), 2),
            "max_drawdown": max_dd,
            "conversion_rate": round(float(conv_rate), 1),
            "equity_curve": [round(x, 2) for x in equity_curve][-30:], # Last 30 points for sparkline
        })

    return {
        "status": "success",
        "total_audited": len(results),
        "strategies": strategy_summary,
        "logs": results[-100:] # Last 100 signals
    }

if __name__ == "__main__":
    print(Fore.MAGENTA + "Midgard is auditing the realm...")
    res = audit_strategies()
    if res['status'] == "success":
        for s in res['strategies']:
            print(f"Strategy: {s['name']} | WR: {s['win_rate']}% | Avg: {s['avg_return']}%")
