import os
from pathlib import Path
import pandas as pd
import asyncio
from core import settings as settings_module
from core.settings import settings

# Hack to point to the production data
prod_data = Path("dist/HorusApp/data")
if prod_data.exists():
    print(f"DEBUG: Found production data at {prod_data.absolute()}")
    # Testing auto-detection: DATA_ROOT should resolve to dist/HorusApp/data if it exists.
    print(f"DEBUG: BASE_DIR = {settings_module.BASE_DIR}")
    print(f"DEBUG: DATA_ROOT = {settings.DATA_ROOT}")
    # Actually, let's just try to change the environment variable if settings.py supports it
    os.environ["DATA_ROOT_OVERRIDE"] = str(prod_data.absolute())

from core.DailyScanner import get_market_signals
from core.AlertManager import filter_new_signals
from core import TimeUtils

async def test():
    print(f"Testing Intraday Scan for {TimeUtils.today()}...")
    
    # Run scanner with live data
    sigs, mon, br, reg = get_market_signals(is_intraday=True)
    print(f"Scanner found {len(sigs)} signals. Breadth: {br:.1f}% ({reg})")
    
    if sigs:
        for s in sigs:
            print(f" Signal: {s.get('Ticker')} | Score: {s.get('Score')} | Confirmation: {s.get('Confirmation')}")
            
        # Test AlertManager filtering
        new_signals = filter_new_signals(sigs, scan_label="INTRADAY")
        print(f"AlertManager kept {len(new_signals)} signals after filtering.")
    else:
        print("No signals found. This might mean the data is still not being pulled correctly.")

if __name__ == "__main__":
    asyncio.run(test())
