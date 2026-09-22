"""
Quick count of successful parses
"""
from core.settings import settings
import os
import sys
import glob
import json
sys.path.insert(0, r'd:\Antigravity Prpjects\MARKET ANALYSIS')

import IntradayReader

folder = settings.METASTOCK_INTRADAY_FOLDER

# Load mapping
with open(settings.TICKER_MAPPING_FILE) as f:
    mapping = json.load(f)

# Try to parse all files
success = 0
fail_no_file = 0
fail_parse = 0

for ticker, info in mapping.items():
    file_id = info.get('file_id', '')
    if not file_id:
        continue
    
    dat_path = os.path.join(folder, f"{file_id}.DAT")
    
    if not os.path.exists(dat_path):
        fail_no_file += 1
        continue
    
    result = IntradayReader.read_intraday_dat(dat_path)
    
    if result:
        success += 1
    else:
        fail_parse += 1

print(f"Total tickers: {len(mapping)}")
print(f"Success: {success}")
print(f"No file in intraday: {fail_no_file}")
print(f"Parse failed: {fail_parse}")
print(f"DAT files in folder: {len(glob.glob(os.path.join(folder, 'F*.DAT')))}")
