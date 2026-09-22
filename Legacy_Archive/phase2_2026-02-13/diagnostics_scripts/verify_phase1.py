
from core.settings import settings
import os
from core.DataManager import DataManager

print("=== VERIFICATION SCRIPT ===")

# Test 1: GlobalSettings loading
print("\n[1] Testing ..")
print(f"TELEGRAM_TOKEN (Hidden): {'***' if settings.TELEGRAM_TOKEN else 'MISSING'}")
print(f"METASTOCK_HISTORY: {settings.METASTOCK_HISTORY_FOLDER}")

if settings.METASTOCK_HISTORY_FOLDER == "C:/Users/TSabr/AppData/Roaming/MubasherTrade/PRO Egypt/UserData/847857994/MetaStock/History/CASE":
    print("✅ Path loaded correctly from .env")
else:
    print("❌ Path does NOT match .env")

# Test 2: DataManager Ticker List
print("\n[2] Testing DataManager.list_tickers()...")
tickers = DataManager.list_tickers()
print(f"Found {len(tickers)} tickers.")
if len(tickers) > 0:
    print(f"First 5: {tickers[:5]}")
    print("✅ DataManager listing works")
else:
    print("⚠️ No tickers found (Check path validity)")

# Test 3: DataManager Load CSV
if len(tickers) > 0:
    test_ticker = tickers[0]
    print(f"\n[3] Testing DataManager.get_stock_data('{test_ticker}')...")
    df = DataManager.get_stock_data(test_ticker)
    if df is not None and not df.empty:
        print(f"✅ Loaded DataFrame with shape {df.shape}")
        print(df.tail(2))
    else:
        print("❌ Failed to load DataFrame")
else:
    print("Skipping Load Test (No tickers)")

print("\n=== VERIFICATION COMPLETE ===")
