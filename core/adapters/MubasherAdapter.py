"""
MUBASHER CSV ADAPTER
====================
Simple CSV reader for Mubasher Trade MetaStock format.
Replaces the complex binary MetaStockAdapter.

History CSV Format: <DATE>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>
Intraday CSV Format: <DTYYYYMMDD>,<HHMMSS>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>

Author: Horus Analytics - EGX
Date: 2026-01-18
"""

from core.settings import settings
import os
import glob
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict



class MubasherAdapter:
    """
    Adapter for reading Mubasher Trade CSV files.
    """
    
    @staticmethod
    def get_stock_data(ticker: str, folder: str = None) -> Optional[pd.DataFrame]:
        """
        Load historical data for a ticker from CSV.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'COMI')
            folder: Folder path (defaults to METASTOCK_HISTORY_FOLDER)
        
        Returns:
            DataFrame with Date index and OHLCV columns, or None if not found
        """
        folder = folder or settings.METASTOCK_HISTORY_FOLDER
        
        # Try exact match first, then case-insensitive
        csv_path = os.path.join(folder, f"{ticker}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(folder, f"{ticker.upper()}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(folder, f"{ticker.lower()}.csv")
        if not os.path.exists(csv_path):
            return None
        
        try:
            df = pd.read_csv(csv_path)
            
            # Normalize column names
            col_map = {}
            for col in df.columns:
                clean = col.strip().replace('<', '').replace('>', '').upper()
                if clean == 'DATE' or clean == 'DTYYYYMMDD':
                    col_map[col] = 'Date'
                elif clean == 'OPEN':
                    col_map[col] = 'Open'
                elif clean == 'HIGH':
                    col_map[col] = 'High'
                elif clean == 'LOW':
                    col_map[col] = 'Low'
                elif clean == 'CLOSE' or clean == 'CLOSED':
                    col_map[col] = 'Close'
                elif clean == 'VOL' or clean == 'VOLUME':
                    col_map[col] = 'Volume'
            
            df = df.rename(columns=col_map)
            
            # Parse date
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d', errors='coerce')
                df = df.dropna(subset=['Date'])
                df = df.set_index('Date')
            
            # Sort by date
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"Error reading {csv_path}: {e}")
            return None
    
    @staticmethod
    def get_intraday_data(ticker: str, folder: str = None) -> Optional[pd.DataFrame]:
        """
        Load intraday data for a ticker from CSV.
        Intraday format has additional TIME column.
        
        Returns:
            DataFrame with DateTime index and OHLCV columns
        """
        folder = folder or settings.METASTOCK_INTRADAY_FOLDER
        
        csv_path = os.path.join(folder, f"{ticker}.csv")
        if not os.path.exists(csv_path):
            csv_path = os.path.join(folder, f"{ticker.upper()}.csv")
        if not os.path.exists(csv_path):
            return None
        
        try:
            df = pd.read_csv(csv_path)
            
            # Get first two column names (Date and Time)
            cols = df.columns.tolist()
            date_col = cols[0]
            time_col = cols[1] if len(cols) > 1 else None
            
            # Normalize column names
            col_map = {}
            for i, col in enumerate(cols):
                clean = col.strip().replace('<', '').replace('>', '').upper()
                if i == 0:  # First column is always date
                    col_map[col] = 'Date'
                elif i == 1 and 'HHMMSS' in clean:  # Second column is time
                    col_map[col] = 'Time'
                elif clean == 'OPEN':
                    col_map[col] = 'Open'
                elif clean == 'HIGH':
                    col_map[col] = 'High'
                elif clean == 'LOW':
                    col_map[col] = 'Low'
                elif clean == 'CLOSE' or clean == 'CLOSED':
                    col_map[col] = 'Close'
                elif clean == 'VOL' or clean == 'VOLUME':
                    col_map[col] = 'Volume'
            
            df = df.rename(columns=col_map)
            
            # Combine Date and Time into DateTime
            if 'Date' in df.columns and 'Time' in df.columns:
                df['DateTime'] = pd.to_datetime(
                    df['Date'].astype(str) + df['Time'].astype(str).str.zfill(6),
                    format='%Y%m%d%H%M%S',
                    errors='coerce'
                )
                df = df.dropna(subset=['DateTime'])
                df = df.set_index('DateTime')
                df = df.drop(columns=['Date', 'Time'], errors='ignore')
            elif 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'].astype(str), format='%Y%m%d', errors='coerce')
                df = df.dropna(subset=['Date'])
                df = df.set_index('Date')
            
            df = df.sort_index()
            
            return df
            
        except Exception as e:
            print(f"Error reading intraday {csv_path}: {e}")
            return None
    
    @staticmethod
    def get_latest_ohlcv(ticker: str, folder: str = None) -> Optional[Dict]:
        """
        Get the most recent OHLCV data for a ticker.
        
        Returns:
            dict with: open, high, low, close, volume, datetime
        """
        df = MubasherAdapter.get_intraday_data(ticker, folder)
        
        if df is None or df.empty:
            return None
        
        last = df.iloc[-1]
        
        return {
            'open': float(last.get('Open', 0)),
            'high': float(last.get('High', 0)),
            'low': float(last.get('Low', 0)),
            'close': float(last.get('Close', 0)),
            'volume': int(last.get('Volume', 0)),
            'datetime': df.index[-1]
        }
    
    @staticmethod
    def get_available_tickers(folder: str = None) -> List[str]:
        """
        Get list of all available ticker symbols from CSV filenames.
        """
        folder = folder or settings.METASTOCK_HISTORY_FOLDER
        
        if not os.path.exists(folder):
            return []
        
        tickers = []
        for f in glob.glob(os.path.join(folder, "*.csv")):
            ticker = os.path.basename(f).replace('.csv', '').upper()
            # Skip index-like files (numbers, EG*, EGX*, REOPEN*)
            if ticker.isdigit():
                continue
            if ticker.startswith('EG') and any(c.isdigit() for c in ticker):
                continue
            if ticker.startswith('REOPEN'):
                continue
            tickers.append(ticker)
        
        return sorted(tickers)


# Aliases for backward compatibility
MUBASHER_HISTORY = settings.METASTOCK_HISTORY_FOLDER
MUBASHER_INTRADAY = settings.METASTOCK_INTRADAY_FOLDER


# === TEST ===
if __name__ == "__main__":
    print("Testing MubasherAdapter...")
    print(f"History Folder: {MUBASHER_HISTORY}")
    print(f"Intraday Folder: {MUBASHER_INTRADAY}")
    
    # Test History
    print("\n=== History Data (COMI) ===")
    df = MubasherAdapter.get_stock_data("COMI")
    if df is not None:
        print(f"Rows: {len(df)}")
        print(df.tail(3))
    else:
        print("Not found")
    
    # Test Intraday
    print("\n=== Intraday Data (ACAMD) ===")
    df = MubasherAdapter.get_intraday_data("ACAMD")
    if df is not None:
        print(f"Rows: {len(df)}")
        print(df.tail(3))
    else:
        print("Not found")
    
    # Test Latest OHLCV
    print("\n=== Latest OHLCV (COMI) ===")
    latest = MubasherAdapter.get_latest_ohlcv("COMI")
    print(latest)
    
    # Test Available Tickers
    print("\n=== Available Tickers ===")
    tickers = MubasherAdapter.get_available_tickers()
    print(f"Count: {len(tickers)}")
    print(f"First 10: {tickers[:10]}")
