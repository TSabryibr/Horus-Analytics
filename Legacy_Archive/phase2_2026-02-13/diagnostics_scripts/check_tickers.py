
from core.settings import settings
import os
import glob
from core.DataManager import DataManager

print("--- DIAGNOSTIC START ---")
print(f"settings.DATA_FOLDER: {settings.DATA_FOLDER}")
print(f"settings.METASTOCK_HISTORY_FOLDER: {settings.METASTOCK_HISTORY_FOLDER}")

# Direct Glob Check
csv_pattern = os.path.join(settings.METASTOCK_HISTORY_FOLDER, "*.csv")
files = glob.glob(csv_pattern)
print(f"Direct glob found {len(files)} *.csv files in {settings.METASTOCK_HISTORY_FOLDER}")
if files:
    print(f"Sample file: {files[0]}")

# DataManager Check
tickers = DataManager.list_tickers()
print(f"DataManager.list_tickers() returned {len(tickers)} tickers")
print(f"Sample tickers: {tickers[:5]}")

# Filter Check
filtered = [t for t in tickers if t.upper() not in ['REPORT', 'EGX30_70_100']]
print(f"After filtering: {len(filtered)} tickers")

print("--- DIAGNOSTIC END ---")
