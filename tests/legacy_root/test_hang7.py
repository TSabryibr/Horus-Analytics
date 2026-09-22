from core import DailyScanner
def prog(curr, tot, tick):
    print(f"[{curr}/{tot}] {tick}")

print("STARTING")
signals, monitored, breadth, regime = DailyScanner.get_market_signals(is_intraday=False, progress_callback=prog)
print(f"DONE. {len(signals)}")
