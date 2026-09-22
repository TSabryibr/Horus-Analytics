"""
MARKET SYNC (THE BRIDGE-BUILDER)
================================
Converts MetaStock data folders into the Partitioned Parquet Data Lake.
Enables fast, unified analysis across all local and global markets.

Author: LOKI for Horus Analytics
"""

from core.settings import settings
import os
import pandas as pd
from pathlib import Path
from colorama import Fore, Style, init
from core.adapters.MetaStockReader import  MetaStockReader
from data_engine import parquet_writer
from data_engine.ticker_filters import is_supported_ticker
from core import Heimdall
init(autoreset=True)

def sync_realm(realm_code):
    """Syncs a specific realm from MetaStock to Parquet."""
    # === REALM CONFIGURATION ===
    REALMS = {
        "EGX": {
            "NAME": "Egyptian Exchange",
            "DATA_SOURCE": "LOCAL_METASTOCK",
            "HISTORY_PATH": settings.METASTOCK_HISTORY_FOLDER
        }
    }

    if realm_code not in REALMS:
        print(Fore.RED + f"❌ Realm {realm_code} not found.")
        return
    
    config = REALMS[realm_code]
    if config["DATA_SOURCE"] != "LOCAL_METASTOCK":
        print(Fore.YELLOW + f"ℹ️ Realm {realm_code} is not a local MetaStock source. Skipping.")
        return
    
    source_path = config["HISTORY_PATH"]
    if not source_path or not os.path.exists(source_path):
        print(Fore.RED + f"❌ Source path missing: {source_path}")
        return
    
    print(Fore.CYAN + f"🔄 SYNCING REALM: {config['NAME']} ({realm_code})")
    print(Fore.CYAN + f"   From: {source_path}")
    print(Fore.CYAN + f"   To:   data/{realm_code}/history/\n")
    
    try:
        reader = MetaStockReader(source_path)
        symbols = reader.get_available_symbols()
        total = len(symbols)
        
        for i, sym in enumerate(symbols):
            print(f"   [{i+1}/{total}] Processing {sym}...", end="\r")
            df = reader.get_data(sym)
            
            if df is not None and not df.empty:
                # MetaStockReader returns Index=Date, Cols=['Open', 'High', 'Low', 'Close', 'Volume']
                # ParquetWriter expects lowercase cols and 'timestamp' or DatetimeIndex
                
                # Normalize column names for parquet_writer
                df.columns = [c.lower() for c in df.columns]
                
                # Save to partitioned lake
                parquet_writer.save_stream(sym, df, folder="history", realm=realm_code)
                
        print(Fore.GREEN + f"\n\n✅ {realm_code} Sync Complete.")
        
    except FileNotFoundError:
        print(Fore.YELLOW + "⚠️ No Binary MetaStock Index found. Attempting CSV Sync...")
        sync_csv_realm(source_path, realm_code)
    except Exception as e:
        print(Fore.RED + f"\n❌ Sync Error for {realm_code}: {e}")

def sync_csv_realm(source_path, realm_code):
    """Fallback: Syncs from CSV files if binary MetaStock is missing."""
    import glob
    csv_files = glob.glob(os.path.join(source_path, "*.csv"))
    
    if not csv_files:
        print(Fore.RED + f"❌ No CSV files found in {source_path}")
        return

    print(Fore.CYAN + f"   Found {len(csv_files)} CSV files. Processing...")
    
    updated_count = 0
    total = len(csv_files)
    for i, filepath in enumerate(csv_files):
        sym = os.path.splitext(os.path.basename(filepath))[0].upper()
        if not is_supported_ticker(sym):
            continue
            
        print(f"   [{i+1}/{total}] Processing {sym} (CSV)...", end="\r")
        
        try:
            # Smart CSV reading: handles files with or without headers, and with extra columns
            # Peek first line for headers
            with open(filepath, 'r') as f:
                first_line = f.readline().upper()
            
            has_header = "<DATE>" in first_line or "DATE" in first_line
            
            if has_header:
                df = pd.read_csv(filepath)
                # Normalize columns names to match our engine
                df.columns = [c.upper().strip() for c in df.columns]
                rename_map = {
                    "<DATE>": "Date", "DATE": "Date",
                    "<OPEN>": "Open", "OPEN": "Open",
                    "<HIGH>": "High", "HIGH": "High",
                    "<LOW>": "Low", "LOW": "Low",
                    "<CLOSE>": "Close", "CLOSE": "Close",
                    "<VOL>": "Volume", "VOL": "Volume", "VOLUME": "Volume"
                }
                df.rename(columns=rename_map, inplace=True)
            else:
                # No header, assume standard 6-column format
                df = pd.read_csv(filepath, header=None, names=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            
            # Keep only the columns we need
            needed = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
            df = df[[col for col in needed if col in df.columns]]
            
            if 'Date' not in df.columns:
                continue

            # Format Date
            df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d', errors='coerce')
            df.set_index('Date', inplace=True)
            
            # Sort and deduplicate before saving
            df = df[~df.index.duplicated(keep='last')].sort_index()
            
            if not df.empty:
                # parquet_writer handles further validation and geometric repair internally
                parquet_writer.save_stream(sym, df, folder="history", realm=realm_code)
                updated_count += 1
                
        except Exception as e:
             # print(f"Skipping {sym}: {e}")
             continue
    
    updated_count = 0 # Track how many actually updated
             
    print(Fore.GREEN + f"\n\n✅ {realm_code} CSV Sync Complete.")

def sync_all_locals():
    """Loops through all local realms and syncs them."""
    # Define realms again or move to global scope if needed, but for now just EGX
    REALMS = {
        "EGX": {
            "DATA_SOURCE": "LOCAL_METASTOCK"
        }
    }
    for realm_code, config in REALMS.items():
        if config["DATA_SOURCE"] == "LOCAL_METASTOCK":
            sync_realm(realm_code)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Sync MetaStock to Parquet.")
    parser.add_argument("--realm", help="Specific realm to sync (e.g., SAUDI). If omitted, syncs all local.")
    args = parser.parse_args()
    
    if args.realm:
        sync_realm(args.realm.upper())
    else:
        sync_all_locals()
