
from core.market import MarketLists

print("\n--- Market Lists Check ---")
egx30 = MarketLists.get_market_list('EGX30')
print(f"EGX30 Count: {len(egx30)}")
print(f"Is ADIB in EGX30? {'ADIB' in egx30}")

egx70 = MarketLists.get_market_list('EGX70')
print(f"EGX70 Count: {len(egx70)}")

# Check if metadata file exists
import os
print(f"Metadata File exists? {os.path.exists(MarketLists.METADATA_FILE)}")
