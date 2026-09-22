"""
VECTORIZED STRATEGY OPTIMIZER WITH MULTIPROCESSING
===================================================
Ultra-fast optimization using NumPy vectorization + multiprocessing.
Shows real-time progress: completed/total with ETA.
Uses SignalEngine for consistent logic with Live Scanner.
"""

from core.settings import settings
import pandas as pd
import time
import json
import numpy as np
import os
import glob
import datetime
import itertools
import inspect
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from core import TimeUtils
import warnings
import traceback
from multiprocessing import Pool, cpu_count
from core.market import MarketLists
from core import SignalEngine   # Logic Decoupling
from core.market.IntradayRealism import  IntradayValidator
from core.DataManager import DataManager
from core import StockLoader


warnings.filterwarnings('ignore')

# --- PARAMETER GRID ---
PARAM_GRID = {
    'VOL_SPIKE': [1.2, 1.5, 2.0, 3.0],
    'MOMENTUM': [0.5, 1.5, 2.5, 3.0],
    'RSI_MIN': [40, 50, 60],
    'RSI_MAX': [75, 85, 90],
    'SL_PCT': [1.0, 1.5, 2.0, 3.0],
    'TP1_PCT': [2.0, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0, 12.5, 15.0],
    'LOOKBACK': [10, 30, 60]
}

# Global data storage for multiprocessing
GLOBAL_DATA = None

def init_worker(shared_data):
    """Initialize worker process with GLOBAL_DATA (Only used by ProcessPoolExecutor)."""
    global GLOBAL_DATA
    GLOBAL_DATA = shared_data

def load_and_prepare_data(
    allowed_tickers=None,
    start=None,
    end=None,
    include_live=False,
    min_rows=200,
    param_grid=None,
):
    """Load stock data from configured source and pre-calculate indicators."""
    print(f"Loading stock data from {settings.DATA_SOURCE_TYPE}...")
    effective_grid = param_grid or PARAM_GRID
    lookbacks = effective_grid.get('LOOKBACK', [settings.LOOKBACK])
    start_ts = pd.to_datetime(start) if start is not None else None
    end_ts = pd.to_datetime(end) if end is not None else None

    # Use DataManager to get unified ticker list
    available_tickers = DataManager.list_tickers()
    
    all_data = []
    
    for ticker in available_tickers:
        if allowed_tickers and ticker not in allowed_tickers: continue
        
        # Load Calculated Data (Indicators already added)
        df = StockLoader.load_stock_with_indicators(ticker, include_adv=False)
        if df is None:
            continue
            
        # Date Filter
        if start_ts is not None:
            df = df.loc[df.index >= start_ts]
        if end_ts is not None:
            df = df.loc[df.index <= end_ts]
            
        if df is None or len(df) < min_rows:
            continue
            
        # Convert to Optimizer Dict
        stock_data = StockLoader.to_optimizer_dict(df, ticker, lookbacks=lookbacks)
        
        # --- [OPTIMIZATION] PRE-CALCULATE VALIDATION MASK ---
        # The validation mask (turnover/volume confirmation) only depends on price/volume data
        # which is constant during the optimization. Calculating it once saves O(N) DF 
        # creations in the hot loop.
        try:
            # We use settings from GlobalSettings as a baseline
            from core.SignalEngine import _validate_long_candidates
            v_mask = _validate_long_candidates(stock_data, settings)
            if v_mask is not None:
                stock_data['validation_mask'] = v_mask['is_valid'].to_numpy(dtype=bool)
        except Exception as e:
            print(f"Warning: Could not pre-calculate validation mask for {ticker}: {e}")
            
        all_data.append(stock_data)
            
    print(f"Loaded {len(all_data)} stocks for optimization.\n")
    return all_data

