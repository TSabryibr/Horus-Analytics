
from core.settings import settings
import sys

# M4 Fix in data_engine/api.py
with open("data_engine/api.py", "r", encoding="utf-8") as f:
    content = f.read()

old_str = """    # 2. Partitioned files glob (ensures latest data in by_date is captured)
    part_glob = DATA_ROOT / realm / tf / "by_date" / "*" / "*.parquet"
    if any((DATA_ROOT / realm / tf / "by_date").glob("*")):
        valid_paths.append(str(part_glob.as_posix()))"""

new_str = """    # 2. Partitioned files glob (ensures latest data in by_date is captured)
    by_date_dir = DATA_ROOT / realm / tf / "by_date"
    if by_date_dir.exists() and any(by_date_dir.glob("*")):
        part_glob = by_date_dir / "*" / "*.parquet"
        valid_paths.append(str(part_glob.as_posix()))"""

content = content.replace(old_str, new_str)
with open("data_engine/api.py", "w", encoding="utf-8") as f:
    f.write(content)


# M3 Fix in Mimir_WFA.py
with open("core/Mimir_WFA.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("from concurrent.futures import ProcessPoolExecutor   # Use Processes for CPU-bound WFA\n", "")

old_func = """def _score_wfa_window_worker(args):
    \"\"\"Worker function for ProcessPoolExecutor.\"\"\"
    win, ticker, indicator_data, cached_df = args
    
    # 1. Prep slice for optimization
    lb_grid = Optimizer.PARAM_GRID.get('LOOKBACK', [10, 30, 60])
    
    stock_data = {
         'index': cached_df.index,
         'ticker': ticker,
         'length': len(cached_df)
    }
    
    # First LB to pull common columns
    first_lb = lb_grid[0] if lb_grid else 30
    base_ind_df = indicator_data.get(first_lb, cached_df)
    common_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Move', 'RSI', 'Rel_Vol', 'Avg_Turnover', 'ATR', 'EMA9', 'EFI']
    for col in common_cols:
         if col in base_ind_df.columns:
              stock_data[col] = base_ind_df[col].to_numpy()
         elif col in cached_df.columns:
              stock_data[col] = cached_df[col].to_numpy()

    # Add lookback-specific columns
    for lb in lb_grid:
         df_lb = indicator_data.get(lb)
         if df_lb is not None:
              for col in [f"EMA_{lb}", f"Res_{lb}", f"Sup_{lb}", f"ATR_{lb}", f"EMA_f_{lb}"]:
                   if col in df_lb.columns:
                        stock_data[col] = df_lb[col].to_numpy()
    
    data_pool = [stock_data]

    best_settings = Optimizer.run_brute_force(
        ticker,
        start=win["train_start"],
        end=win["train_end"],
        min_rows=90,
        data_override=data_pool,
        max_workers=1
    )

    if best_settings is None:
        validation = {
            "total_return_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": 0,
            "bars": 0,
            "win_rate_pct": 0.0,
            "reason": "no_train_solution",
            "trade_allowed": False,
        }
    else:
        lb = int(best_settings.get("LOOKBACK", settings.LOOKBACK))
        win_df = indicator_data.get(lb, cached_df)
        validation = _validate_window_settings(ticker, best_settings, win["train_end"], win["val_end"], win_df)

    win["params"] = best_settings
    win["val_perf"] = validation
    return win"""

content = content.replace(old_func, "")
with open("core/Mimir_WFA.py", "w", encoding="utf-8") as f:
    f.write(content)

# H6 Fix in Optimizer.py: parallelize validator intraday
with open("Optimizer.py", "r", encoding="utf-8") as f:
    opt_content = f.read()

old_h6_loop = """                real_wins = 0
                real_losses = 0
                total_real_trades = 0
                
                # Scan through GLOBAL_DATA to find trades for this strategy
                # Limit to last 6 months (Intraday Data Range)
                cutoff_date = TimeUtils.now() - datetime.timedelta(days=180)
                
                for stock in all_data:
                    ticker = stock['ticker']
                    
                    # Convert settings
                    full_settings = strat['params'].copy()
                    if 'MIN_TURNOVER' not in full_settings: full_settings['MIN_TURNOVER'] = settings.MIN_TURNOVER
                    if 'VOL_SPIKE' not in full_settings: full_settings['VOL_SPIKE'] = settings.VOL_SPIKE
                    
                    # Generate signals
                    # We need a way to get signal dates quickly.
                    # SignalEngine.vectorize_signals returns a boolean array.
                    # We need to map boolean array back to Dates.
                    
                    if 'Dates' not in stock:
                        continue
                        
                    # Calculate signals
                    full_signals = SignalEngine.vectorize_signals(stock, full_settings, f"Res_{full_settings['LOOKBACK']}")
                    
                    # Get indices where signal is True
                    # Limit to indices corresponding to dates > cutoff_date
                    dates_arr = stock.get('Dates', [])
                    if len(dates_arr) == 0:
                        continue
                        
                    dates = pd.to_datetime(dates_arr)
                    valid_mask = (dates > cutoff_date)
                    
                    # Combine signal mask and date mask
                    final_mask = full_signals & valid_mask
                    signal_indices = np.where(final_mask)[0]
                    
                    # --- PERFORMANCE FIX: Random Sample 50 trades max ---
                    if len(signal_indices) > 50:
                        signal_indices = np.random.choice(signal_indices, size=50, replace=False)
                    
                    for idx in signal_indices:
                        total_real_trades += 1
                        
                        # Extract trade details
                        signal_date = dates[idx]
                        entry_price = float(stock['Close'][idx]) # Optimistic: Enter at Close
                        
                        sl_pct = full_settings['SL_PCT']
                        tp_pct = full_settings['TP1_PCT']
                        
                        sl_price = entry_price * (1 - sl_pct/100)
                        tp_price = entry_price * (1 + tp_pct/100)
                        
                        # Validate with Trailing Stop support
                        outcome = validator.validate_trade(
                            ticker, 
                            signal_date, 
                            entry_price, 
                            sl_price, 
                            tp_price,
                            trailing_stop=full_settings.get('TRAILING_STOP_VALUE')
                        )
                        
                        if outcome['outcome'] == 'WIN':
                            real_wins += 1
                        elif outcome['outcome'] == 'LOSS':
                            real_losses += 1
                        # Time exit count as loss or neutral? Usually treated as loss of opportunity or small loss.
                        # For Win Rate calc, we usually count WIN / Total."""

new_h6_loop = """                real_wins = 0
                real_losses = 0
                total_real_trades = 0
                
                # Scan through GLOBAL_DATA to find trades for this strategy
                # Limit to last 6 months (Intraday Data Range)
                cutoff_date = TimeUtils.now() - datetime.timedelta(days=180)
                
                def validate_stock_h6(stock):
                    ticker = stock['ticker']
                    full_settings = strat['params'].copy()
                    if 'MIN_TURNOVER' not in full_settings: full_settings['MIN_TURNOVER'] = settings.MIN_TURNOVER
                    if 'VOL_SPIKE' not in full_settings: full_settings['VOL_SPIKE'] = settings.VOL_SPIKE
                    
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
                            print(f"H6 intraday validation error: {e}")"""

opt_content = opt_content.replace(old_h6_loop, new_h6_loop)
with open("Optimizer.py", "w", encoding="utf-8") as f:
    f.write(opt_content)

print("Done")
