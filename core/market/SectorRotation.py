"""
SECTOR ROTATION MAP (THE BIFRÖST)
=================================
Tracks the flow of capital between sectors.
Identifies which sectors are outperforming the Benchmark (EGX30).

Logic:
1. Build Synthetic Sector Indices (Average performance of constituent stocks).
2. Calculate Relative Strength Ratio (Sector / EGX30).
3. Determine Rotation Phase:
   - LEADING (Ratio rising, Momentum rising)
   - WEAKENING (Ratio falling, but still high)
   - LAGGING (Ratio falling, Momentum falling)
   - IMPROVING (Ratio rising, Momentum low)

Author: LOKI for Horus Analytics
"""

import pandas as pd
import numpy as np
import logging
from core import DataManager
from core.market import MarketLists

logger = logging.getLogger(__name__)

# Sectors to track (Must match MarketLists metadata keys roughly)
SECTORS = [
    'Banks', 'Basic Resources', 'Building Materials', 'Contracting & Construction Engineering',
    'Educational Service', 'Energy & Support Services', 'Food, Beverages and Tobacco',
    'Healthcare and Pharmaceuticals', 'IT , Media & Communication Services',
    'Industrial Goods and Services and Automobiles', 'Non-bank financial services',
    'Paper & Packaging', 'Real Estate', 'Shipping & Transportation Services',
    'Textiles & Durables', 'Trade & Distribution', 'Travel & Leisure', 'Utilities'
]

BENCHMARK = 'EGX30'
LOOKBACK = 90  # Days for analysis

def _get_top_driver_for_sector(sector_name):
    all_tickers = MarketLists.get_market_list("ALL")
    sector_tickers = [t for t in all_tickers if MarketLists.get_sector(t) == sector_name]
    best_t = None
    best_adv = -1.0
    for t in sector_tickers:
        df = DataManager.DataManager.get_stock_data(t)
        if df is not None and not df.empty and 'Close' in df.columns and 'Volume' in df.columns:
            adv = float((df['Close'] * df['Volume']).iloc[-20:].mean())
            if not np.isnan(adv) and adv > best_adv:
                best_adv = adv
                best_t = t
    return best_t or (sector_tickers[0] if sector_tickers else "N/A")

def build_sector_index(sector_name):
    """
    Creates an ADV volume-weighted synthetic index for a sector.
    """
    all_tickers = MarketLists.get_market_list("ALL")
    sector_tickers = [t for t in all_tickers if MarketLists.get_sector(t) == sector_name]
    
    if len(sector_tickers) < 1:
        return None

    ret_dict = {}
    weights = {}
    
    for t in sector_tickers:
        df = DataManager.DataManager.get_stock_data(t)
        if df is not None and not df.empty and len(df) > LOOKBACK and 'Close' in df.columns:
            rets = df['Close'].pct_change(fill_method=None)
            rets = rets.replace([np.inf, -np.inf], np.nan)
            rets = rets.clip(-0.2, 0.2)
            ret_dict[t] = rets
            
            if 'Volume' in df.columns:
                adv = float((df['Close'] * df['Volume']).iloc[-20:].mean())
                weights[t] = max(adv, 1.0) if not np.isnan(adv) else 1.0
            else:
                weights[t] = 1.0

    if not ret_dict:
        return None

    sector_returns = pd.DataFrame(ret_dict)
    weight_series = pd.Series(weights)
    
    total_weight = weight_series.sum()
    if total_weight > 0:
        norm_weights = weight_series / total_weight
        avg_daily_ret = (sector_returns * norm_weights).sum(axis=1, min_count=1).fillna(0)
    else:
        avg_daily_ret = sector_returns.mean(axis=1).fillna(0)

    avg_daily_ret = avg_daily_ret.clip(-0.2, 0.2)
    sector_index = (1 + avg_daily_ret).cumprod() * 100
    return sector_index.iloc[-LOOKBACK:]

def analyze_rotation(trail_days=10):
    """
    Analyzes Sector Rotation and returns current state + historical trail + velocity + top driver.
    """
    logger.debug("SectorRotation: mapping sector-level capital flow")
    
    # 1. Get Benchmark Data
    bench_df = DataManager.DataManager.get_stock_data(BENCHMARK)
    if bench_df is None: return []
        
    bench_close = bench_df['Close'].iloc[-(LOOKBACK + trail_days):]
    if bench_close.empty or bench_close.iloc[0] == 0: return []
    
    # Pre-normalize bench to 100 at start of analysis window
    bench_index = (bench_close / bench_close.iloc[0]) * 100
    
    rotation_data = []
    
    # 2. Analyze Each Sector
    for sector in SECTORS:
        try:
            sec_idx = build_sector_index(sector)
            if sec_idx is None: continue
            
            # Align dates
            common_idx = bench_index.index.intersection(sec_idx.index)
            if len(common_idx) < 30: continue
            
            b_aligned = bench_index.loc[common_idx]
            s_aligned = sec_idx.loc[common_idx]
            
            # Re-normalize sector index to match benchmark start
            s_aligned = (s_aligned / s_aligned.iloc[0]) * 100
            
            # Calculate RS Ratio
            rs_ratio = s_aligned / b_aligned.replace(0, np.nan)
            rs_ratio = rs_ratio.dropna()
            
            if len(rs_ratio) < trail_days + 15: continue
            
            # Calculate Trail
            trail = []
            for i in range(trail_days, -1, -1):
                idx_offset = len(rs_ratio) - 1 - i
                if idx_offset < 20: continue
                
                current_rs = rs_ratio.iloc[idx_offset]
                
                y_slice = rs_ratio.iloc[idx_offset-19 : idx_offset+1].values
                x_slice = np.arange(len(y_slice))
                slope, _ = np.polyfit(x_slice, y_slice, 1)
                
                strength = (current_rs - 1.0) * 100
                momentum = slope * 1000
                
                trail.append({'x': round(float(momentum), 2), 'y': round(float(strength), 2)})

            if not trail: continue
            
            latest = trail[-1]
            status = "LAGGING"
            if latest['x'] > 0 and latest['y'] > 0: status = "LEADING"
            elif latest['x'] < 0 and latest['y'] > 0: status = "WEAKENING" 
            elif latest['x'] > 0 and latest['y'] < 0: status = "IMPROVING"
            elif latest['x'] < 0 and latest['y'] < 0: status = "LAGGING"
            
            p_start = trail[-min(5, len(trail))]
            dx = latest['x'] - p_start['x']
            dy = latest['y'] - p_start['y']
            velocity = float(round(float(np.sqrt(dx*dx + dy*dy)), 2))
            top_driver = _get_top_driver_for_sector(sector)

            rotation_data.append({
                'Sector': sector,
                'Status': status,
                'x': latest['x'],
                'y': latest['y'],
                'trail': trail,
                'Velocity': velocity,
                'TopDriver': top_driver,
            })
            
        except Exception:
            continue

    return rotation_data

