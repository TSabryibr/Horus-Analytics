"""
SIGNAL ENGINE
=============
Unified logic for calculating indicators and generating signals.
Designed to be used by both:
1. DailyScanner.py (Live/Iterative)
2. Optimizer.py (Backtest/Vectorized)
"""

from core.settings import settings
import pandas as pd
import numpy as np
from core.market import MarketLists
from core.market_profiles import EGX30_TREND_PROFILE, EGX70_TACTICAL_PROFILE, MarketProfile
from core.signal_validation import validate_long_signal, validate_long_signals

STRATEGY_DEFAULT_KEYS = (
    'LOOKBACK',
    'VOL_SPIKE',
    'MOMENTUM',
    'RSI_MIN',
    'RSI_MAX',
    'SL_PCT',
    'TP1_PCT',
    'MIN_TURNOVER',
    'TRAILING_STOP_ENABLED',
    'TRAILING_STOP_TYPE',
    'TRAILING_STOP_VALUE',
    'USE_ATR_EXITS',
    'ATR_TP_MULTIPLIER',
    'ATR_SL_MULTIPLIER',
)


def merge_strategy_defaults(strategy_settings):
    if not isinstance(strategy_settings, dict):
        return strategy_settings

    merged = dict(strategy_settings)
    for key in STRATEGY_DEFAULT_KEYS:
        if key not in merged and hasattr(settings, key):
            merged[key] = getattr(settings, key)
    return merged


def add_indicators(df, lookback=30):
    """
    Adds technical indicators to the DataFrame in-place.
    """
    try:
        # Native ATR Calculation (Wilder's Smoothing)
        tr1 = df['High'] - df['Low']
        tr2 = (df['High'] - df['Close'].shift()).abs()
        tr3 = (df['Low'] - df['Close'].shift()).abs()
        tr = np.fmax.reduce([tr1.to_numpy(), tr2.to_numpy(), tr3.to_numpy()])
        df['ATR'] = pd.Series(tr, index=df.index).ewm(alpha=1/14, min_periods=14, adjust=False).mean()

        # Native EFI Calculation
        df['EFI'] = (df['Close'].diff(1) * df['Volume']).ewm(span=13, adjust=False).mean()

        # EMA9
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()

        # Native RSI Calculation (Wilder's Smoothing)
        delta = df['Close'].diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, min_periods=14, adjust=False).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100.0 - (100.0 / (1.0 + rs))
        
        # Volume & Turnover
        df['Avg_Vol'] = df['Volume'].rolling(20).mean()
        df['Rel_Vol'] = (df['Volume'] / df['Avg_Vol']).replace([np.inf, -np.inf], 0).fillna(0)
        df['Turnover'] = df['Close'] * df['Volume']
        df['Avg_Turnover'] = df['Turnover'].rolling(20).mean()
        
        # Price Movement
        df['Move'] = ((df['Close'] - df['Open']) / df['Open']) * 100
        
        # Resistance & Support
        df[f'Res_{lookback}'] = df['High'].rolling(lookback).max().shift(1)
        df[f'Sup_{lookback}'] = df['Low'].rolling(lookback).min().shift(1)
        
        return df
    except Exception as e:
        print(f"SignalEngine Error (Indicators): {e}")
        return df

