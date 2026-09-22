import sqlite3
import pandas as pd
import os

db_paths = [
    r"D:\Antigravity Prpjects\MARKET ANALYSIS\Mubasher_DB.db",
    "Mubasher_DB.db",
    "data/Mubasher_DB.db"
]

for p in db_paths:
    if os.path.exists(p):
        print(f"Connecting to {p}...")
        try:
            conn = sqlite3.connect(p)
            df = pd.read_sql("SELECT DISTINCT Ticker FROM HistoricalData WHERE Ticker LIKE 'EGX%'", conn)
            print("Found Indices:")
            print(df.values.flatten().tolist())
            break
        except Exception as e:
            print(f"Error querying {p}: {e}")
