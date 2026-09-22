import requests
from colorama import init, Fore

init(autoreset=True)

BASE_URL = "http://localhost:8200/api"

def test_endpoint(name, url, method="GET", payload=None):
    print(Fore.CYAN + f"\nTesting {name}...")
    try:
        if method == "GET":
            res = requests.get(url)
        else:
            res = requests.post(url, json=payload)
            
        if res.status_code == 200:
            print(Fore.GREEN + f"✅ {name} Success!")
            # print(res.json())
        else:
            print(Fore.RED + f"❌ {name} Failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(Fore.RED + f"❌ {name} Error: {e}")

if __name__ == "__main__":
    test_endpoint("Portfolio", f"{BASE_URL}/portfolio")
    test_endpoint("Health", f"{BASE_URL}/health")
    test_endpoint("Whales", f"{BASE_URL}/whales")
