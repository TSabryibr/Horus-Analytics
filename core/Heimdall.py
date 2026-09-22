"""
HEIMDALL (THE GUARDIAN)
=======================
"I can hear the grass grow. I can hear the wool grow on a sheep."

The Portfolio Health Check.
1. Hidden Crashes (Stress Test)
2. Hidden Accumulation/Distribution (Whale Check)
3. Traps (Fakeouts)
4. Squeezes (Explosions)

Refactored from PortfolioGuardian.py.
"""

import pandas as pd
import numpy as np
import database
from colorama import Fore, Style, init

init(autoreset=True)

# LEGACY CONSTANTS (For ChitauriScepter)
CURRENT_REALM = "EGX"

def get_active_realm():
    """Returns the current active realm metadata for legacy CLI."""
    return {
        "ID": 12,
        "NAME": "HEIMDALL (THE GUARDIAN)",
        "SYMBOL": "🛡️",
        "COLOR": Fore.YELLOW
    }


def get_portfolio_tickers():
    """Fetches unique tickers from open positions in the database."""
    from core import TimeUtils
    try:
        # Time Travel Filter: Only see positions entered ON OR BEFORE "now"
        positions = database.Position.select(database.Position.ticker).where(
            (database.Position.status == "OPEN") &
            (database.Position.entry_date <= TimeUtils.now())
        ).distinct()
        return [p.ticker for p in positions]
    except Exception as e:
        return []

def diagnose_stock(ticker):
    """
    Runs a full diagnostic suite on a single stock.
    Returns a dict with all signals.
    """
    from core import DataManager
    df = DataManager.DataManager.get_stock_data(ticker)
    if df is None or len(df) < 100:
        return {"status": "error", "message": "Insufficient Data"}

    last_price = float(df['Close'].iloc[-1])
    results = {
        "ticker": ticker,
        "price": last_price,
        "whale_activity": "NEUTRAL",
        "volatility_status": "NORMAL",
        "trap_status": "NONE",
        "crash_risk_pct": 0.0,
        "signals": []
    }

    # === TEST 1: THE WHISPERER (Smart Money) ===
    # Check OBV Divergence (Native implementation to avoid ta overhead)
    # OBV = Cumulative sum of (sign(price_change) * volume)
    price_change = df['Close'].diff()
    df['OBV'] = (np.sign(price_change) * df['Volume']).fillna(0).cumsum()
    
    recent_price = df['Close'].iloc[-20:].values
    recent_obv = df['OBV'].iloc[-20:].values
    
    # We use np.polyfit for slope calculation as it is already vectorized and efficient
    price_slope = np.polyfit(range(20), recent_price, 1)[0]
    obv_slope = np.polyfit(range(20), recent_obv, 1)[0]
    
    if price_slope < 0 and obv_slope > 0:
        results["whale_activity"] = "ACCUMULATION"
        results["signals"].append("Whale Accumulation (Bullish Divergence)")
    elif price_slope > 0 and obv_slope < 0:
        results["whale_activity"] = "DISTRIBUTION"
        results["signals"].append("Whale Distribution (Bearish Divergence)")
    elif price_slope > 0 and obv_slope > 0:
        results["whale_activity"] = "HEALTHY_UP"
    elif price_slope < 0 and obv_slope < 0:
        results["whale_activity"] = "HEALTHY_DOWN"

    # === TEST 2: THE COIL (Volatility) ===
    # Native Bollinger Bandwidth calculation
    rolling_mean = df['Close'].rolling(window=20).mean()
    rolling_std = df['Close'].rolling(window=20).std()
    ubb = rolling_mean + (2.0 * rolling_std)
    lbb = rolling_mean - (2.0 * rolling_std)
    
    # Bandwidth = (Upper - Lower) / Middle
    bw = (ubb - lbb) / rolling_mean
    current_bw = bw.iloc[-1]
    # We look for the 120-period minimum bandwidth to identify a "squeeze" relative to local history
    min_bw = bw.rolling(120).min().iloc[-1]
    
    if pd.notna(current_bw) and pd.notna(min_bw):
        if current_bw <= min_bw * 1.1:
            results["volatility_status"] = "SQUEEZE"
            results["signals"].append("Volatility Squeeze (Potential Explosion)")

    # === TEST 3: LAEVATEINN (Traps) ===
    recent = df.iloc[-3:]
    swing_high = df['High'].rolling(20).max().shift(1)
    swing_low = df['Low'].rolling(20).min().shift(1)
    
    for idx, row in recent.iterrows():
        sh = swing_high.loc[idx]
        sl = swing_low.loc[idx]
        
        if row['High'] > sh and row['Close'] < sh:
            results["trap_status"] = "BULL_TRAP"
            results["signals"].append(f"Bull Trap detected on {idx.strftime('%Y-%m-%d')}")
        elif row['Low'] < sl and row['Close'] > sl:
            results["trap_status"] = "BEAR_TRAP"
            results["signals"].append(f"Bear Trap detected on {idx.strftime('%Y-%m-%d')}")

    # === TEST 4: STRESS TEST (Crash Sim) ===
    worst_drop = df['Close'].pct_change().rolling(30).min().iloc[-1] * 100
    if pd.isna(worst_drop):
        results["crash_risk_pct"] = 0.0
    else:
        results["crash_risk_pct"] = float(round(worst_drop, 2))

    return results

