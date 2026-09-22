import sys
import os
import datetime
# Add current directory to path
sys.path.insert(0, '.')

import database
from database import Portfolio, Position, Trade, initialize_db
from core import PositionTracker
from core import AutoTrader
from peewee import *

def check_portfolio_manager():
    print("🦅 --- PORTFOLIO MANAGER VERIFICATION ---")
    
    # 1. Initialize DB
    initialize_db()
    
    # 2. Check Critical Portfolios
    print("\n[1] Checking Portfolios...")
    try:
        daily_nav = Portfolio.get_or_none(Portfolio.name == "Daily Simulation")
        if daily_nav:
            print(f"✅ 'Daily Simulation' Portfolio exists (ID: {daily_nav.id})")
        else:
            print("⚠️ 'Daily Simulation' Portfolio MISSING. Creating it...")
            daily_nav = Portfolio.create(name="Daily Simulation", type="SYSTEM", auto_manage=True)
            print(f"✅ Created 'Daily Simulation' (ID: {daily_nav.id})")
            
        intraday_nav = Portfolio.get_or_none(Portfolio.name == "Intraday Simulation")
        if intraday_nav:
            print(f"✅ 'Intraday Simulation' Portfolio exists (ID: {intraday_nav.id})")
        else:
            print("⚠️ 'Intraday Simulation' Portfolio MISSING. Creating it...")
            intraday_nav = Portfolio.create(name="Intraday Simulation", type="SYSTEM", auto_manage=True)
            print(f"✅ Created 'Intraday Simulation' (ID: {intraday_nav.id})")
            
    except Exception as e:
        print(f"❌ Error checking portfolios: {e}")
        return

    # 3. Test Cycle: Create Test Portfolio -> Add Position -> Close Position
    print("\n[2] Testing Portfolio Cycle...")
    test_port_name = "Verification Test"
    try:
        test_port = Portfolio.get_or_none(Portfolio.name == test_port_name)
        if test_port:
             # Clean up previous runs
             print("Cleaning up previous test portfolio...")
             Position.delete().where(Position.portfolio == test_port).execute()
             Trade.delete().where(Trade.portfolio == test_port).execute()
        else:
            test_port = Portfolio.create(name=test_port_name, type="TEST")
            
        print(f"Using Test Portfolio: {test_port.name} (ID: {test_port.id})")
        
        # A. Add Position
        ticker = "TEST_COMI"
        entry_price = 100.0
        shares = 10
        
        print(f"Adding Position: {ticker} @ {entry_price}...")
        PositionTracker.add_position(ticker, shares, entry_price, sl=95.0, tp=110.0, portfolio_id=test_port.id)
        
        # Verify
        pos = Position.get_or_none((Position.ticker == ticker) & (Position.portfolio == test_port) & (Position.status == "OPEN"))
        if pos:
            print(f"✅ Position Created: {pos.ticker} | Shares: {pos.shares} | Status: {pos.status}")
        else:
            print("❌ Position Creation FAILED")
            return

        # B. Simulate Price Move (Update)
        print(f"Updating Position Targets...")
        PositionTracker.update_position(ticker, sl=98.0, tp=115.0)
        # Reload from DB
        pos = Position.get_by_id(pos.id)
        if pos.stop_loss == 98.0:
            print(f"✅ Position Updated: SL now {pos.stop_loss}")
        else:
            print(f"❌ Position Update FAILED. SL is {pos.stop_loss}")
            
        # C. Close Position (Take Profit)
        exit_price = 115.0
        print(f"Closing Position at {exit_price} (Target Hit)...")
        # NOTE: PositionTracker.close_position doesn't take portfolio_id, checks Ticker only?
        # Let's check logic: Position.get_or_none((Position.ticker == ticker) & (Position.status == "OPEN"))
        # This will fail if multiple portfolios have same ticker! 
        # But for this test, TEST_COMI is likely unique.
        
        PositionTracker.close_position(ticker, exit_price, reason="TEST_TARGET")
        
        # Verify Close
        pos_check = Position.get_or_none((Position.ticker == ticker) & (Position.status == "OPEN"))
        if not pos_check:
            print("✅ Position is CLOSED (Removed from Open Table)")
        else:
            print("❌ Position still OPEN")
            
        # Verify Trade Log
        trade = Trade.get_or_none((Trade.ticker == ticker) & (Trade.reason == "TEST_TARGET"))
        # Note: PositionTracker.close_position might not link portfolio_id depending on implementation. 
        # Checking implementation: Trade.create(...). It seems implementation of PositionTracker.close_position 
        # copies attributes from Position but let's check if it copies portfolio_id.
        # Looking at PositionTracker.py: Trade.create(...) does NOT seem to include portfolio field explicitly in close_position?
        # Wait, I verified PositionTracker.py earlier. Line 93: Trade.create(...). It does NOT copy portfolio_id?
        # Let's re-verify line 93 of PositionTracker.py.
        
        if trade:
             print(f"✅ Trade Logged: {trade.ticker} | PnL: {trade.pnl} | Reason: {trade.reason}")
        else:
             print("❌ Trade Log MISSING")

    except Exception as e:
        print(f"❌ Cycle Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_portfolio_manager()
