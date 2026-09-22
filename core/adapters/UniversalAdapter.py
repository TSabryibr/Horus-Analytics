"""
UNIVERSAL DATA ADAPTER (THE WORLD-EATER)
========================================
"I drink from the well of Mimir, and I drink from the fire of Muspelheim."

Abstracts data fetching from multiple sources into a single, standard format.
Supports:
1. YFINANCE (USA, Forex, Global Indices)
2. CCXT (Crypto Exchanges like Binance)
3. LOCAL (MetaStock/CSV for EGX/KSA)

Standard Output:
DataFrame with Index=Date, Columns=['Open', 'High', 'Low', 'Close', 'Volume']

Author: LOKI for Horus Analytics
"""

import pandas as pd
import numpy as np
import os
import datetime
from colorama import Fore

# === 1. EXTERNAL LIBRARIES (Lazy Import) ===
try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import ccxt
except ImportError:
    ccxt = None

# === 2. LOCAL ADAPTERS ===
try:
    from core.adapters import MetaStockReader
except ImportError:
    MetaStockReader = None

class UniversalDataEngine:
    
    @staticmethod
    def get_history(ticker, source="YFINANCE", lookback_days=365*2):
        """
        Main entry point. Fetches historical data from the specified source.
        """
        ticker = ticker.strip().upper()
        source = source.strip().upper()
        
        print(Fore.CYAN + f"⚡ FETCHING DATA: {ticker} via {source}...")
        
        df = pd.DataFrame()
        
        try:
            # === SOURCE: YAHOO FINANCE ===
            if source == "YFINANCE" or source == "USA" or source == "FOREX":
                if yf is None:
                    print(Fore.RED + "❌ yfinance library not installed.")
                    return None
                
                # Fetch
                # yfinance expects tickers like 'AAPL', 'EURUSD=X', 'BTC-USD'
                try:
                    df = yf.download(ticker, period="2y", progress=False, auto_adjust=True)
                except Exception as e:
                    print(Fore.RED + f"YF Error: {e}")
                    return None
                
                if df.empty: return None
                
                # Normalize Columns
                # YF returns: Open, High, Low, Close, Volume
                # Sometimes MultiIndex columns if auto_adjust=False
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # Ensure columns are present before slicing
                cols_to_keep = []
                for c in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if c in df.columns:
                        cols_to_keep.append(c)
                
                df = df[cols_to_keep]
            
            # === SOURCE: CRYPTO EXCHANGES (CCXT) ===
            elif source == "CCXT" or source == "CRYPTO":
                if ccxt is None:
                    print(Fore.RED + "❌ ccxt library not installed.")
                    return None
                
                # Default to Binance for liquid pairs, or generic
                exchange = ccxt.binance({'enableRateLimit': True})
                # Ticker format must be standard 'BTC/USDT'
                symbol = ticker.replace('-', '/').replace('_', '/')
                if '/' not in symbol: symbol += '/USDT' # Assumption
                
                try:
                    timeframe = '1d'
                    since = exchange.parse8601((datetime.datetime.now() - datetime.timedelta(days=lookback_days)).isoformat())
                    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)
                    
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
                    df['Date'] = pd.to_datetime(df['timestamp'], unit='ms')
                    df = df.set_index('Date')
                    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
                    
                except Exception as e:
                    print(Fore.RED + f"CCXT Error: {e}")
                    return None

            # === SOURCE: LOCAL METASTOCK (EGX/KSA) ===
            elif "LOCAL" in source or source == "EGX" or source == "KSA" or source == "UAE":
                # Delegate to existing MetaStockReader if available
                # Or assume DataManager handles this logic
                from core import DataManager
                # Check if DataManager has the logic, if not we assume standard file read
                # For this adapter, we will rely on DataManager for local
                df = DataManager.DataManager.get_stock_data(ticker)
                # It should already be normalized
                
            else:
                print(Fore.RED + f"❌ Unknown Source: {source}")
                return None
                
            # === FINAL STANDARDIZATION ===
            if df is not None and not df.empty:
                # Ensure Index is Datetime
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                
                # Ensure Columns exist
                required = ['Open', 'High', 'Low', 'Close', 'Volume']
                for col in required:
                    if col not in df.columns:
                        df[col] = 0.0
                
                # Sort Chronologically
                df = df.sort_index()
                
                # Clean NaNs
                df = df.dropna()
                
                print(Fore.GREEN + f"   ✅ Loaded {len(df)} candles. Last: {df.index[-1].date()}")
                return df
                
        except Exception as e:
            print(Fore.RED + f"❌ CRITICAL DATA ERROR: {e}")
            return None

    @staticmethod
    def get_live_price(ticker, source="YFINANCE"):
        """
        Fast fetch for current price only.
        """
        # (Simplified implementation - usually fetches last candle)
        df = UniversalDataEngine.get_history(ticker, source, lookback_days=5)
        if df is not None and not df.empty:
            return df['Close'].iloc[-1]
        return None

# Simple Test
if __name__ == "__main__":
    print("Testing Universal Adapter...")
    
    # Test USA
    UniversalDataEngine.get_history("AAPL", "YFINANCE")
    
    # Test Crypto
    UniversalDataEngine.get_history("BTC/USDT", "CCXT")
    
    # Test Forex
    UniversalDataEngine.get_history("EURUSD=X", "YFINANCE")
