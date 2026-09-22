"""
PORTFOLIO SIMULATOR
===================
Simulates trading 200K EGP starting from January 2025 using the STA strategy.

Settings:
- Starting Capital: 200,000 EGP
- Position Sizing: Equal allocation (portfolio / max_positions)
- Max Concurrent Positions: 10
- Currency: EGP stocks only
- Strategy: Optimized STA parameters

Author: Horus Analytics - EGX
Date: 2026-01-12
"""

from core.settings import settings
from core.exclusions import EXCLUDED_TICKERS
import pandas as pd
import numpy as np
import glob
import os
import datetime
import warnings
from core.market import MarketLists
from core.DataManager import DataManager
from core import StockLoader
from core.execution_model import (
    build_microstructure_contract,
    build_shadow_diagnostics,
    estimate_fill,
    prepare_adv_metrics,
)
from core.market_profiles import EGX30_TREND_PROFILE, EGX70_TACTICAL_PROFILE
warnings.filterwarnings('ignore')

# === SIMULATION SETTINGS (from GlobalSettings) ===
STARTING_CAPITAL = settings.STARTING_CAPITAL
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"
MAX_POSITIONS = settings.MAX_POSITIONS
HOLDING_PERIOD = 20

# === STRATEGY PARAMETERS ===
DATA_FOLDER = settings.DATA_FOLDER
LOOKBACK = settings.LOOKBACK
VOL_SPIKE_FACTOR = settings.VOL_SPIKE
MOMENTUM_THRESHOLD = settings.MOMENTUM
RSI_MIN = settings.RSI_MIN
RSI_MAX = settings.RSI_MAX
SL_BUFFER_PCT = settings.SL_PCT
TP1_PCT = settings.TP1_PCT
TP2_RR_RATIO = 2.0
MIN_TURNOVER = settings.MIN_TURNOVER
COMMISSION_PCT = settings.COMMISSION_PCT
SLIPPAGE_PCT = getattr(settings, 'SLIPPAGE_PCT', 0.5)

def load_all_stocks(allowed_tickers=None, params=None):
    """
    Load stock data from configured source (CSV or MetaStock).
    If allowed_tickers is set (set of strings), only load those tickers.
    """
    print(f"Loading stock data from {settings.DATA_SOURCE_TYPE}...")
    
    # Get available tickers from current data source
    tickers = DataManager.list_tickers()
    tickers = [t for t in tickers if t.upper() not in ['REPORT', 'EGX30_70_100']]
    
    stocks = {}
    
    for ticker in tickers:
        # Skip Excluded stocks
        if ticker in EXCLUDED_TICKERS:
            continue
            
        # Filter by Index (if specified)
        if allowed_tickers is not None:
            if ticker not in allowed_tickers:
                continue
        
        try:
            # Load data from configured source
            df = DataManager.get_stock_data(ticker, include_live=False)
            if df is None:
                continue
                
            # Normalize column names
            if 'Closed' in df.columns and 'Close' not in df.columns:
                df.rename(columns={'Closed': 'Close'}, inplace=True)
            df.columns = df.columns.str.strip().str.title()
            
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                df.set_index('Date', inplace=True)
            df.sort_index(ascending=True, inplace=True)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            required = ['Open', 'High', 'Low', 'Close', 'Volume']
            if not all(col in df.columns for col in required):
                continue
            
            if len(df) < 100:
                continue
            
            # Standardize indicator calculation via SignalEngine
            from core import SignalEngine
            lookback = params.get('LOOKBACK', settings.LOOKBACK) if params else settings.LOOKBACK
            df = SignalEngine.add_indicators(df, lookback=lookback)
            df = prepare_adv_metrics(df, window=10)
            
            stocks[ticker] = df
            
        except Exception as e:
            continue
    
    print(f"Loaded {len(stocks)} EGP stocks\n")
    return stocks

