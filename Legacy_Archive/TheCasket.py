"""
THE CASKET (SEASONALITY SCANNER)
================================
"Time is a flat circle. Everything we have done, we will do again."

Analyzes historical seasonality to find Time-Based Edges.
1. Day of Week Analysis (Do Mondays always bleed?)
2. Monthly Seasonality (Is 'Sell in May' real?)
3. Turn-of-Month Effect (The Payday Pump).

Author: LOKI for Horus Analytics
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt # Optional, for internal plotting logic
from core import DataManager
from core.market import MarketLists
from colorama import Fore, Style, init
from datetime import datetime
from core import TimeUtils
init(autoreset=True)

# CONFIGURATION
MIN_HISTORY_YEARS = 3   # Need at least 3 years to call it a pattern
TARGET_TICKER = "EGX30" # Default target

def analyze_seasonality(ticker=None):
    if ticker is None:
        print(Fore.CYAN + "Enter Ticker to freeze in time (e.g., COMI, EGX30):")
        ticker = input(Fore.WHITE + "> ").strip().upper()
    
    print(Fore.BLUE + f"\n❄️  OPENING THE CASKET FOR: {ticker}...")
    
    df = DataManager.DataManager.get_stock_data(ticker)
    if df is None or df.empty:
        print(Fore.RED + "Ticker not found or empty.")
        return

    # Ensure Date Index
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Needs enough data
    years_avail = (df.index[-1] - df.index[0]).days / 365
    if years_avail < MIN_HISTORY_YEARS:
        print(Fore.RED + f"Not enough history ({years_avail:.1f} years). Need {MIN_HISTORY_YEARS}+.")
        return

    # Add Time Columns
    df['Year'] = df.index.year
    df['Month'] = df.index.month
    df['Month_Name'] = df.index.month_name().str[:3]
    df['Day'] = df.index.day_name().str[:3]
    df['Day_Num'] = df.index.dayofweek # 0=Mon, 6=Sun
    df['Return'] = df['Close'].pct_change(fill_method=None) * 100
    
    # === 1. DAY OF WEEK ANALYSIS ===
    print(Fore.CYAN + "\n📅 DAY OF THE WEEK PATTERNS:")
    dow_stats = df.groupby('Day_Num')['Return'].agg(['mean', 'median', 'count', lambda x: (x > 0).mean() * 100])
    dow_stats.columns = ['Avg_Return%', 'Median%', 'Count', 'Win_Rate%']
    
    # Map back to names (Sunday is start of week in Egypt)
    # 0=Monday in Python. Egypt trades Sun-Thu.
    # So we need to map accurately. 
    # Just use the 'Day' column aggregation to be safe
    dow_stats_named = df.groupby('Day')['Return'].mean().sort_values(ascending=False)
    
    # Display nicely
    for day, ret in dow_stats_named.items():
        color = Fore.GREEN if ret > 0 else Fore.RED
        print(f"  {day}: {color}{ret:+.2f}%")
        
    best_day = dow_stats_named.idxmax()
    worst_day = dow_stats_named.idxmin()
    print(Fore.YELLOW + f">> TACTIC: Buy close of {worst_day}, Sell close of {best_day}.")

    # === 2. MONTHLY SEASONALITY ===
    print(Fore.CYAN + "\n🗓️  MONTHLY SEASONALITY (The Annual Cycle):")
    monthly_stats = df.groupby('Month')['Return'].mean()
    monthly_win = df.groupby('Month')['Return'].apply(lambda x: (x > 0).mean() * 100)
    
    # Identify Current Month
    current_month = TimeUtils.now().month
    curr_perf = monthly_stats.get(current_month, 0)
    
    print(Fore.WHITE + f"Current Month ({TimeUtils.now().strftime('%b')}): " + 
          (Fore.GREEN if curr_perf > 0 else Fore.RED) + f"{curr_perf:+.2f}% Avg")
    
    # Find the "Golden Month"
    best_mo_idx = monthly_stats.idxmax()
    worst_mo_idx = monthly_stats.idxmin()
    
    import calendar
    best_mo_name = calendar.month_abbr[best_mo_idx]
    worst_mo_name = calendar.month_abbr[worst_mo_idx]
    
    print(Fore.GREEN + f"  Best Month: {best_mo_name} ({monthly_stats.max():+.2f}%)")
    print(Fore.RED +   f"  Worst Month: {worst_mo_name} ({monthly_stats.min():+.2f}%)")
    
    # === 3. TURN OF THE MONTH (Payday Effect) ===
    # Look at last day of month and first 3 days of next month
    print(Fore.CYAN + "\n💰 PAYDAY EFFECT (Turn of Month):")
    
    # Mark TOM days (-1 to +3)
    # This is a bit complex to vectorise perfectly without heavy libs, 
    # so we'll approximate by Day of Month
    df['Day_Of_Month'] = df.index.day
    
    # Filter for days 1, 2, 3 and days > 28
    tom_mask = (df['Day_Of_Month'] <= 3) | (df['Day_Of_Month'] >= 28)
    rest_mask = ~tom_mask
    
    tom_return = df.loc[tom_mask, 'Return'].mean()
    rest_return = df.loc[rest_mask, 'Return'].mean()
    
    print(f"  Avg Return during Payday Window (28th-3rd): {Fore.GREEN if tom_return > 0 else Fore.RED}{tom_return:+.2f}%")
    print(f"  Avg Return Rest of Month: {Fore.WHITE}{rest_return:+.2f}%")
    
    if tom_return > rest_return * 2:
        print(Fore.YELLOW + ">> CONFIRMED: Strong Payday Effect detected. Buy end of month.")
    
    # === 4. RECENT STREAK ===
    # What usually happens after 3 green days?
    # Simple conditional probability
    print(Fore.CYAN + "\n🎲 CONDITIONAL PROBABILITY (The Gambler's Fallacy):")
    df['Green'] = df['Return'] > 0
    df['Streak'] = df['Green'].ne(df['Green'].shift()).cumsum()
    
    # Check what happens after 3 UP days
    # This is a basic way to check streaks
    # (Advanced logic omitted for brevity, keeping it robust)
    
    # Probability of UP tomorrow if today is UP
    up_after_up = df[df['Return'].shift(1) > 0]['Return'] > 0
    prob_continuation = up_after_up.mean() * 100
    
    print(f"  If Today is GREEN, chance Tomorrow is GREEN: {Fore.MAGENTA}{prob_continuation:.1f}%")
    if prob_continuation > 55:
        print("  >> Momentum Player (Trend tends to continue).")
    elif prob_continuation < 45:
        print("  >> Mean Reversion Player (Trend tends to flip).")
    else:
        print("  >> Random Walk (Coin flip).")

    print(Fore.BLUE + "\n❄️  CASKET CLOSED.")

if __name__ == "__main__":
    analyze_seasonality()
