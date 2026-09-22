"""
METASTOCK READER
================
Properly reads MetaStock data files using MASTER/XMASTER index files.
Auto-detects EOD (28 bytes) vs Intraday (32 bytes) record format.

Based on user-provided implementation.
"""

from core.settings import settings
import os
import struct
import pandas as pd
import datetime

class MetaStockReader:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.master_file = os.path.join(data_folder, 'MASTER')
        self.xmaster_file = os.path.join(data_folder, 'XMASTER')
        self.symbols = {}  # Symbol -> {'file': filename, 'name': name}

        if not os.path.exists(self.master_file) and not os.path.exists(self.xmaster_file):
            raise FileNotFoundError(f"No MASTER or XMASTER file found in {data_folder}")
        
        # Load indices
        self._load_master_index()
        self._load_xmaster_index()
        print(f"[{data_folder}] Index loaded: {len(self.symbols)} symbols found.")

    def _mbf_to_float(self, binary_data):
        """Converts Microsoft Binary Format (MBF) to standard IEEE float."""
        if len(binary_data) != 4: return 0.0
        b = struct.unpack('<BBBB', binary_data)
        
        exponent = b[3]
        part1 = b[2]
        part2 = b[1]
        part3 = b[0]
        
        if exponent == 0: return 0.0
        
        sign = -1.0 if (part1 & 0x80) else 1.0
        part1 = part1 & 0x7F
        mantissa_val = 1.0 + (part1 * 65536.0 + part2 * 256.0 + part3) / 8388608.0
        
        # Exponent bias correction (MBF 128 -> IEEE 127 equivalent)
        val = sign * mantissa_val * (2.0 ** (exponent - 128))
        return val

    def _load_master_index(self):
        """Reads the standard MASTER file (Files 1-255)."""
        if not os.path.exists(self.master_file): return
        
        # MASTER record size is typically 53 bytes
        RECORD_LEN = 53
        with open(self.master_file, 'rb') as f:
            header = f.read(RECORD_LEN) # Skip header
            while True:
                chunk = f.read(RECORD_LEN)
                if len(chunk) < RECORD_LEN: break
                
                try:
                    file_num = chunk[0]
                    # Symbol (Bytes 7-20)
                    symbol = chunk[7:21].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                    # Name (Bytes 32-48)
                    name = chunk[32:48].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                    
                    if symbol and file_num > 0:
                        self.symbols[symbol] = {'file': f"F{file_num}.DAT", 'name': name or symbol}
                except: continue

    def _load_xmaster_index(self):
        """Reads the XMASTER file (Files 256+)."""
        if not os.path.exists(self.xmaster_file): return
        
        # XMASTER record size is typically 150 bytes
        RECORD_LEN = 150
        with open(self.xmaster_file, 'rb') as f:
            f.read(RECORD_LEN) # Skip header
            while True:
                chunk = f.read(RECORD_LEN)
                if len(chunk) < RECORD_LEN: break
                
                try:
                    # Symbol (Bytes 11-25 approx)
                    symbol = chunk[11:25].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                    name = chunk[32:48].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                    
                    # File ID is usually in byte 2-3 (unsigned short)
                    file_id = struct.unpack('<H', chunk[2:4])[0]
                    
                    if symbol:
                        # Files > 255 are usually .MWD, < 255 are .DAT (but XMaster can track both)
                        ext = "MWD" if file_id > 255 else "DAT"
                        self.symbols[symbol] = {'file': f"F{file_id}.{ext}", 'name': name or symbol}
                except: continue

    def _detect_layout(self, filepath):
        """
        Determines if a file is EOD (28 bytes) or Intraday (32 bytes) 
        based on file size modulo.
        """
        file_size = os.path.getsize(filepath)
        # Check standard header sizes (usually 2 or 4 bytes)
        # We test header size 2, 4, 0 against record sizes 28, 32
        
        candidates = []
        for header in [4, 2, 0]:
            size = file_size - header
            if size > 0:
                if size % 32 == 0: candidates.append(32)
                if size % 28 == 0: candidates.append(28)
        
        if 32 in candidates and 28 not in candidates: return 32
        if 28 in candidates and 32 not in candidates: return 28
        
        # If ambiguous, default to Intraday (32) as it's safer to over-read than under-read
        # or check the specific folder context. 
        # Given your context, if it's ambiguous, it's likely 32 (Intraday often has clean modulo)
        return 32 if 32 in candidates else 28

    def get_data(self, symbol):
        """Reads data for a symbol, automatically detecting Intraday vs EOD."""
        if symbol not in self.symbols:
            print(f"Symbol {symbol} not found.")
            return None

        filename = self.symbols[symbol]['file']
        filepath = os.path.join(self.data_folder, filename)
        
        if not os.path.exists(filepath):
            # Try swapping extension if missing (sometimes XMASTER says DAT but it is MWD)
            base, ext = os.path.splitext(filepath)
            swap_ext = ".MWD" if ext == ".DAT" else ".DAT"
            filepath = base + swap_ext
            if not os.path.exists(filepath):
                print(f"File for {symbol} missing.")
                return None

        # Auto-detect record size
        record_len = self._detect_layout(filepath)
        is_intraday = (record_len == 32)
        
        data = []
        with open(filepath, 'rb') as f:
            # Skip header bytes (detect based on modulo)
            f.seek(0, 2)
            file_len = f.tell()
            f.seek(0)
            
            # Find correct header skip
            header_skip = 0
            for h in [4, 2, 0]:
                if (file_len - h) % record_len == 0:
                    header_skip = h
                    break
            
            f.seek(header_skip)
            
            while True:
                chunk = f.read(record_len)
                if len(chunk) < record_len: break
                
                try:
                    # Parse Fields
                    # 1. Date (YYMMDD float)
                    raw_date = self._mbf_to_float(chunk[0:4])
                    date_int = int(raw_date)
                    
                    # 2-7. OHLCV, OI
                    open_p = self._mbf_to_float(chunk[4:8])
                    high_p = self._mbf_to_float(chunk[8:12])
                    low_p = self._mbf_to_float(chunk[12:16])
                    close_p = self._mbf_to_float(chunk[16:20])
                    vol = self._mbf_to_float(chunk[20:24])
                    
                    # Date Conversion
                    dt = self._parse_date(date_int)
                    if not dt: continue
                    
                    row = {
                        'Date': dt, 'Open': open_p, 'High': high_p, 
                        'Low': low_p, 'Close': close_p, 'Volume': vol
                    }

                    if is_intraday:
                        # Intraday: Bytes 28-32 are Time
                        raw_time = self._mbf_to_float(chunk[28:32])
                        row['Time'] = self._parse_time(raw_time)
                        # Merge into DateTime
                        row['Date'] = row['Date'].replace(
                            hour=row['Time'].hour, 
                            minute=row['Time'].minute
                        )
                        del row['Time']
                    
                    data.append(row)
                except: continue

        if not data: return pd.DataFrame()
        
        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)
        return df

    def _parse_date(self, date_int):
        try:
            d_str = str(date_int).zfill(6)
            year = int(d_str[0:2])
            month = int(d_str[2:4])
            day = int(d_str[4:6])
            full_year = 1900 + year if year >= 50 else 2000 + year
            return datetime.datetime(full_year, month, day)
        except: return None

    def _parse_time(self, time_float):
        try:
            t_int = int(time_float) # e.g. 1430
            t_str = str(t_int).zfill(4)
            return datetime.time(int(t_str[:2]), int(t_str[2:]))
        except: return datetime.time(0,0)
    
    def get_latest_ohlcv(self, symbol):
        """Get just the latest OHLCV for a symbol."""
        df = self.get_data(symbol)
        if df is None or df.empty:
            return None
        
        last = df.iloc[-1]
        return {
            'open': round(float(last['Open']), 4),
            'high': round(float(last['High']), 4),
            'low': round(float(last['Low']), 4),
            'close': round(float(last['Close']), 4),
            'volume': int(last['Volume']),
            'date': df.index[-1]
        }
    
    def get_available_symbols(self):
        """Return list of available symbols."""
        return list(self.symbols.keys())


