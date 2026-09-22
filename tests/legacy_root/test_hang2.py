from data_engine import api as data_engine_api
from data_engine.ticker_filters import is_supported_ticker
print("calling list_tickers")
tickers = data_engine_api.list_tickers(timeframe='history', realm="EGX")
print("tickers loaded:", len(tickers))
for i, t in enumerate(tickers):
    print(f"checking {t}")
    is_supported_ticker(t)

print("done")
