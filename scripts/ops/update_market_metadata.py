"""
DirectFN Metadata Parser
========================
Reads DirectFN metadata CSV files to extract:
1. Sector Mappings (Ticker -> Sector Name)
2. Index Constituents (EGX30, EGX70, EGX100 lists)
3. Company Names

Outputs: market_metadata.json
"""

import os
import csv
import json

# DirectFN Paths
DFN_ROOT = r"C:\Users\TSabr\DFN\DirectFNPro10Plus-Egypt"
META_EN = os.path.join(DFN_ROOT, "metafiles", "WATCHLISTMETA", "CASE", "EN")
SOURCE_EN = os.path.join(DFN_ROOT, "metafiles", "SOURCEMETA", "CASE", "EN")

FILE_SECTORS = os.path.join(SOURCE_EN, "SECTOR_DEFINITIONS.csv")
FILE_TICKERS = os.path.join(META_EN, "TICKER_DEFINITIONS.csv")
FILE_WATCHLISTS = os.path.join(META_EN, "WL_TICKER_DEFINITIONS.csv")

OUTPUT_FILE = r"d:\Antigravity Prpjects\MARKET ANALYSIS\market_metadata.json"

def parse_metadata():
    print("Parsing DirectFN Metadata...")
    
    # 1. Load Sector Definitions (ID -> Name)
    sector_map = {}
    if os.path.exists(FILE_SECTORS):
        with open(FILE_SECTORS, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='|')
            for row in reader:
                sid = row.get('SECTOR')
                name = row.get('SECT_DSC')
                if sid and name:
                    sector_map[sid] = name.strip()
    print(f"Loaded {len(sector_map)} sectors")

    # 2. Load Ticker Info (Symbol -> SectorID)
    ticker_info = {}
    if os.path.exists(FILE_TICKERS):
        with open(FILE_TICKERS, 'r', encoding='utf-8') as f:
            # Handle potential BOM or encoding issues if any, usually utf-8 works
            lines = f.readlines()
            
        # Parse manually since some lines might be malformed or header complex
        header = lines[0].strip().split('|')
        try:
            idx_sym = header.index('SYMBOL')
            idx_sec = header.index('SECTOR')
            idx_desc = header.index('SYMBOL_DESCRIPTION')
        except ValueError:
            print("Error: Column headers not found in TICKER_DEFINITIONS")
            return

        for line in lines[1:]:
            parts = line.strip().split('|')
            if len(parts) > max(idx_sym, idx_sec, idx_desc):
                symbol = parts[idx_sym]
                sec_id = parts[idx_sec]
                desc = parts[idx_desc]
                
                if symbol:
                    sector_name = sector_map.get(sec_id, "Unknown")
                    ticker_info[symbol] = {
                        "name": desc,
                        "sector": sector_name
                    }
    print(f"Loaded details for {len(ticker_info)} tickers")

    # 3. Load Index Constituents
    indices = {
        "EGX30": [],
        "EGX70": [],
        "EGX100": []
    }
    
    # Map Watchlist IDs to our internal Index names
    # Based on FILE_WATCHLISTS inspection:
    # CASE_EGX30 -> EGX30
    # CASE_EGX70_EWI -> EGX70
    # CASE_EGX100_EWI -> EGX100
    wl_map = {
        "CASE_EGX30": "EGX30",
        "CASE_EGX70_EWI": "EGX70",
        "CASE_EGX100_EWI": "EGX100"
    }

    if os.path.exists(FILE_WATCHLISTS):
        with open(FILE_WATCHLISTS, 'r', encoding='utf-8') as f:
             reader = csv.DictReader(f, delimiter='|')
             for row in reader:
                 wl_id = row.get('WL_ID')
                 tkr_lst = row.get('TKR_LST')
                 
                 if wl_id in wl_map and tkr_lst:
                     target_idx = wl_map[wl_id]
                     # TKR_LST can be space or 0x1C (File Separator) separated
                     # Replace \x1c with space then split
                     clean_list = tkr_lst.replace('\x1c', ' ').strip()
                     tickers = clean_list.split(' ')
                     indices[target_idx] = [t for t in tickers if t] # Clean empty strings

    print(f"Indices loaded: EGX30 ({len(indices['EGX30'])}), EGX70 ({len(indices['EGX70'])}), EGX100 ({len(indices['EGX100'])})")

    # 4. Construct Final Data Structure
    # {
    #   "sectors": { "COMI": "Banks", ... },
    #   "names": { "COMI": "Commercial International Bank", ... },
    #   "indices": { "EGX30": ["COMI", ...], ... }
    # }
    
    final_data = {
        "sectors": {t: info["sector"] for t, info in ticker_info.items()},
        "names": {t: info["name"] for t, info in ticker_info.items()},
        "indices": indices
    }
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=2)
    
    print(f"Successfully saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    parse_metadata()
