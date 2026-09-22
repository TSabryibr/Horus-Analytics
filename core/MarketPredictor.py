"""
MARKET PREDICTOR (THE ORACLE)
=============================
Advanced logic to predict market direction using:
1. Divergence (The Canary): Index Price vs Market Breadth
2. Volatility Compression (The Coil): Stocks ready to explode

Author: LOKI for Horus Analytics
"""
import pandas as pd
import numpy as np
from core import DataManager
from core.market import MarketLists

# === SETTINGS ===
DIVERGENCE_LOOKBACK = 30
SQUEEZE_LENGTH = 20
SQUEEZE_STD = 2.0
MIN_LIQUIDITY = 1000000  # 1M EGP daily volume min for squeeze candidates
MAX_SQUEEZE_BANDWIDTH = 0.25  # Reject names that are still objectively wide-band.

def calculate_market_breadth():
    """
    Calculates the 'Net Advances' line for the entire market.
    Breadth = (Number of Stocks Rising) - (Number of Stocks Falling)
    """
    print("[THE CANARY] Calculating Market Breadth...")
    tickers = MarketLists.get_market_list("ALL")
    
    # Dictionary to hold all closes efficiently
    cl_dict = {}
    
    for t in tickers:
        df = DataManager.DataManager.get_stock_data(t)
        if df is not None and not df.empty and len(df) > 60:
            cl_dict[t] = df['Close']
            
    if not cl_dict:
        print("[THE CANARY] No data available for breadth.")
        return None
        
    # Create DataFrame once to avoid fragmentation
    market_closes = pd.DataFrame(cl_dict)
    
    # Calculate daily percent changes
    # fill_method=None to avoid FutureWarnings in newer pandas
    daily_changes = market_closes.pct_change(fill_method=None)
    
    # 1. Count Advancing Stocks (> 0)
    advances = (daily_changes > 0).sum(axis=1)
    
    # 2. Count Declining Stocks (< 0)
    declines = (daily_changes < 0).sum(axis=1)
    
    # 3. Net Line (Cumulative Sum)
    # This line represents the "True" health of the market
    ad_line = (advances - declines).cumsum()
    
    return ad_line

def check_macro_health(index_ticker="EGX30"):
    """
    Compares the Index Price Action vs. The Market Breadth.
    Look for DIVERGENCE (The Lie).
    """
    ad_line = calculate_market_breadth()
    if ad_line is None: 
        return {
            "status": "error",
            "message": "No breadth data available for macro analysis.",
            "ticker": index_ticker,
            "signal": "NO_DATA"
        }

    # Map the raw ticker input if necessary (e.g. from frontend tab switches)
    # Standardize to exact Parquet filenames
    mapping = {
        "EGX30": "EGX30",
        "EGX70": "EGX70 EWI",
        "EGX70 EWI": "EGX70 EWI",
        "EGX100": "EGX100 EWI",
        "EGX100 EWI": "EGX100 EWI"
    }
    search_ticker = mapping.get(index_ticker.upper(), index_ticker)

    # Get Index Data with Retry (Wait for startup sync if needed)
    import time
    index_df = None
    max_retries = 10
    for attempt in range(max_retries):
        index_df = DataManager.DataManager.get_stock_data(search_ticker)
        if index_df is not None and not index_df.empty:
            break
        if attempt < max_retries - 1:
            time.sleep(2) # Wait 2s between checks during startup warm-up
            
    if index_df is None or index_df.empty:
        print(f"[THE CANARY] Index {search_ticker} not found or empty after {max_retries} attempts. Cannot compare.")
        return {
            "status": "error",
            "message": f"Index {search_ticker} not found.",
            "ticker": index_ticker,
            "signal": "NO_INDEX_DATA"
        }

    # Align Data
    common_idx = index_df.index.intersection(ad_line.index)
    price = index_df.loc[common_idx, 'Close']
    breadth = ad_line.loc[common_idx]
    
    # Focus on the recent trend (e.g., last 30 days)
    recent_price = price.iloc[-DIVERGENCE_LOOKBACK:]
    recent_breadth = breadth.iloc[-DIVERGENCE_LOOKBACK:]
    
    # Correlation Check
    correlation = recent_price.corr(recent_breadth)
    
    # Slope Check (Linear Regression Slope) to see direction
    price_slope = np.polyfit(range(len(recent_price)), recent_price.values, 1)[0]
    breadth_slope = np.polyfit(range(len(recent_breadth)), recent_breadth.values, 1)[0]
    
    print(f"\n[MACRO PREDICTION] ({index_ticker}):")
    print(f"Correlation (Price vs Internal Strength): {correlation:.2f}")
    
    # === INTERPRETATION LOGIC ===
    signal = "NEUTRAL"
    msg = "Market is confused."
    
    # 1. Bearish Divergence (Price UP, Breadth DOWN)
    if price_slope > 0 and breadth_slope < 0:
        signal = "BEARISH DIVERGENCE"
        msg = "The Generals are leading, but the soldiers are fleeing. CRASH IMMINENT."
    
    # 2. Bullish Divergence (Price DOWN, Breadth UP)
    elif price_slope < 0 and breadth_slope > 0:
        signal = "BULLISH DIVERGENCE"
        msg = "The Index is dropping, but most stocks are silently rising. ACCUMULATION."
        
    # 3. Strong Uptrend (Both UP)
    elif price_slope > 0 and breadth_slope > 0:
        signal = "HEALTHY UPTREND"
        msg = "The broad market supports the rally. Safe to buy."
        
    # 4. Strong Downtrend (Both DOWN)
    elif price_slope < 0 and breadth_slope < 0:
        signal = "HEALTHY DOWNTREND"
        msg = "Everything is selling off. Cash is King."
        
    analysis = {
        "ticker": index_ticker,
        "correlation": round(correlation, 2),
        "signal": signal,
        "message": msg,
        "price_history": recent_price.to_dict(),
        "breadth_history": recent_breadth.to_dict()
    }
    
    return analysis

