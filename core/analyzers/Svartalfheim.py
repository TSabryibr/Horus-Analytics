"""
SVARTALFHEIM (THE TRAP HUNTER)
==============================
"The wound that never heals."

Detects False Breakouts (Bull Traps) and False Breakdowns (Bear Traps).
These are the most powerful reversal signals in the market.

Logic:
1. Identify Key Swing Levels (Support/Resistance).
2. Watch for a breach of these levels.
3. Confirm if the breach failed (Price closed back inside the range).
4. Signal the violent reversal.

Author: LOKI for Horus Analytics
"""

import pandas as pd
import numpy as np
import logging
from core import DataManager
from core.market import MarketLists
from colorama import Fore, Style, init

init(autoreset=True)
logger = logging.getLogger(__name__)

# CONFIGURATION
LOOKBACK = 20           # Days to look for Swing Highs/Lows
TRAP_WINDOW = 3         # How recent must the trap be? (Last 3 days)
MIN_VOL_FACTOR = 1.2    # Volume must be 1.2x average to confirm the trap (Effort vs Result)

def detect_fractals(df):
    """
    Identifies Swing Highs and Lows (Fractals).
    """
    # Simple Donchian Channel / Rolling Max approach for robustness
    df['Swing_High'] = df['High'].rolling(LOOKBACK).max().shift(1)
    df['Swing_Low'] = df['Low'].rolling(LOOKBACK).min().shift(1)
    return df

def _process_ticker(t):
    try:
        df = DataManager.DataManager.get_stock_data(t, include_live=False)
        if df is None or len(df) < LOOKBACK + 5: return None
        
        # Liquidity Check (Skip dead stocks)
        if (df['Close'] * df['Volume']).iloc[-1] < 500000: return None
        
        # 1. Map the Battlefield (Levels)
        df = detect_fractals(df)
        df['Avg_Vol'] = df['Volume'].rolling(20).mean()
        
        # Check the last few days for a trap
        recent_slice = df.iloc[-TRAP_WINDOW:]
        ticker_traps = []
        
        for date, row in recent_slice.iterrows():
            signal = None
            details = ""
            wick_ratio = 0.0
            candle_range = max(row['High'] - row['Low'], 0.0001)
            
            # === PATTERN 1: THE BULL TRAP (The Slaughter of Greed) ===
            if (row['High'] > row['Swing_High']) and (row['Close'] < row['Swing_High']):
                upper_wick = row['High'] - max(row['Open'], row['Close'])
                wick_ratio = upper_wick / candle_range
                if row['Volume'] > row['Avg_Vol'] * MIN_VOL_FACTOR and wick_ratio >= 0.30:
                    signal = "BULL TRAP (SELL)"
                    details = f"Failed break of {row['Swing_High']:.2f} (Wick: {int(wick_ratio*100)}%)"
            
            # === PATTERN 2: THE BEAR TRAP (The Slaughter of Fear) ===
            elif (row['Low'] < row['Swing_Low']) and (row['Close'] > row['Swing_Low']):
                lower_wick = min(row['Open'], row['Close']) - row['Low']
                wick_ratio = lower_wick / candle_range
                if row['Volume'] > row['Avg_Vol'] * MIN_VOL_FACTOR and wick_ratio >= 0.30:
                    signal = "BEAR TRAP (BUY)"
                    details = f"Failed break of {row['Swing_Low']:.2f} (Wick: {int(wick_ratio*100)}%)"
            
            if signal:
                if "BULL" in signal:
                    fakeout_pct = (row['High'] - row['Swing_High']) / row['Swing_High'] * 100
                else:
                    fakeout_pct = (row['Swing_Low'] - row['Low']) / row['Swing_Low'] * 100
                    
                ticker_traps.append({
                    'Ticker': t,
                    'Date': date.strftime('%Y-%m-%d'),
                    'Signal': signal,
                    'Price': float(row['Close']),
                    'Fakeout_Depth_%': round(fakeout_pct, 2),
                    'Wick_Ratio_%': round(wick_ratio * 100, 1),
                    'Details': details
                })
        return ticker_traps
    except Exception as e:
        logger.error(f"Error analyzing {t} for traps: {e}")
        return None

def hunt_traps(universe=None):
    logger.debug("Svartalfheim: scanning for bull/bear traps (parallel)")
    from concurrent.futures import ThreadPoolExecutor
    
    tickers = list(universe) if universe is not None else list(MarketLists.get_market_list("ALL"))
    traps = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(_process_ticker, tickers)
        for res in results:
            if res:
                traps.extend(res)

            
    # Report Results
    if not traps:
        return {"status": "none", "bull_traps": [], "bear_traps": []}
        
    df_res = pd.DataFrame(traps)
    
    # Sort by Recency and Depth of the fakeout
    df_res = df_res.sort_values(['Date', 'Fakeout_Depth_%'], ascending=[False, False])
    
    bull_traps = df_res[df_res['Signal'].str.contains("BULL")]
    bear_traps = df_res[df_res['Signal'].str.contains("BEAR")]
    
    return {
         "status": "found",
         "bull_traps": bull_traps.to_dict(orient='records'),
         "bear_traps": bear_traps.to_dict(orient='records')
    }

async def async_hunt_traps():
    """
    Async version of hunt_traps for non-blocking backend.
    """
    import asyncio
    # Since hunt_traps already uses ThreadPoolExecutor internally, we just wrap it
    return await asyncio.to_thread(hunt_traps)

def print_traps(data):
    """CLI Output Handler"""
    
    if data['status'] == "none":
        print(Fore.YELLOW + "The market is honest today. No traps detected.")
        return

    print(Fore.CYAN + "\n[!] LÆVATEINN STRIKES (Traps Detected):")
    print(Fore.RED + "=" * 80)
    
    if data['bull_traps']:
        df_bull = pd.DataFrame(data['bull_traps'])
        print(Fore.MAGENTA + "\n[!] BULL TRAPS (Fake Breakouts - Short/Exit Now):")
        print(Fore.WHITE + df_bull[['Ticker', 'Date', 'Price', 'Fakeout_Depth_%', 'Details']].to_string(index=False))
        
    if data['bear_traps']:
        df_bear = pd.DataFrame(data['bear_traps'])
        print(Fore.GREEN + "\n[!] BEAR TRAPS (Springboards - Buy Aggressively):")
        print(Fore.WHITE + df_bear[['Ticker', 'Date', 'Price', 'Fakeout_Depth_%', 'Details']].to_string(index=False))
        
    print(Fore.RED + "=" * 80)
    print(Fore.YELLOW + ">> STRATEGY: A Bear Trap is the highest probability 'Buy' signal in existence.")
    print(Fore.YELLOW + ">> STRATEGY: A Bull Trap means the trend is dead. Cut losses.")

if __name__ == "__main__":
    import sys
    try:
        # Use getattr to satisfy linters and handle environments without reconfigure
        reconfig = getattr(sys.stdout, 'reconfigure', None)
        if reconfig:
            reconfig(encoding='utf-8')
    except (AttributeError, Exception):
        pass

    print("\n[!] SVARTALFHEIM: SCANNING FOR BULL/BEAR TRAPS...")
    print("=" * 60)
    
    results = hunt_traps()
    print_traps(results)
