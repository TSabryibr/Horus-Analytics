from core.settings import settings
from core.exclusions import EXCLUDED_TICKERS
import threading
import logging
import time
from core import SignalEngine, TimeUtils

from core.execution_model import prepare_adv_metrics

logger = logging.getLogger(__name__)

# --- CALCULATION CACHE ---
_STOCK_CACHE_LOCK = threading.Lock()
_STOCK_CACHE = {} # Key: (ticker, mode), Value: (DataFrame, Fingerprint, Expiry)

_TICKERS_CACHE = None
_TICKERS_CACHE_EXPIRY = 0

def clear_cache():
    """Wipes the calculation cache."""
    with _STOCK_CACHE_LOCK:
        _STOCK_CACHE.clear()
    global _TICKERS_CACHE
    _TICKERS_CACHE = None
    logger.info("StockLoader: Cache cleared.")

CACHE_TTL = 30 # Seconds to trust the in-memory cache without re-checking DataManager

def load_stock_with_indicators(ticker, include_adv=False):
    """
    Load a single stock with indicators and optional execution metrics.
    Uses a memory cache to avoid redundant calculations and disk checks.
    """
    now = time.time()
    
    # Isolation: Include simulation date in cache key to prevent future leaks
    sim_date = TimeUtils.today() if TimeUtils.is_simulating() else None
    cache_key = (ticker, include_adv, sim_date)
    
    # 1. Check Memory Cache (Fast Path)
    with _STOCK_CACHE_LOCK:
        if cache_key in _STOCK_CACHE:
            df, fp, expiry = _STOCK_CACHE[cache_key]
            if now < expiry:
                return df
    
    try:
        # 2. Re-verify with DataManager (Slow Path - every 30s)
        from core.DataManager import DataManager
        df = DataManager.get_stock_data(ticker, include_live=False)
        if df is None or len(df) < 100:
            return None
        
        # Fingerprint
        new_fp = (len(df), df.index[-1] if not df.empty else None)
        
        with _STOCK_CACHE_LOCK:
            if cache_key in _STOCK_CACHE:
                old_df, old_fp, old_expiry = _STOCK_CACHE[cache_key]
                if new_fp == old_fp:
                    # Update expiry and return old_df to save memory
                    _STOCK_CACHE[cache_key] = (old_df, old_fp, now + CACHE_TTL)
                    return old_df
        
        # 3. Recalculate if changed or new
        df = SignalEngine.add_indicators(df, lookback=settings.LOOKBACK)
        df['Price_Move'] = ((df['Close'] - df['Open']) / df['Open']) * 100
        
        if include_adv:
            df = prepare_adv_metrics(df, window=10)
            
        with _STOCK_CACHE_LOCK:
            _STOCK_CACHE[cache_key] = (df, new_fp, now + CACHE_TTL)
            if len(_STOCK_CACHE) > 512:
                _STOCK_CACHE.pop(next(iter(_STOCK_CACHE)))
                
        return df
    except Exception as e:
        logger.error(f"Error loading {ticker}: {e}")
        return None

def load_universe_calculated(tickers=None, include_adv=False):
    """
    Load a set of tickers with pre-calculated indicators.
    """
    import time
    global _TICKERS_CACHE, _TICKERS_CACHE_EXPIRY
    
    if tickers is None:
        # Cache ticker list for 60 seconds
        now = time.time()
        if _TICKERS_CACHE is None or now > _TICKERS_CACHE_EXPIRY:
            from core.DataManager import DataManager
            all_tickers = DataManager.list_tickers()
            _TICKERS_CACHE = [t for t in all_tickers if t.upper() not in ['REPORT', 'EGX30_70_100']]
            _TICKERS_CACHE_EXPIRY = now + 60
        tickers = _TICKERS_CACHE
    
    # Pre-loading from DataManager is the bottleneck.
    # In a real environment, DataManager itself caches raw data.
    # We rely on StockLoader for indicator calculation caching.
    
    # H7 Optimization: Parallelize universe warm-up
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    stocks = {}
    workers = max(1, min(len(tickers), 16))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_ticker = {
            executor.submit(load_stock_with_indicators, ticker, include_adv=include_adv): ticker 
            for ticker in tickers if ticker not in EXCLUDED_TICKERS
        }
        
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                df = future.result()
                if df is not None:
                    stocks[ticker] = df
            except Exception as e:
                logger.error(f"Parallel load failed for {ticker}: {e}")
                
    return stocks

def to_optimizer_dict(df, ticker, lookbacks=None):
    """
    Convert a calculated DataFrame to the dictionary format expected by Optimizer.py.
    """
    import numpy as np
    data = {
        'ticker': ticker,
        'Close': df['Close'].values,
        'Low': df['Low'].values,
        'High': df['High'].values,
        'EFI': df['EFI'].values,
        'EMA9': df['EMA9'].values,
        'RSI': df['RSI'].values,
        'Rel_Vol': df['Rel_Vol'].values,
        'Move': df['Move'].values,
        'Avg_Turnover': df['Avg_Turnover'].values,
        'Dates': df.index.values,
        'length': len(df)
    }
    
    # resistance arrays
    if lookbacks:
        for lb in lookbacks:
            # Check if column exists in df, else calculate on the fly
            col = f'Res_{lb}'
            if col in df.columns:
                data[col] = df[col].values
            else:
                data[col] = df['High'].rolling(lb).max().shift(1).values
                
    return data

def warm_up_universe(tickers=None, include_adv=False):
    """
    Bulk pre-calculates indicators for the entire universe (or a subset).
    Returns basic stats about the warm-up run.
    """
    start_t = time.time()
    
    if tickers is None:
        from core.DataManager import DataManager
        tickers = DataManager.list_tickers()
        
    logger.info(f"StockLoader: Warming up cache for {len(tickers)} tickers (adv={include_adv})")
    
    success_count = 0
    for ticker in tickers:
        try:
            df = load_stock_with_indicators(ticker, include_adv=include_adv)
            if df is not None:
                success_count += 1
        except Exception:
            continue
            
    elapsed = time.time() - start_t
    logger.info(f"StockLoader: Warm-up complete. {success_count}/{len(tickers)} cached in {elapsed:.2f}s")
    return {
        "status": "completed",
        "tickers_requested": len(tickers),
        "tickers_cached": success_count,
        "elapsed_seconds": round(elapsed, 2)
    }
