"""
SIGNAL ACCURACY CHECKER
=======================
Validates historical signal accuracy by scanning past dates and checking outcomes.
No look-forward bias - only uses data available at the time of the signal.

Author: Horus Analytics
Date: 2026-01-14
"""

from core.settings import settings
import logging
import warnings
import threading

import numpy as np
import pandas as pd

from core.market import MarketLists
from core import SignalEngine, StockLoader

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)

# === STRATEGY PARAMETERS (static - read at import) ===
LOOKBACK = settings.LOOKBACK
VOL_SPIKE = settings.VOL_SPIKE
MOMENTUM = settings.MOMENTUM
RSI_MIN = settings.RSI_MIN
RSI_MAX = settings.RSI_MAX
MIN_TURNOVER = settings.MIN_TURNOVER
# Note: SL_PCT and TP1_PCT are read dynamically inside functions
# to allow Dashboard to modify them at runtime


def load_all_stocks(allowed_tickers=None):
    """
    Load all stock data with calculated indicators using the central StockLoader.
    """
    return StockLoader.load_universe_calculated(tickers=allowed_tickers, include_adv=False)


def generate_historical_signal(df, date):
    """
    Generate signal for a specific date using only data available at that time.
    Returns signal dict or None if no signal.
    """
    if date not in df.index:
        return None
    
    idx = df.index.get_loc(date)
    if idx < 60:  # Need enough history
        return None
    
    try:
        close = df['Close'].iloc[idx]
        low = df['Low'].iloc[idx]
        open_price = df['Open'].iloc[idx]
        resistance = df['Resistance'].iloc[idx]
        power = df['EFI'].iloc[idx]
        ema9 = df['EMA9'].iloc[idx]
        rsi = df['RSI'].iloc[idx]
        rel_vol = df['Rel_Vol'].iloc[idx]
        avg_turnover = df['Avg_Turnover'].iloc[idx]
        price_move = df['Price_Move'].iloc[idx]
        
        if pd.isna(resistance) or pd.isna(rsi):
            return None
        
        # === SIGNAL CONDITIONS (same as DailyScanner) ===
        is_liquid = avg_turnover > MIN_TURNOVER
        volume_spike = rel_vol > VOL_SPIKE
        momentum_move = price_move >= MOMENTUM
        rsi_valid = RSI_MIN < rsi < RSI_MAX
        breakout = close > resistance
        
        # All conditions must be met
        if not (is_liquid and volume_spike and momentum_move and rsi_valid and breakout):
            return None
        
        # Calculate score (simplified - matches PortfolioSimulator logic)
        score = 0
        power_positive = power > 0
        above_ema = close > ema9
        vol_high = rel_vol > 1.5
        rsi_optimal = RSI_MIN < rsi < 70
        
        if breakout and power_positive:
            score += 3
        if is_liquid and (volume_spike and momentum_move):
            score += 5
        if vol_high:
            score += 1
        if rsi_optimal:
            score += 1
        if above_ema:
            score += 1
        
        # Calculate entry/SL/TP - READ DYNAMICALLY from GlobalSettings
        sl_pct = settings.SL_PCT
        tp_pct = settings.TP1_PCT
        entry_price = close
        stop_loss = low * (1 - sl_pct / 100)
        target_price = close * (1 + tp_pct / 100)
        
        return {
            'entry_price': round(entry_price, settings.PRICE_PRECISION),
            'stop_loss': round(stop_loss, settings.PRICE_PRECISION),
            'target_price': round(target_price, settings.PRICE_PRECISION),
            'score': score,
            'rsi': round(rsi, 1),
            'rel_vol': round(rel_vol, 1)
        }
        
    except Exception:
        return None


