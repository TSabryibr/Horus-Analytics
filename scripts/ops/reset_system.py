"""
SYSTEM RESET SCRIPT
===================
Wipes all data from the database for a clean start.
Does NOT delete the database file, just truncates tables.
"""

from database import db, Portfolio, Position, Trade, Signal, initialize_db

def reset_system():
    print("⚠️  WARNING: This will DELETE ALL DATA from 'horus.db'.")
    confirm = input("Are you sure? Type 'RESET' to confirm: ")
    
    if confirm != "RESET":
        print("❌ Reset cancelled.")
        return

    print("\n🧹 Cleaning Database...")
    db.connect()
    
    # Order matters due to foreign keys
    Trade.delete().execute()
    Position.delete().execute()
    Signal.delete().execute()
    Portfolio.delete().execute()
    
    print("✅ All tables truncated.")
    
    print("🔄 Re-initializing Defaults...")
    # Create default 'Daily Simulation' portfolio
    try:
        Portfolio.create(name="Daily Simulation", type="SYSTEM", auto_manage=True)
        Portfolio.create(name="Intraday Simulation", type="SYSTEM", auto_manage=True)
        print("✅ Default Portfolios created.")
    except:
        print("⚠️  Defaults already exist (or error).")
        
    db.close()
    print("\n🚀 System Reset Complete. You have a clean slate.")

if __name__ == "__main__":
    reset_system()
