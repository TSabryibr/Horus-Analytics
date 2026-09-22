"""
SMART MONEY TRACKER (THE WHISPERER)
===================================
Detects hidden accumulation or distribution using On-Balance Volume (OBV).
Tracks where the 'Whales' are putting their money before the price moves.

Logic:
- Bullish Divergence: Price is falling/flat, but OBV is rising (Smart Buy).
- Bearish Divergence: Price is rising, but OBV is falling (Smart Sell).

Author: LOKI for Horus Analytics
"""

import pandas as pd
import numpy as np
from core import DataManager
from core.market import MarketLists

# Configuration
LOOKBACK_WINDOW = 30   # Days to analyze for divergence
MIN_AVG_VOLUME = 500000 # Filter out illiquid trash

def calculate_slope(series):
    """Calculates the linear slope of a series (direction)."""
    if len(series) < 2: return 0
    y = series.values
    x = np.arange(len(y))
    slope, _ = np.polyfit(x, y, 1)
    return slope

def scan_for_whales():
    """
    Scans the market for OBV Divergences.
    """
    print("👂 [THE WHISPERER] Listening for Smart Money movements...")
    
    tickers = list(MarketLists.get_market_list("ALL"))
    results = []
    
    for ticker in tickers:
        try:
            df = DataManager.DataManager.get_stock_data(ticker)
            if df is None or len(df) < LOOKBACK_WINDOW + 10:
                continue
                
            # Liquidity Check
            avg_vol_val = (df['Close'] * df['Volume']).rolling(20).mean().iloc[-1]
            if avg_vol_val < MIN_AVG_VOLUME:
                continue
                
            # Calculate OBV (Native Pandas)
            df['OBV'] = (np.sign(df['Close'].diff().fillna(0)) * df['Volume']).cumsum()
            
            # Get recent window
            recent = df.iloc[-LOOKBACK_WINDOW:]
            
            # Normalize to compare slopes properly
            price_norm = recent['Close'] / recent['Close'].iloc[0]
            obv_norm = recent['OBV'] / recent['OBV'].iloc[0]
            
            price_slope = calculate_slope(price_norm)
            obv_slope = calculate_slope(obv_norm)
            
            # === DIVERGENCE LOGIC ===
            signal = None
            strength = 0
            
            # Case 1: BULLISH WHISPER (Price Down/Flat, OBV Up)
            # Whales are buying the dip aggressively
            if price_slope <= 0.001 and obv_slope > 0.005:
                signal = "ACCUMULATION (Buy)"
                strength = obv_slope - price_slope
                
            # Case 2: BEARISH WHISPER (Price Up, OBV Down/Flat)
            # Whales are selling into the rally
            elif price_slope > 0.005 and obv_slope <= 0:
                signal = "DISTRIBUTION (Sell)"
                strength = price_slope - obv_slope

            if signal:
                results.append({
                    'Ticker': ticker,
                    'Sector': MarketLists.get_sector(ticker),
                    'Price_Trend': "UP" if price_slope > 0 else "DOWN",
                    'Volume_Trend': "UP" if obv_slope > 0 else "DOWN",
                    'Signal': signal,
                    'Strength': round(strength * 100, 2),
                    'Last_Price': df['Close'].iloc[-1]
                })
                
        except Exception as e:
            continue

    # Sort and Display
    if results:
        df_res = pd.DataFrame(results)
        df_res = df_res.sort_values('Strength', ascending=False)
        
        print(f"\n🐋 WHALE ACTIVITY DETECTED ({len(df_res)} Stocks):")
        print("=" * 70)
        # Split into Buy and Sell
        buys = df_res[df_res['Signal'].str.contains("ACCUMULATION")]
        sells = df_res[df_res['Signal'].str.contains("DISTRIBUTION")]
        
        if not buys.empty:
            print("\n🟢 SECRET ACCUMULATION (Buying the Dip):")
            print(buys[['Ticker', 'Sector', 'Price_Trend', 'Strength']].head(10).to_string(index=False))
            
        if not sells.empty:
            print("\n🔴 SECRET DISTRIBUTION (Selling the Rally):")
            print(sells[['Ticker', 'Sector', 'Price_Trend', 'Strength']].head(10).to_string(index=False))
            
        return df_res
    else:
        print("No significant smart money divergence found.")
        return pd.DataFrame()

if __name__ == "__main__":
    scan_for_whales()
