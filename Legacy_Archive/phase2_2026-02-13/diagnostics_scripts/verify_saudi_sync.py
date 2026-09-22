from core import Heimdall
from core import DataManager
from colorama import Fore

def verify_saudi():
    print(Fore.CYAN + "🧪 VERIFYING SAUDI REALM INTEGRATION...")
    
    # 1. Switch to Saudi
    if not Heimdall.open_bifrost("SAUDI"):
        print(Fore.RED + "Failed to open Bifrost to SAUDI.")
        return
        
    # 2. List Tickers
    tickers = DataManager.DataManager.list_tickers()
    print(f"Found {len(tickers)} Saudi tickers in Parquet Lake.")
    
    if not tickers:
        print(Fore.RED + "No tickers found for SAUDI realm.")
        return
        
    # 3. Load sample ticker data
    sample_ticker = tickers[0]
    print(Fore.YELLOW + f"Loading data for sample ticker: {sample_ticker}...")
    df = DataManager.DataManager.get_stock_data(sample_ticker)
    
    if df is not None and not df.empty:
        print(Fore.GREEN + f"✅ SUCCESS: Loaded {len(df)} rows for {sample_ticker}.")
        print(df.head())
    else:
        print(Fore.RED + f"❌ FAILED to load data for {sample_ticker}.")

if __name__ == "__main__":
    verify_saudi()
