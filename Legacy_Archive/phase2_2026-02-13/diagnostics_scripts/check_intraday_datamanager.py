
from core.settings import settings
from core.DataManager import DataManager
import pandas as pd
import os

# Override Intraday Path temporarily for test
settings.METASTOCK_INTRADAY_FOLDER = r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE"

print("\n--- Testing Intraday COMI Loading ---")
# Force folder to ensure we test the right file
df = DataManager.get_stock_data("COMI", source="CSV", folder=settings.METASTOCK_INTRADAY_FOLDER)

if df is not None:
    print("Loaded Successfully!")
    print(df.tail())
    print(f"Index Type: {df.index.dtype}")
    print(f"Last Index: {df.index[-1]}")
    
    # Check if time component exists (should be datetime with hours/mins)
    sample_date = df.index[-1]
    if sample_date.hour == 0 and sample_date.minute == 0:
        print("WARNING: Time component seems missing or zeroed out!")
    else:
        print(f"Time Component Verified: {sample_date.time()}")
else:
    print("FAILED to load COMI Intraday")
