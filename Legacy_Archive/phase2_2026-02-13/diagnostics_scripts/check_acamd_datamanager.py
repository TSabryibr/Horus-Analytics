
from core.DataManager import DataManager
import pandas as pd

# 1. Test Listing
print("\n--- Testing Ticker Listing ---")
tickers = DataManager.list_tickers(source="CSV")
print(f"Total Tickers: {len(tickers)}")
print(f"Sample: {tickers[:10]}")
numeric_found = any(t.isdigit() for t in tickers)
print(f"Numeric Tickers Found? {numeric_found}")

# 2. Test Data Loading
print("\n--- Testing ACAMD Loading ---")
df = DataManager.get_stock_data("ACAMD", source="CSV")
if df is not None:
    print("Loaded Successfully!")
    print(df.tail())
    print(f"Index Type: {df.index.dtype}")
    print(f"Last Date: {df.index[-1]}")
else:
    print("FAILED to load ACAMD")
