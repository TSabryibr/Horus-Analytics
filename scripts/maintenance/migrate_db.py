"""
MIGRATION SCRIPT
================
Migrates data from legacy JSON files to SQLite.
"""

import json
import os
import datetime
from database import db, Position, initialize_db

def migrate_positions():
    JSON_FILE = "positions.json"
    
    if not os.path.exists(JSON_FILE):
        print("No positions.json found. Skipping.")
        return

    print(f"Migrating {JSON_FILE} to SQLite...")
    
    try:
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
            
        with db.atomic():
            for ticker, details in data.items():
                # Check if exists
                if Position.select().where((Position.ticker == ticker) & (Position.status == "OPEN")).exists():
                    print(f"Skipping {ticker} (Already in DB)")
                    continue
                
                # Parse Date
                try:
                    fmt = "%Y-%m-%d"
                    entry_date = datetime.datetime.strptime(details.get("date", datetime.date.today().strftime(fmt)), fmt)
                except:
                    entry_date = datetime.datetime.now()
                    
                Position.create(
                    ticker=ticker,
                    shares=details.get("shares", 0),
                    entry_price=details.get("entry_price", 0.0),
                    stop_loss=details.get("stop_loss", 0.0),
                    target_price=details.get("target1", details.get("entry_price", 0.0) * 1.04),
                    entry_date=entry_date,
                    status="OPEN"
                )
                print(f"✅ Migrated {ticker}")
                
    except Exception as e:
        print(f"Migration Failed: {e}")

if __name__ == "__main__":
    initialize_db()
    migrate_positions()