def get_portfolio_health():
    """
    Runs diagnosis on the entire portfolio using the high-performance StockLoader.
    """
    tickers = get_portfolio_tickers()
    if not tickers:
        return {"status": "none", "diagnoses": []}

    # Bulk Load with StockLoader (Hot Cache)
    from core import StockLoader
    stocks = StockLoader.load_universe_calculated(tickers=tickers, include_adv=False)
    
    diagnoses = []
    for t in tickers:
        if t not in stocks:
            continue
        try:
            # Re-use the individual diagnose_stock but we could vectorize further
            diag = diagnose_stock_optimized(t, stocks[t])
            diagnoses.append(diag)
        except Exception:
            continue
            
    return {
        "status": "success",
        "count": len(diagnoses),
        "diagnoses": diagnoses
    }

def diagnose_stock_optimized(ticker, df):
    """
    Diagnostic suite using a pre-loaded DataFrame.
    """
    last_price = float(df['Close'].iloc[-1])
    results = {
        "ticker": ticker,
        "price": last_price,
        "whale_activity": "NEUTRAL",
        "volatility_status": "NORMAL",
        "trap_status": "NONE",
        "crash_risk_pct": 0.0,
        "signals": []
    }

    # Calculations on the existing DF
    price_change = df['Close'].diff()
    df['OBV'] = (np.sign(price_change) * df['Volume']).fillna(0).cumsum()
    
    recent_price = df['Close'].iloc[-20:].values
    recent_obv = df['OBV'].iloc[-20:].values
    price_slope = np.polyfit(range(20), recent_price, 1)[0]
    obv_slope = np.polyfit(range(20), recent_obv, 1)[0]
    
    if price_slope < 0 and obv_slope > 0:
        results["whale_activity"] = "ACCUMULATION"
    elif price_slope > 0 and obv_slope < 0:
        results["whale_activity"] = "DISTRIBUTION"

    # Bollinger Bandwidth
    rolling_mean = df['Close'].rolling(window=20).mean()
    rolling_std = df['Close'].rolling(window=20).std()
    ubb = rolling_mean + (2.0 * rolling_std)
    lbb = rolling_mean - (2.0 * rolling_std)
    bw = (ubb - lbb) / rolling_mean
    current_bw = bw.iloc[-1]
    min_bw = bw.rolling(120).min().iloc[-1]
    
    if pd.notna(current_bw) and pd.notna(min_bw) and current_bw <= min_bw * 1.1:
        results["volatility_status"] = "SQUEEZE"

    # Traps
    recent = df.iloc[-3:]
    swing_high = df['High'].rolling(20).max().shift(1)
    swing_low = df['Low'].rolling(20).min().shift(1)
    
    for idx, row in recent.iterrows():
        sh = swing_high.loc[idx]
        sl = swing_low.loc[idx]
        if row['High'] > sh and row['Close'] < sh:
            results["trap_status"] = "BULL_TRAP"
        elif row['Low'] < sl and row['Close'] > sl:
            results["trap_status"] = "BEAR_TRAP"

    results["crash_risk_pct"] = float(round(df['Close'].pct_change().rolling(30).min().iloc[-1] * 100, 2))
    return results

# === CLI ADAPTER ===
def run_heimdall_cli():
    print(Fore.YELLOW + Style.BRIGHT + "🛡️  HEIMDALL'S SIGHT (PORTFOLIO DIAGNOSIS)")
    print(Fore.YELLOW + "=" * 50)
    
    data = get_portfolio_health()
    if data['status'] == "none":
        print(Fore.YELLOW + "   No active holdings found in database.")
        return

    for d in data['diagnoses']:
        print(Fore.CYAN + f"\n🔍 DIAGNOSING: {d['ticker']}...")
        print(Fore.WHITE + f"   Price: {d['price']:.2f}")
        
        whale_color = Fore.GREEN if "ACCUMULATION" in d['whale_activity'] else (Fore.RED if "DISTRIBUTION" in d['whale_activity'] else Fore.WHITE)
        print(f"   🐋 Whale Activity: {whale_color}{d['whale_activity']}")
        
        vol_color = Fore.YELLOW if d['volatility_status'] == "SQUEEZE" else Fore.WHITE
        print(f"   🐍 Volatility: {vol_color}{d['volatility_status']}")
        
        trap_color = Fore.MAGENTA if "BULL" in d['trap_status'] else (Fore.GREEN if "BEAR" in d['trap_status'] else Fore.WHITE)
        print(f"   ⚔️  Traps: {trap_color}{d['trap_status']}")
        
        print(f"   💀 Crash Risk: {Fore.RED}{d['crash_risk_pct']}%")
        
        if d['signals']:
            print(Fore.YELLOW + "   📡 ALERT SIGNALS:")
            for s in d['signals']:
                print(f"      - {s}")
        print(Fore.CYAN + "-" * 40)

if __name__ == "__main__":
    run_heimdall_cli()
