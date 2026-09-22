
import sys
import os
import pandas as pd

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.DataManager import DataManager

def check_comi():
    try:
        print("Fetching COMI data...")
        df = DataManager.get_stock_data("COMI", include_live=False)
        
        if df is None or df.empty:
            print("No data found for COMI.")
            return

        last_row = df.iloc[-1]
        last_date = last_row.name # Index is Date
        last_price = last_row['Close']
        
        print(f"Latest Data for COMI:")
        print(f"Date: {last_date}")
        print(f"Close Price: {last_price}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_comi()
