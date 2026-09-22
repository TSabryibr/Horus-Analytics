from core.DataManager import DataManager
import os

print(f"LOCAL_FEED_PROVIDER={os.getenv('LOCAL_FEED_PROVIDER')}")
print(f"METASTOCK_HISTORY_DIR={os.getenv('METASTOCK_HISTORY_DIR')}")

tickers = ["MFPC", "BIOC", "NIPH", "CICH", "EPCO"]

print("--- History Data (include_live=False) ---")
for ticker in tickers:
    print(f"\n{ticker}:")
    df = DataManager.get_stock_data(ticker, include_live=False)
    if df is not None and not df.empty:
        print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
    else:
        print("No data found.")

print("\n--- Intraday Data ---")
for ticker in tickers:
    print(f"\n{ticker}:")
    df = DataManager.get_intraday_data(ticker)
    if df is not None and not df.empty:
        print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
    else:
        print("No data found.")

print("\n--- History Data (include_live=True) ---")
for ticker in tickers:
    print(f"\n{ticker}:")
    df = DataManager.get_stock_data(ticker, include_live=True)
    if df is not None and not df.empty:
        print(df[['Open', 'High', 'Low', 'Close', 'Volume']].tail(3))
    else:
        print("No data found.")
