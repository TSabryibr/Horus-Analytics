"""
SIGNAL COMPARISON BACKTEST
==========================
Compares accuracy of two signal scoring systems:
1. Scanner Engine (SignalEngine.py) - 10-point scale
2. MomentumBreakoutScanner Engine (MomentumBreakoutScanner.py) - 11-point scale

Runs both engines on 2 years of historical data and compares outcomes.

Author: Horus Analytics
Date: 2026-02-02
"""

from core.settings import settings
from core.exclusions import EXCLUDED_TICKERS
import pandas as pd
import numpy as np
import os
import datetime
import warnings
from collections import defaultdict

from core.market import MarketLists
from core.DataManager import DataManager

warnings.filterwarnings('ignore')

# === SHARED SETTINGS ===
LOOKBACK = settings.LOOKBACK
VOL_SPIKE = settings.VOL_SPIKE
MOMENTUM = settings.MOMENTUM
RSI_MIN = settings.RSI_MIN
RSI_MAX = settings.RSI_MAX
MIN_TURNOVER = settings.MIN_TURNOVER


def load_all_stocks(allowed_tickers=None):
    """
    Load all stock data with calculated indicators.
    Returns dict of {ticker: DataFrame}.
    """
    tickers = DataManager.list_tickers()
    tickers = [t for t in tickers if t.upper() not in ['REPORT', 'EGX30_70_100']]
    
    stocks = {}
    
    for ticker in tickers:
        if ticker in EXCLUDED_TICKERS:
            continue
        
        if allowed_tickers is not None and ticker not in allowed_tickers:
            continue
        
        try:
            df = DataManager.get_stock_data(ticker, include_live=False)
            if df is None:
                continue
            
            # Normalize columns
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
            
            # Calculate ALL indicators needed by both engines (Native Pandas)
            tr1 = df['High'] - df['Low']
            tr2 = (df['High'] - df['Close'].shift()).abs()
            tr3 = (df['Low'] - df['Close'].shift()).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            df['ATR'] = tr.ewm(alpha=1/14, min_periods=14, adjust=False).mean()

            efi = df['Close'].diff(1) * df['Volume']
            df['EFI'] = efi.ewm(span=13, adjust=False).mean()

            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()

            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14, adjust=False).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            df['Avg_Vol'] = df['Volume'].rolling(20).mean()
            df['Rel_Vol'] = (df['Volume'] / df['Avg_Vol']).replace([np.inf, -np.inf], 0).fillna(0)
            df['Price_Move'] = ((df['Close'] - df['Open']) / df['Open']) * 100
            df['Turnover'] = df['Close'] * df['Volume']
            df['Avg_Turnover'] = df['Turnover'].rolling(20).mean()
            df['Resistance'] = df['High'].rolling(LOOKBACK).max().shift(1)
            
            stocks[ticker] = df
            
        except Exception:
            continue
    
    return stocks


def generate_scanner_signal(df, date):
    """
    Generate signal using SCANNER ENGINE logic (SignalEngine.py).
    10-point scoring scale.
    """
    if date not in df.index:
        return None
    
    idx = df.index.get_loc(date)
    if idx < 60:
        return None
    
    try:
        close = df['Close'].iloc[idx]
        low = df['Low'].iloc[idx]
        resistance = df['Resistance'].iloc[idx]
        power = df['EFI'].iloc[idx]
        ema9 = df['EMA9'].iloc[idx]
        rsi = df['RSI'].iloc[idx]
        rel_vol = df['Rel_Vol'].iloc[idx]
        avg_turnover = df['Avg_Turnover'].iloc[idx]
        price_move = df['Price_Move'].iloc[idx]
        
        if pd.isna(resistance) or pd.isna(rsi):
            return None
        
        # === SCANNER CONDITIONS ===
        is_liquid = avg_turnover > MIN_TURNOVER
        volume_spike = rel_vol > VOL_SPIKE
        momentum_move = price_move >= MOMENTUM
        rsi_valid = RSI_MIN < rsi < RSI_MAX
        breakout = close > resistance
        
        if not (is_liquid and volume_spike and momentum_move and rsi_valid and breakout):
            return None
        
        # === SCANNER SCORING (10-point scale) ===
        score = 0
        if breakout: score += 2
        if power > 0: score += 1
        if is_liquid and volume_spike: score += 4
        if rsi < 70: score += 1
        if close > ema9: score += 2
        
        # Calculate targets
        sl_pct = settings.SL_PCT
        tp_pct = settings.TP1_PCT
        entry_price = close
        stop_loss = low * (1 - sl_pct / 100)
        target_price = close * (1 + tp_pct / 100)
        
        return {
            'engine': 'SCANNER',
            'entry_price': round(entry_price, 4),
            'stop_loss': round(stop_loss, 4),
            'target_price': round(target_price, 4),
            'score': score,
            'max_score': 10,
            'rsi': round(rsi, 1),
            'rel_vol': round(rel_vol, 2)
        }
        
    except Exception:
        return None


