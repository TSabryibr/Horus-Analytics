"""
MARKET REGIME MODULE
====================
Calculates the overall market health ("Regime") based on multi-timeframe breadth:
1. Long-term Breadth (% of stocks > SMA200)
2. Medium-term Breadth (% of stocks > SMA50)
3. Short-term Breadth (% of stocks > SMA20)
4. Sector Momentum Overlay

Returns: 'BULLISH', 'BEARISH', or 'NEUTRAL'
"""

import pandas as pd
import numpy as np
import logging
from core.market import MarketLists
from core.DataManager import DataManager

logger = logging.getLogger('MarketRegime')

# Periods
L_PERIOD = 200  # Long-term
M_PERIOD = 50   # Medium-term
S_PERIOD = 20   # Short-term

def calculate_market_regime():
    """
    Analyzes the market universe to determine complex regime health.
    
    Returns dict:
    {
        'regime': str,
        'score': int (0-10),
        'breadth': { '200': float, '50': float, '20': float },
        'sector_health': dict,
        'description': str
    }
    """
    # Get universe (EGX 30 is the standard benchmark)
    tickers = list(MarketLists.get_market_list("30"))
    if not tickers:
        tickers = DataManager.list_tickers()
    
    if not tickers:
        return _unknown_status("No tickers available for analysis")
    
    stats = {
        'above_200': 0, 'above_50': 0, 'above_20': 0,
        'total_valid': 0,
        'sectors': {}
    }
    
    for ticker in tickers:
        df = DataManager.get_stock_data(ticker)
        if df is None or len(df) < L_PERIOD:
            continue
            
        if 'Close' not in df.columns: continue
        
        current_price = float(df['Close'].iloc[-1])
        sma_200 = df['Close'].rolling(window=L_PERIOD).mean().iloc[-1]
        sma_50 = df['Close'].rolling(window=M_PERIOD).mean().iloc[-1]
        sma_20 = df['Close'].rolling(window=S_PERIOD).mean().iloc[-1]
        
        if pd.isna(sma_200): continue
        
        stats['total_valid'] += 1
        
        # Breadth Hits
        is_above_200 = current_price > sma_200
        is_above_50 = current_price > sma_50
        is_above_20 = current_price > sma_20
        
        if is_above_200: stats['above_200'] += 1
        if is_above_50: stats['above_50'] += 1
        if is_above_20: stats['above_20'] += 1
        
        # Sector Tracking
        sector = MarketLists.get_sector(ticker) or "Other"
        if sector not in stats['sectors']:
            stats['sectors'][sector] = {'total': 0, 'above_50': 0}
        
        stats['sectors'][sector]['total'] += 1
        if is_above_50:
            stats['sectors'][sector]['above_50'] += 1
                
    if stats['total_valid'] == 0:
         return _unknown_status("Insufficient data depth for regime calculation")
        
    # Calculate Percentages
    pct_200 = (stats['above_200'] / stats['total_valid']) * 100
    pct_50 = (stats['above_50'] / stats['total_valid']) * 100
    pct_20 = (stats['above_20'] / stats['total_valid']) * 100
    
    # Sector Momentum Calculation
    sector_momentum = {}
    for sector, s_data in stats['sectors'].items():
        s_pct = (s_data['above_50'] / s_data['total']) * 100
        sector_momentum[sector] = round(s_pct, 1)
    
    # Scoring Logic (Institutional Grade)
    # Long Term (Weight: 5)
    score = 0
    if pct_200 > 75: score += 5
    elif pct_200 > 50: score += 3
    elif pct_200 > 25: score += 1
    
    # Med Term (Weight: 3)
    if pct_50 > 75: score += 3
    elif pct_50 > 50: score += 2
    elif pct_50 > 25: score += 1
    
    # Short Term (Weight: 2)
    if pct_20 > 75: score += 2
    elif pct_20 > 50: score += 1
    
    # Determination
    if score >= 8:
        regime = "FULL BULL"
        desc = "Broad-based uptrend. Aggressive risk-on."
    elif score >= 6:
        regime = "MILD BULL"
        desc = "Advancing market. Selective buying recommended."
    elif score >= 4:
        regime = "NEUTRAL"
        desc = "Consolidating market. Wait for clarity."
    elif score >= 2:
        regime = "MILD BEAR"
        desc = "Distribution detected. Defensive positioning."
    else:
        regime = "FULL BEAR"
        desc = "Systemic downtrend. Capital preservation mode."
        
    return {
        'regime': regime,
        'score': score,
        'breadth': {
            'L_200': round(pct_200, 1),
            'M_50': round(pct_50, 1),
            'S_20': round(pct_20, 1)
        },
        'sector_momentum': sector_momentum,
        'description': desc,
        'valid_count': stats['total_valid']
    }

def _unknown_status(msg):
    return {
        'regime': 'UNKNOWN', 
        'score': 0, 
        'breadth': {'L_200': 0, 'M_50': 0, 'S_20': 0},
        'sector_momentum': {},
        'description': msg,
        'valid_count': 0
    }

if __name__ == "__main__":
    print("Calculating Institutional Market Regime...")
    res = calculate_market_regime()
    print(f"\nREGIME: {res['regime']} ({res['score']}/10)")
    print(f"Breadth: L={res['breadth']['L_200']}% | M={res['breadth']['M_50']}% | S={res['breadth']['S_20']}%")
    print(f"Advice: {res['description']}")
    print("\nSector Momentum:")
    for s, m in res['sector_momentum'].items():
        print(f"  - {s}: {m}%")
