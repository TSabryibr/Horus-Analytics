"""
Build ticker-to-file mapping by matching CSV data with MetaStock files.
Saves mapping to ticker_mapping.json for future use.

FIXED: CSV files are in DESCENDING order (newest first), MetaStock in ASCENDING.
"""
import os
import glob
import pandas as pd
import json
from core.adapters.MetaStockAdapter import  read_dat_file, METASTOCK_HISTORY

# Your current CSV data folder
CSV_FOLDER = r"D:\STOCKS DATA\Current"

# Output mapping file
MAPPING_FILE = r"d:\Antigravity Prpjects\MARKET ANALYSIS\ticker_mapping.json"

print("=" * 60)
print("AUTO-MATCHING TICKERS TO METASTOCK FILES")
print("=" * 60)

# Get all CSV files
csv_files = glob.glob(os.path.join(CSV_FOLDER, "*.csv"))
print(f"\nFound {len(csv_files)} CSV files")

# Get all MetaStock files
dat_files = sorted(glob.glob(os.path.join(METASTOCK_HISTORY, "F*.DAT")))
mwd_files = sorted(glob.glob(os.path.join(METASTOCK_HISTORY, "F*.MWD")))
all_ms_files = dat_files + mwd_files
print(f"Found {len(all_ms_files)} MetaStock files")

# Pre-load MetaStock data
print("\nLoading MetaStock data...")
ms_data = {}
for i, ms_path in enumerate(all_ms_files):
    if i % 50 == 0:
        print(f"  Loading {i}/{len(all_ms_files)}...")
    file_id = os.path.basename(ms_path).split('.')[0]
    try:
        df = read_dat_file(ms_path)
        if not df.empty and len(df) >= 5:
            ms_data[file_id] = {
                'path': ms_path,
                'last_prices': df['Close'].tail(10).tolist(),  # Last 10 prices (ascending order)
            }
    except Exception as e:
        pass

print(f"  Loaded {len(ms_data)} valid MetaStock files")

# Match each CSV to MetaStock
print("\nMatching CSV files to MetaStock...")
mapping = {}
matched = 0
unmatched = []

for csv_path in csv_files:
    ticker = os.path.basename(csv_path).replace('.csv', '').upper()
    
    # Skip non-stock files
    if ticker in ['REPORT', 'EGX', 'SUMMARY', 'EGX30_70_100']:
        continue
    
    try:
        csv_df = pd.read_csv(csv_path)
        if 'Closed' not in csv_df.columns or len(csv_df) < 5:
            continue
        
        # CSV is DESCENDING, so head() gives newest prices
        # Reverse to get ascending order like MetaStock
        csv_prices = csv_df['Closed'].head(10).tolist()[::-1]  # Reverse to ascending
        
        best_match = None
        best_score = 0
        
        # Compare with each MetaStock file
        for file_id, ms_info in ms_data.items():
            ms_prices = ms_info['last_prices']  # Already ascending from tail()
            
            # Calculate match score
            min_len = min(len(csv_prices), len(ms_prices))
            if min_len < 3:
                continue
            
            # Compare last N prices
            matches = 0
            for p1, p2 in zip(csv_prices[-min_len:], ms_prices[-min_len:]):
                if abs(p1 - p2) / max(abs(p1), 0.01) < 0.01:  # 1% tolerance
                    matches += 1
            
            if matches > best_score:
                best_score = matches
                best_match = file_id
        
        if best_score >= 5:  # At least 5 matching prices
            mapping[ticker] = {
                'file_id': best_match,
                'match_score': best_score
            }
            matched += 1
            if matched <= 20:  # Show first 20 matches
                print(f"  Matched: {ticker} -> {best_match} (score={best_score})")
        else:
            unmatched.append(ticker)
            
    except Exception as e:
        unmatched.append(ticker)

print(f"\n{'=' * 60}")
print(f"RESULTS: {matched} matched, {len(unmatched)} unmatched")

# Save mapping
with open(MAPPING_FILE, 'w') as f:
    json.dump(mapping, f, indent=2)
print(f"\nSaved mapping to: {MAPPING_FILE}")

# Show sample of unmatched
if unmatched and len(unmatched) <= 20:
    print(f"\nUnmatched tickers: {unmatched}")
elif unmatched:
    print(f"\nUnmatched tickers (first 10): {unmatched[:10]}")

print("\nDONE!")