def generate_eye_signal(df, date):
    """
    Generate signal using MomentumBreakoutScanner ENGINE logic (MomentumBreakoutScanner.py).
    11-point scoring scale with institutional activity detection.
    """
    if date not in df.index:
        return None
    
    idx = df.index.get_loc(date)
    if idx < 60:
        return None
    
    try:
        close = df['Close'].iloc[idx]
        low = df['Low'].iloc[idx]
        resistance = df['Resistance'].iloc[idx]
        power = df['EFI'].iloc[idx]
        ema9 = df['EMA9'].iloc[idx]
        rsi = df['RSI'].iloc[idx]
        rel_vol = df['Rel_Vol'].iloc[idx]
        avg_turnover = df['Avg_Turnover'].iloc[idx]
        price_move = df['Price_Move'].iloc[idx]
        
        if pd.isna(resistance) or pd.isna(rsi):
            return None
        
        # === MomentumBreakoutScanner CONDITIONS ===
        # More lenient entry - just need SOME positive signals
        breakout = close > resistance
        
        # Institutional Activity Detection (stricter)
        is_liquid = avg_turnover > MIN_TURNOVER
        is_momentum_spike = (
            rel_vol > VOL_SPIKE and 
            price_move >= MOMENTUM and 
            RSI_MIN < rsi < RSI_MAX
        )
        institutional_signal = is_liquid and is_momentum_spike
        
        # Need at least one major condition
        if not (breakout or institutional_signal):
            return None
        
        # === MomentumBreakoutScanner SCORING (11-point scale) ===
        score = 0
        
        # STA Signals (original logic)
        if breakout and power > 0:
            score += 3
        
        # Institutional Activity Signal
        if institutional_signal:
            score += 5
        
        # Volume confirmation
        if rel_vol > 1.5:
            score += 1
        
        # RSI confirmation (not overbought)
        if 50 < rsi < 70:
            score += 1
        
        # Price above EMA9
        if close > ema9:
            score += 1
        
        # Must have minimum score to be valid
        if score < 3:
            return None
        
        # Calculate targets (same as MomentumBreakoutScanner.py)
        sl_buffer_pct = 1.5
        tp1_pct = 4.0
        entry_price = close
        stop_loss = low * (1 - sl_buffer_pct / 100)
        target_price = close * (1 + tp1_pct / 100)
        
        return {
            'engine': 'MomentumBreakoutScanner',
            'entry_price': round(entry_price, 4),
            'stop_loss': round(stop_loss, 4),
            'target_price': round(target_price, 4),
            'score': score,
            'max_score': 11,
            'rsi': round(rsi, 1),
            'rel_vol': round(rel_vol, 2),
            'institutional': institutional_signal
        }
        
    except Exception:
        return None


def check_signal_outcome(df, signal_date, entry_price, stop_loss, target_price, window_days):
    """
    Check if a signal hit TP, SL, or expired within the time window.
    """
    if signal_date not in df.index:
        return None
    
    entry_idx = df.index.get_loc(signal_date)
    
    for days_held in range(1, window_days + 1):
        if entry_idx + days_held >= len(df):
            break
        
        high = df['High'].iloc[entry_idx + days_held]
        low = df['Low'].iloc[entry_idx + days_held]
        check_date = df.index[entry_idx + days_held]
        
        # Check TP hit first
        if high >= target_price:
            pnl_pct = ((target_price - entry_price) / entry_price) * 100
            return {
                'outcome': 'TP_HIT',
                'exit_date': check_date,
                'days_held': days_held,
                'pnl_pct': round(pnl_pct, 2)
            }
        
        # Check SL hit
        if low <= stop_loss:
            pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
            return {
                'outcome': 'SL_HIT',
                'exit_date': check_date,
                'days_held': days_held,
                'pnl_pct': round(pnl_pct, 2)
            }
    
    # Expired
    if entry_idx + window_days < len(df):
        exit_idx = entry_idx + window_days
        exit_price = df['Close'].iloc[exit_idx]
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100
        return {
            'outcome': 'EXPIRED',
            'exit_date': df.index[exit_idx],
            'days_held': window_days,
            'pnl_pct': round(pnl_pct, 2)
        }
    
    return {'outcome': 'NO_DATA', 'days_held': 0, 'pnl_pct': 0}


