
import sys
import os
sys.path.append(os.getcwd())
from database import Position, db
from core.DataManager import DataManager

def force_update_prices():
    if db.is_closed():
        db.connect()
    
    query = Position.select().where(Position.status == "OPEN")
    print(f"Updating {query.count()} positions...")
    
    count = 0
    for p in query:
        # Get latest price from DataManager (which uses Parquet)
        df = DataManager.get_stock_data(p.ticker)
        if df is not None and not df.empty:
            last_price = float(df.iloc[-1]['Close'])
            p.current_price = last_price
            p.save()
            print(f"✅ Updated {p.ticker}: {last_price}")
            count += 1
        else:
            # Fallback to entry price if no data available so dashboard isn't 0
            p.current_price = p.entry_price
            p.save()
            print(f"⚠️ No data for {p.ticker}, fallback to entry: {p.entry_price}")
            count += 1
            
    if not db.is_closed():
        db.close()
    print(f"Done. Updated {count} positions.")

if __name__ == "__main__":
    force_update_prices()
