import json
import os
from colorama import Fore, Style, init

init(autoreset=True)

WATCHLIST_FILE = "watchlist.json"

def load_watchlist():
    if not os.path.exists(WATCHLIST_FILE):
        return []
    with open(WATCHLIST_FILE, "r") as f:
        return json.load(f)

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        json.dump(watchlist, f, indent=4)

def add_to_watchlist(ticker):
    watchlist = load_watchlist()
    ticker = ticker.upper().strip()
    if ticker not in watchlist:
        watchlist.append(ticker)
        save_watchlist(watchlist)
        print(f"{Fore.GREEN}Added {ticker} to watchlist.")
    else:
        print(f"{Fore.YELLOW}{ticker} is already in watchlist.")

def remove_from_watchlist(ticker):
    watchlist = load_watchlist()
    ticker = ticker.upper().strip()
    if ticker in watchlist:
        watchlist.remove(ticker)
        save_watchlist(watchlist)
        print(f"{Fore.RED}Removed {ticker} from watchlist.")
    else:
        print(f"{Fore.YELLOW}{ticker} not found in watchlist.")

def list_watchlist():
    watchlist = load_watchlist()
    if not watchlist:
        print(f"{Fore.CYAN}Watchlist is empty.")
        return
    print(f"\n{Style.BRIGHT}{Fore.YELLOW}WATCHLIST:")
    print("-" * 20)
    for ticker in sorted(watchlist):
        print(f"{Fore.WHITE}- {ticker}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        list_watchlist()
    else:
        cmd = sys.argv[1].lower()
        if cmd == "add" and len(sys.argv) >= 3:
            add_to_watchlist(sys.argv[2])
        elif cmd == "remove" and len(sys.argv) >= 3:
            remove_from_watchlist(sys.argv[2])
        elif cmd == "list":
            list_watchlist()
        else:
            print("Usage:")
            print("  python Watchlist.py list")
            print("  python Watchlist.py add TICKER")
            print("  python Watchlist.py remove TICKER")
