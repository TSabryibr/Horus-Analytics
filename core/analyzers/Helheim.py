"""
HELHEIM (THE CASKET)
====================
"History is a graveyard of patterns."

The Seasonality Tracker.
Analyzes historical performance across:
1. Month of Year (January Effect, etc.)
2. Day of Week (Monday Blues vs Weekend Rallies)
3. Specific Days of Month (Payday Effect)

Author: LOKI for Horus Analytics
"""

import pandas as pd
import numpy as np
from core import DataManager
from core.market import MarketLists
from colorama import Fore, Style, init

init(autoreset=True)

MONTH_LABELS = {
    1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
    7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
}

WEEKDAY_LABELS = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}


def _normalize_ticker(ticker):
    return str(ticker or "").strip().upper()


def _prepare_price_frame(df):
    if df is None or len(df) == 0:
        return None

    out = df.copy()
    # Helheim requires datetime-aware calendar dimensions.
    out.index = pd.to_datetime(out.index, errors='coerce')
    out = out[~out.index.isna()]
    if out.empty:
        return None

    if 'Close' not in out.columns:
        return None

    out['Close'] = pd.to_numeric(out['Close'], errors='coerce')
    out = out.dropna(subset=['Close'])
    if out.empty:
        return None

    # Prefer true candle open when available; fallback keeps backward compatibility.
    if 'Open' in out.columns:
        out['Open'] = pd.to_numeric(out['Open'], errors='coerce')
    else:
        out['Open'] = out['Close']
    out['Open'] = out['Open'].fillna(out['Close'])

    out['Returns'] = out['Close'].pct_change() * 100
    # Keep the first NaN return row so monthly candle stats retain full history.
    if out['Returns'].notna().sum() == 0:
        return None

    out['Month'] = out.index.month
    out['DayOfWeek'] = out.index.dayofweek
    out['DayOfMonth'] = out.index.day
    return out


def analyze_seasonality(ticker):
    """
    Analyzes seasonality for a single ticker.
    """
    ticker_norm = _normalize_ticker(ticker)
    if not ticker_norm:
        return {"status": "error", "message": "Invalid ticker"}

    df = DataManager.DataManager.get_stock_data(ticker_norm)
    if df is None or len(df) < 250: # Need at least 1 year
        return {"status": "error", "message": "Insufficient Data"}

    prepared = _prepare_price_frame(df)
    if prepared is None or len(prepared) < 60:
        return {"status": "error", "message": "Insufficient Data"}
    
    # 1. Month Seasonality (monthly candle return: month open -> month close)
    monthly_candles = (
        prepared
        .assign(Year=prepared.index.year, Month=prepared.index.month)
        .groupby(['Year', 'Month'], as_index=False)
        .agg(month_open=('Open', 'first'), month_close=('Close', 'last'))
    )
    monthly_candles = monthly_candles.dropna(subset=['month_open', 'month_close'])
    monthly_candles = monthly_candles[monthly_candles['month_open'] > 0]
    if monthly_candles.empty:
        return {"status": "error", "message": "Insufficient Data"}

    monthly_candles['monthly_return'] = (
        (monthly_candles['month_close'] / monthly_candles['month_open']) - 1.0
    ) * 100.0

    month_res = []
    for m, month_slice in monthly_candles.groupby('Month'):
        month_returns = month_slice['monthly_return']
        month_res.append({
            "label": MONTH_LABELS.get(int(m), str(m)),
            "average_return": float(round(month_returns.mean(), 2)),
            "count": int(month_returns.count()),
            "win_rate": float(round((month_returns > 0).mean() * 100, 1))
        })
    month_res.sort(key=lambda x: list(MONTH_LABELS.values()).index(x['label']) if x['label'] in MONTH_LABELS.values() else 99)

    # 2. Weekday Seasonality (daily returns)
    daily_returns = prepared.dropna(subset=['Returns'])
    if daily_returns.empty:
        return {"status": "error", "message": "Insufficient Data"}

    weekday_stats = daily_returns.groupby('DayOfWeek')['Returns'].agg(['mean', 'count']).round(2)
    weekday_res = []
    for d, row in weekday_stats.iterrows():
        weekday_res.append({
            "label": WEEKDAY_LABELS.get(int(d), str(d)),
            "average_return": float(row['mean']),
            "win_rate": float(round((daily_returns[daily_returns['DayOfWeek'] == d]['Returns'] > 0).mean() * 100, 1))
        })
    weekday_res.sort(key=lambda x: list(WEEKDAY_LABELS.values()).index(x['label']) if x['label'] in WEEKDAY_LABELS.values() else 99)

    if not month_res:
        return {"status": "error", "message": "Insufficient Data"}

    # 3. Overall Verdict
    best_month = max(month_res, key=lambda x: x['average_return'])
    worst_month = min(month_res, key=lambda x: x['average_return'])
    
    return {
        "status": "success",
        "ticker": ticker_norm,
        "months": month_res,
        "weekdays": weekday_res,
        "verdict": {
            "best_month": best_month['label'],
            "worst_month": worst_month['label'],
            "summary": f"Historical best month is {best_month['label']} ({best_month['average_return']}%)"
        }
    }

def get_market_seasonality():
    """Returns top seasonality picks for the current month."""
    from core import TimeUtils
    current_month = TimeUtils.now().month
    
    universe = MarketLists.get_market_list("EGX30") # Limit to EGX30 for speed
    picks = []
    
    for t in universe:
        try:
            res = analyze_seasonality(t)
            if res['status'] == "success":
                # Find stats for current month
                c_month_stat = next((m for m in res['months'] if m['label'] == MONTH_LABELS[current_month]), None)
                if c_month_stat and c_month_stat['average_return'] > 2.0: # High expectation
                    picks.append({
                        "ticker": t,
                        "avg_return": c_month_stat['average_return'],
                        "win_rate": c_month_stat['win_rate'],
                        "best_month": res['verdict']['best_month']
                    })
        except:
            continue
            
    picks.sort(key=lambda x: x['avg_return'], reverse=True)
    return {
        "status": "success",
        "month": current_month,
        "month_label": MONTH_LABELS[current_month],
        "top_historical_performers": picks[:10]
    }

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "COMI"
    print(f"Opening the Casket for {ticker}...")
    res = analyze_seasonality(ticker)
    if res['status'] == "success":
        print(f"\nMONTHLY RESULTS:")
        for m in res['months']:
            color = Fore.GREEN if m['average_return'] > 0 else Fore.RED
            print(f"{m['label']}: {color}{m['average_return']}%{Fore.RESET} (WR: {m['win_rate']}%)")
        print(f"\nVERDICT: {res['verdict']['summary']}")
