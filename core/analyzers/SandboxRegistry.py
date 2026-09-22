"""
JOTUNHEIM (THE MIRROR)
======================
"Why guess the future when you can watch the echo?"

Finds pairs of stocks where one acts as a LEADER and the other as a FOLLOWER.
Identifies lagged correlations (e.g., Stock A moves, Stock B follows X days later).

Refactored from TheMirror.py for God Mode.
"""

from core.exclusions import EXCLUDED_TICKERS
import pandas as pd # type: ignore
import numpy as np # type: ignore
from core import DataManager  # type: ignore
from core.market import MarketLists # type: ignore
from itertools import combinations
from colorama import Fore, Style, init # type: ignore
from typing import List, Dict, Any, Optional, Set, Tuple

init(autoreset=True)

# CONFIGURATION
UNIVERSE_SIZE = 60   # Increased slightly
MAX_LAG = 3          # Look for delays up to 3 days
MIN_CORR = 0.35      # Lowered to capture subtle leads
MIN_LIQUIDITY = 500000 # Lowered from 1.5M

_UNIVERSE_MODE_LABELS = {
    "default": "EGX100 default universe",
    "extended": "extended market universe",
}


def normalize_universe_mode(universe: Optional[str] = None) -> str:
    raw = str(universe or "default").strip().lower()
    aliases = {
        "default": "default",
        "egx100": "default",
        "100": "default",
        "core": "default",
        "extended": "extended",
        "all": "extended",
        "market": "extended",
    }
    return aliases.get(raw, "default")


def _load_universe_tickers(universe: Optional[str] = None) -> List[str]:
    universe_mode = normalize_universe_mode(universe)
    if universe_mode == "extended":
        tickers = DataManager.DataManager.list_tickers() or []
        excluded = {str(t).upper() for t in EXCLUDED_TICKERS}
        filtered = [
            t for t in tickers
            if str(t).upper() not in excluded and str(t).upper() not in {"REPORT", "EGX30_70_100"}
        ]
        return list(dict.fromkeys(filtered))
    return list(MarketLists.get_market_list("100"))

def get_top_liquid_stocks(limit: int = 40, universe: Optional[str] = None) -> List[str]:
    universe_mode = normalize_universe_mode(universe)
    tickers: List[str] = _load_universe_tickers(universe_mode)
    scored_tickers: List[Tuple[str, float]] = []
    
    universe_label = _UNIVERSE_MODE_LABELS[universe_mode]
    print(f"[SandboxRegistry] Scoring {len(tickers)} tickers for liquidity ({universe_label})...")
    for i, t in enumerate(tickers):
        if i % 50 == 0 and i > 0:
            print(f"  ... processed {i}/{len(tickers)} ...")
        try:
            df: Optional[pd.DataFrame] = DataManager.DataManager.get_stock_data(t)
            if df is None:
                # print(f"[SandboxRegistry] {t} data is None")
                continue
            if len(df) < 100:
                # print(f"[SandboxRegistry] {t} data insufficient ({len(df)} days)")
                continue
            
            # Use safe turnover calculation
            close = float(df['Close'].iloc[-1])
            vol = float(df['Volume'].iloc[-1])
            turnover = float((df['Close'] * df['Volume']).rolling(20).mean().iloc[-1])
            
            if turnover > MIN_LIQUIDITY:
                scored_tickers.append((t, turnover))
        except Exception as e:
            # print(f"[SandboxRegistry] Error scoring {t}: {e}")
            continue
            
    scored_tickers.sort(key=lambda x: x[1], reverse=True)
    if not scored_tickers:
        print("[SandboxRegistry] No stocks passed liquidity threshold. Reducing threshold...")
        # Emergency fallback to get at least something
        for t in tickers[:10]: # type: ignore
             scored_tickers.append((t, 0.0))
             
    return [x[0] for x in scored_tickers[:limit]] # type: ignore

def _compute_stock_atr_brackets(ticker: str) -> Tuple[float, float]:
    """
    Computes stock-specific ATR_14 SL (-1.5x ATR%) and TP (+2.5x ATR%) bounds.
    """
    df = DataManager.DataManager.get_stock_data(ticker)
    if df is not None and not df.empty and len(df) >= 14 and 'High' in df.columns and 'Low' in df.columns and 'Close' in df.columns:
        high = df['High']
        low = df['Low']
        close = df['Close']
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr14 = float(tr.rolling(14).mean().iloc[-1])
        last_close = float(close.iloc[-1])
        if last_close > 0 and not np.isnan(atr14):
            atr_pct = (atr14 / last_close) * 100
            sl_pct = float(round(max(0.5, min(10.0, 1.5 * atr_pct)), 2))
            tp_pct = float(round(max(1.0, min(20.0, 2.5 * atr_pct)), 2))
            return sl_pct, tp_pct
    return 1.5, 2.5

