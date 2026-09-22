from core.DataManager import DataManager
print("testing...")
tickers = DataManager.list_tickers()
print("done! count:", len(tickers))
