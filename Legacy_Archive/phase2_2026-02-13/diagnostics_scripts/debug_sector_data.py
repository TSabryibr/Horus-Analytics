
import pandas as pd
from core import DataManager
from core.market import MarketLists
from core.market import SectorRotation
from colorama import init, Fore

init(autoreset=True)

SECTOR = "Real Estate"
print(Fore.YELLOW + f"🔍 DEBUGGING SECTOR: {SECTOR}")
print("-" * 50)

# 1. Get Tickers
all_tickers = MarketLists.get_market_list("ALL")
sector_tickers = [t for t in all_tickers if MarketLists.get_sector(t) == SECTOR]
print(f"Found {len(sector_tickers)} tickers in sector.")

# 2. Inspect Returns
suspicious = []

for t in sector_tickers:
    df = DataManager.DataManager.get_stock_data(t)
    if df is not None and not df.empty and len(df) > 90:
        # Check last 90 days
        recent = df.iloc[-90:]
        
        # Calculate raw change using start/end price
        start_p = recent.iloc[0]['Close']
        end_p = recent.iloc[-1]['Close']
        
        if start_p == 0:
            print(Fore.RED + f"⚠️  {t}: Start Price is 0.0!")
            suspicious.append(t)
            continue
            
        change_pct = ((end_p - start_p) / start_p) * 100
        
        # Check for massive jumps in daily returns
        daily_ret = recent['Close'].pct_change()
        max_daily = daily_ret.max()
        min_daily = daily_ret.min()
        
        if change_pct > 100 or max_daily > 0.5: # > 100% total or > 50% daily
            print(Fore.MAGENTA + f"🚨 {t}: Total Change: {change_pct:.2f}% | Max Daily: {max_daily:.2%}")
            print(f"   Start: {start_p} -> End: {end_p}")
            suspicious.append(t)
        else:
            # print(f"   {t}: OK ({change_pct:.1f}%)")
            pass

# 3. Test Patch
print("-" * 50)
print(Fore.CYAN + "🧪 TESTING PATCHED LOGIC...")
try:
    idx = SectorRotation.build_sector_index(SECTOR)
    if idx is None:
        print(Fore.RED + "❌ Sector Index build failed (None returned).")
    else:
        start_val = idx.iloc[0]
        end_val = idx.iloc[-1]
        print(Fore.GREEN + f"✅ Sector Index Built Successfully!")
        print(f"   Start: {start_val:.2f}")
        print(f"   End:   {end_val:.2f}")
        print(f"   Total Return: {((end_val/start_val)-1)*100:.2f}%")
        
        if end_val > 10000:
            print(Fore.RED + "❌ STILL EXPLODING!")
        else:
            print(Fore.GREEN + "✅ SANITY CHECK PASSED.")

except Exception as e:
    print(Fore.RED + f"❌ Error: {e}")
