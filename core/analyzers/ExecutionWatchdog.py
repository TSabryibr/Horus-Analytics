"""
FENRIR (THE UNBOUND)
====================
"The chains are broken. The laws are rewritten."

Dynamic Strategy Adapter.
Automatically adjusts global trading parameters (Stop Loss, TP, RSI, Risk)
based on the current Market Regime and Volatility.

Logic:
- BULL REGIME: Widen Stops (let runners run), Aggressive Entries, High Risk.
- BEAR REGIME: Tight Stops (protect capital), Deep Value Entries only, Low Risk.
- CHOP (SIDEWAYS): Quick Profit Taking (Scalp mode), Moderate Risk.

Author: LOKI for Horus Analytics
"""

from core.settings import settings
import pandas as pd
import numpy as np
from core import DataManager
from core.market import MarketRegime
from colorama import Fore, Style, init

init(autoreset=True)

# CONFIGURATION
BENCHMARK_TICKER = "EGX30"

def get_market_volatility(ticker=BENCHMARK_TICKER):
    """
    Calculates the current 'Temperature' of the market (ATR %).
    """
    df = DataManager.DataManager.get_stock_data(ticker)
    if df is None or len(df) < 20: return 1.5, 1.5 # Adjusted to return two values
    
    # Calculate ATR % (Average True Range as % of price) (Native Pandas)
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift()).abs()
    tr3 = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
    df['ATR_Pct'] = (df['ATR'] / df['Close']) * 100
    
    current_vol = df['ATR_Pct'].iloc[-1]
    avg_vol = df['ATR_Pct'].rolling(60).mean().iloc[-1]
    
    return current_vol, avg_vol

def generate_strategy_proposal():
    """
    Analyzes the market and returns a proposed strategy.
    """
    # 1. Get The Terrain (Regime)
    regime_data = MarketRegime.calculate_market_regime()
    regime = regime_data['regime']
    score = regime_data['score']
    
    # 2. Get The Weather (Volatility)
    curr_vol, avg_vol = get_market_volatility()
    vol_status = "NORMAL"
    if curr_vol > avg_vol * 1.5: vol_status = "HIGH (Stormy)"
    elif curr_vol < avg_vol * 0.7: vol_status = "LOW (Calm)"
    
    # 3. Rewrite The Laws (Adapt Parameters)
    new_settings = {}
    adaptation_reason = ""
    
    # === SCENARIO A: THE BULL RUN (Risk On) ===
    if "BULL" in regime:
        adaptation_reason = "BULL MARKET DETECTED. MAXIMIZING AGGRESSION."
        new_settings['SL_PCT'] = max(3.0, curr_vol * 2.0)
        new_settings['TP1_PCT'] = max(6.0, curr_vol * 4.0)
        new_settings['RSI_MIN'] = 40
        new_settings['RSI_MAX'] = 85
        new_settings['RISK_PER_TRADE'] = 2.0
        new_settings['TRAILING_STOP_ENABLED'] = True
        
    # === SCENARIO B: THE BEAR WINTER (Risk Off) ===
    elif "BEAR" in regime:
        adaptation_reason = "BEAR MARKET DETECTED. SHIELDS UP."
        new_settings['SL_PCT'] = min(1.5, curr_vol * 1.0)
        new_settings['TP1_PCT'] = 3.0
        new_settings['RSI_MIN'] = 25
        new_settings['RSI_MAX'] = 60
        new_settings['RISK_PER_TRADE'] = 0.5
        new_settings['TRAILING_STOP_ENABLED'] = False
        
    # === SCENARIO C: THE CHOP (Guerrilla Warfare) ===
    else: 
        adaptation_reason = "UNCERTAINTY DETECTED. SCALPING MODE."
        new_settings['SL_PCT'] = 2.0
        new_settings['TP1_PCT'] = 4.0
        new_settings['RSI_MIN'] = 30
        new_settings['RSI_MAX'] = 75
        new_settings['RISK_PER_TRADE'] = 1.0
        new_settings['TRAILING_STOP_ENABLED'] = False
        
    # Adjust for High Volatility
    if "HIGH" in vol_status:
        new_settings['SL_PCT'] *= 1.2
        new_settings['RISK_PER_TRADE'] *= 0.8
        adaptation_reason += " + VOLATILITY ADJUSTMENT."

    # Compare with current settings
    changes = []
    params_to_check = ['SL_PCT', 'TP1_PCT', 'RSI_MIN', 'RISK_PER_TRADE']
    
    for p in params_to_check:
        old_val = getattr(settings, p, 0)
        new_val = new_settings.get(p, 0)
        
        changes.append({
            "parameter": p,
            "old_value": float(round(old_val, 2)),
            "new_value": float(round(new_val, 2)),
            "changed": bool(old_val != new_val)
        })

    # 4. Global Risk Engine (Phase 1)
    kelly_fraction = settings.calculate_kelly_size(win_rate=0.55, win_loss_ratio=1.8) # Mock stats for now
    
    return {
        "regime": str(regime),
        "regime_score": int(score),
        "volatility": str(vol_status),
        "volatility_value": float(round(curr_vol, 2)),
        "reasoning": str(adaptation_reason),
        "risk_engine": {
            "kelly_fraction_suggested": float(round(kelly_fraction, 4)),
            "volatility_target_adjustment": float(round(1.0 / (curr_vol / avg_vol), 2)) if avg_vol > 0 else 1.0,
            "portfolio_heat_limit": "Institutional (Safe)" if curr_vol > avg_vol else "Aggressive"
        },
        "proposed_settings": {k: float(v) if isinstance(v, (int, float)) else v for k, v in new_settings.items()},
        "changes": changes
    }