def add_indicators_universe(df, lookback=30):
    """
    Adds technical indicators to a MultiIndex DataFrame [Ticker, Date] in-place.
    """
    try:
        g = df.groupby(level=0, sort=False, group_keys=False)
        close = df['Close']
        delta = g['Close'].diff()
        prev_close = g['Close'].shift(1)
        
        # High-performance True Range using NumPy
        tr = np.fmax.reduce([
            (df['High'] - df['Low']).values,
            (df['High'] - prev_close).abs().values,
            (df['Low'] - prev_close).abs().values
        ])
        
        df['ATR'] = (
            pd.Series(tr, index=df.index)
            .groupby(level=0, sort=False)
            .ewm(alpha=1/14, min_periods=14, adjust=False)
            .mean()
            .droplevel(0)
        )
        df['EFI'] = (
            (delta * df['Volume'])
            .groupby(level=0, sort=False)
            .ewm(span=13, adjust=False)
            .mean()
            .droplevel(0)
        )
        df['EMA9'] = (
            g['Close']
            .ewm(span=9, adjust=False)
            .mean()
            .droplevel(0)
        )
        
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = (
            pd.Series(gain, index=df.index)
            .groupby(level=0, sort=False)
            .ewm(alpha=1/14, min_periods=14, adjust=False)
            .mean()
            .droplevel(0)
        )
        avg_loss = (
            pd.Series(loss, index=df.index)
            .groupby(level=0, sort=False)
            .ewm(alpha=1/14, min_periods=14, adjust=False)
            .mean()
            .droplevel(0)
        )
        rs = avg_gain / avg_loss
        df['RSI'] = 100.0 - (100.0 / (1.0 + rs))
        
        df['Avg_Vol'] = g['Volume'].rolling(20).mean().droplevel(0)
        df['Rel_Vol'] = (df['Volume'] / df['Avg_Vol']).replace([np.inf, -np.inf], 0).fillna(0)
        df['Turnover'] = close * df['Volume']
        df['Avg_Turnover'] = (
            df.groupby(level=0, sort=False)['Turnover']
            .rolling(20)
            .mean()
            .droplevel(0)
        )
        df['Move'] = ((close - df['Open']) / df['Open']) * 100
        df[f'Res_{lookback}'] = (
            g['High']
            .rolling(lookback)
            .max()
            .groupby(level=0)
            .shift(1)
            .droplevel(0)
        )
        df[f'Sup_{lookback}'] = (
            g['Low']
            .rolling(lookback)
            .min()
            .groupby(level=0)
            .shift(1)
            .droplevel(0)
        )
        
        return df
    except Exception as e:
        print(f"SignalEngine Error (Universe Indicators): {e}")
        return df

def check_buy_signal(row, settings, resistance_col='Res_30', profile: MarketProfile = EGX30_TREND_PROFILE):
    """
    Checks a single row (Series) for a Buy Signal.
    Used by DailyScanner.py (Iterative).
    """
    try:
        if pd.isna(row.get(resistance_col)) or pd.isna(row.get('RSI')):
            return None
            
        close = row['Close']
        res = row[resistance_col]
        rsi = row['RSI']
        turnover = row.get('Avg_Turnover', 0)
        rel_vol = row.get('Rel_Vol', 0)
        move = row.get('Move', 0)
        efi = row.get('EFI', 0)
        
        # Block low-liquidity pumps (manipulation check)
        potential_manipulation = (rel_vol > 5.0) and (turnover < 4000000.0)
        if potential_manipulation:
            return None

        is_liquid = turnover > settings.MIN_TURNOVER
        volume_spike = rel_vol > settings.VOL_SPIKE
        momentum = move >= settings.MOMENTUM
        rsi_valid = settings.RSI_MIN < rsi < settings.RSI_MAX
        breakout = close > res
        
        if is_liquid and volume_spike and momentum and rsi_valid and breakout:
            validation = validate_long_signal(row, settings, profile=profile)
            if not validation['is_valid']:
                return None

            score = 0
            if breakout: score += 2
            if efi > 0: score += 1
            if is_liquid and volume_spike: score += 4
            if rsi < 70: score += 1
            if close > row.get('EMA9', 0): score += 2
            
            if getattr(settings, 'USE_ATR_EXITS', False) and pd.notna(row.get('ATR')):
                sl = close - (row['ATR'] * getattr(settings, 'ATR_SL_MULTIPLIER', 1.5))
                tp = close + (row['ATR'] * getattr(settings, 'ATR_TP_MULTIPLIER', 2.0))
            else:
                sl = close * (1 - settings.SL_PCT/100)
                tp = close * (1 + settings.TP1_PCT/100)
            tp2_pct = float(getattr(settings, 'TP2_PCT', 4.0))
            tp2 = tp * (1 + tp2_pct / 100.0)
            
            return {
                'Signal_Type': 'BUY',
                'Entry_Price': close,
                'Stop_Loss': sl,
                'Target_Price': tp,
                'Target_Price_2': tp2,
                'RSI': rsi,
                'Score': score,
                'Volume_Spike': rel_vol,
                'ATR': row.get('ATR', 0),
                'Volume_Mult_20': validation['volume_mult_20'],
                'VSA_Valid': validation['is_valid'],
                'Validation_Profile': validation['profile_name'],
                'Validation_Turnover': validation['turnover'],
            }
    except Exception:
        return None
    return None

