import requests
import json
from colorama import init, Fore

init(autoreset=True)

URL = "http://localhost:8200/api/prediction"

def test_macro():
    print(Fore.CYAN + "Testing ORACLE (MACRO MODE)...")
    try:
        res = requests.post(URL, json={"mode": "MACRO", "index": "EGX30"})
        if res.status_code == 200:
            data = res.json()
            print(Fore.GREEN + f"✅ Success: {data['data']['signal']}")
            print(f"   Correlation: {data['data']['correlation']}")
            print(f"   Message: {data['data']['message']}")
        else:
            print(Fore.RED + f"❌ Failed: {res.text}")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

def test_squeeze():
    print(Fore.CYAN + "\nTesting ORACLE (SQUEEZE MODE)...")
    try:
        res = requests.post(URL, json={"mode": "SQUEEZE"})
        if res.status_code == 200:
            data = res.json()
            print(Fore.GREEN + f"✅ Success: Found {data['data']['count']} coils.")
            if data['data']['count'] > 0:
                print(f"   Top Pick: {data['data']['candidates'][0]['Ticker']} (BW: {data['data']['candidates'][0]['BandWidth']})")
        else:
            print(Fore.RED + f"❌ Failed: {res.text}")
    except Exception as e:
        print(Fore.RED + f"❌ Error: {e}")

if __name__ == "__main__":
    test_macro()
    test_squeeze()
