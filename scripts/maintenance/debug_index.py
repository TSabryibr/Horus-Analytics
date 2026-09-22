import os
from pathlib import Path
from data_engine.api import list_tickers, get_data, DATA_ROOT

ticker = "EGX30"
realm = "EGX"
timeframe = "history"

print(f"DATA_ROOT is: {DATA_ROOT.absolute()}")
flat_path = DATA_ROOT / realm / timeframe / f"{ticker}.parquet"
print(f"Checking flat_path: {flat_path.absolute()}")
print(f"Exists: {flat_path.exists()}")

part_root = DATA_ROOT / realm / timeframe / "by_date"
print(f"Checking part_root: {part_root.absolute()}")
print(f"Exists: {part_root.exists()}")

print("\nScanning for EGX30...")
tickers = list_tickers(timeframe=timeframe, realm=realm)
if ticker in tickers:
    print(f"{ticker} found in history ticker list.")
else:
    print(f"{ticker} NOT found in history ticker list.")

print(f"\nAttempting to load {ticker} history...")
df = get_data(ticker, timeframe=timeframe, realm=realm)
if df is not None and not df.empty:
    print(f"Successfully loaded {ticker}. Rows: {len(df)}")
    print(df.tail(3))
else:
    print(f"Failed to load {ticker} data.")