def _save_optimization_checkpoint(index_choice, results, completed, total):
    """Save intermediate results to disk to prevent data loss (H3.2)"""
    try:
        checkpoint_dir = Path("storage/checkpoints")
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Sort and take top 50 to keep checkpoint files small
        current_results = list(results)
        current_results.sort(key=lambda x: x['score'], reverse=True)
        top_results = sanitize_floats(current_results[:50])
        
        filename = f"opt_{index_choice}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_p{completed}.json"
        target = checkpoint_dir / filename
        
        with open(target, 'w') as f:
            json.dump({
                "index_choice": index_choice,
                "completed": completed,
                "total": total,
                "timestamp": datetime.datetime.now().isoformat(),
                "top_results": top_results
            }, f, indent=4)
        
        # Keep only the last 3 checkpoints for this run type to save space
        all_checks = sorted(checkpoint_dir.glob(f"opt_{index_choice}_*.json"), key=os.path.getmtime)
        if len(all_checks) > 3:
            for old in all_checks[:-3]:
                try: os.remove(old)
                except: pass
                
    except Exception as e:
        print(f"Warning: Checkpoint failed: {e}")

def vectorized_backtest_single(params, all_data=None):
    """Backtest a single parameter combination (using SignalEngine logic equivalent)."""
    if all_data is None:
            if all_data is None: return None
    
    total_wins = 0
    total_losses = 0
    total_return = 0.0
    
    # Extract Params
    vol_spike = params['VOL_SPIKE']
    momentum = params['MOMENTUM']
    rsi_min = params['RSI_MIN']
    rsi_max = params['RSI_MAX']
    sl_pct = params['SL_PCT']
    tp1_pct = params['TP1_PCT']
    lookback = params['LOOKBACK']
    trailing_value = params.get('TRAILING_STOP_VALUE', 0.0)
    
    for stock in all_data:
        n = stock['length']
        if n < 100: continue
        
        # Slicing for valid range (Reserve space for forward window)
        lookback = params['LOOKBACK']
        holding_period = params.get('HOLDING_PERIOD')
        if holding_period is None:
            # Divine Scaling: 1/2 of LOOKBACK for short terms, 1/3 for long terms
            if lookback <= 20: holding_period = 10
            elif lookback <= 40: holding_period = 20
            else: holding_period = 30
            
        start = 60
        end = n - 60
        
        # --- SIGNAL LOGIC (Unified via SignalEngine) ---
        full_settings = _inject_global_defaults(params)
        
        # Use pre-calculated mask if available (Saves O(N) memory/CPU)
        v_mask = stock.get('validation_mask')
        full_signals = SignalEngine.vectorize_signals(stock, full_settings, f'Res_{lookback}', validation_mask=v_mask)
        
        if full_signals is None: continue
            
        valid = full_signals[start:end]
        if valid.sum() == 0: continue
        
        # Close array
        close = stock['Close']
        entry_prices = close[start:end][valid]
        
        # targets
        stop = entry_prices * (1 - sl_pct/100)
        target = entry_prices * (1 + tp1_pct/100)
        
        # Path-Aware Vectorization (Pessimistic)
        count = valid.sum()
        hit_target_day = np.full(count, 999.0)
        hit_stop_day = np.full(count, 999.0)
        
        valid_indices = np.where(valid)[0] + start
        
        high_array = stock['High']
        low_array = stock['Low']
        
        for d in range(1, holding_period + 1):
            day_high = high_array[valid_indices + d]
            day_low = low_array[valid_indices + d]
            
            # Identify first day target or stop is hit
            t_mask = (day_high >= target) & (hit_target_day == 999.0)
            s_mask = (day_low <= stop) & (hit_stop_day == 999.0)
            
            hit_target_day[t_mask] = d
            hit_stop_day[s_mask] = d
            
        # Outcome: Win only if target hit BEFORE stop
        # Pessimistic: If both on same day, Stop wins
        actual_win = hit_target_day < hit_stop_day
        actual_loss = hit_stop_day <= hit_target_day
        time_exit = (hit_target_day == 999.0) & (hit_stop_day == 999.0)
        
        # End Price for Time Exits
        end_prices = stock['Close'][valid_indices + holding_period]
        
        pnl = np.where(actual_win, tp1_pct,
              np.where(actual_loss, -sl_pct,
              ((end_prices - entry_prices)/entry_prices)*100))
              
        # Costs
        total_costs = (2 * settings.COMMISSION_PCT) + (2 * getattr(settings, 'SLIPPAGE_PCT', 0.5))
        pnl -= total_costs
        
        total_wins += (pnl > 0).sum()
        total_losses += (pnl <= 0).sum()
        total_return += pnl.sum()
        
    total = total_wins + total_losses
    if total == 0: return None
    
    # DIVINE SCORING: Win Rate * Avg Return * (Wins / max(Losses, 1))
    win_rate = total_wins / total * 100
    avg_return = total_return / total
    score = win_rate * max(avg_return, 0.01) * (total_wins / max(total_losses, 1))
    
    return {
        'params': params,
        'trades': total,
        'win_rate': round(win_rate, 2),
        'avg_return': round(avg_return, 2),
        'score': round(score, 4)
    }

