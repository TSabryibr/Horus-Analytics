from core import DataManager
from core.analyzers import Svartalfheim
ticker = 'COMI'
df = DataManager.DataManager.get_stock_data(ticker)
df = Svartalfheim.detect_fractals(df)
traps = Svartalfheim.check_traps(df, ticker)
print(f"Traps found for {ticker}: {traps}")
