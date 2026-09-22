from core.exclusions import get_all_exclusions
from core import DailyScanner
from core.market import MarketLists
from core.DataManager import DataManager

print("1. getting market list")
lists = MarketLists.get_market_list("ALL")

print("2. listing tickers from DataManager")
tickers = DataManager.list_tickers()

print("3. getting exclusions from GlobalSettings")
exc = get_all_exclusions()

print("Done with pre-scan setup")
