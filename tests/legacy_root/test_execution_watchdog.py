import requests
import json
from colorama import init, Fore

init(autoreset=True)

URL = "http://localhost:8200/api/strategy"

def test_execution_watchdog():
    print(Fore.CYAN + "Testing FENRIR (Get Proposal)...")
    try:
        res = requests.get(URL)
        if res.status_code == 200:
            data = res.json()
            if data['status'] == 'success':
                d = data['data']
                print(Fore.GREEN + f"✅ Success: Proposal Generated")
                print(f"   Regime: {d['regime']} (Score: {d['regime_score']})")
                print(f"   Reason: {d['reasoning']}")
                print(f"   Proposed SL: {d['proposed_settings']['SL_PCT']}%")
                
                print(Fore.YELLOW + "   Changes:")
                for c in d['changes']:
                    if c['changed']:
                        print(f"   > {c['parameter']}: {c['old_value']} -> {c['new_value']}")
            else:
                print(Fore.RED + f"❌ Logic Error: {data.get('message')}")
        else:
            print(Fore.RED + f"❌ Failed: {res.text}")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

if __name__ == "__main__":
    test_execution_watchdog()
