import sqlite3
import pandas as pd
from pathlib import Path
import os
import sys

# Production database path
DB_PATH = Path("dist/HorusApp/data/EGX/intraday_store.sqlite")
# Fallback if running from a different context
if not DB_PATH.exists():
    DB_PATH = Path("data/EGX/intraday_store.sqlite")
print(f"DEBUG: Processing DB at {DB_PATH.absolute()}")

if not DB_PATH.exists():
    print("ERROR: DB File does not exist!")
    sys.exit(1)

try:
    conn = sqlite3.connect(DB_PATH)
    
    # Check tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"DEBUG: Tables found: {tables}")
    
    if not any('intraday_bars' in str(t) for t in tables):
        print("ERROR: Table 'intraday_bars' not found!")
        sys.exit(1)

    total_records = conn.execute("SELECT COUNT(*) FROM intraday_bars").fetchone()[0]
    print(f"[Info] Total intraday records: {total_records}")
    
    # Check for March 15th, 2026
    mar15_records = conn.execute(
        "SELECT COUNT(*) FROM intraday_bars WHERE timestamp LIKE '2026-03-15%'"
    ).fetchone()[0]
    print(f"[Info] Found {mar15_records} intraday records for 2026-03-15 in {DB_PATH.name}")
    
    if mar15_records > 0:
        print("\n[Sample Records for March 15th]:")
        samples = conn.execute(
            "SELECT ticker, timestamp, close, volume FROM intraday_bars WHERE timestamp LIKE '2026-03-15%' LIMIT 10"
        ).fetchall()
        for s in samples:
            print(f" {s[0]} | {s[1]} | {s[2]} | {s[3]}")
    else:
        print(f"\n[Warning] No records found for March 15th in {DB_PATH.absolute()}")
        
    conn.close()
    print("DEBUG: Done.")
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    sys.exit(1)
