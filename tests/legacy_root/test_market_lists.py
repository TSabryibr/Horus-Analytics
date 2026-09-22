from core.market import MarketLists

print(f"Indices Loaded: EGX30={len(MarketLists.EGX_30)}, EGX70={len(MarketLists.EGX_70)}")
print(f"COMI Sector: {MarketLists.get_sector('COMI')}")
print(f"COMI Name: {MarketLists.get_company_name('COMI')}")
print(f"Is COMI in EGX30? {'COMI' in MarketLists.EGX_30}")
print(f"ABUK Sector: {MarketLists.get_sector('ABUK')}")
