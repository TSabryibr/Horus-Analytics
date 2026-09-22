"""
VANAHEIM (THE WHISPERER)
========================
"Price lies. Volume speaks."

The Smart Money Tracker.
Focuses on On-Balance Volume (OBV) to detect:
1. Accumulation: Price drops or remains flat while OBV rises (Bulls buying silently).
2. Distribution: Price rises while OBV drops or remains flat (Bulls selling silently).

Author: LOKI for Horus Analytics
"""

from core.settings import settings
import pandas as pd
import numpy as np
import logging
from core import DataManager, StockLoader
from core.market import MarketLists
from colorama import Fore, Style, init

init(autoreset=True)
logger = logging.getLogger(__name__)

# CONFIGURATION
DIVERGENCE_LOOKBACK = 20
MIN_LIQUIDITY = 1000000 # 1M EGP daily turnover

async def async_hunt_whales(universe=None):
    """
    Async version of hunt_whales for non-blocking backend integration.
    """
    logger.debug("Vanaheim: async scanning for whale accumulation/distribution")
    
    universe = list(universe) if universe is not None else list(MarketLists.get_market_list("ALL"))
    leads = []
    
    # Note: For strictly non-blocking, we'd want DataManager to be async.
    # For now, we use run_in_executor to avoid blocking the event loop on CPU-bound processing.
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def process_ticker(ticker):
        try:
            # We reuse the sync get_stock_data for now as it's safe in a threadpool
            df = DataManager.DataManager.get_stock_data(ticker, include_live=False)
            if df is None or len(df) < DIVERGENCE_LOOKBACK + 10: return None
            
            # ... (Rest of logic remains identical)
            avg_turnover = (df['Close'] * df['Volume']).rolling(20).mean().iloc[-1]
            if avg_turnover < MIN_LIQUIDITY: return None
            
            df['OBV'] = (np.sign(df['Close'].diff().fillna(0)) * df['Volume']).cumsum()
            price_slice = df['Close'].iloc[-DIVERGENCE_LOOKBACK:]
            obv_slice = df['OBV'].iloc[-DIVERGENCE_LOOKBACK:]
            price_slope = np.polyfit(range(DIVERGENCE_LOOKBACK), price_slice.values, 1)[0]
            obv_slope = np.polyfit(range(DIVERGENCE_LOOKBACK), obv_slice.values, 1)[0]
            
            signal = None
            if price_slope <= 0 and obv_slope > 0: signal = "ACCUMULATION"
            elif price_slope >= 0 and obv_slope < 0: signal = "DISTRIBUTION"
            
            if signal:
                price_diff_sign = np.sign(df['Close'].diff().fillna(0).iloc[-DIVERGENCE_LOOKBACK:])
                turnover_slice = (df['Close'] * df['Volume']).iloc[-DIVERGENCE_LOOKBACK:]
                net_flow = (price_diff_sign * turnover_slice).sum()
                net_flow_m = float(round(net_flow / 1_000_000, 2))
                support_anchor = float(round(df['Low'].iloc[-DIVERGENCE_LOOKBACK:].min(), settings.PRICE_PRECISION))
                resistance_anchor = float(round(df['High'].iloc[-DIVERGENCE_LOOKBACK:].max(), settings.PRICE_PRECISION))
                
                return {
                    "Ticker": ticker,
                    "Sector": MarketLists.get_sector(ticker),
                    "Last_Price": float(round(df['Close'].iloc[-1], settings.PRICE_PRECISION)),
                    "Signal": signal,
                    "Strength": float(round(abs(obv_slope), 2)),
                    "Price_Slope": float(round(price_slope, 4)),
                    "OBV_Slope": float(round(obv_slope, 4)),
                    "Flow_EGP_Millions": net_flow_m,
                    "Support_Anchor": support_anchor,
                    "Resistance_Anchor": resistance_anchor
                }
        except Exception:
            return None
        return None

    # Process in chunks to avoid overwhelming threads
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [loop.run_in_executor(executor, process_ticker, ticker) for ticker in universe]
        results = await asyncio.gather(*futures)
        leads = [r for r in results if r]

    leads.sort(key=lambda x: (x['Signal'], -abs(x['OBV_Slope'])))
    return {"status": "success", "count": len(leads), "candidates": leads}