def run_comparison(start_date, end_date, window_days=5, index_choice="ALL",
                   scanner_min_score=9, scanner_max_score=10,
                   eye_min_score=10, eye_max_score=11):
    """
    Main comparison function.
    Runs both engines on historical data and compares outcomes.
    
    Args:
        scanner_min_score, scanner_max_score: Score filter for Scanner (default 9-10)
        eye_min_score, eye_max_score: Score filter for MomentumBreakoutScanner (default 10-11)
    """
    print("=" * 70)
    print("         SIGNAL ENGINE COMPARISON BACKTEST")
    print("         [HIGH CONVICTION SIGNALS ONLY]")
    print("=" * 70)
    print(f"Period: {start_date} to {end_date}")
    print(f"Holding Window: {window_days} days")
    print(f"Index Filter: {index_choice}")
    print(f"Scanner Filter: Score {scanner_min_score}-{scanner_max_score}")
    print(f"MomentumBreakoutScanner Filter: Score {eye_min_score}-{eye_max_score}")
    print("=" * 70)
    
    # Get market filter
    market_filter = MarketLists.get_market_list(index_choice) if index_choice != "ALL" else None
    
    # Load stocks
    print("\n[*] Loading stock data...")
    stocks = load_all_stocks(market_filter)
    print(f"   Loaded {len(stocks)} stocks")
    
    if not stocks:
        print("[X] No stocks loaded!")
        return None
    
    # Convert dates
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Get trading dates
    sample_stock = list(stocks.values())[0]
    trading_dates = [d for d in sample_stock.loc[start:end].index if start <= d <= end]
    
    print(f"   Checking {len(trading_dates)} trading days...")
    
    # Collect signals
    scanner_signals = []
    eye_signals = []
    
    processed = 0
    for date in trading_dates:
        for ticker, df in stocks.items():
            # Generate signals from both engines
            scanner_sig = generate_scanner_signal(df, date)
            eye_sig = generate_eye_signal(df, date)
            
            # Process Scanner signal - filter by score
            if scanner_sig and scanner_min_score <= scanner_sig['score'] <= scanner_max_score:
                outcome = check_signal_outcome(
                    df, date,
                    scanner_sig['entry_price'],
                    scanner_sig['stop_loss'],
                    scanner_sig['target_price'],
                    window_days
                )
                if outcome and outcome['outcome'] != 'NO_DATA':
                    scanner_signals.append({
                        'ticker': ticker,
                        'date': date,
                        **scanner_sig,
                        **outcome
                    })
            
            # Process MomentumBreakoutScanner signal - filter by score
            if eye_sig and eye_min_score <= eye_sig['score'] <= eye_max_score:
                outcome = check_signal_outcome(
                    df, date,
                    eye_sig['entry_price'],
                    eye_sig['stop_loss'],
                    eye_sig['target_price'],
                    window_days
                )
                if outcome and outcome['outcome'] != 'NO_DATA':
                    eye_signals.append({
                        'ticker': ticker,
                        'date': date,
                        **eye_sig,
                        **outcome
                    })
        
        processed += 1
        if processed % 50 == 0:
            print(f"   ✅ Processed {processed}/{len(trading_dates)} days...")
    
    # Calculate statistics
    def calc_stats(signals, name):
        if not signals:
            return {'name': name, 'total': 0, 'win_rate': 0, 'avg_days': 0, 'avg_gain': 0, 'profit_factor': 0}
        
        total = len(signals)
        tp_hits = sum(1 for s in signals if s['outcome'] == 'TP_HIT')
        sl_hits = sum(1 for s in signals if s['outcome'] == 'SL_HIT')
        
        win_rate = (tp_hits / total * 100) if total > 0 else 0
        
        tp_sigs = [s for s in signals if s['outcome'] == 'TP_HIT']
        avg_days = np.mean([s['days_held'] for s in tp_sigs]) if tp_sigs else 0
        
        avg_gain = np.mean([s['pnl_pct'] for s in signals])
        
        total_gains = sum(s['pnl_pct'] for s in signals if s['pnl_pct'] > 0)
        total_losses = abs(sum(s['pnl_pct'] for s in signals if s['pnl_pct'] < 0))
        profit_factor = total_gains / total_losses if total_losses > 0 else float('inf')
        
        return {
            'name': name,
            'total': total,
            'tp_hits': tp_hits,
            'sl_hits': sl_hits,
            'expired': total - tp_hits - sl_hits,
            'win_rate': round(win_rate, 1),
            'avg_days': round(avg_days, 1),
            'avg_gain': round(avg_gain, 2),
            'profit_factor': round(profit_factor, 2)
        }
    
    scanner_stats = calc_stats(scanner_signals, 'SCANNER')
    eye_stats = calc_stats(eye_signals, 'MomentumBreakoutScanner')
    
    # Score breakdown
    def score_breakdown(signals, max_score):
        by_score = defaultdict(lambda: {'total': 0, 'wins': 0})
        for s in signals:
            score = s['score']
            by_score[score]['total'] += 1
            if s['outcome'] == 'TP_HIT':
                by_score[score]['wins'] += 1
        
        result = {}
        for score in sorted(by_score.keys(), reverse=True):
            data = by_score[score]
            wr = (data['wins'] / data['total'] * 100) if data['total'] > 0 else 0
            result[score] = {'signals': data['total'], 'win_rate': round(wr, 1)}
        return result
    
    scanner_by_score = score_breakdown(scanner_signals, 10)
    eye_by_score = score_breakdown(eye_signals, 11)
    
    # Print Results
    print("\n")
    print("=" * 70)
    print("                      COMPARISON RESULTS")
    print("=" * 70)
    print(f"\n{'Metric':<25} {'SCANNER (10pt)':<20} {'MomentumBreakoutScanner (11pt)':<20}")
    print("-" * 65)
    print(f"{'Total Signals':<25} {scanner_stats['total']:<20} {eye_stats['total']:<20}")
    print(f"{'TP Hits':<25} {scanner_stats['tp_hits']:<20} {eye_stats['tp_hits']:<20}")
    print(f"{'SL Hits':<25} {scanner_stats['sl_hits']:<20} {eye_stats['sl_hits']:<20}")
    print(f"{'Expired':<25} {scanner_stats['expired']:<20} {eye_stats['expired']:<20}")
    print(f"{'Win Rate %':<25} {scanner_stats['win_rate']:<20} {eye_stats['win_rate']:<20}")
    print(f"{'Avg Days to TP':<25} {scanner_stats['avg_days']:<20} {eye_stats['avg_days']:<20}")
    print(f"{'Avg Gain %':<25} {scanner_stats['avg_gain']:<20} {eye_stats['avg_gain']:<20}")
    print(f"{'Profit Factor':<25} {scanner_stats['profit_factor']:<20} {eye_stats['profit_factor']:<20}")
    
    # Score breakdown
    print("\n" + "=" * 70)
    print("                     WIN RATE BY SCORE")
    print("=" * 70)
    
    print("\n📊 SCANNER Engine (by score):")
    for score, data in scanner_by_score.items():
        bar = "█" * int(data['win_rate'] / 5)
        print(f"   Score {score:>2}: {data['signals']:>4} signals | {data['win_rate']:>5.1f}% {bar}")
    
    print("\n👁️ MomentumBreakoutScanner Engine (by score):")
    for score, data in eye_by_score.items():
        bar = "█" * int(data['win_rate'] / 5)
        print(f"   Score {score:>2}: {data['signals']:>4} signals | {data['win_rate']:>5.1f}% {bar}")
    
    # Determine winner
    print("\n" + "=" * 70)
    print("                         VERDICT")
    print("=" * 70)
    
    if scanner_stats['win_rate'] > eye_stats['win_rate']:
        winner = "SCANNER"
        diff = scanner_stats['win_rate'] - eye_stats['win_rate']
    elif eye_stats['win_rate'] > scanner_stats['win_rate']:
        winner = "MomentumBreakoutScanner"
        diff = eye_stats['win_rate'] - scanner_stats['win_rate']
    else:
        winner = "TIE"
        diff = 0
    
    if winner != "TIE":
        print(f"\n   🏆 WINNER: {winner} Engine")
        print(f"   📈 Win Rate Advantage: +{diff:.1f}%")
    else:
        print(f"\n   🤝 TIE - Both engines have equal win rates")
    
    if scanner_stats['profit_factor'] > eye_stats['profit_factor']:
        print(f"   💰 Better Profit Factor: SCANNER ({scanner_stats['profit_factor']})")
    else:
        print(f"   💰 Better Profit Factor: MomentumBreakoutScanner ({eye_stats['profit_factor']})")
    
    print("\n" + "=" * 70)
    
    # Generate report
    report_path = os.path.join(settings.DATA_FOLDER, "Signal_Comparison_Report.md")
    generate_report(
        scanner_stats, eye_stats,
        scanner_by_score, eye_by_score,
        start_date, end_date, window_days,
        report_path
    )
    print(f"\n📄 Full report saved to: {report_path}")
    
    return {
        'scanner': scanner_stats,
        'eye': eye_stats,
        'scanner_by_score': scanner_by_score,
        'eye_by_score': eye_by_score,
        'scanner_signals': scanner_signals,
        'eye_signals': eye_signals
    }


