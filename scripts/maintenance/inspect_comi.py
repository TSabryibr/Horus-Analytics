from core import DataManager
from core.analyzers.Svartalfheim import  detect_fractals
ticker = 'COMI'
df = DataManager.DataManager.get_stock_data(ticker)
df = detect_fractals(df)
print(df[['High', 'Close', 'Swing_High']].tail(10))