def _worker_accepts_all_data(worker):
    """Keep compatibility with injected backtest workers that only accept params."""
    try:
        signature = inspect.signature(worker)
    except (TypeError, ValueError):
        return True

    for parameter in signature.parameters.values():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            return True
        if parameter.name == "all_data":
            return True
    return False

def _run_vectorized_backtest_worker(params, all_data=None, worker=None, accepts_all_data=None):
    target_worker = worker or vectorized_backtest_single
    supports_all_data = accepts_all_data
    if supports_all_data is None:
        supports_all_data = _worker_accepts_all_data(target_worker)

    if supports_all_data:
        return target_worker(params, all_data=all_data)
    return target_worker(params)

def sanitize_floats(obj):
    if isinstance(obj, (float, np.float32, np.float64)): 
        return 0.0 if (np.isnan(obj) or np.isinf(obj)) else float(obj)
    elif isinstance(obj, np.generic): return sanitize_floats(obj.item())
    elif isinstance(obj, dict): return {k: sanitize_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list): return [sanitize_floats(x) for x in obj]
    return obj

def _resolve_universe_tickers(universe):
    if universe is None:
        return None
    if isinstance(universe, (set, list, tuple)):
        return set(universe)
    if isinstance(universe, str):
        choice = universe.strip().upper()
        known_indices = {"ALL", "30", "70", "100", "EGX30", "EGX70", "EGX100"}
        if choice in known_indices:
            return MarketLists.get_market_list(choice)
        # Any other string is treated as a single ticker symbol.
        return {universe.strip().upper()}
    return None

def _inject_global_defaults(params):
    return SignalEngine.merge_strategy_defaults(params)

def optimize_strategy_vectorized(
    tickers=None,
    start=None,
    end=None,
    param_grid=None,
    max_workers=None,
    sort_by='Net_Profit',
):
    """
    Main Orchestrator for Hyper-Parameter Optimization.
    Uses Vectorized Simulation logic for speed.
    Now uses ProcessPoolExecutor for true CPU parallelization (No GIL).
    """
        
    # 1. Prepare Data
    allowed_tickers = _resolve_universe_tickers(tickers)
    GLOBAL_DATA = load_and_prepare_data(allowed_tickers=allowed_tickers, start=start, end=end, param_grid=param_grid)
    if not GLOBAL_DATA:
        return []
        
    start_time = time.time()
    
    # 2. Build Combinations
    grid = param_grid or PARAM_GRID
    keys = grid.keys()
    combinations = [dict(zip(keys, v)) for v in itertools.product(*grid.values())]
    
    print(f"Starting Vectorized Optimization across {len(combinations)} combinations using {max_workers or 'ALL'} cores...")
    
    results = []
    
    # 3. Parallel Execution (True Multiprocessing)
    # We pass GLOBAL_DATA once to the initializer to keep processes fast
    with ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker, initargs=(GLOBAL_DATA,)) as executor:
        futures = {executor.submit(vectorized_backtest_single, p): p for p in combinations}
        
        count = 0
        for future in as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
            
            count += 1
            if count % 100 == 0:
                print(f"Progress: {count}/{len(combinations)} ({(count/len(combinations))*100:.1f}%)")
                
    results.sort(key=lambda x: x['score'], reverse=True)
    return sanitize_floats(results)

