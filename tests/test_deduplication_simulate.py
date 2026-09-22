import os
import sys

# Add parent directory to path so we can import Horus modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from core import TimeUtils
from core import AlertManager
print("Starting Deduplication Test")
base_signals = [
    {"Ticker": "ACAMD", "Score": 9, "Entry_Price": 100},
    {"Ticker": "COSG", "Score": 8, "Entry_Price": 50},
    {"Ticker": "ICID", "Score": 7, "Entry_Price": 25}
]

dedup_file = AlertManager.DEDUP_FILE
if os.path.exists(dedup_file):
    os.remove(dedup_file)

def print_result(filtered_list):
    if not filtered_list:
        return "None (DUPLICATES PREVENTED)"
    tickers = ", ".join([s["Ticker"] for s in filtered_list])
    return tickers

# --- 1. INTRADAY SCAN 1 (Should Broadcast 3) ---
print("\n--- INTRADAY SCAN 1 (0 mins) ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "INTRADAY")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)}")

# --- 2. INTRADAY SCAN 2 (Should NOT Broadcast) ---
print("\n--- INTRADAY SCAN 2 (5 mins later) ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "INTRADAY")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)}")

# --- 3. INTRADAY SCAN 3 (Should NOT Broadcast) ---
print("\n--- INTRADAY SCAN 3 (10 mins later) ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "INTRADAY")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)}")

# --- 4. INTRADAY SCAN 4 (Should NOT Broadcast) ---
print("\n--- INTRADAY SCAN 4 (15 mins later) ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "INTRADAY")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)}")

# --- 5. INTRADAY SCAN 5 (Should NOT Broadcast) ---
print("\n--- INTRADAY SCAN 5 (20 mins later) ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "INTRADAY")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)}")

# --- 6. PRE-CLOSE SCAN (Should Broadcast 3 - different label) ---
print("\n--- PRE-CLOSE SCAN ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "PRE-CLOSE")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)} (ALLOWED - DIFFERENT LABEL)")

# --- 7. DAILY SCAN (Should Broadcast 3 - different label) ---
print("\n--- DAILY SCAN ---")
filtered = AlertManager.filter_new_signals(list(base_signals), "DAILY SIGNAL")
print(f"Filtered: {len(filtered)} - Broadcasting: {print_result(filtered)} (ALLOWED - DIFFERENT LABEL)")


# Show final deduplication file
print("\n--- FINAL STATE of sent_signals.json ---")
with open(dedup_file, "r") as f:
    print(json.dumps(json.load(f), indent=2))