def check_signal(df, date, params=None):
    """
    Legacy compatibility wrapper for check_signal.
    In the optimized run_simulation, we use precomputed bitmasks instead.
    """
    if date not in df.index: return None
    idx = df.index.get_loc(date)
    if idx < 60: return None
    
    try:
        # This function is kept for backward compatibility but is slower than the vectorized lookup
        from core import SignalEngine
        active_settings = params or settings
        lookback = params.get('LOOKBACK', active_settings.LOOKBACK) if params else active_settings.LOOKBACK
        res_col = f'Res_{lookback}'
        if res_col not in df.columns:
            df[res_col] = df['High'].rolling(lookback).max().shift(1)
        
        row = df.iloc[idx]
        sig = SignalEngine.check_buy_signal(row, active_settings, resistance_col=res_col)
        if sig:
            return {
                'entry_price': sig['Entry_Price'],
                'stop_loss': sig['Stop_Loss'],
                'target1': sig['Target_Price'],
                'target2': sig['Target_Price_2'],
                'score': sig['Score']
            }
    except Exception:
        pass
    return None

def check_exit(df, entry_date, entry_price, stop_loss, target1, target2, params=None):
    """Check if position should be exited - supports trailing stops"""
    if entry_date not in df.index:
        return None
    
    entry_idx = df.index.get_loc(entry_date)
    
    if params is None: params = {}
    
    trailing_enabled = params.get('TRAILING_STOP_ENABLED', settings.TRAILING_STOP_ENABLED)
    trailing_type = params.get('TRAILING_STOP_TYPE', settings.TRAILING_STOP_TYPE)
    trailing_value = params.get('TRAILING_STOP_VALUE', settings.TRAILING_STOP_VALUE)
    
    current_stop = stop_loss
    highest_price = entry_price
    
    for days_held in range(1, HOLDING_PERIOD + 1):
        if entry_idx + days_held >= len(df):
            break
        
        current_date = df.index[entry_idx + days_held]
        high = df['High'].iloc[entry_idx + days_held]
        low = df['Low'].iloc[entry_idx + days_held]
        
        # === TRAILING STOP LOGIC ===
        if trailing_enabled and high > highest_price:
            highest_price = high
            
            if trailing_type == "FIXED":
                new_stop = highest_price * (1 - trailing_value / 100)
            elif trailing_type == "ATR":
                atr = df['ATR'].iloc[entry_idx + days_held] if 'ATR' in df.columns else 0
                if pd.notna(atr) and atr > 0:
                    new_stop = highest_price - (atr * trailing_value)
                else:
                    new_stop = current_stop
            else:  # PERCENT
                profit = highest_price - entry_price
                new_stop = entry_price + (profit * (1 - trailing_value / 100))
            
            if new_stop > current_stop:
                current_stop = new_stop
        
        # Check exit conditions
        if high >= target2:
            return {'exit_date': current_date, 'exit_price': target2, 'reason': 'TARGET2'}
        elif high >= target1:
            return {'exit_date': current_date, 'exit_price': target1, 'reason': 'TARGET1'}
        elif low <= current_stop:
            reason = 'TRAILING_STOP' if trailing_enabled and current_stop > stop_loss else 'STOP_LOSS'
            return {'exit_date': current_date, 'exit_price': current_stop, 'reason': reason}
    
    if entry_idx + HOLDING_PERIOD < len(df):
        exit_date = df.index[entry_idx + HOLDING_PERIOD]
        exit_price = df['Close'].iloc[entry_idx + HOLDING_PERIOD]
        return {'exit_date': exit_date, 'exit_price': exit_price, 'reason': 'TIME_EXIT'}
    
    return None

