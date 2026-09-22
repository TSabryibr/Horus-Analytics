
import sys
import os
import pandas as pd
from pathlib import Path
import datetime
import traceback

# Add root to sys.path
sys.path.append(os.getcwd())

# Import deps
try:
    from core import DataManager
    from core import Heimdall
except ImportError as e:
    print(f"Import Failed: {e}")
    sys.exit(1)

def test_logic():
    print("Testing DataManager.get_data_status()...")
    
    # 1. Call logic via class
    try:
        status = DataManager.DataManager.get_data_status()
        print("Result from DataManager:", status)
    except Exception as e:
        print("DataManager call failed:", e)
        traceback.print_exc()

    # 2. Replicate logic manually
    print("\n--- Manual Replication ---")
    realm = getattr(Heimdall, "CURRENT_REALM", "EGX")
    history_path = Path(f"data/{realm}/history")
    comi_path = history_path / "COMI.parquet"
    
    print(f"Path Constructed: {comi_path}")
    print(f"Path Absolute: {comi_path.absolute()}")
    print(f"Exists: {comi_path.exists()}")
    
    if comi_path.exists():
        try:
            print("Attempting pd.read_parquet(..., columns=['timestamp'])")
            df = pd.read_parquet(comi_path, columns=['timestamp'])
            
            print("Read Success!")
            print("Columns:", df.columns)
            print("Tail:\n", df.tail())
            
            if not df.empty:
                last_ts = df['timestamp'].iloc[-1]
                print(f"Last Timestamp (Raw): {last_ts} (Type: {type(last_ts)})")
                print(f"Formatted: {last_ts.strftime('%Y-%m-%d')}")
            else:
                print("DataFrame is empty.")
                
        except Exception as e:
            print("Read Failed:", e)
            traceback.print_exc()
            
            print("\nAttempting full read (no columns arg)...")
            try:
                df_full = pd.read_parquet(comi_path)
                print("Full Read Success. Columns:", df_full.columns)
            except Exception as e2:
                print("Full Read Failed:", e2)

if __name__ == "__main__":
    test_logic()
