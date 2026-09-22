"""
BACKTEST REPORTING MODULE
=========================
Implements the 'Backtest Metrics & Reporting' skill.
Standardizes performance metrics and report generation for all strategies.
"""

import pandas as pd
import numpy as np
import os
import datetime

def calculate_metrics(trades_df, daily_df, starting_capital):
    """
    Compute standard performance metrics.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trade history.
        daily_df (pd.DataFrame): DataFrame containing daily equity values.
        starting_capital (float): Initial capital.
        
    Returns:
        dict: A dictionary of calculated metrics.
    """
    if daily_df.empty:
        return {}

    # Ensure Date index
    if 'date' in daily_df.columns:
        daily_df['date'] = pd.to_datetime(daily_df['date'])
        daily_df.set_index('date', inplace=True)
    
    # 1. Equity & Returns
    final_value = daily_df['value'].iloc[-1]
    total_return = (final_value - starting_capital) / starting_capital
    days = (daily_df.index[-1] - daily_df.index[0]).days
    years = days / 365.25 if days > 0 else 0
    
    cagr = ((final_value / starting_capital) ** (1 / years)) - 1 if years > 0 else 0
    
    # Daily Returns
    daily_df['return'] = daily_df['value'].pct_change().fillna(0)
    mean_daily_ret = daily_df['return'].mean()
    std_daily_ret = daily_df['return'].std()
    
    # 2. Risk Metrics (Sharpe, Sortino)
    risk_free_rate = 0.0 # Assumption
    sharpe = (mean_daily_ret / std_daily_ret * np.sqrt(252)) if std_daily_ret != 0 else 0
    
    downside_returns = daily_df.loc[daily_df['return'] < 0, 'return']
    std_downside = downside_returns.std()
    sortino = (mean_daily_ret / std_downside * np.sqrt(252)) if std_downside != 0 else 0
    
    # 3. Drawdown
    daily_df['peak'] = daily_df['value'].cummax()
    daily_df['drawdown'] = (daily_df['value'] / daily_df['peak']) - 1
    max_drawdown = daily_df['drawdown'].min()
    
    # Max DD Duration (approximate in days)
    is_dd = daily_df['drawdown'] < 0
    dd_duration = 0
    current_dd_duration = 0
    for dd in is_dd:
        if dd:
            current_dd_duration += 1
        else:
            if current_dd_duration > dd_duration:
                dd_duration = current_dd_duration
            current_dd_duration = 0
    
    # 4. Trade Statistics
    if not trades_df.empty:
        total_trades = len(trades_df)
        wins = trades_df[trades_df['pnl'] > 0]
        losses = trades_df[trades_df['pnl'] <= 0]
        
        win_rate = len(wins) / total_trades
        
        avg_win = wins['pnl'].mean() if not wins.empty else 0
        avg_loss = losses['pnl'].mean() if not losses.empty else 0
        
        profit_factor = abs(wins['pnl'].sum() / losses['pnl'].sum()) if losses['pnl'].sum() != 0 else float('inf')
        
        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Exposure (Time in Market)
        # Using daily positions count > 0 as a proxy
        exposure_days = (daily_df['positions'] > 0).sum()
        exposure_pct = exposure_days / len(daily_df)
        
    else:
        total_trades = 0
        win_rate = 0
        profit_factor = 0
        expectancy = 0
        exposure_pct = 0

    metrics = {
        "Start Date": daily_df.index[0].strftime('%Y-%m-%d'),
        "End Date": daily_df.index[-1].strftime('%Y-%m-%d'),
        "Duration (Years)": round(years, 2),
        "Starting Capital": starting_capital,
        "Final Equity": round(final_value, 2),
        "Total Return %": round(total_return * 100, 2),
        "CAGR %": round(cagr * 100, 2),
        "Sharpe Ratio": round(sharpe, 2),
        "Sortino Ratio": round(sortino, 2),
        "Max Drawdown %": round(max_drawdown * 100, 2),
        "Max DD Duration (Days)": dd_duration,
        "Total Trades": total_trades,
        "Win Rate %": round(win_rate * 100, 2),
        "Profit Factor": round(profit_factor, 2),
        "Expectancy (EGP)": round(expectancy, 2),
        "Exposure %": round(exposure_pct * 100, 2)
    }

    return metrics

def generate_markdown_report(metrics_raw, trades_df, save_path=None):
    """
    Generate a human-readable Markdown report.
    """
    metrics = metrics_raw if isinstance(metrics_raw, dict) else {}
    
    report = f"""# 📊 Backtest Performance Report
**Generated:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 Key Performance Metrics

| Metric | Value |
| :--- | :--- |
| **Total Return** | `{metrics.get('Total Return %', 0)}%` |
| **CAGR** | `{metrics.get('CAGR %', 0)}%` |
| **Sharpe Ratio** | `{metrics.get('Sharpe Ratio', 0)}` |
| **Max Drawdown** | `{metrics.get('Max Drawdown %', 0)}%` |
| **Profit Factor** | `{metrics.get('Profit Factor', 0)}` |
| **Win Rate** | `{metrics.get('Win Rate %', 0)}%` |

## 💰 Capital Analysis
* **Starting Capital:** {metrics.get('Starting Capital', 0):,.0f} EGP
* **Final Equity:** {metrics.get('Final Equity', 0):,.0f} EGP
* **Expectancy per Trade:** {metrics.get('Expectancy (EGP)', 0):,.0f} EGP

## 🛠️ Strategy Robustness
* **Total Trades:** {metrics.get('Total Trades', 0)}
* **Market Exposure:** {metrics.get('Exposure %', 0)}%
* **Sortino Ratio:** {metrics.get('Sortino Ratio', 0)}

"""
    
    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(report)
            
    return report
