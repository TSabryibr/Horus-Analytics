"""
METASTOCK DATA ADAPTER (COMMERCIAL GRADE + FALLBACK)
=====================================================
Uses 'metastock2pd' library first, falls back to JSON mapping if library fails.
Maintains robustness across different MetaStock data formats.

Author: Horus Analytics - EGX
Date: 2026-01-16
"""

import os
import json
import struct
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
try:
    from metastock2pd import metastock_read_master, metastock_read
    METASTOCK2PD_AVAILABLE = True
except ImportError:
    print("INFO: metastock2pd not installed. Using legacy adapter.")
    metastock_read_master = None
    metastock_read = None
    METASTOCK2PD_AVAILABLE = False

# === CONFIGURATION ===
DIRECTFN_ROOT = r"C:\Users\TSabr\DFN\DirectFNPro10Plus-Egypt"
METASTOCK_HISTORY = os.path.join(DIRECTFN_ROOT, "ostoul26", "metastock", "history", "CASE")
METASTOCK_INTRADAY = os.path.join(DIRECTFN_ROOT, "ostoul26", "metastock", "intraday", "CASE")
TICKER_MAPPING_FILE = r"d:\Antigravity Prpjects\MARKET ANALYSIS\ticker_mapping.json"

# MetaStock record sizes (for legacy reader)
DAT_RECORD_SIZE = 28  # 7 x 4-byte floats

def mbf_to_ieee(mbf_bytes: bytes) -> float:
    """Convert Microsoft Binary Format float to IEEE 754."""
    if len(mbf_bytes) != 4:
        return 0.0
    b0, b1, b2, exp = mbf_bytes
    if exp == 0:
        return 0.0
    sign = (b2 >> 7) & 1
    mantissa = ((b2 & 0x7F) << 16) | (b1 << 8) | b0
    ieee_exp = exp - 2
    ieee_int = (sign << 31) | (ieee_exp << 23) | mantissa
    return struct.unpack('<f', struct.pack('<I', ieee_int))[0]

def ms_date_to_datetime(ms_date: float):
    """Convert MetaStock date float to Python datetime."""
    if ms_date <= 0:
        return None
    try:
        date_int = int(ms_date)
        if date_int > 19000000:
            year = date_int // 10000
            month = (date_int % 10000) // 100
            day = date_int % 100
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
        if 1000000 <= date_int <= 9999999:
            yyy = date_int // 10000
            month = (date_int % 10000) // 100
            day = date_int % 100
            year = 1900 + yyy
            if 1 <= month <= 12 and 1 <= day <= 31:
                return datetime(year, month, day)
        if 1 < date_int < 100000:
            base = datetime(1900, 1, 1)
            return base + timedelta(days=date_int - 2)
        return None
    except:
        return None

