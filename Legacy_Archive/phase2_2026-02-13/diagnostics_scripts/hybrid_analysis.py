import pandas as pd

files = {
    '15m (Hybrid)': r'd:\Antigravity Prpjects\Horus Analytics\Pine\Horus_EGX_COSG_2026-01-23_37e55.csv',
    '1D (Daily)': r'd:\Antigravity Prpjects\Horus Analytics\Pine\Horus_EGX_COSG_2026-01-23_7ac7b.csv'
}

print(f"{'Timeframe':<15} | {'Trades':<8} | {'Win Rate':<10} | {'Profit Factor':<15} | {'Net P&L':<15}")
print("-" * 80)

for tf, path in files.items():
    try:
        df = pd.read_csv(path)
        closed = df[df['Type'].str.contains('Exit')]
        total = len(closed)
        
        if total == 0:
            print(f"{tf:<15} | {0:<8} | 0.0%       | 0.00            | 0.0            ")
            continue
            
        wins = len(closed[closed['Net P&L EGP'] > 0])
        win_rate = (wins / total) * 100
        
        gross_win = closed[closed['Net P&L EGP'] > 0]['Net P&L EGP'].sum()
        gross_loss = abs(closed[closed['Net P&L EGP'] < 0]['Net P&L EGP'].sum())
        pf = gross_win / gross_loss if gross_loss != 0 else 999.0
        
        net_pnl = closed['Net P&L EGP'].sum()
        
        print(f"{tf:<15} | {total:<8} | {win_rate:<10.1f}% | {pf:<15.2f} | {net_pnl:<15.2f}")
    except Exception as e:
        print(f"Error {tf}: {e}")