def check_signal_outcome(df, signal_date, entry_price, stop_loss, target_price, window_days):
    """
    Check if a signal hit TP, SL, or expired within the time window.
    Returns outcome dict.
    """
    if signal_date not in df.index:
        return None
    
    entry_idx = df.index.get_loc(signal_date)
    
    for days_held in range(1, window_days + 1):
        if entry_idx + days_held >= len(df):
            break
        
        check_date = df.index[entry_idx + days_held]
        high = df['High'].iloc[entry_idx + days_held]
        low = df['Low'].iloc[entry_idx + days_held]
        close = df['Close'].iloc[entry_idx + days_held]
        
        # Check TP hit first (assume intraday TP hit if high >= target)
        if high >= target_price:
            pnl_pct = ((target_price - entry_price) / entry_price) * 100
            return {
                'outcome': 'TP_HIT',
                'exit_date': check_date,
                'exit_price': target_price,
                'days_held': days_held,
                'pnl_pct': round(pnl_pct, 2)
            }
        
        # Check SL hit (assume intraday SL hit if low <= stop loss)
        if low <= stop_loss:
            pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
            return {
                'outcome': 'SL_HIT',
                'exit_date': check_date,
                'exit_price': stop_loss,
                'days_held': days_held,
                'pnl_pct': round(pnl_pct, 2)
            }
    
    # Neither TP nor SL hit within window - expired
    if entry_idx + window_days < len(df):
        exit_idx = entry_idx + window_days
        exit_date = df.index[exit_idx]
        exit_price = df['Close'].iloc[exit_idx]
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        return {
            'outcome': 'EXPIRED',
            'exit_date': exit_date,
            'exit_price': round(exit_price, settings.PRICE_PRECISION),
            'days_held': window_days,
            'pnl_pct': round(pnl_pct, 2)
        }
    
    # Not enough future data to determine outcome
    return {
        'outcome': 'NO_DATA',
        'exit_date': None,
        'exit_price': None,
        'days_held': 0,
        'pnl_pct': 0
    }