# Singleton instance for intraday data
_intraday_reader = None

def get_intraday_reader():
    """Get or create the intraday MetaStockReader instance."""
    global _intraday_reader
    if _intraday_reader is None:
        folder = settings.METASTOCK_INTRADAY_FOLDER
        try:
            _intraday_reader = MetaStockReader(folder)
        except FileNotFoundError as e:
            print(f"[MetaStockReader] {e}")
            return None
    return _intraday_reader


# --- HOW TO RUN ---
if __name__ == "__main__":
    import sys
    sys.path.insert(0, r'd:\Antigravity Prpjects\MARKET ANALYSIS')
    
    # Test with intraday folder
    intraday_path = settings.METASTOCK_INTRADAY_FOLDER
    
    print(f"Scanning {intraday_path}...")
    try:
        reader = MetaStockReader(intraday_path)
        
        # Print available symbols
        symbols = reader.get_available_symbols()
        print(f"Total symbols: {len(symbols)}")
        print("First 10:", symbols[:10])
        
        # Test reading some symbols
        test_symbols = ['COMI', 'ACAMD', 'EFIH', 'EAST']
        for sym in test_symbols:
            if sym in symbols:
                result = reader.get_latest_ohlcv(sym)
                if result:
                    print(f"{sym}: Close={result['close']:.2f}, Vol={result['volume']}, Date={result['date']}")
                else:
                    print(f"{sym}: No data")
            else:
                print(f"{sym}: Not in index")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
