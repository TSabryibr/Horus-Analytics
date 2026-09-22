
from core.settings import settings
import json
from core.market import MarketLists
import os

print("Metadata Content:")
print(f"EGX30 sample: {list(MarketLists.EGX_30)[:5]}")

print("\nFiles in Folder:")
files = os.listdir(settings.METASTOCK_HISTORY_FOLDER)
print(files[:10])

print("\nMapping Content:")
try:
    with open('ticker_mapping.json', 'r') as f:
        mapping = json.load(f)
        
    # Check if COMI is in keys
    print(f"COMI in mapping: {'COMI' in mapping}")
    if 'COMI' in mapping:
        print(f"COMI data: {mapping['COMI']}")
        
    # Check if '1' is in keys
    print(f"'1' in mapping: {'1' in mapping}")
        
except Exception as e:
    print(e)
