"""
Count stocks with volume
"""
from core.settings import settings
import os
import sys
import json
sys.path.insert(0, r'd:\Antigravity Prpjects\MARKET ANALYSIS')

import IntradayReader

folder = settings.METASTOCK_INTRADAY_FOLDER

with open(settings.TICKER_MAPPING_FILE) as f:
    mapping = json.load(f)

success = 0
with_vol = 0

for ticker, info in mapping.items():
    file_id = info.get('file_id', '')
    if not file_id:
        continue
    
    dat_path = os.path.join(folder, f'{file_id}.DAT')
    result = IntradayReader.read_intraday_dat(dat_path)
    
    if result:
        success += 1
        if result['volume'] > 0:
            with_vol += 1

print(f"Total parsed: {success}")
print(f"With volume > 0: {with_vol}")