def get_lagged_correlations(universe: Optional[str] = None) -> Dict[str, Any]:
    """
    Scans the market for echoes. Returns structured data for API.
    """
    universe_mode = normalize_universe_mode(universe)
    top_tickers: List[str] = get_top_liquid_stocks(UNIVERSE_SIZE, universe=universe_mode)
    
    # 1. Build Price Matrix (Returns)
    price_matrix = pd.DataFrame()
    for t in top_tickers:
        df: Optional[pd.DataFrame] = DataManager.DataManager.get_stock_data(t)
        if df is None or df.empty or 'Close' not in df.columns:
            continue
        price_matrix[t] = df['Close'].pct_change()
        
    price_matrix = price_matrix.dropna()
    if len(price_matrix) < 60:
        return {
            "status": "error",
            "message": "Insufficient common history",
            "count": 0,
            "mirrors": [],
            "universe": universe_mode,
        }

    ghost_pairs: List[Dict[str, Any]] = []
    pairs: List[Tuple[str, str]] = list(combinations(top_tickers, 2))
    
    for stock_a, stock_b in pairs:
        series_a = price_matrix[stock_a]
        series_b = price_matrix[stock_b]
        
        for lag in range(0, MAX_LAG + 1):  # Include Lag 0 for Sympathy moves
            # A leads B or Sympathy
            score = float(series_a.shift(lag).corr(series_b))
            
            if abs(score) > MIN_CORR:
                label = "Sympathy" if lag == 0 else "Lagged"
                
                # Z-Score Calculation (Leader vs Follower spread)
                # Spread = (Return A - Return B)
                spread = series_a.shift(lag) - series_b
                z_score = 0.0
                spread_clean = spread.dropna()
                if len(spread_clean) > 20:
                    roll_mean = spread.rolling(20).mean()
                    roll_std = spread.rolling(20).std()
                    z_series = (spread - roll_mean) / roll_std
                    last_z = float(z_series.iloc[-1])
                    if not np.isnan(last_z):
                        z_score = last_z

                sl_pct, tp_pct = _compute_stock_atr_brackets(stock_b)
                ghost_pairs.append({
                    'Leader': stock_a,
                    'Follower': stock_b,
                    'Lag': lag,
                    'Confidence': float(round(score * 100, 2)), # type: ignore
                    'Type': 'Positive' if score > 0 else 'Inverse',
                    'Label': label,
                    'ZScore': float(round(z_score, 2)), # type: ignore
                    'StopLossPct': sl_pct,
                    'TakeProfitPct': tp_pct,
                    'HedgingState': 'Unhedged Single-Leg (Follower)',
                })
            
            # For lagged cases, also check B leading A
            if lag > 0:
                score_b = float(series_b.shift(lag).corr(series_a))
                if abs(score_b) > MIN_CORR:
                    spread_b = series_b.shift(lag) - series_a
                    z_score_b = 0.0
                    spread_b_clean = spread_b.dropna()
                    if len(spread_b_clean) > 20:
                        roll_mean_b = spread_b.rolling(20).mean()
                        roll_std_b = spread_b.rolling(20).std()
                        z_series_b = (spread_b - roll_mean_b) / roll_std_b
                        last_z_b = float(z_series_b.iloc[-1])
                        if not np.isnan(last_z_b):
                            z_score_b = last_z_b

                    sl_pct_b, tp_pct_b = _compute_stock_atr_brackets(stock_a)
                    ghost_pairs.append({
                        'Leader': stock_b,
                        'Follower': stock_a,
                        'Lag': lag,
                        'Confidence': float(round(score_b * 100, 2)), # type: ignore
                        'Type': 'Positive' if score_b > 0 else 'Inverse',
                        'Label': 'Lagged',
                        'ZScore': float(round(z_score_b, 2)), # type: ignore
                        'StopLossPct': sl_pct_b,
                        'TakeProfitPct': tp_pct_b,
                        'HedgingState': 'Unhedged Single-Leg (Follower)',
                    })

    # Sort and Deduplicate
    # BOOST Lagged correlations by 20% for ranking purposes to surface "Echoes" over "Mirrors"
    ghost_pairs.sort(key=lambda x: abs(float(x['Confidence'])) * (1.2 if int(x['Lag']) > 0 else 1.0), reverse=True)
    
    # Simple deduplication (keep highest confidence for a pair)
    final_pairs: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for p in ghost_pairs:
        key: str = f"{p['Leader']}-{p['Follower']}"
        if key not in seen:
            final_pairs.append(p)
            seen.add(key)
            
    return {
        "status": "success",
        "universe": universe_mode,
        "count": len(final_pairs),
        "mirrors": final_pairs[:20] # type: ignore
    }

def print_mirrors() -> None:
    print(Fore.CYAN + "[JOTUNHEIM] Scanning the Multiverse for Lead-Lag Echoes...")
    data: Dict[str, Any] = get_lagged_correlations()
    if data['status'] == "error":
        print(data['message'])
        return
        
    mirrors: List[Dict[str, Any]] = data['mirrors'] # type: ignore
    print(Fore.GREEN + f"\nTHE MIRROR REVEALS ({data['count']} Pairs):")
    print("-" * 60)
    for p in mirrors:
        print(f"{p['Leader']:<10} -> {p['Follower']:<10} | Lag: {p['Lag']}d | Conf: {p['Confidence']}% ({p['Type']})")

if __name__ == "__main__":
    print_mirrors()