def run_simulation(cap=None, start_date=None, end_date=None, index_choice=None, max_positions=None, params=None):
    """Run the portfolio simulation"""
    print("\n" + "=" * 70)
    print("PORTFOLIO SIMULATOR")
    print("=" * 70)
    
    starting_capital = cap if cap is not None else None
    start_date_str = start_date if start_date is not None else START_DATE
    end_date_str = end_date if end_date is not None else END_DATE
    max_pos = max_positions if max_positions is not None else MAX_POSITIONS
    
    if starting_capital is None:
        try:
            cap_str = input(f"Starting Capital [{STARTING_CAPITAL}]: ").strip()
            starting_capital = float(cap_str) if cap_str else STARTING_CAPITAL
            start_str = input(f"Start Date [{START_DATE}]: ").strip()
            start_date_str = start_str if start_str else START_DATE
            end_str = input(f"End Date [{END_DATE}]: ").strip()
            end_date_str = end_str if end_str else END_DATE
            max_str = input(f"Max Positions [{MAX_POSITIONS}]: ").strip()
            max_pos = int(max_str) if max_str else MAX_POSITIONS
            idx_str = input(f"Index Filter (30/70/100/ALL) [ALL]: ").strip()
            market_filter = MarketLists.get_market_list(idx_str)
            filter_name = f"EGX {idx_str}" if market_filter else "ALL STOCKS"
        except ValueError:
            starting_capital = STARTING_CAPITAL
            start_date_str = START_DATE
            end_date_str = END_DATE
            market_filter = None
            filter_name = "ALL STOCKS"
    else:
        market_filter = MarketLists.get_market_list(index_choice) if index_choice else None
        filter_name = f"EGX {index_choice}" if index_choice else "ALL STOCKS"

    print(f"Starting Capital: {starting_capital:,.0f} EGP")
    print(f"Period: {start_date_str} to {end_date_str}")
    print(f"Universe: {filter_name}")
    print("=" * 70 + "\n")
    
    microstructure_diagnostics = build_shadow_diagnostics()
    active_profile = _select_simulation_profile(index_choice)
    run_commission_pct = _resolve_run_cost_pct(params, 'COMMISSION_PCT', COMMISSION_PCT)
    run_slippage_pct = _resolve_run_cost_pct(params, 'SLIPPAGE_PCT', SLIPPAGE_PCT)
    
    # Load stocks
    stocks = load_all_stocks(market_filter, params=params)
    
    # --- [OPTIMIZATION] PRE-CALCULATE SIGNALS ---
    print("Pre-calculating signals for the entire universe...")
    from core import SignalEngine
    precomputed_signals = {}
    for ticker, df in stocks.items():
        try:
            lookback = params.get('LOOKBACK', settings.LOOKBACK) if params else settings.LOOKBACK
            sig_mask = SignalEngine.vectorize_signals(df, params or settings, f'Res_{lookback}')
            if sig_mask is not None:
                precomputed_signals[ticker] = sig_mask
        except Exception as e:
            print(f"Warning: Could not pre-calculate signals for {ticker}: {e}")
    
    if not stocks:
        print("No stocks loaded!")
        return {
            'starting_capital': starting_capital,
            'final_value': starting_capital,
            'total_return': 0,
            'trades': [],
            'daily_values': [],
            'microstructure': build_microstructure_contract(microstructure_diagnostics),
        }
    
    sample_stock = list(stocks.values())[0]
    start = pd.to_datetime(start_date_str)
    end = pd.to_datetime(end_date_str)
    trading_dates = sample_stock.loc[start:end].index.tolist()
    
    print(f"Trading days: {len(trading_dates)}")
    
    cash = starting_capital
    positions = {}
    pending_entries = []
    trades = []
    daily_values = []
    
    print("\nRunning simulation...")
    
    for i, date in enumerate(trading_dates):
        if pd.isna(date): continue
        
        # Check exits
        tickers_to_close = []
        for ticker, pos in positions.items():
            df = stocks[ticker]
            exit_info = check_exit(df, pos['entry_date'], pos['entry_price'], 
                                   pos['stop_loss'], pos['target1'], pos['target2'], params)
            
            try:
                if exit_info and pd.notna(exit_info.get('exit_date')) and exit_info['exit_date'] <= date:
                    fill_row = df.loc[date]
                    exit_estimate = estimate_fill(
                        desired_shares=pos['shares'],
                        reference_price=float(exit_info['exit_price']),
                        adv_10_shares=fill_row.get('adv_10_shares'),
                        adv_10_notional=fill_row.get('adv_10_notional'),
                        profile=active_profile,
                        side='sell',
                        slippage_floor_pct=run_slippage_pct,
                    )
                    _record_execution_estimate(microstructure_diagnostics, exit_estimate, active_profile.name)
                    
                    sold_shares = exit_estimate.fillable_shares
                    exit_price = exit_estimate.effective_fill_price
                    entry_cost = (sold_shares * pos['entry_price']) * (run_commission_pct / 100)
                    exit_cost = (sold_shares * exit_price) * (run_commission_pct / 100)
                    total_fees = entry_cost + exit_cost
                    gross_pnl = (exit_price - pos['entry_price']) * sold_shares
                    pnl = gross_pnl - total_fees
                    invested = sold_shares * pos['entry_price']
                    pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
                    
                    cash += (sold_shares * exit_price) - exit_cost
                    trades.append({
                        'ticker': ticker,
                        'entry_date': pos['entry_date'],
                        'entry_price': pos['entry_price'],
                        'exit_date': date,
                        'exit_price': exit_price,
                        'shares': sold_shares,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'reason': exit_info['reason'],
                        'entry_rejected_shares': pos.get('entry_rejected_shares', 0),
                        'exit_rejected_shares': exit_estimate.rejected_shares,
                        'entry_slippage_pct': pos.get('entry_slippage_pct', 0.0),
                        'exit_slippage_pct': exit_estimate.slippage_pct,
                        'entry_commission': entry_cost,
                        'exit_commission': exit_cost,
                    })
                    if sold_shares >= pos['shares']:
                        tickers_to_close.append(ticker)
                    else:
                        pos['shares'] -= sold_shares
            except Exception as e:
                continue
        
        for ticker in tickers_to_close:
            del positions[ticker]

        # Fill pending entries
        still_pending = []
        for pending in pending_entries:
            if pending['fill_date'] != date:
                still_pending.append(pending)
                continue
            ticker = pending['ticker']
            if ticker in positions or ticker not in stocks: continue
            
            fill_row = stocks[ticker].loc[date]
            fill_estimate = estimate_fill(
                desired_shares=pending['desired_shares'],
                reference_price=float(fill_row['Open']),
                adv_10_shares=fill_row.get('adv_10_shares'),
                adv_10_notional=fill_row.get('adv_10_notional'),
                profile=active_profile,
                side='buy',
                slippage_floor_pct=run_slippage_pct,
            )
            _record_execution_estimate(microstructure_diagnostics, fill_estimate, active_profile.name)
            if fill_estimate.fillable_shares <= 0: continue
            
            fill_cost = fill_estimate.fillable_shares * fill_estimate.effective_fill_price
            entry_commission = fill_cost * (run_commission_pct / 100)
            total_entry_cost = fill_cost + entry_commission
            if total_entry_cost > cash:
                affordable_shares = int(cash / (fill_estimate.effective_fill_price * (1 + run_commission_pct / 100)))
                if affordable_shares <= 0: continue
                fill_estimate = estimate_fill(
                    desired_shares=affordable_shares,
                    reference_price=float(fill_row['Open']),
                    adv_10_shares=fill_row.get('adv_10_shares'),
                    adv_10_notional=fill_row.get('adv_10_notional'),
                    profile=active_profile,
                    side='buy',
                    slippage_floor_pct=run_slippage_pct,
                )
                fill_cost = fill_estimate.fillable_shares * fill_estimate.effective_fill_price
                entry_commission = fill_cost * (run_commission_pct / 100)
                total_entry_cost = fill_cost + entry_commission
                if fill_estimate.fillable_shares <= 0 or total_entry_cost > cash: continue
                
            cash -= total_entry_cost
            positions[ticker] = {
                'shares': fill_estimate.fillable_shares,
                'entry_price': fill_estimate.effective_fill_price,
                'entry_date': date,
                'stop_loss': pending['signal']['stop_loss'],
                'target1': pending['signal']['target1'],
                'target2': pending['signal']['target2'],
                'entry_rejected_shares': fill_estimate.rejected_shares,
                'entry_slippage_pct': fill_estimate.slippage_pct,
                'entry_commission': entry_commission,
            }
        pending_entries = still_pending
        
        # Daily Equity Curve
        port_val = cash
        for t, p in positions.items():
            if t in stocks and date in stocks[t].index:
                port_val += p['shares'] * stocks[t].loc[date, 'Close']
        daily_values.append({'date': date, 'value': port_val, 'cash': cash, 'positions': len(positions)})
        
        # New Signals (Looking ahead for next day execution)
        if len(positions) < max_pos:
            pos_size = cash / (max_pos - len(positions)) if cash > 0 else 0
            potentials = []
            for ticker, df in stocks.items():
                if ticker in positions: continue
                sig_mask = precomputed_signals.get(ticker)
                
                # We need to find the index of 'date' in the precomputed mask
                # Since stocks and trading_dates are aligned, we can use 'i'
                if sig_mask is not None and i < len(sig_mask) and sig_mask.iloc[i]:
                    cur_close = float(df['Close'].iloc[i])
                    sl_pct = params.get('SL_PCT', settings.SL_PCT) if params else settings.SL_PCT
                    tp_pct = params.get('TP1_PCT', settings.TP1_PCT) if params else settings.TP1_PCT
                    
                    potentials.append((ticker, {
                        'entry_price': cur_close,
                        'stop_loss': cur_close * (1 - sl_pct/100),
                        'target1': cur_close * (1 + tp_pct/100),
                        'target2': cur_close * (1 + (params.get('TP2_PCT', 4.0) if params else 4.0)/100),
                        'score': 10
                    }))
            
            potentials.sort(key=lambda x: x[1]['score'], reverse=True)
            available = max_pos - len(positions)
            for ticker, sig in potentials[:available]:
                if pos_size < 1000: break # Min trade size
                if i + 1 >= len(trading_dates): continue
                next_date = trading_dates[i+1]
                if next_date not in stocks[ticker].index: continue
                next_open = stocks[ticker].loc[next_date, 'Open']
                if pd.isna(next_open) or next_open <= 0: continue
                
                shares = int(pos_size / float(next_open))
                if shares > 0:
                    pending_entries.append({
                        'ticker': ticker,
                        'signal': sig,
                        'fill_date': next_date,
                        'desired_shares': shares
                    })
        
        if (i+1) % 50 == 0:
            print(f"  Day {i+1}/{len(trading_dates)} - Portfolio: {port_val:,.0f} EGP")

    # Closing
    final_date = trading_dates[-1]
    from core.simulation import BacktestReporting
    df_trades = pd.DataFrame(trades) if trades else pd.DataFrame()
    df_daily = pd.DataFrame(daily_values)
    metrics = BacktestReporting.calculate_metrics(df_trades, df_daily, starting_capital)
    report = BacktestReporting.generate_markdown_report(metrics, df_trades)
    print(report)

    for ticker, pos in positions.items():
        if ticker in stocks and final_date in stocks[ticker].index:
            mark_price = float(stocks[ticker].loc[final_date, 'Close'])
        else:
            mark_price = float(pos['entry_price'])
        microstructure_diagnostics['unliquidated_shares'] += int(pos['shares'])
        microstructure_diagnostics['unliquidated_notional'] += float(pos['shares'] * mark_price)
    
    return {
        'starting_capital': starting_capital,
        'final_value': daily_values[-1]['value'] if daily_values else starting_capital,
        'total_return': (metrics or {}).get('Total Return %', 0.0),
        'trades': trades,
        'daily_values': daily_values,
        'microstructure': build_microstructure_contract(microstructure_diagnostics),
    }

def _select_simulation_profile(index_choice):
    normalized = (index_choice or "").strip().upper()
    if normalized == "EGX70" or normalized == "70":
        return EGX70_TACTICAL_PROFILE
    return EGX30_TREND_PROFILE

def _record_execution_estimate(diagnostics, estimate, profile_name):
    diagnostics['route_counts'][profile_name] = diagnostics['route_counts'].get(profile_name, 0) + 1
    diagnostics['slippage_bucket_usage'][estimate.slippage_bucket] = diagnostics['slippage_bucket_usage'].get(estimate.slippage_bucket, 0) + 1
    diagnostics['rejected_notional'] += float(estimate.rejected_notional)
    if estimate.rejected_shares > 0:
        diagnostics['liquidity_cap_hits'] += 1

def _resolve_run_cost_pct(params, key, default):
    if isinstance(params, dict) and key in params:
        raw_value = params.get(key)
    elif params is not None and hasattr(params, key):
        raw_value = getattr(params, key)
    else:
        raw_value = default
    try:
        return max(0.0, float(raw_value))
    except (TypeError, ValueError):
        return max(0.0, float(default or 0.0))

if __name__ == "__main__":
    run_simulation()