def run_accuracy_check(start_date, end_date, window_days, data_folder=None, index_choice="ALL"):
    """
    Main function to check signal accuracy over a date range.
    
    Args:
        start_date: Start date string (YYYY-MM-DD) or date object
        end_date: End date string (YYYY-MM-DD) or date object
        window_days: Number of days to check for TP/SL hit (1, 5, 10, etc.)
        data_folder: Deprecated legacy argument; ignored when DataManager is active.
        index_choice: Market filter ("ALL", "30", "70", "100")
    
    Returns:
        dict with 'summary', 'by_score', and 'signals' keys
    """
    # Get market filter
    market_filter = MarketLists.get_market_list(index_choice) if index_choice != "ALL" else None
    
    # Load all stocks
    if data_folder:
        logger.debug("run_accuracy_check received legacy data_folder=%s (ignored)", data_folder)
    logger.debug("Loading stock universe from DataManager (index_choice=%s)", index_choice)
    stocks = load_all_stocks(market_filter)
    
    if not stocks:
        return {
            'summary': {'total_signals': 0, 'tp_hits': 0, 'sl_hits': 0, 'expired': 0,
                        'win_rate': 0, 'avg_days_to_tp': 0, 'avg_gain_pct': 0},
            'by_score': {},
            'signals': []
        }
    
    # Convert dates
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Get trading dates from sample stock
    sample_stock = list(stocks.values())[0]
    trading_dates = sample_stock.loc[start:end].index.tolist()
    trading_dates = [d for d in trading_dates if start <= d <= end]
    
    logger.debug("Checking %d trading days in accuracy run", len(trading_dates))
    
    # Collect all signals and their outcomes
    all_signals = []
    
    res_col = f'Res_{LOOKBACK}'
    sl_pct = settings.SL_PCT
    tp_pct = settings.TP1_PCT
    
    for ticker, df in stocks.items():
        # 1. Vectorized Signal Generation
        # Map required settings to what SignalEngine expects
        settings_mock = settings
        
        # Get all signals for this stock at once
        signal_mask = SignalEngine.vectorize_signals(df, settings_mock, res_col)
        if signal_mask is None or signal_mask.sum() == 0:
            continue
            
        # Filter to requested date range
        date_mask = (df.index >= start) & (df.index <= end)
        final_mask = signal_mask & date_mask
        
        if final_mask.sum() == 0:
            continue
            
        # 2. Vectorized Outcome Validation
        # Get indices of signals
        signal_indices = np.where(final_mask)[0]
        
        high_arr = df['High'].values
        low_arr = df['Low'].values
        close_arr = df['Close'].values
        dates_arr = df.index.values
        
        for idx in signal_indices:
            signal_date = dates_arr[idx]
            entry_price = float(close_arr[idx])
            stop_loss = float(df['Low'].iloc[idx]) * (1 - sl_pct / 100)
            target_price = entry_price * (1 + tp_pct / 100)
            
            # Efficient slice lookup for outcome
            # We check the next 'window_days'
            end_idx = min(idx + window_days + 1, len(df))
            future_high = high_arr[idx+1:end_idx]
            future_low = low_arr[idx+1:end_idx]
            future_close = close_arr[idx+1:end_idx]
            
            if len(future_high) == 0:
                continue
                
            # Find first occurrence of TP or SL
            tp_hits = np.where(future_high >= target_price)[0]
            sl_hits = np.where(future_low <= stop_loss)[0]
            
            first_tp = tp_hits[0] if len(tp_hits) > 0 else 999
            first_sl = sl_hits[0] if len(sl_hits) > 0 else 999
            
            if first_tp == 999 and first_sl == 999:
                # Expired or No Data
                if len(future_high) < window_days:
                    outcome = {'outcome': 'NO_DATA', 'pnl_pct': 0, 'days_held': 0, 'exit_date': None, 'exit_price': None}
                else:
                    exit_price = future_close[-1]
                    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
                    outcome = {
                        'outcome': 'EXPIRED',
                        'exit_date': dates_arr[idx + window_days],
                        'exit_price': round(exit_price, settings.PRICE_PRECISION),
                        'days_held': window_days,
                        'pnl_pct': round(pnl_pct, 2)
                    }
            elif first_tp <= first_sl:
                # TP Hit (Pessimistic: if both on same day, SL wins or we can choose)
                # Most traders assume TP first if both are hit on same day if logic is fast
                # But to be safe we can check if both hit on same day.
                pnl_pct = ((target_price - entry_price) / entry_price) * 100
                outcome = {
                    'outcome': 'TP_HIT',
                    'exit_date': dates_arr[idx + 1 + first_tp],
                    'exit_price': target_price,
                    'days_held': int(first_tp + 1),
                    'pnl_pct': round(pnl_pct, 2)
                }
            else:
                pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                outcome = {
                    'outcome': 'SL_HIT',
                    'exit_date': dates_arr[idx + 1 + first_sl],
                    'exit_price': stop_loss,
                    'days_held': int(first_sl + 1),
                    'pnl_pct': round(pnl_pct, 2)
                }
                
            if outcome['outcome'] != 'NO_DATA':
                all_signals.append({
                    'ticker': ticker,
                    'signal_date': signal_date,
                    'entry': entry_price,
                    'sl': stop_loss,
                    'tp': target_price,
                    'score': int(df['score'].iloc[idx]) if 'score' in df.columns else 0, # Note: core engine score calculation
                    'rsi': round(df['RSI'].iloc[idx], 1),
                    'rel_vol': round(df['Rel_Vol'].iloc[idx], 1),
                    **outcome
                })
    
    # Calculate summary statistics
    total_signals = len(all_signals)
    tp_hits = sum(1 for s in all_signals if s['outcome'] == 'TP_HIT')
    sl_hits = sum(1 for s in all_signals if s['outcome'] == 'SL_HIT')
    expired = sum(1 for s in all_signals if s['outcome'] == 'EXPIRED')
    
    win_rate = (tp_hits / total_signals * 100) if total_signals > 0 else 0
    
    # Calculate average days to TP for winning signals
    tp_signals = [s for s in all_signals if s['outcome'] == 'TP_HIT']
    avg_days_to_tp = np.mean([s['days_held'] for s in tp_signals]) if tp_signals else 0
    
    # Calculate average gain/loss
    avg_gain = np.mean([s['pnl_pct'] for s in all_signals]) if all_signals else 0
    
    # Breakdown by score
    by_score = {}
    scores = set(s['score'] for s in all_signals)
    for score in sorted(scores):
        score_signals = [s for s in all_signals if s['score'] == score]
        score_tp = sum(1 for s in score_signals if s['outcome'] == 'TP_HIT')
        by_score[score] = {
            'signals': len(score_signals),
            'win_rate': round(score_tp / len(score_signals) * 100, 1) if score_signals else 0
        }
    
    logger.debug("Accuracy run complete: signals=%d win_rate=%.1f%%", total_signals, win_rate)
    
    return {
        'summary': {
            'total_signals': total_signals,
            'tp_hits': tp_hits,
            'sl_hits': sl_hits,
            'expired': expired,
            'win_rate': round(win_rate, 1),
            'avg_days_to_tp': round(avg_days_to_tp, 1),
            'avg_gain_pct': round(avg_gain, 2)
        },
        'by_score': by_score,
        'signals': all_signals
    }


if __name__ == "__main__":
    # Example usage
    results = run_accuracy_check(
        start_date="2025-01-01",
        end_date="2025-06-30",
        window_days=5
    )
    
    print("\n=== ACCURACY CHECK RESULTS ===")
    print(f"Total Signals: {results['summary']['total_signals']}")
    print(f"Win Rate: {results['summary']['win_rate']}%")
    print(f"TP Hits: {results['summary']['tp_hits']}")
    print(f"SL Hits: {results['summary']['sl_hits']}")
    print(f"Expired: {results['summary']['expired']}")
    print(f"Avg Days to TP: {results['summary']['avg_days_to_tp']}")
    
    print("\n--- By Score ---")
    for score, data in results['by_score'].items():
        print(f"Score {score}: {data['signals']} signals, {data['win_rate']}% win rate")