async def async_generate_strategy_proposal():
    """
    Async version of generate_strategy_proposal.
    """
    import asyncio
    return await asyncio.to_thread(generate_strategy_proposal)

def apply_strategy(proposal):
    """
    Applies the proposed settings to 
    """
    new_settings = proposal['proposed_settings']
    settings.SL_PCT = new_settings['SL_PCT']
    settings.TP1_PCT = new_settings['TP1_PCT']
    settings.RSI_MIN = new_settings['RSI_MIN']
    settings.RSI_MAX = new_settings['RSI_MAX']
    settings.RISK_PER_TRADE = new_settings['RISK_PER_TRADE']
    settings.TRAILING_STOP_ENABLED = new_settings['TRAILING_STOP_ENABLED']
    
    # Save to file
    settings.save_settings("fenrir_optimized")
    return True

def print_fenrir_adaptation():
    """CLI Output Handler"""
    print(Fore.RED + Style.BRIGHT + "\\n🐺 FENRIR IS AWAKE. SNIFFING THE AIR...")
    
    proposal = generate_strategy_proposal()
    
    print(Fore.WHITE + f"  Market Regime: {Fore.YELLOW}{proposal['regime']} (Score: {proposal['regime_score']}/10)")
    print(Fore.WHITE + f"  Volatility:    {Fore.YELLOW}{proposal['volatility']} ({proposal['volatility_value']}%)")
    
    print(Fore.CYAN + "\\n🧬 FENRIR'S ADAPTATION:")
    print(Fore.CYAN + "=" * 50)
    print(f"STRATEGY: {proposal['reasoning']}")
    print("-" * 50)
    print(f"{'PARAMETER':<20} {'OLD LAW':<10} {'NEW LAW':<10}")
    print("-" * 50)
    
    for c in proposal['changes']:
        color = Fore.GREEN if c['changed'] else Fore.WHITE
        print(f"{c['parameter']:<20} {c['old_value']:<10} {color}{c['new_value']:<10}")
        
    print(Fore.CYAN + "=" * 50)
    
    confirm = input(Fore.YELLOW + "Shall ExecutionWatchdog break the chains and apply these laws? (Y/N): ").strip().upper()
    
    if confirm == 'Y':
        apply_strategy(proposal)
        print(Fore.GREEN + "\\n⚡ DONE. The system has shapeshifted. The hunt begins.")
    else:
        print(Fore.WHITE + "\\nFenrir sleeps. The old laws remain.")

if __name__ == "__main__":
    print_fenrir_adaptation()