def run_brute_force(
    universe="ALL",
    start=None,
    end=None,
    progress_dict=None,
    top_n=1,
    param_grid=None,
    min_rows=100,
    max_workers=None,
    data_override=None,
    executor=None,
):
    """
    Run optimization on a bounded date range and return best params.
    Used by Walk-Forward Analysis (WFA) for rolling train windows.

    Args:
        universe: Index choice ("ALL", "EGX30", ...) OR a single ticker OR iterable of tickers.
        start: Training window start date.
        end: Training window end date.
        progress_dict: Optional shared dict for UI progress.
        top_n: Number of top candidates to return (1 returns params dict or None).
        param_grid: Optional grid override.
        min_rows: Minimum rows required after date filtering.
    """
    if top_n < 1:
        raise ValueError("top_n must be >= 1")

    grid = param_grid or PARAM_GRID
    keys = list(grid.keys())
    combos = [dict(zip(keys, values)) for values in itertools.product(*grid.values())]

    allowed_tickers = _resolve_universe_tickers(universe)
    
    if data_override is not None:
        all_data = data_override
    else:
        all_data = load_and_prepare_data(
            allowed_tickers=allowed_tickers,
            start=start,
            end=end,
            include_live=False,
            min_rows=min_rows,
            param_grid=grid,
        )

    if not all_data:
        if progress_dict is not None:
            progress_dict["status"] = "ERROR"
            progress_dict["error"] = "No Data"
        return None if top_n == 1 else []


    if progress_dict is not None:
        progress_dict["status"] = "RUNNING"
        progress_dict["total"] = len(combos)
        progress_dict["completed"] = 0

    completed = 0
    results = []
    worker = vectorized_backtest_single
    worker_accepts_all_data = _worker_accepts_all_data(worker)
    
    # Helper to process futures using THREADS (NumPy releases GIL)
    # This is MUCH faster on Windows for small-data/high-grid optimization
    import concurrent.futures
    def _run_threaded(executor_obj):
        try:
             # Submit all combinations
             futures = {
                 executor_obj.submit(
                     _run_vectorized_backtest_worker,
                     combo,
                     all_data,
                     worker,
                     worker_accepts_all_data,
                 ): combo
                 for combo in combos
             }
             for future in concurrent.futures.as_completed(futures):
                  res = future.result()
                  if res: results.append(res)
        except Exception as e:
             print(f"  Brute Force Threading Error: {e}")

    if max_workers == 1:
          for combo in combos:
               completed += 1
               res = _run_vectorized_backtest_worker(
                   combo,
                   all_data,
                   worker,
                   worker_accepts_all_data,
               )
               if res: results.append(res)
               if progress_dict is not None and completed % 25 == 0:
                   progress_dict["completed"] = completed
                   progress_dict["progress"] = round((completed / len(combos)) * 100, 1)
    elif executor is not None:
         # USE EXTERNAL REUSABLE POOL (THREADS)
         _run_threaded(executor)
    else:
         # Create temporary thread pool
         # ThreadPoolExecutor is stable and has zero pickling overhead
         max_t = max_workers or min(32, cpu_count() * 4) # Threads can be higher for I/O but here we match CPU
         with concurrent.futures.ThreadPoolExecutor(max_workers=max_t) as temp_executor:
              _run_threaded(temp_executor)

    if not results:
        if progress_dict is not None:
            progress_dict["status"] = "COMPLETED"
            progress_dict["result"] = []
        return None if top_n == 1 else []

    results.sort(key=lambda x: x['score'], reverse=True)
    unique_results = []
    seen_profiles = set()
    for r in results:
        profile = (
            round(r['score'], 4), 
            round(r['win_rate'], 4), 
            r['trades'], 
            round(r['avg_return'], 4),
            r['params'].get('TP1_PCT'),
            r['params'].get('SL_PCT')
        )
        if profile in seen_profiles:
            continue
        normalized = dict(r)
        normalized['params'] = _inject_global_defaults(r['params'])
        unique_results.append(normalized)
        seen_profiles.add(profile)

    selected = sanitize_floats(unique_results[:top_n])
    if progress_dict is not None:
        progress_dict["status"] = "COMPLETED"
        progress_dict["result"] = selected

    if top_n == 1:
        return selected[0]['params'] if selected else None
    return selected

