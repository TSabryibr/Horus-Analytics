import os
import sys
import json

# Add current dir to sys.path to import core
sys.path.append(os.getcwd())

from core import AlertManager
from core import TimeUtils

print(f"Current Working Directory: {os.getcwd()}")
print(f"Active DEDUP_FILE path: {AlertManager.DEDUP_FILE}")

if os.path.exists(AlertManager.DEDUP_FILE):
    print("File exists. Contents:")
    with open(AlertManager.DEDUP_FILE, "r", encoding="utf-8") as f:
        print(json.dumps(json.load(f), indent=2))
else:
    print("File does not exist at this path.")

today_str = TimeUtils.today().strftime("%Y-%m-%d")
print(f"Current logic 'today': {today_str}")
