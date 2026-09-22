from core.settings import settings
import os
import sys
import pandas as pd

# Add current dir to sys.path
sys.path.append(os.getcwd())

from core import DailyScanner
from core.DataManager import DataManager

# Force settings to match the user's report
settings.load_settings("custom")

print("--- Running Intraday Scan Logic ---")
signals, monitored, breadth, regime = DailyScanner.get_market_signals(is_intraday=True)

print(f"Regime: {regime}")
print(f"Breadth: {breadth:.1f}%")
print(f"Total Signals Found: {len(signals)}")

for s in signals:
    print(f"- {s['Ticker']}: Score={s['Score']} Price={s['Entry_Price']}")

# Inspect specific stocks the user mentioned
tickers_to_check = ['BONY', 'ARVA', 'MHOT']
print("\n--- Inspecting Specific Tickers ---")
universe_df = DataManager.get_universe_data(tickers_to_check)
if universe_df is not None and not universe_df.empty:
    for ticker in tickers_to_check:
        if ticker in universe_df.index:
            last = universe_df.loc[ticker].iloc[-1]
            print(f"\n{ticker} Latest Row Data:")
            print(f"Date: {last.name}")
            print(f"Close: {last['Close']}")
            print(f"Rel_Vol: {last.get('Rel_Vol', 'N/A')}")
            print(f"RSI: {last.get('RSI', 'N/A')}")
        else:
            print(f"{ticker} not found in universe data.")
else:
    print("Failed to load universe data for specific tickers.")
