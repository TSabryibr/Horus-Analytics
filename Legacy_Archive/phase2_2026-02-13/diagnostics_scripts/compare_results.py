import pandas as pd
import glob

files = {
    '15m': r'd:\Antigravity Prpjects\Horus Analytics\Pine\Horus_EGX_ACAMD_2026-01-23_f05c0.csv',
    '1H': r'd:\Antigravity Prpjects\Horus Analytics\Pine\Horus_EGX_ACAMD_2026-01-23_3d091.csv',
    '1D': r'd:\Antigravity Prpjects\Horus Analytics\Pine\Horus_EGX_ACAMD_2026-01-23_2057b.csv'
}

print(f"{'Timeframe':<10} | {'Trades':<8} | {'Win Rate':<10} | {'Profit Factor':<15} | {'Net P&L (EGP)':<15}")
print("-" * 75)

for tf, path in files.items():
    try:
        df = pd.read_csv(path)
        # Filter for closed trades
        closed = df[df['Type'] == 'Exit long']
        
        total = len(closed)
        if total == 0:
            print(f"{tf:<10} | {0:<8} | {0.0:<10.1f}% | {0.0:<15.2f} | {0.0:<15.2f}")
            continue
            
        wins = len(closed[closed['Net P&L EGP'] > 0])
        win_rate = (wins / total) * 100
        
        gross_win = closed[closed['Net P&L EGP'] > 0]['Net P&L EGP'].sum()
        gross_loss = abs(closed[closed['Net P&L EGP'] < 0]['Net P&L EGP'].sum())
        pf = gross_win / gross_loss if gross_loss != 0 else 999.0
        
        net_pnl = closed['Net P&L EGP'].sum()
        
        print(f"{tf:<10} | {total:<8} | {win_rate:<10.1f}% | {pf:<15.2f} | {net_pnl:<15.2f}")
    except Exception as e:
        print(f"Error analyzing {tf}: {e}")
