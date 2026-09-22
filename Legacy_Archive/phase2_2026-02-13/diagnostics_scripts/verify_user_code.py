"""
Verify what symbols are returned by the user's MetaStockReader logic
"""
from core.settings import settings
import sys
sys.path.insert(0, r'd:\Antigravity Prpjects\MARKET ANALYSIS')
from core.adapters import MetaStockReader

folder = settings.METASTOCK_INTRADAY_FOLDER
print(f"Reading from: {folder}")

try:
    reader = MetaStockReader.MetaStockReader(folder)
    all_tickers = list(reader.symbols.keys())
    
    print(f"Total Symbols Found: {len(all_tickers)}")
    print("First 20 Symbols:", all_tickers[:20])
    
    # Check if expected tickers are there
    expected = ['COMI', 'ACAMD', 'EAST', 'EFIH']
    found = [t for t in expected if t in all_tickers]
    print(f"Found expected tickers: {found} out of {len(expected)}")
    
except Exception as e:
    print(f"Error: {e}")
