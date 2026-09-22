from core.settings import settings
from core.market import MarketRegime
from core.analyzers import ExecutionWatchdog
from colorama import init, Fore

init(autoreset=True)

print(Fore.CYAN + "Testing ..")
print(f"SL_PCT: {getattr(settings, 'SL_PCT', 'MISSING')}")

print(Fore.CYAN + "\nTesting MarketRegime...")
try:
    res = MarketRegime.calculate_market_regime()
    print(Fore.GREEN + f"✅ Regime: {res}")
except Exception as e:
    print(Fore.RED + f"❌ Regime Failed: {e}")
    import traceback
    traceback.print_exc()

print(Fore.CYAN + "\nTesting ExecutionWatchdog Proposal...")
try:
    res = ExecutionWatchdog.generate_strategy_proposal()
    print(Fore.GREEN + f"✅ Proposal: {res['regime']}")
except Exception as e:
    print(Fore.RED + f"❌ ExecutionWatchdog Failed: {e}")
    import traceback
    traceback.print_exc()

print(Fore.CYAN + "\nTesting JSON Serialization...")
import json
try:
    json_str = json.dumps(res)
    print(Fore.GREEN + "✅ JSON Dump Successful!")
except TypeError as e:
    print(Fore.RED + f"❌ JSON Dump Failed: {e}")
    # checking what failed
    for k, v in res.items():
        try:
            json.dumps({k: v})
        except:
            print(f"   ⚠️ Bad Field: {k} ({type(v)})")

