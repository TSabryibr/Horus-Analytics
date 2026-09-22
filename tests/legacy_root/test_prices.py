import sys
sys.path.insert(0, r'd:\Antigravity Prpjects\MARKET ANALYSIS')

from core.adapters.MetaStockAdapter import  MetaStockAdapter, METASTOCK_HISTORY

tickers = ['COMI', 'MBSC', 'EAST', 'EFIH']
print('Testing real prices from HISTORY folder:')
print('=' * 50)

for t in tickers:
    df = MetaStockAdapter.get_stock_data(t, METASTOCK_HISTORY)
    if df is not None and len(df) > 0:
        last = df.iloc[-1]
        print(f"{t}: Close={last['Close']:.2f}, Date={df.index[-1]}")
    else:
        print(f"{t}: No data")