def read_dat_file_legacy(file_path: str) -> pd.DataFrame:
    """Legacy reader using MBF conversion (fallback)."""
    if not os.path.exists(file_path):
        return pd.DataFrame()
    file_size = os.path.getsize(file_path)
    if file_size < DAT_RECORD_SIZE * 2:
        return pd.DataFrame()
    num_records = (file_size // DAT_RECORD_SIZE) - 1
    if num_records <= 0:
        return pd.DataFrame()
    records = []
    with open(file_path, 'rb') as f:
        f.read(DAT_RECORD_SIZE)  # Skip header
        for _ in range(num_records):
            raw = f.read(DAT_RECORD_SIZE)
            if len(raw) < DAT_RECORD_SIZE:
                break
            try:
                date_val = mbf_to_ieee(raw[0:4])
                o = mbf_to_ieee(raw[4:8])
                h = mbf_to_ieee(raw[8:12])
                l = mbf_to_ieee(raw[12:16])
                c = mbf_to_ieee(raw[16:20])
                v = mbf_to_ieee(raw[20:24])
                dt = ms_date_to_datetime(date_val)
                if dt and c > 0:
                    records.append({
                        'Date': dt, 'Open': round(o, 4), 'High': round(h, 4),
                        'Low': round(l, 4), 'Close': round(c, 4), 'Volume': int(v)
                    })
            except:
                continue
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

class MetaStockAdapter:
    _master_cache = {}
    _json_mapping_cache = None
    _use_library = True  # Will be set to False if library fails

    @staticmethod
    def _load_json_mapping():
        """Load ticker mapping from JSON file (fallback)."""
        if MetaStockAdapter._json_mapping_cache is not None:
            return MetaStockAdapter._json_mapping_cache
        if os.path.exists(TICKER_MAPPING_FILE):
            try:
                with open(TICKER_MAPPING_FILE, 'r') as f:
                    MetaStockAdapter._json_mapping_cache = json.load(f)
                return MetaStockAdapter._json_mapping_cache
            except:
                pass
        MetaStockAdapter._json_mapping_cache = {}
        return {}

    @staticmethod
    def get_master_data(folder_path):
        """Reads ticker mapping, preferring library, falling back to JSON."""
        # Check cache first
        if folder_path in MetaStockAdapter._master_cache:
            return MetaStockAdapter._master_cache[folder_path]
        
        # Try library first if available and not previously failed
        if METASTOCK2PD_AVAILABLE and MetaStockAdapter._use_library and metastock_read_master:
            try:
                master_data = metastock_read_master(folder_path)
                ticker_map = {}
                
                if isinstance(master_data, pd.DataFrame):
                    for _, row in master_data.iterrows():
                        sym = str(row.get('symbol', '')).upper().strip()
                        fname = str(row.get('filename', ''))
                        if sym and fname:
                            ticker_map[sym] = {'file_path': os.path.join(folder_path, fname), 'name': row.get('name', '')}
                elif isinstance(master_data, dict):
                    for fname, info in master_data.items():
                        sym = info.get('symbol', '').upper().strip()
                        if sym:
                            if not fname.lower().endswith(('.dat', '.mwd')):
                                if os.path.exists(os.path.join(folder_path, fname + ".DAT")):
                                    fname += ".DAT"
                                elif os.path.exists(os.path.join(folder_path, fname + ".MWD")):
                                    fname += ".MWD"
                            ticker_map[sym] = {'file_path': os.path.join(folder_path, fname), 'name': info.get('name', '')}
                
                if ticker_map:
                    MetaStockAdapter._master_cache[folder_path] = ticker_map
                    return ticker_map
                    
            except Exception as e:
                # Silently fallback - library has issues with DirectFN date format
                MetaStockAdapter._use_library = False
        
        # FALLBACK: Use JSON mapping
        json_mapping = MetaStockAdapter._load_json_mapping()
        if json_mapping:
            ticker_map = {}
            for ticker, info in json_mapping.items():
                file_id = info.get('file_id', '')
                if file_id:
                    # Try DAT then MWD
                    for ext in ['DAT', 'MWD']:
                        path = os.path.join(folder_path, f"{file_id}.{ext}")
                        if os.path.exists(path):
                            ticker_map[ticker.upper()] = {'file_path': path, 'name': info.get('name', '')}
                            break
            MetaStockAdapter._master_cache[folder_path] = ticker_map
            return ticker_map
        
        return {}

    @staticmethod
    def get_stock_data(ticker, folder_path=METASTOCK_HISTORY):
        """Get OHLCV data for a ticker."""
        mapping = MetaStockAdapter.get_master_data(folder_path)
        ticker_upper = ticker.upper()
        
        if ticker_upper not in mapping:
            return None
        
        file_path = mapping[ticker_upper]['file_path']
        
        # Try library first
        if METASTOCK2PD_AVAILABLE and metastock_read and MetaStockAdapter._use_library:
            try:
                df = metastock_read(file_path)
                if df is not None and not df.empty:
                    df.columns = [c.capitalize() for c in df.columns]
                    if 'Date' in df.columns:
                        df['Date'] = pd.to_datetime(df['Date'])
                        df.set_index('Date', inplace=True)
                    if 'Close' in df.columns:
                        return df[['Open', 'High', 'Low', 'Close', 'Volume']].sort_index()
            except:
                pass
        
        # Fallback to legacy reader
        df = read_dat_file_legacy(file_path)
        if not df.empty:
            if 'Date' in df.columns:
                df.set_index('Date', inplace=True)
            
            # Price Validation (Corrupt Data Detection)
            if 'Close' in df.columns:
                if df['Close'].max() > 100000 or df['Close'].min() < 0:
                    print(f"WARNING: Suspicious price data for {ticker}. Possible corruption.")
                    return None
            
            return df
        
        return None

    @staticmethod
    def get_available_tickers(folder_path=METASTOCK_HISTORY):
        """List all tickers available."""
        mapping = MetaStockAdapter.get_master_data(folder_path)
        return sorted(list(mapping.keys()))

# Legacy compatibility
def read_dat_file(file_path):
    """For backward compatibility."""
    return read_dat_file_legacy(file_path)

if __name__ == "__main__":
    print("Testing MetaStock Adapter with Fallback...")
    tickers = MetaStockAdapter.get_available_tickers()
    print(f"Found {len(tickers)} tickers.")
    if tickers:
        test_ticker = tickers[0]
        print(f"Reading {test_ticker}...")
        df = MetaStockAdapter.get_stock_data(test_ticker)
        if df is not None:
            print(df.tail())
