import os
import shutil
import pandas as pd
from pathlib import Path
from core import DataManager
from data_engine import ingest_history

def repair_data_lake():
    print("Starting Data Lake Repair...")
    tickers = DataManager.DataManager.list_tickers()
    print(f"Total tickers to check: {len(tickers)}")
    
    corrupted = []
    for ticker in tickers:
        df = DataManager.DataManager.get_stock_data(ticker, include_live=False)
        if df is None or len(df) < 50:
            print(f"Ticker {ticker} has insufficient history ({len(df) if df is not None else 0} rows). Marking for repair.")
            corrupted.append(ticker)
    
    if not corrupted:
        print("All tickers have sufficient history. No repair needed.")
        return
    
    print(f"Found {len(corrupted)} tickers needing repair.")
    
    # Actually we can just force a full ingest by setting a flag or deleting files
    # Deleting files is safer to ensure a clean slate
    for ticker in corrupted:
        p_path = Path(f"data/EGX/history/{ticker}.parquet")
        if p_path.exists():
            p_path.unlink()
            print(f"Deleted truncated file: {p_path}")
            
    print("Initiating full re-ingestion for corrupted tickers...")
    # ingest_history will now see missing files and load them fully
    # We can run it normally
    ingest_history.ingest_history(force_recent_days=0)
    print("Repair complete.")

if __name__ == "__main__":
    repair_data_lake()
