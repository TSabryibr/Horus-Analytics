from core.settings import settings
from core.analyzers import EYE
import time
import sys

# Ensure we can import from current directory
sys.path.insert(0, '.')

print("--- Simulating Horus Eye Scan Logic ---")
try:
    from core.DataManager import DataManager
    tickers = DataManager.list_tickers(source="CSV", folder=settings.METASTOCK_HISTORY_FOLDER)
    print(f"Total Tickers Found: {len(tickers)}")

    if tickers:
        print(f"Testing first 5 tickers: {tickers[:5]}")
        for ticker in tickers[:5]:
            print(f"Analyzing {ticker}...")
            try:
                res = EYE.analyze_stock(ticker)
                if res:
                    print(f"✅ Success: {ticker} -> Score: {res['Signal_Score']}, Status: {res['Status']}")
                else:
                    print(f"⚠️ No Result (Skipped): {ticker}")
            except Exception as e:
                print(f"❌ Exception analyzing {ticker}: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("❌ No tickers found!")
except Exception as e:
    print(f"❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()
