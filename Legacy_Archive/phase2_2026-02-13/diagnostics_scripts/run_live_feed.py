from data_engine.live_sentinel import MarketSentinel
from data_engine.signal_detector import analyze_bar
from pathlib import Path

# Hardcoded path for user convenience
DATA_PATH = Path(r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE")

def run_live_trading():
    print("--- 🔴 STARTING LIVE FEED MONITOR ---")
    print(f"Target: {DATA_PATH}")
    print("Waiting for updates... (Press Ctrl+C to stop)")
    
    sentinel = MarketSentinel(DATA_PATH)
    
    # Watch mainly COMI and maybe EGX30 for testing
    sentinel.start(tickers=['COMI', 'EGX30'], on_data_callback=analyze_bar)

if __name__ == "__main__":
    run_live_trading()
