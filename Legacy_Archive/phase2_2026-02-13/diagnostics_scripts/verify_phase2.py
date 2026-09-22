
import database
from database import Position, Trade, Signal
from core import PositionTracker
from core import DailyScanner
import datetime

print("=== VERIFICATION PHASE 2 ===")

# 1. Database Persistence
print("\n[1] Testing Database Persistence...")
test_ticker = "TEST_DB_1"
PositionTracker.add_position(test_ticker, 100, 10.0)

# Verify Raw DB
p = Position.get_or_none(Position.ticker == test_ticker)
if p:
    print(f"✅ Position {test_ticker} found in DB (Shares: {p.shares})")
else:
    print("❌ Position NOT found in DB")

# Close it
PositionTracker.close_position(test_ticker, 11.0, "TEST")
if Trade.select().where(Trade.ticker == test_ticker).exists():
    print(f"✅ Trade {test_ticker} moved to History")
else:
    print("❌ Trade not found in History")

# 2. Scanner Logic
print("\n[2] Testing Pure Scanner Logic...")
try:
    signals, monitored, breadth, regime = DailyScanner.get_market_signals()
    print(f"✅ Scanner ran successfully.")
    print(f"   Signals: {len(signals)}")
    print(f"   Breadth: {breadth:.1f}% ({regime})")
    
    if len(signals) > 0:
        print(f"   First Signal: {signals[0]}")
except Exception as e:
    print(f"❌ Scanner Failed: {e}")

print("\n=== VERIFICATION COMPLETE ===")
