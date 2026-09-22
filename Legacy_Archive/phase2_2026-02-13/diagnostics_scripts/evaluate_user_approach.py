import struct
import os
import glob
import math

class MetaStockReader:
    def __init__(self):
        pass

    def read_mbf(self, data):
         # Standard MBF to Float conversion
        if not data or len(data) < 4:
            return 0.0
            
        exp = data[3]
        if exp == 0:
            return 0.0
            
        sign = -1.0 if (data[2] & 0x80) else 1.0
        
        # man_val = ((data[2] & 0x7f) << 16) | (data[1] << 8) | data[0]
        # in MBF, the hidden bit is always 1, so we add 2^23 (0x800000)
        # man_val |= 0x800000
        # val = man_val * (2.0 ** (exp - 128 - 23))
        
        # My previous working implementation:
        b0, b1, b2, exp = data
        part1 = b2 & 0x7F
        mantissa_val = 1.0 + (part1 * 65536.0 + b1 * 256.0 + b0) / 8388608.0
        val = mantissa_val * (2.0 ** (exp - 128))
        
        return val * sign

    def read_data_file(self, file_path, symbol="Unknown"):
        if not os.path.exists(file_path):
             return

        file_size = os.path.getsize(file_path)
        if file_size < 100:
             return

        # Determine format
        rec_size = 28
        has_time = False
        header_size = 28 # Default standard
        
        if file_size % 32 == 0:
            rec_size = 32
            has_time = True
            header_size = 0 
        elif (file_size - 2) % 32 == 0:
            rec_size = 32
            has_time = True
            header_size = 2
        elif (file_size - 28) % 32 == 0:
            rec_size = 32
            has_time = True
            header_size = 28
        elif (file_size - 28) % 28 == 0:
            rec_size = 28
            header_size = 28
        
        print(f"Reading {symbol} ({os.path.basename(file_path)}) - Size: {file_size} bytes, RecSize: {rec_size}")

        with open(file_path, 'rb') as f:
            f.seek(header_size)
            
            count = 0
            while True:
                chunk = f.read(rec_size)
                if len(chunk) < rec_size: break
                
                try:
                    offset = 0
                    date_val = self.read_mbf(chunk[0:4])
                    offset += 4
                    
                    time_val = 0.0
                    if has_time:
                        time_val = self.read_mbf(chunk[offset:offset+4])
                        offset += 4
                        
                    open_val = self.read_mbf(chunk[offset:offset+4])
                    offset += 4
                    high_val = self.read_mbf(chunk[offset:offset+4])
                    offset += 4
                    low_val = self.read_mbf(chunk[offset:offset+4])
                    offset += 4
                    close_val = self.read_mbf(chunk[offset:offset+4])
                    offset += 4
                    vol_val = self.read_mbf(chunk[offset:offset+4])
                    
                    # Date Formatting
                    d_int = int(date_val)
                    date_str = str(d_int)
                    
                    # Time Formatting
                    t_str = ""
                    if has_time:
                        t_int = int(time_val)
                        t_str = f" {t_int}"

                    # Print logic
                    if count < 5:
                        print(f"  [{count}] Date: {date_str}{t_str} | O:{open_val:.3f} H:{high_val:.3f} L:{low_val:.3f} C:{close_val:.3f} V:{vol_val:.0f}")
                    
                    count += 1
                    if count > 5: break # limit for demo
                    
                except Exception as e:
                    continue

    def scan_folder(self, folder_path):
        print(f"\nScanning Folder: {folder_path}")
        master_path = os.path.join(folder_path, 'MASTER')
        xmaster_path = os.path.join(folder_path, 'XMASTER')
        
        stocks = []
        if os.path.exists(xmaster_path):
            stocks = self.parse_xmaster(xmaster_path)
        else:
            print("No XMASTER found.")
            return

        print(f"Found {len(stocks)} symbols in XMASTER.")
        
        # Look for COMI
        comi = next((s for s in stocks if s['symbol'] == 'COMI' or 'F84' in str(s['file_num'])), None)
        if comi:
            print(f"Found COMI: {comi}")
        else:
            # Check F84 directly (COMI's file)
            print("COMI ticker not found in XMASTER, checking F84.DAT...")
            
        
        # Read a few files
        processed = 0
        for stock in stocks[:3]:
             data_file = os.path.join(folder_path, f"F{stock['file_num']}.DAT")
             if os.path.exists(data_file):
                 self.read_data_file(data_file, symbol=stock['symbol'])
                 processed += 1

    def parse_xmaster(self, file_path):
        stocks = []
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                RECORD_SIZE = 150
                num_records = len(content) // RECORD_SIZE
                
                for i in range(num_records):
                    start = i * RECORD_SIZE
                    rec = content[start : start + RECORD_SIZE]
                    
                    try:
                        # Try user's suggested offsets
                        # symbol = rec[2:16]
                        symbol = rec[2:16].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                        name = rec[17:33].split(b'\x00')[0].decode('utf-8', errors='ignore').strip()
                        
                        # Try to find file num
                        fnum = struct.unpack('<H', rec[4:6])[0] # Wait, user said 4:6 inside the try block, but symbol is 2:16? Overlap?
                        # Offset 4 is inside 2:16. That's weird.
                        # Let's check the offsets printed in my previous debug script
                        
                        stocks.append({'symbol': symbol, 'name': name, 'file_num': fnum})
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error reading XMASTER: {e}")
            
        return stocks

if __name__ == '__main__':
    reader = MetaStockReader()
    intraday_path = r'C:\Users\TSabr\DFN\DirectFNPro10Plus-Egypt\ostoul26\metastock\intraday\CASE'
    print("\n=== Analyzing Intraday ===")
    reader.scan_folder(intraday_path)
