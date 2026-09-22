from core import DataManager
from core.analyzers.Svartalfheim import  detect_fractals
ticker = 'COMI'
df = DataManager.DataManager.get_stock_data(ticker)
df = detect_fractals(df)
df['Vol_Avg'] = df['Volume'].rolling(20).mean()
print(df[['High', 'Close', 'Swing_High', 'Volume', 'Vol_Avg']].tail(10))
