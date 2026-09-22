
from core import AutoTrader
from core import PositionTracker
from database import Position, db
import datetime

# 1. Setup Mock Signal
mock_signal = {
    'Ticker': 'TEST_AUTO',
    'Signal_Type': 'BUY',
    'Entry_Price': 100.0,
    'Stop_Loss': 95.0,
    'Target_Price': 110.0,
    'Score': 10,
    'Sector': 'Testing'
}

print("\n--- 1. Testing Auto-Entry ---")
AutoTrader.process_scanner_signals([mock_signal])

# Verify
pos = Position.get_or_none(Position.ticker == 'TEST_AUTO')
if pos:
    print(f"✅ Position Created: {pos.ticker} @ {pos.entry_price}")
    print(f"   SL: {pos.stop_loss} | TP: {pos.target_price}")
else:
    print("❌ Position Creation FAILED")

print("\n--- 2. Testing Monitor Loop ---")
# This should run without error, even if it can't find data for TEST_AUTO
try:
    AutoTrader.monitor_positions()
    print("✅ Monitor Loop ran successfully")
except Exception as e:
    print(f"❌ Monitor Loop Crashed: {e}")

print("\n--- 3. Cleanup ---")
if pos:
    pos.delete_instance()
    print("Cleaned up test position.")