def generate_report(scanner, eye, scanner_scores, eye_scores, start, end, window, path):
    """Generate markdown comparison report."""
    report = f"""# 📊 Signal Engine Comparison Report

**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Period:** {start} to {end}
**Holding Window:** {window} days

---

## 🏆 Summary

| Metric | Scanner Engine | MomentumBreakoutScanner Engine | Winner |
|--------|----------------|------------|--------|
| Total Signals | {scanner['total']} | {eye['total']} | {'SCANNER' if scanner['total'] > eye['total'] else 'MomentumBreakoutScanner'} |
| Win Rate | {scanner['win_rate']}% | {eye['win_rate']}% | **{'SCANNER' if scanner['win_rate'] > eye['win_rate'] else 'MomentumBreakoutScanner'}** |
| Avg Days to TP | {scanner['avg_days']} | {eye['avg_days']} | {'SCANNER' if scanner['avg_days'] < eye['avg_days'] else 'MomentumBreakoutScanner'} |
| Avg Gain % | {scanner['avg_gain']}% | {eye['avg_gain']}% | {'SCANNER' if scanner['avg_gain'] > eye['avg_gain'] else 'MomentumBreakoutScanner'} |
| Profit Factor | {scanner['profit_factor']} | {eye['profit_factor']} | {'SCANNER' if scanner['profit_factor'] > eye['profit_factor'] else 'MomentumBreakoutScanner'} |

---

## 📈 Win Rate by Score

### Scanner Engine (10-point scale)
| Score | Signals | Win Rate |
|-------|---------|----------|
"""
    for score, data in scanner_scores.items():
        report += f"| {score} | {data['signals']} | {data['win_rate']}% |\n"
    
    report += "\n### MomentumBreakoutScanner Engine (11-point scale)\n| Score | Signals | Win Rate |\n|-------|---------|----------|\n"
    for score, data in eye_scores.items():
        report += f"| {score} | {data['signals']} | {data['win_rate']}% |\n"
    
    report += f"""
---

## 🎯 Recommendation

Based on the backtest results:

"""
    if scanner['win_rate'] > eye['win_rate'] and scanner['profit_factor'] > eye['profit_factor']:
        report += "> **Use SCANNER Engine** - Higher win rate AND better profit factor.\n"
    elif eye['win_rate'] > scanner['win_rate'] and eye['profit_factor'] > scanner['profit_factor']:
        report += "> **Use MomentumBreakoutScanner Engine** - Higher win rate AND better profit factor.\n"
    else:
        report += "> **Mixed Results** - Consider using the engine with higher win rate for your trading style.\n"
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    # Run 2-year backtest with HIGH CONVICTION signals only
    # Scanner: 9-10, MomentumBreakoutScanner: 10-11
    # Filter: EGX100 stocks only
    results = run_comparison(
        start_date="2024-02-01",
        end_date="2026-02-01",
        window_days=5,
        index_choice="100",  # EGX100 stocks only
        scanner_min_score=9,
        scanner_max_score=10,
        eye_min_score=10,
        eye_max_score=11
    )

