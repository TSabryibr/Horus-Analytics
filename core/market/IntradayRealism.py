import pandas as pd
import numpy as np
from core.DataManager import DataManager
from datetime import timedelta

class IntradayValidator:
    """
    The 'Supreme Court' of Backtesting.
    Validates daily strategy signals against tick-level intraday data
    to resolve path dependency (Did we hit SL or TP first?).
    """
    
    def __init__(self):
        self.cache = {} # Cache intraday dataframes to avoid repetitive loading

    def get_intraday(self, ticker):
        """Load and cache intraday data."""
        if ticker in self.cache:
            return self.cache[ticker]
            
        df = DataManager.get_intraday_data(ticker)
        if df is None or df.empty:
            return None
            
        # Ensure timestamp index is sorted
        df = df.sort_index()
        self.cache[ticker] = df
        return df

    def validate_trade(self, ticker, signal_date, entry_price, sl_price, tp_price, validity_days=5, trailing_stop=None):
        """
        Simulate a trade outcome using minute-level data.
        
        Args:
            ticker (str): Ticker symbol.
            signal_date (pd.Timestamp): Date the signal was generated (EOD).
            entry_price (float): Assumed entry price.
            sl_price (float): Initial Stop Loss Price.
            tp_price (float): Target Profit Price.
            validity_days (int): Max days to hold before Time Exit.
            trailing_stop (float): Trailing stop percentage (optional).
            
        Returns:
            dict: Trade outcome.
        """
        df = self.get_intraday(ticker)
        if df is None:
            return {'outcome': 'UNKNOWN', 'reason': 'No Intraday Data', 'pnl_pct': 0.0}

        # Vectorized slicing bypassing Pandas copy
        times_arr = df.index.values
        signal_dt64 = np.datetime64(signal_date)
        
        # Find index marking start of post-signal data
        start_idx = np.searchsorted(times_arr, signal_dt64, side='right')
        
        if start_idx >= len(times_arr):
             return {'outcome': 'UNKNOWN', 'reason': 'No Future Data', 'pnl_pct': 0.0}
             
        # Find validity window cutoff index
        start_time = times_arr[start_idx]
        end_dt64 = start_time + np.timedelta64(validity_days, 'D')
        end_idx = np.searchsorted(times_arr, end_dt64, side='right')
        
        # Raw C-level memory views directly off the cache (Zero-Copy)
        high_arr = df['High'].values[start_idx:end_idx]
        low_arr = df['Low'].values[start_idx:end_idx]
        close_arr = df['Close'].values[start_idx:end_idx]
        slice_times = times_arr[start_idx:end_idx]
        
        if len(high_arr) == 0:
             return {'outcome': 'UNKNOWN', 'reason': 'No Future Data', 'pnl_pct': 0.0}

        # 1. Trailing Stop Calculation (Vectorized)
        if trailing_stop:
            # highest_price[i] = max(entry_price, high_arr[0], ..., high_arr[i])
            highest_prices = np.maximum.accumulate(np.insert(high_arr, 0, entry_price))[1:]
            sl_prices = highest_prices * (1 - trailing_stop/100)
            # Ensure SL only moves up
            sl_prices = np.maximum.accumulate(np.insert(sl_prices, 0, sl_price))[1:]
        else:
            sl_prices = np.full(len(high_arr), sl_price)

        # 2. Find Hits
        # Stop Loss Hits: Low <= SL
        sl_hits = np.where(low_arr <= sl_prices)[0]
        # Target Profit Hits: High >= TP
        tp_hits = np.where(high_arr >= tp_price)[0]

        first_sl = sl_hits[0] if len(sl_hits) > 0 else 999999
        first_tp = tp_hits[0] if len(tp_hits) > 0 else 999999

        if first_sl == 999999 and first_tp == 999999:
            # Time Exit
            last_price = close_arr[-1]
            return {
                'outcome': 'TIME',
                'pnl_pct': ((last_price - entry_price) / entry_price) * 100,
                'exit_date': slice_times[-1],
                'exit_price': last_price,
                'reason': 'Time Exit'
            }
        
        if first_sl <= first_tp:
            # SL Hit (Pessimistic: same day = SL)
            hit_idx = first_sl
            exit_price = sl_prices[hit_idx]
            return {
                'outcome': 'LOSS',
                'pnl_pct': ((exit_price - entry_price) / entry_price) * 100,
                'exit_date': slice_times[hit_idx],
                'exit_price': exit_price,
                'reason': 'Trailing Stop' if trailing_stop and exit_price > sl_price else 'Hit SL'
            }
        else:
            # TP Hit
            hit_idx = first_tp
            return {
                'outcome': 'WIN',
                'pnl_pct': ((tp_price - entry_price) / entry_price) * 100,
                'exit_date': slice_times[hit_idx],
                'exit_price': tp_price,
                'reason': 'Hit TP (Intraday)'
            }

    def simulate_1405_entry(self, ticker, signal):
        """
        Special Logic:
        Signal generated at 14:05 on Day 0.
        Entry: 14:05 candle close.
        Validation: Remainder of Day 0 + Next Days.
        """
        pass # To implement