def hunt_whales(universe=None):
    """
    Scans the market for major volume divergences using the high-performance StockLoader.
    """
    logger.debug("Vanaheim: scanning for whale accumulation/distribution")
    
    universe = list(universe) if universe is not None else list(MarketLists.get_market_list("ALL"))
    
    # Bulk Load All Stocks (Hot Cache)
    stocks = StockLoader.load_universe_calculated(tickers=universe, include_adv=False)
    
    leads = []
    for ticker, df in stocks.items():
        try:
            if len(df) < DIVERGENCE_LOOKBACK + 10: continue
            
            # Liquidity Filter
            avg_turnover = (df['Close'] * df['Volume']).rolling(20).mean().iloc[-1]
            if avg_turnover < MIN_LIQUIDITY: continue
            
            # Calculate OBV (Native Pandas) - Note: StockLoader could cache this too
            df['OBV'] = (np.sign(df['Close'].diff().fillna(0)) * df['Volume']).cumsum()
            
            # Check Trends (Slopes)
            price_slice = df['Close'].iloc[-DIVERGENCE_LOOKBACK:].values
            obv_slice = df['OBV'].iloc[-DIVERGENCE_LOOKBACK:].values
            
            # Linear Regression (Fast polyfit on small arrays)
            price_slope = np.polyfit(range(DIVERGENCE_LOOKBACK), price_slice, 1)[0]
            obv_slope = np.polyfit(range(DIVERGENCE_LOOKBACK), obv_slice, 1)[0]
            
            signal = None
            if price_slope <= 0 and obv_slope > 0:
                signal = "ACCUMULATION"
            elif price_slope >= 0 and obv_slope < 0:
                signal = "DISTRIBUTION"
            
            if signal:
                price_diff_sign = np.sign(df['Close'].diff().fillna(0).iloc[-DIVERGENCE_LOOKBACK:])
                turnover_slice = (df['Close'] * df['Volume']).iloc[-DIVERGENCE_LOOKBACK:]
                net_flow = (price_diff_sign * turnover_slice).sum()
                net_flow_m = float(round(net_flow / 1_000_000, 2))
                support_anchor = float(round(df['Low'].iloc[-DIVERGENCE_LOOKBACK:].min(), settings.PRICE_PRECISION))
                resistance_anchor = float(round(df['High'].iloc[-DIVERGENCE_LOOKBACK:].max(), settings.PRICE_PRECISION))
                
                leads.append({
                    "Ticker": ticker,
                    "Sector": MarketLists.get_sector(ticker),
                    "Last_Price": float(round(df['Close'].iloc[-1], settings.PRICE_PRECISION)),
                    "Signal": signal,
                    "Strength": float(round(abs(obv_slope), 2)),
                    "Price_Slope": float(round(price_slope, 4)),
                    "OBV_Slope": float(round(obv_slope, 4)),
                    "Flow_EGP_Millions": net_flow_m,
                    "Support_Anchor": support_anchor,
                    "Resistance_Anchor": resistance_anchor
                })
        except Exception:
            continue
            
    leads.sort(key=lambda x: (x['Signal'], -abs(x['OBV_Slope'])))
    return {"status": "success", "count": len(leads), "candidates": leads}

def print_whales():
    """CLI Output"""
    import asyncio
    try:
        data = asyncio.run(async_hunt_whales())
    except Exception:
        # Fallback if no loop
        universe = MarketLists.get_market_list("ALL")
        leads = []
        for ticker in universe:
            # Basic sync implementation if needed, but we prefer async
            pass
        return
    if not data['candidates']:
        print("No significant whale movement detected.")
        return
        
    print(f"\nVANAHEIM STRIKES ({data['count']} Leads):")
    print("-" * 60)
    for lead in data['candidates']:
        color = Fore.GREEN if lead['Signal'] == "ACCUMULATION" else Fore.RED
        print(f"{lead['Ticker']:<10} | {lead['Sector']:<20} | {color}{lead['Signal']:<15}{Fore.RESET} | Strength: {lead['Strength']}")

if __name__ == "__main__":
    print_whales()