def run_optimization_api(index_choice="ALL", progress_dict=None):
        # Wrapper for API ... matching previous implementation structure
    # ... (Keep logic for spawning pool) ...
    try:
        if progress_dict is not None:
            progress_dict["status"] = "PREPARING"
            progress_dict["progress"] = 0
            
        # Calculate total
        total_combos = 1
        for k, v in PARAM_GRID.items(): total_combos *= len(v)
            
        market_filter = MarketLists.get_market_list(index_choice)
        all_data = load_and_prepare_data(market_filter)
        
        if not all_data:
             if progress_dict: progress_dict["status"] = "ERROR"; progress_dict["error"] = "No Data"
             return []
             
        keys = list(PARAM_GRID.keys())
        combos = [dict(zip(keys, v)) for v in itertools.product(*PARAM_GRID.values())]
        
        if progress_dict:
            progress_dict["status"] = "RUNNING"
            progress_dict["total"] = total_combos
            progress_dict["completed"] = 0
        
        completed = 0
        results = []
        start_time = datetime.datetime.now()
        worker = vectorized_backtest_single
        worker_accepts_all_data = _worker_accepts_all_data(worker)
        
        # USE MULTIPROCESSING (THREADS) FOR STABILITY ON WINDOWS
        # Multiprocessing on Windows can hang due to spawn issues with complex imports.
        # Threads are safer here as NumPy releases GIL.
        import concurrent.futures
        from functools import partial
        bound_worker = partial(
            _run_vectorized_backtest_worker,
            all_data=all_data,
            worker=worker,
            accepts_all_data=worker_accepts_all_data,
        )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, cpu_count() * 4)) as executor:
             # Submit all jobs
             future_to_combo = {executor.submit(bound_worker, combo): combo for combo in combos}
             
             for future in concurrent.futures.as_completed(future_to_combo):
                 try:
                     result = future.result()
                     completed += 1
                     if result: results.append(result)
                     
                     if progress_dict and completed % 50 == 0:
                         elapsed = (datetime.datetime.now() - start_time).total_seconds()
                         rate = completed / elapsed if elapsed > 0 else 0
                         eta = (total_combos - completed) / rate if rate > 0 else 0
                         progress_dict["progress"] = round((completed/total_combos)*100, 1)
                         progress_dict["completed"] = completed
                         progress_dict["eta"] = round(eta, 0)
                         progress_dict["found"] = len(results)
                         if results:
                             best = max(results, key=lambda x: x['score'])
                             progress_dict["best_win_rate"] = sanitize_floats(round(best['win_rate'], 1))
                             
                         # [PHASE 3] Intermediate Checkpointing (H3.2)
                         if completed % 100 == 0:
                             _save_optimization_checkpoint(index_choice, results, completed, total_combos)

                 except Exception as exc:
                     print(f"Task generated an exception: {exc}")

        if results:
 
            results.sort(key=lambda x: x['score'], reverse=True)
            
            # DEDUPLICATION: Remove identical results (performance profiles)
            unique_results = []
            seen_profiles = set()
            for r in results:
                profile = (
                    round(r['score'], 4), 
                    round(r['win_rate'], 4), 
                    r['trades'], 
                    round(r['avg_return'], 4),
                    r['params'].get('TP1_PCT'),
                    r['params'].get('SL_PCT')
                )
                if profile not in seen_profiles:
                    normalized = dict(r)
                    normalized['params'] = _inject_global_defaults(r['params'])
                    unique_results.append(normalized)
                    seen_profiles.add(profile)
            results = unique_results

            # SHARE INTERMEDIATE RESULTS IMMEDIATELY
            if progress_dict:
                progress_dict["result"] = sanitize_floats(results[:50])
                progress_dict["status"] = "VALIDATING"
        
        
        if results:
            print("\n[PHASE 6] Starting Intraday Reality Check on Top Candidates...")
            validator = IntradayValidator()
            top_candidates = results[:3] # Validate top 3
            
            for i, strat in enumerate(top_candidates):
                if progress_dict is not None:
                    progress_dict["status"] = f"VALIDATING ({i+1}/3)"
                
                # We need to re-generate signals for this strategy to get dates and prices
                # Use Global Data (already loaded)
                
                # Simplify: Just validate on one representative stock (e.g. COMI) if available, 
                # or random sample to save time? 
                # Better: Validate on highly active stocks where intraday data is most reliable.
                
                real_wins = 0
                real_losses = 0
                total_real_trades = 0
                
                # Scan through GLOBAL_DATA to find trades for this strategy
                # Limit to last 6 months (Intraday Data Range)
                cutoff_date = TimeUtils.now() - datetime.timedelta(days=180)
                
                def validate_stock_h6(stock):
                    ticker = stock['ticker']
                    full_settings = _inject_global_defaults(strat['params'])
                    
                    if 'Dates' not in stock:
                        return 0, 0, 0
                    full_signals = SignalEngine.vectorize_signals(stock, full_settings, f"Res_{full_settings['LOOKBACK']}")
                    dates_arr = stock.get('Dates', [])
                    if len(dates_arr) == 0:
                        return 0, 0, 0
                        
                    dates = pd.to_datetime(dates_arr)
                    valid_mask = (dates > cutoff_date)
                    final_mask = full_signals & valid_mask
                    signal_indices = np.where(final_mask)[0]
                    
                    s_wins, s_losses, s_total = 0, 0, 0
                    if len(signal_indices) == 0:
                        return s_wins, s_losses, s_total
                        
                    if len(signal_indices) > 50:
                        signal_indices = np.random.choice(signal_indices, size=50, replace=False)
                    
                    for idx in signal_indices:
                        s_total += 1
                        signal_date = dates[idx]
                        entry_price = float(stock['Close'][idx])
                        sl_pct = full_settings['SL_PCT']
                        tp_pct = full_settings['TP1_PCT']
                        sl_price = entry_price * (1 - sl_pct/100)
                        tp_price = entry_price * (1 + tp_pct/100)
                        
                        outcome = validator.validate_trade(
                            ticker, signal_date, entry_price, sl_price, tp_price,
                            trailing_stop=full_settings.get('TRAILING_STOP_VALUE')
                        )
                        if outcome['outcome'] == 'WIN': s_wins += 1
                        elif outcome['outcome'] == 'LOSS': s_losses += 1
                    return s_wins, s_losses, s_total

                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(32, len(all_data))) as executor:
                    futures = [executor.submit(validate_stock_h6, s) for s in all_data]
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            w, l, t = future.result()
                            real_wins += w
                            real_losses += l
                            total_real_trades += t
                        except Exception as e:
                            print(f"H6 intraday validation error: {e}")
                        
                # Calc Real Win Rate for this Strategy
                if total_real_trades > 0:
                    real_win_rate = (real_wins / total_real_trades) * 100
                    strat['real_win_rate'] = round(real_win_rate, 2)
                    strat['real_trades'] = total_real_trades
                    strat['drop_off'] = round(strat['win_rate'] - real_win_rate, 1)
                else:
                    strat['real_win_rate'] = 0.0
                    strat['real_trades'] = 0
                    strat['drop_off'] = 0.0
                    
                print(f"   Strategy #{i+1}: Daily WR {strat['win_rate']}% -> Real WR {strat['real_win_rate']}% ({total_real_trades} trades)")

        sanitized = sanitize_floats(results[:50])
        if progress_dict is not None:
            progress_dict["status"] = "COMPLETED"
            progress_dict["result"] = sanitized
            
        return sanitized
    except Exception as e:
        err_msg = f"Optimizer Crash: {str(e)}\n{traceback.format_exc()}"
        print(err_msg)
        if progress_dict: 
            progress_dict["status"] = "ERROR"
            progress_dict["error"] = str(e) # Send short error to UI
        return []

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()
    run_optimization_api()
