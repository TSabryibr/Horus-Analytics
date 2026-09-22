from core.settings import settings
import os
import struct
import pandas as pd
import datetime
import sys

# Insert path to access GlobalSettings
sys.path.insert(0, r'd:\Antigravity Prpjects\MARKET ANALYSIS')

class MetaStockReader:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.master_file = os.path.join(data_folder, 'MASTER')
        self.xmaster_file = os.path.join(data_folder, 'XMASTER')
        self.symbols = {}  # Symbol -> {'file': filename, 'name': name}

        if not os.path.exists(self.master_file) and not os.path.exists(self.xmaster_file):
            raise FileNotFoundError(f"No MASTER or XMASTER file found in {data_folder}")
        
        self._load_master_index()
        self._load_xmaster_index()
        print(f"[{data_folder}] Index loaded: {len(self.symbols)} symbols found.")

    def _clean_string(self, byte_chunk):
        """Helper to decode and clean binary strings."""
        try:
            # Split by null byte to get the actual string
            return byte_chunk.split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
        except:
            return ""

    def _smart_assign(self, field1, field2):
        """
        Decides which field is the Symbol and which is the Name.
        """
        s1 = field1.strip()
        s2 = field2.strip()
        
        is_s1_ticker = False
        is_s2_ticker = False
        
        # Check if s1 looks like a ticker (short, no spaces)
        if len(s1) > 0 and len(s1) <= 8 and ' ' not in s1:
            is_s1_ticker = True
            
        # Check if s2 looks like a ticker
        if len(s2) > 0 and len(s2) <= 8 and ' ' not in s2:
            is_s2_ticker = True
            
        # Decision Logic:
        # If Field 2 looks like a ticker and Field 1 has spaces or is long -> SWAP
        if is_s2_ticker and (not is_s1_ticker or len(s1) > len(s2)):
            return s2, s1 # Symbol, Name
        
        # Default
        return s1, s2 # Symbol, Name

    def _load_master_index(self):
        """Reads the standard MASTER file (Files 1-255) with Smart Detection."""
        if not os.path.exists(self.master_file): return
        
        RECORD_LEN = 53
        with open(self.master_file, 'rb') as f:
            f.read(RECORD_LEN) # Skip header
            while True:
                chunk = f.read(RECORD_LEN)
                if len(chunk) < RECORD_LEN: break
                
                try:
                    file_num = chunk[0]
                    
                    # Read both potential text fields
                    # Standard Master: Symbol at 7, Name at 32
                    raw_field_1 = self._clean_string(chunk[7:21])  # Standard Symbol Location
                    raw_field_2 = self._clean_string(chunk[32:48]) # Standard Name Location
                    
                    # Determine which is which
                    symbol, name = self._smart_assign(raw_field_1, raw_field_2)
                    
                    if symbol and file_num > 0:
                        self.symbols[symbol] = {'file': f"F{file_num}.DAT", 'name': name}
                except: continue

    def _load_xmaster_index(self):
        """Reads the XMASTER file (Files 256+) with Smart Detection."""
        if not os.path.exists(self.xmaster_file): return
        
        RECORD_LEN = 150
        with open(self.xmaster_file, 'rb') as f:
            f.read(RECORD_LEN) # Skip header
            while True:
                chunk = f.read(RECORD_LEN)
                if len(chunk) < RECORD_LEN: break
                
                try:
                    # In XMASTER, layout varies, but usually:
                    # Field A: ~Byte 11 (Standard Symbol)
                    # Field B: ~Byte 32 (Standard Name)
                    raw_field_1 = self._clean_string(chunk[11:25])
                    raw_field_2 = self._clean_string(chunk[32:48])

                    file_id = struct.unpack('<H', chunk[2:4])[0]
                    
                    symbol, name = self._smart_assign(raw_field_1, raw_field_2)

                    if symbol:
                        ext = "MWD" if file_id > 255 else "DAT"
                        self.symbols[symbol] = {'file': f"F{file_id}.{ext}", 'name': name}
                except: continue

if __name__ == "__main__":
    folder = settings.METASTOCK_INTRADAY_FOLDER
    print(f"Testing on: {folder}")
    
    reader = MetaStockReader(folder)
    
    print(f"Total Symbols: {len(reader.symbols)}")
    print("First 10 Symbols:", list(reader.symbols.keys())[:10])
    
    # Check for known good tickers
    known_tickers = ['COMI', 'ACAMD', 'EAST', 'EFIH', 'ABUK', 'FWRY']
    found = [t for t in known_tickers if t in reader.symbols]
    print(f"Found known tickers: {found}")
    
    # Print what IS mapped for some known file IDs if possible (manual check)
    # File IDs for above: F84=COMI, F7=ACAMD?
    # Let's just print a few random entries to see what they look like
    print("\nSample Entries:")
    for sym in list(reader.symbols.keys())[:5]:
        print(f"  {sym}: {reader.symbols[sym]}")