def check_short_signal(row, settings, support_col='Sup_30'):
    """
    Checks a single row (Series) for a Short Signal.
    """
    try:
        if pd.isna(row.get(support_col)) or pd.isna(row.get('RSI')):
            return None
            
        close = row['Close']
        sup = row[support_col]
        rsi = row['RSI']
        turnover = row.get('Avg_Turnover', 0)
        rel_vol = row.get('Rel_Vol', 0)
        move = row.get('Move', 0)
        
        is_liquid = turnover > settings.MIN_TURNOVER
        volume_spike = rel_vol > settings.VOL_SPIKE
        momentum = move <= -settings.MOMENTUM
        rsi_valid = rsi >= getattr(settings, 'RSI_SHORT_MIN', 80)
        breakdown = close < sup
        
        if is_liquid and volume_spike and momentum and rsi_valid and breakdown:
            if getattr(settings, 'USE_ATR_EXITS', False) and pd.notna(row.get('ATR')):
                sl = close + (row['ATR'] * getattr(settings, 'ATR_SL_MULTIPLIER', 1.5))
                tp = close - (row['ATR'] * getattr(settings, 'ATR_TP_MULTIPLIER', 2.0))
            else:
                sl = close * (1 + settings.SL_PCT/100)
                tp = close * (1 - settings.TP1_PCT/100)
            tp2_pct = float(getattr(settings, 'TP2_PCT', 4.0))
            tp2 = tp * (1 - tp2_pct / 100.0)
            
            return {
                'Signal_Type': 'SELL',
                'Entry_Price': close,
                'Stop_Loss': sl,
                'Target_Price': tp,
                'Target_Price_2': tp2,
                'RSI': rsi,
                'Score': 6,
                'Volume_Spike': rel_vol,
                'ATR': row.get('ATR', 0)
            }
    except Exception:
        return None
    return None

def check_trickster_signal(df, row_idx=-1, settings=None):
    """
    Mean-reversion setup that hunts oversold rebounds.
    Identifies 'blood in the streets' conditions where price is significantly 
    disconnected from the EMA9 mean.
    """
    try:
        if df is None or len(df) == 0:
            return None
            
        row = df.iloc[row_idx]
        
        # 1. Data Integrity
        required_cols = ('RSI', 'EMA9', 'Close', 'ATR', 'Open')
        for col in required_cols:
            if pd.isna(row.get(col)):
                return None
        
        close = float(row['Close'])
        open_price = float(row['Open'])
        ema9 = float(row['EMA9'])
        rsi = float(row['RSI'])
        atr = float(row['ATR'])
        rel_vol = row.get('Rel_Vol', 0.0)
        
        # Block low-liquidity pumps (manipulation check — mirrors check_buy_signal guard)
        turnover_val = float(row.get('Avg_Turnover', row.get('Turnover', 0)) or 0)
        potential_manipulation = (rel_vol > 5.0) and (turnover_val < 4_000_000.0)
        if potential_manipulation:
            return None
        
        # 2. Adaptation Logic (Evolved thresholds)
        def _get_setting(key, default):
            if settings is None: return default
            if isinstance(settings, dict):
                val = settings.get(key, default)
                return default if val is None else val
            val = getattr(settings, key, default)
            return default if val is None else val

        # Trickster RSI cap defaults to RSI_MIN - 20 (capped at 30)
        rsi_min_base = float(_get_setting('RSI_MIN', 50.0))
        default_rsi_max = min(30.0, rsi_min_base - 20.0)
        trickster_rsi_max = float(_get_setting('TRICKSTER_RSI_MAX', default_rsi_max))
        
        # Trickster Rel Vol min defaults to VOL_SPIKE * 0.7 (capped at 1.5)
        vol_spike_base = float(_get_setting('VOL_SPIKE', 1.5))
        default_rel_vol = min(1.5, vol_spike_base * 0.7)
        trickster_rel_vol_min = float(_get_setting('TRICKSTER_REL_VOL_MIN', default_rel_vol))
        
        # Stretch ATR defaults to MOMENTUM threshold (capped at 3.0)
        mom_base = float(_get_setting('MOMENTUM', 2.0))
        default_stretch = min(3.0, mom_base)
        trickster_stretch_atr = float(_get_setting('TRICKSTER_STRETCH_ATR', default_stretch))
        
        # 3. Core Logic
        is_blood = rsi < trickster_rsi_max
        # Distance from mean in units of ATR
        ema_dist = (ema9 - close) / atr if atr > 0 else 0
        is_stretched = ema_dist > trickster_stretch_atr
        # We want signs of 'turning': Close > Open (Bottom wick)
        is_turning = close > open_price
        participation = rel_vol >= trickster_rel_vol_min
        
        if is_blood and is_stretched and is_turning and participation:
            use_atr_exits = bool(_get_setting('USE_ATR_EXITS', True))
            atr_sl_mult = float(_get_setting('ATR_SL_MULTIPLIER', 1.5))
            sl_pct = float(_get_setting('SL_PCT', 1.5))
            
            # Target is the Mean (EMA9) or at least 1 ATR away
            target_price = ema9 if ema9 > close else close + (atr * 1.0)
            target_price_2 = target_price + (atr * 0.75)
            
            if use_atr_exits:
                stop_loss = close - (atr * max(0.5, atr_sl_mult)) # Guard against negative mults
            else:
                stop_loss = close * (1 - sl_pct / 100.0)
                
            return {
                'Signal_Type': 'BUY',
                'Signal_Setup': 'TRICKSTER_REVERSAL',
                'Conviction': 'High' if rsi < 20 else 'Moderate',
                'Entry_Price': close,
                'Stop_Loss': stop_loss,
                'Target_Price': target_price,
                'Target_Price_2': target_price_2,
                'RSI': rsi,
                'Score': 6,
                'Volume_Spike': float(rel_vol),
                'Trickster_RSI_Max': trickster_rsi_max,
                'Trickster_RelVol_Min': trickster_rel_vol_min,
                'Trickster_Stretch_ATR': trickster_stretch_atr
            }
    except Exception:
        pass
    return None

