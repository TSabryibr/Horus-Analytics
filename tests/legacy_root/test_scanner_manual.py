print("Importing...)")
from core import DailyScanner
print("Imported DailyScanner")
signals, monitored, breadth, regime = DailyScanner.get_market_signals(is_intraday=False)
print("Finished get_market_signals")