def print_macro_health(index_ticker="EGX30"):
    """CLI Output Handler"""
    data = check_macro_health(index_ticker)
    if not data: return

    print(f"\n[MACRO PREDICTION] ({data['ticker']}):")
    print(f"Correlation (Price vs Internal Strength): {data['correlation']}")
    print(f"SIGNAL: {data['signal']}")
    print(f"Analysis: {data['message']}\\n")

def hunt_the_coil():
    """
    Scans for Volatility Squeezes (The Coil).
    Stocks with Bollinger Band Width at 6-month lows.
    """
    print("[THE COIL] Hunting for explosive moves...")
    
    # Scan Liquid Stocks Only (EGX 30 + 70)
    universe = list(MarketLists.get_market_list("30")) + list(MarketLists.get_market_list("70"))
    universe = list(set(universe)) # Remove duplicates
    
    candidates = []
    
    for ticker in universe:
        try:
            df = DataManager.DataManager.get_stock_data(ticker)
            if df is None or len(df) < 130: continue
            
            # Check Liquidity
            avg_vol_value = (df['Close'] * df['Volume']).rolling(20).mean().iloc[-1]
            if avg_vol_value < MIN_LIQUIDITY: continue
            
            # Calculate Bollinger Bands (Native Pandas)
            rolling = df['Close'].rolling(window=SQUEEZE_LENGTH)
            mid = rolling.mean()
            std = rolling.std()
            upper = mid + (SQUEEZE_STD * std)
            lower = mid - (SQUEEZE_STD * std)
            
            df['BW'] = (upper - lower) / mid
            
            # Is today's Bandwidth the lowest in 6 months (125 days)?
            # We allow a tiny buffer (within 5% of the minimum)
            min_bw_6m = df['BW'].rolling(125).min().iloc[-1]
            current_bw = df['BW'].iloc[-1]
            
            if (
                pd.notna(current_bw)
                and pd.notna(min_bw_6m)
                and current_bw > 0
                and current_bw <= MAX_SQUEEZE_BANDWIDTH
                and current_bw <= min_bw_6m * 1.05
            ):
                # We found a coil! Now, which way will it break?
                # Look at Relative Volume
                rel_vol = df['Volume'].iloc[-1] / df['Volume'].rolling(20).mean().iloc[-1]
                
                candidates.append({
                    'Ticker': ticker,
                    'Sector': MarketLists.get_sector(ticker),
                    'BandWidth': round(current_bw, 4),
                    'Rel_Vol': round(rel_vol, 2),
                    'Price': df['Close'].iloc[-1]
                })
        except:
            continue
            
    # Sort by tightness (lower bandwidth is more explosive)
    df_res = pd.DataFrame(candidates)
    if not df_res.empty:
        df_res = df_res.sort_values('BandWidth')
        return {
            "status": "found",
            "count": len(df_res),
            "candidates": df_res.to_dict(orient='records')
        }
    
    return {"status": "none", "count": 0, "candidates": []}

def print_the_coil():
    """CLI Output Handler"""
    data = hunt_the_coil()
    
    if data['status'] == 'none':
        print("No coils found. Market is expanded.")
        return

    df_res = pd.DataFrame(data['candidates'])
    print(f"\\nFOUND {data['count']} STOCKS COILING FOR A MOVE:")
    print(df_res.head(10).to_string(index=False))
    print("\\n>> STRATEGY: Place Buy Stop above High / Sell Stop below Low.")

if __name__ == "__main__":
    print_macro_health()
    print_the_coil()
