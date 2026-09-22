
import pandas as pd
import os

path = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\History\CASE\ACAMD.csv"

if os.path.exists(path):
    try:
        df = pd.read_csv(path)
        print(f"File: {path}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {df.columns.tolist()}")
        print("--- LAST ROW ---")
        print(df.iloc[-1])
        
        # Date Parsing Check
        if 'Date' in df.columns:
            last_date = pd.to_datetime(df['Date'].iloc[-1], errors='coerce')
            print(f"Parsed Last Date: {last_date}")
        elif df.index.name == 'Date':
             print(f"Parsed Last Date (Index): {df.index[-1]}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
else:
    print(f"File not found: {path}")