async def async_analyze_rotation(trail_days=10):
    """
    Async version of analyze_rotation.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    # Run the heavy computation in a thread pool to avoid blocking the event loop
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        return await loop.run_in_executor(executor, analyze_rotation, trail_days)

def analyze_stock_rotation(view_mode="ALL", sector_name=None, trail_days=10):
    """
    Analyzes individual stock rotation vs Benchmark.
    """
    logger.debug("SectorRotation: mapping stock RRG mode=%s sector=%s", view_mode, sector_name)
    
    # 1. Get Tickers
    if view_mode == "SECTOR" and sector_name:
        all_t = MarketLists.get_market_list("ALL")
        tickers = [t for t in all_t if MarketLists.get_sector(t) == sector_name]
    elif view_mode == "WATCHLIST":
        # Placeholder for user watchlist if implemented, otherwise use a subset
        tickers = MarketLists.get_market_list("EGX30")
    else:
        # For ALL, we use EGX100 to avoid overwhelming the chart
        tickers = MarketLists.get_market_list("EGX100")

    bench_df = DataManager.DataManager.get_stock_data(BENCHMARK)
    if bench_df is None: return []
    bench_close = bench_df['Close'].iloc[-(LOOKBACK + trail_days):]
    bench_index = (bench_close / bench_close.iloc[0]) * 100

    results = []
    
    for t in tickers:
        try:
            df = DataManager.DataManager.get_stock_data(t)
            if df is None or len(df) < LOOKBACK: continue
            
            s_close = df['Close'].iloc[-(LOOKBACK + trail_days):]
            common_idx = bench_index.index.intersection(s_close.index)
            if len(common_idx) < 30: continue
            
            b_aligned = bench_index.loc[common_idx]
            s_aligned = (s_close.loc[common_idx] / s_close.loc[common_idx].iloc[0]) * 100
            
            rs_ratio = s_aligned / b_aligned.replace(0, np.nan)
            rs_ratio = rs_ratio.dropna()
            
            if len(rs_ratio) < trail_days + 15: continue
            
            trail = []
            for i in range(trail_days, -1, -1):
                idx_offset = len(rs_ratio) - 1 - i
                if idx_offset < 15: continue
                
                # Momentum (10 day for stocks - more responsive)
                y_slice = rs_ratio.iloc[idx_offset-9 : idx_offset+1].values
                x_slice = np.arange(len(y_slice))
                slope, _ = np.polyfit(x_slice, y_slice, 1)
                
                strength = (rs_ratio.iloc[idx_offset] - 1.0) * 100
                momentum = slope * 2000 # Higher scale for stocks
                
                trail.append({'x': round(float(momentum), 2), 'y': round(float(strength), 2)})

            if not trail: continue
            latest = trail[-1]
            status = "LAGGING"
            if latest['x'] > 0 and latest['y'] > 0: status = "LEADING"
            elif latest['x'] < 0 and latest['y'] > 0: status = "WEAKENING" 
            elif latest['x'] > 0 and latest['y'] < 0: status = "IMPROVING"
            else: status = "LAGGING"

            p_start = trail[-min(5, len(trail))]
            dx = latest['x'] - p_start['x']
            dy = latest['y'] - p_start['y']
            velocity = float(round(float(np.sqrt(dx*dx + dy*dy)), 2))

            results.append({
                'ticker': t,
                'Sector': MarketLists.get_sector(t),
                'Status': status,
                'x': latest['x'],
                'y': latest['y'],
                'trail': trail,
                'Velocity': velocity,
                'TopDriver': t,
            })
        except Exception:
            continue
        
    return results

def print_rotation_map():
    """CLI Output Handler"""
    data = analyze_rotation()
    if not data:
        print("Could not generate rotation map.")
        return

    df_rot = pd.DataFrame(data)
    print(f"\\n🌍 SECTOR ROTATION MATRIX (vs {BENCHMARK}):")
    print("=" * 60)
    print(df_rot.to_string(index=False))
    
    print("\\n>> TACTICAL ADVICE:")
    leaders = df_rot[df_rot['Status'].str.contains("LEADING")]['Sector'].tolist()
    improvers = df_rot[df_rot['Status'].str.contains("IMPROVING")]['Sector'].tolist()
    
    if leaders:
        print(f"🔥 ATTACK: Focus long positions in {', '.join(leaders)}.")
    if improvers:
        print(f"👀 WATCH: Look for entries in {', '.join(improvers)} (Turning around).")
    print(f"⛔ AVOID: Sectors marked LAGGING are dead money.")

if __name__ == "__main__":
    print_rotation_map()