def vectorize_signals(data, settings, resistance_col='Res_30', profile: MarketProfile | None = None, validation_mask=None):
    """
    Vectorized calculation of buy signals. 
    Accepts DataFrame or Dict of NumPy arrays (for Optimizer speed).
    """
    try:
        settings = merge_strategy_defaults(settings)

        def get_setting(s, key):
            return s[key] if isinstance(s, dict) else getattr(s, key)

        min_turnover = get_setting(settings, 'MIN_TURNOVER')
        vol_spike = get_setting(settings, 'VOL_SPIKE')
        momentum = get_setting(settings, 'MOMENTUM')
        rsi_min = get_setting(settings, 'RSI_MIN')
        rsi_max = get_setting(settings, 'RSI_MAX')
        
        close = data['Close']
        move = data['Move']
        rsi = data['RSI']
        rel_vol = data['Rel_Vol']
        turnover = data['Avg_Turnover']
        res = data[resistance_col]
        
        is_liquid = turnover > min_turnover
        volume_spike = rel_vol > vol_spike
        mom_move = move >= momentum
        rsi_valid = (rsi > rsi_min) & (rsi < rsi_max)
        breakout = close > res

        raw_candidates = is_liquid & volume_spike & mom_move & rsi_valid & breakout

        if validation_mask is not None:
            if isinstance(data, pd.DataFrame):
                return raw_candidates & validation_mask
            return np.asarray(raw_candidates, dtype=bool) & np.asarray(validation_mask, dtype=bool)

        validation = _validate_long_candidates(data, settings, profile=profile)

        if isinstance(data, pd.DataFrame):
            return raw_candidates & validation['is_valid']
        return np.asarray(raw_candidates, dtype=bool) & validation['is_valid'].to_numpy(dtype=bool)
        
    except Exception as e:
        print(f"Vectorization Error: {e}")
        return None

def _validate_long_candidates(data, settings, profile: MarketProfile | None = None):
    validation_frame = _coerce_validation_frame(data)
    if profile is not None:
        return validate_long_signals(validation_frame, settings, profile=profile)

    validation = validate_long_signals(validation_frame, settings, profile=EGX30_TREND_PROFILE)
    if validation_frame.empty: return validation

    egx70_mask = pd.Index(validation_frame.index).isin(MarketLists.EGX_70)
    if egx70_mask.any():
        egx70_validation = validate_long_signals(validation_frame.loc[egx70_mask], settings, profile=EGX70_TACTICAL_PROFILE)
        validation.loc[egx70_mask] = egx70_validation
    return validation

def _coerce_validation_frame(data):
    if isinstance(data, pd.DataFrame): return data
    if isinstance(data, dict):
        normalized = {}
        for key, value in data.items():
            normalized[key] = pd.Series(value) if not isinstance(value, pd.Series) else value.reset_index(drop=True)
        return pd.DataFrame(normalized)
    return data
