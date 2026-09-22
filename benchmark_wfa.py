import time
import pandas as pd
from core.Mimir_WFA import WalkForwardForge

def run_benchmark():
    ticker = "ABUK"
    start_date = "2023-01-01"
    end_date = "2024-01-01"  # Reduced to 1 year for baseline speed
    
    print(f"Starting WFA Benchmark for {ticker} ({start_date} to {end_date})...")
    forge = WalkForwardForge(ticker)
    
    start_time = time.time()
    history = forge.run_forge(start_date, end_date)
    duration = time.time() - start_time
    
    print(f"\nWFA Benchmark Complete!")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Windows processed: {len(history)}")
    if history:
        print(f"Latest Params: {history[-1]['params']}")

if __name__ == "__main__":
    run_benchmark()
