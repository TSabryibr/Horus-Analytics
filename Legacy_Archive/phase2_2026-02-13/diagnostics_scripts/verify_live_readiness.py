
from core.settings import settings
import os
import sys
import requests
import pandas as pd
from dotenv import load_dotenv

# Load Env
load_dotenv()

print("="*60)
print("HORUS ANALYTICS - FINAL PRE-FLIGHT CHECK")
print("="*60)

failures = []

def check(name, condition, error_msg):
    if condition:
        print(f"[OK] {name}")
    else:
        print(f"[FAIL] {name}: {error_msg}")
        failures.append(name)

# 1. Environment
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
require_telegram = (os.getenv("VERIFY_REQUIRE_TELEGRAM", "0") or "0").strip().lower() in {"1", "true", "yes", "on"}
if require_telegram:
    check("Telegram Token", bool(token and token != "YOUR_INDIVIDUAL_BOT_TOKEN"), "Missing TELEGRAM_TOKEN")
    check("Chat ID", bool(chat_id), "Missing TELEGRAM_CHAT_ID/CHAT_ID")
else:
    if token and chat_id:
        check("Telegram Config", True, "")
    else:
        print("[INFO] Telegram config optional for this check. Set VERIFY_REQUIRE_TELEGRAM=1 to enforce.")

# 2. Database
try:
    from database import db, Signal, Portfolio
    db.connect()
    count = Signal.select().count()
    check("Database Connection", True, "")
    print(f"     -> Signals in DB: {count}")
    print(f"     -> Portfolios: {Portfolio.select().count()}")
    db.close()
except Exception as e:
    check("Database Connection", False, str(e))

# 3. Data Engine
try:
    from core.DataManager import DataManager
    
    # Check History
    tickers = DataManager.list_tickers(source="CSV", folder=settings.METASTOCK_HISTORY_FOLDER)
    check("History Data Access", len(tickers) > 0, "No tickers found in History folder")
    if len(tickers) > 0:
        print(f"     -> Found {len(tickers)} Historical Tickers")
        
    # Check Intraday
    intraday_tickers = DataManager.list_tickers(source="CSV", folder=settings.METASTOCK_INTRADAY_FOLDER)
    check("Intraday Data Access", len(intraday_tickers) > 0, "No tickers found in Intraday folder")
    if len(intraday_tickers) > 0:
        print(f"     -> Found {len(intraday_tickers)} Intraday Tickers")

except Exception as e:
    check("Data Access", False, str(e))

# 4. Signal Engine Dry Run
try:
    from core import SignalEngine
    from core import DailyScanner
    # Test on first available ticker
    test_ticker = "COMI"
    df = DataManager.get_stock_data(test_ticker)
    
    if df is not None:
        df = SignalEngine.add_indicators(df)
        last = df.iloc[-1]
        check("Signal Engine Indicators", "RSI" in last and "EMA9" in last, "Indicators missing")
        print(f"     -> COMI RSI: {last['RSI']:.2f}")
    else:
        check("Signal Engine Dry Run", False, "Could not load COMI for test")

except Exception as e:
    check("Signal Engine Dry Run", False, str(e))

# 5. Telegram Connectivity (Live Test)
if token and chat_id:
    try:
        from core import TelegramBot_Alerts
        msg = "HORUS SYSTEM READY\\nPre-Flight Check Complete.\\nMode: GOD MODE"
        # Send silent message
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": msg, "parse_mode": "Markdown", "disable_notification": True}
        res = requests.post(url, json=payload, timeout=5)
        check("Telegram Connectivity", res.ok, f"API Error: {res.text}")
    except Exception as e:
        check("Telegram Connectivity", False, str(e))
else:
    print("[SKIP] Telegram Check (Missing Config)")

print("-" * 60)
if not failures:
    print("[OK] SYSTEM READY FOR LAUNCH")
else:
    print(f"[FAIL] SYSTEM NOT READY. Failures: {failures}")
    sys.exit(1)
