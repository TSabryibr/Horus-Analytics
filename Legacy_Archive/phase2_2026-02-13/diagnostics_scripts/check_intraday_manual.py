
import pandas as pd
import os

# User provided path
intraday_path = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE\COMI.csv"

if os.path.exists(intraday_path):
    print(f"File found: {intraday_path}")
    
    # 1. Read Raw Lines to see exact format
    print("\n--- RAW HEADERS ---")
    with open(intraday_path, 'r') as f:
        print(f.readline().strip())
        print(f.readline().strip())
        print(f.readline().strip())
        
    # 2. Pandas Load Test
    print("\n--- PANDAS CHECK ---")
    try:
        df = pd.read_csv(intraday_path)
        print(f"Columns: {df.columns.tolist()}")
        print(f"Row 0: {df.iloc[0].values}")
        print(f"Row -1: {df.iloc[-1].values}")
    except Exception as e:
        print(f"Pandas Error: {e}")

else:
    print(f"File NOT found: {intraday_path}")
