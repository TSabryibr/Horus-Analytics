from __future__ import annotations

import pandas as pd
from core.settings import settings

# --- SETTINGS ---
DATA_FOLDER = settings.DATA_FOLDER
LOOKBACK = settings.LOOKBACK
ATR_PERIOD = 14  # Volatility setting
FORCE_PERIOD = 13  # Elder's Force Index period
MIN_DATA_POINTS = 100  # Minimum data points required

# --- VOLUME ANALYSIS SETTINGS ---
MIN_TURNOVER_EGP = 2000000  # Minimum daily turnover in EGP for liquidity
VOL_SPIKE_FACTOR = 1.5      # Volume spike multiplier (OPTIMIZED: was 2.5)
MOMENTUM_THRESHOLD = 2.5    # Minimum price % move (OPTIMIZED: was 2.0)
RSI_PERIOD = 14             # RSI calculation period
RSI_MIN = 55                # Minimum RSI (OPTIMIZED: was 50)
RSI_MAX = 85                # Maximum RSI for momentum signal
EMA_FAST = 9                # Fast EMA for trend confirmation
VOL_AVG_PERIOD = 20         # Volume averaging period

# --- LIQUIDITY GUARD CONFIGURATION ---
MAX_SPREAD_PCT = 0.008      # Maximum allowed bid-ask spread percentage (0.8%)
MIN_AVG_VOLUME_20D = 10000   # Minimum 20-day average daily volume

# --- MANIPULATION SENTRY CONFIGURATION ---
MANIP_LOW_VOL_THRESHOLD = 0.8   # Rel_Volume below this on a breakout = suspicious
MANIP_LOW_VOL_PRICE_MIN = 3.0   # Min Price_Move_% to trigger low-vol breakout flag
MANIP_ABSORB_VOL_THRESHOLD = 3.0  # Rel_Volume above this = potential absorption
MANIP_ABSORB_PRICE_MAX = 0.5   # Max |Price_Move_%| to flag absorption (big vol, no move)

# --- PROFIT TARGET RATIOS ---
SL_BUFFER_PCT = 1.5         # Stop loss buffer % (OPTIMIZED: was 1.0)
TP1_PCT = 4.0               # TP1: Fixed 4% gain (OPTIMIZED: was 3.0)
TP2_RR_RATIO = 2.0          # TP2: 2:1 Risk/Reward ratio
TP3_RR_RATIO = 3.5          # TP3: 3.5:1 Risk/Reward ratio
TP4_RR_RATIO = 5.0          # TP4: 5:1 Risk/Reward ratio

# --- USD STOCKS IN EGYPTIAN MARKET ---
USD_STOCKS = {'EGBE', 'TRTO', 'NAHO', 'GPPL', 'SAIB', 'NDRL', 'FAITA', 'EGSA', 'MOIL', 'CFGH', 'GTEX'}


def find_pivot_highs(df: pd.DataFrame, lookback: int = 5) -> list[float]:
    """Find pivot high points (resistance levels) using vectorized rolling window."""
    if len(df) < 2 * lookback + 1:
        return []

    rolling_max = df['High'].rolling(window=2*lookback+1, center=True, min_periods=1).max()
    is_pivot = df['High'] == rolling_max
    is_pivot.iloc[:lookback] = False
    is_pivot.iloc[-lookback:] = False

    return df['High'][is_pivot].tolist()


def find_pivot_lows(df: pd.DataFrame, lookback: int = 5) -> list[float]:
    """Find pivot low points (support levels) using vectorized rolling window."""
    if len(df) < 2 * lookback + 1:
        return []

    rolling_min = df['Low'].rolling(window=2*lookback+1, center=True, min_periods=1).min()
    is_pivot = df['Low'] == rolling_min
    is_pivot.iloc[:lookback] = False
    is_pivot.iloc[-lookback:] = False

    return df['Low'][is_pivot].tolist()


def calculate_critical_points(df: pd.DataFrame, current_price: float, atr: float) -> tuple[float, float, str]:
    """
    Calculate two critical points for momentum continuation
    CP1: Near-term level (closer to price)
    CP2: Major level (further from price)

    For uptrends: These are resistance levels above price
    For downtrends: These are support levels below price
    """
    if len(df) >= 50:
        sma_50 = df['Close'].rolling(50).mean().iloc[-1]
        is_bullish = current_price > sma_50
    else:
        is_bullish = current_price > df['Close'].rolling(20).mean().iloc[-1]

    pivot_highs_short = find_pivot_highs(df.tail(60), lookback=5)
    pivot_highs_long = find_pivot_highs(df.tail(120), lookback=10)

    pivot_lows_short = find_pivot_lows(df.tail(60), lookback=5)
    pivot_lows_long = find_pivot_lows(df.tail(120), lookback=10)

    if is_bullish:
        resistance_short = [h for h in pivot_highs_short if h > current_price]
        resistance_long = [h for h in pivot_highs_long if h > current_price]

        if resistance_short:
            cp1 = min(resistance_short)
        elif resistance_long:
            cp1 = min(resistance_long)
        else:
            cp1 = current_price + (1.5 * atr)

        if resistance_long:
            candidates = [r for r in resistance_long if r > cp1 + atr]
            cp2 = min(candidates) if candidates else (cp1 + (2.5 * atr))
        else:
            cp2 = cp1 + (2.5 * atr)

        direction = "BULLISH"
    else:
        support_short = [l for l in pivot_lows_short if l < current_price]
        support_long = [l for l in pivot_lows_long if l < current_price]

        if support_short:
            cp1 = max(support_short)
        elif support_long:
            cp1 = max(support_long)
        else:
            cp1 = current_price - (1.5 * atr)

        if support_long:
            candidates = [s for s in support_long if s < cp1 - atr]
            cp2 = max(candidates) if candidates else (cp1 - (2.5 * atr))
        else:
            cp2 = cp1 - (2.5 * atr)

        direction = "BEARISH"

    return cp1, cp2, direction


def _prepare_analysis_frame(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """Normalize a history frame into the columns/index expected by the scanner."""
    if df is None or df.empty:
        return None

    if isinstance(df.index, pd.MultiIndex):
        df = df.droplevel(0)

    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if 'Closed' in df.columns and 'Close' not in df.columns:
        df.rename(columns={'Closed': 'Close'}, inplace=True)
    df.columns = df.columns.str.strip().str.title()

    if 'Date' in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df['Date']):
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.set_index('Date', inplace=True)

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index, errors='coerce')

    df = df[~df.index.isna()]
    df.sort_index(ascending=True, inplace=True)

    return df
