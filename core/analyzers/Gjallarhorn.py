"""
GJALLARHORN (THE OMNIPRESENT SENTINEL)
======================================
"I hear the grass grow. I hear the wool grow on sheep. 
 And I hear when the market is about to bleed."

Live Market Monitor & Alert System.
MODES:
1. SNIPER: Watches your specific 'My_Holdings' list.
2. GOD_MODE: Watches the ENTIRE MARKET (EGX100 or ALL).

Author: LOKI for Horus Analytics
"""

from core.settings import settings
import time
import datetime
import pandas as pd
from core import TimeUtils
from colorama import Fore, Style, init
import winsound 

# IMPORT THE GODS
from core import DataManager
from core.analyzers import Svartalfheim
from core import MarketPredictor
from core.market import MarketLists # <--- New Import for God Mode
from core import TelegramBot_Alerts
init(autoreset=True)

# === ⚙️ CONFIGURATION ===
# 'SNIPER' = Watch only specific list
# 'GOD_MODE' = Watch the whole market defined in TARGET_LIST_NAME
SCAN_MODE = "GOD_MODE" 

# If GOD_MODE, which universe? ("30", "70", "100", "ALL")
# Recommendation: "100" (Liquid stocks). "ALL" includes dead stocks.
TARGET_UNIVERSE = "100" 

# If SNIPER mode, put your stocks here
MY_HOLDINGS = ['ACAMD', 'GTEX', 'COSG', 'ELEC', 'ICID'] 

INDEX_TICKER = "EGX30"
CHECK_INTERVAL = 60  # Seconds between scans
ENABLE_TELEGRAM = True  # Dual Alert Mode

def get_watch_targets():
    """
    Decides who to watch based on the Mode.
    """
    if SCAN_MODE == "SNIPER":
        return MY_HOLDINGS
    
    elif SCAN_MODE == "GOD_MODE":
        # Fetch from MarketLists
        targets = MarketLists.get_market_list(TARGET_UNIVERSE)
        
        # If 'ALL' was selected, MarketLists returns None, so we grab everything
        if targets is None or TARGET_UNIVERSE == "ALL":
            targets = list(MarketLists.SECTOR_MAP.keys())
        else:
            targets = list(targets)
            
        return targets
    
    return []

def play_alarm(type="DANGER"):
    try:
        if type == "DANGER":
            winsound.Beep(440, 500); winsound.Beep(440, 500)
        elif type == "OPPORTUNITY":
            winsound.Beep(1000, 200); winsound.Beep(1000, 200); winsound.Beep(1000, 200)
    except:
        print("\a")

def send_alert(message):
    timestamp = TimeUtils.now().strftime("%H:%M:%S")
    full_msg = f"[{timestamp}] 🔔 {message}"
    
    # Color code the alerts
    if "TRAP" in message or "CRASH" in message or "SELL" in message:
        print("\n" + Fore.MAGENTA + Style.BRIGHT + full_msg)
        play_alarm("DANGER")
    else:
        print("\n" + Fore.GREEN + Style.BRIGHT + full_msg)
        play_alarm("OPPORTUNITY")
        
    # 3. Telegram Alert
    if ENABLE_TELEGRAM:
        TelegramBot_Alerts.send_message(full_msg)

def live_watch():
    targets = get_watch_targets()
    print(Fore.RED + Style.BRIGHT + "📯 GJALLARHORN (OMNIPRESENT MODE) IS SOUNDING.")
    print(Fore.WHITE + f"   Mode: {SCAN_MODE}")
    print(Fore.WHITE + f"   Watching: {len(targets)} Tickers")
    print(Fore.WHITE + f"   Interval: {CHECK_INTERVAL}s")
    print(Fore.CYAN + "=" * 60)
    
    last_signals = {} 

    try:
        while True:
            now = TimeUtils.now().strftime("%H:%M:%S")
            
            # === MARKET HOURS CHECK ===
            if not settings.is_market_open():
                print(f"\r💤 Market is CLOSED. Gjallarhorn is idling... [{now}]", end="", flush=True)
                time.sleep(300) # Check every 5 minutes when closed
                continue
                
            # Show a spinning scanner so you know it's alive
            print(f"\r👁️  Scanning {len(targets)} stocks... [{now}]", end="", flush=True)
            
            # === 1. MACRO CHECK ===
            idx_df = DataManager.DataManager.get_stock_data(INDEX_TICKER)
            if idx_df is not None:
                pct = idx_df['Close'].pct_change().iloc[-1] * 100
                if pct < -2.0 and "CRASH" not in last_signals.get("MACRO", ""):
                    send_alert(f"MARKET CRASH WARNING: {INDEX_TICKER} down {pct:.2f}%!")
                    last_signals["MACRO"] = "CRASH"
            
            # === 2. SCAN THE TARGETS ===
            for ticker in targets:
                try:
                    df = DataManager.DataManager.get_stock_data(ticker)
                    if df is None or df.empty or len(df) < 25: continue
                    
                    last_close = df['Close'].iloc[-1]
                    high = df['High'].iloc[-1]
                    low = df['Low'].iloc[-1]
                    prev_high = df['High'].iloc[-20:-1].max()
                    prev_low = df['Low'].iloc[-20:-1].min()
                    
                    # --- CHECK TRAPS ---
                    # Bull Trap (Fake Breakout)
                    if high > prev_high and last_close < prev_high:
                        sig_key = f"{ticker}_BULLTRAP_{TimeUtils.now().hour}"
                        if sig_key not in last_signals:
                            send_alert(f"BULL TRAP: {ticker} faked break of {prev_high:.2f}. SELL.")
                            last_signals[sig_key] = True
                    
                    # Bear Trap (Springboard)
                    if low < prev_low and last_close > prev_low:
                        sig_key = f"{ticker}_BEARTRAP_{TimeUtils.now().hour}"
                        if sig_key not in last_signals:
                            send_alert(f"BEAR TRAP: {ticker} rejected low of {prev_low:.2f}. BUY.")
                            last_signals[sig_key] = True

                    # --- CHECK SQUEEZE EXPLOSIONS ---
                    # Volume > 3x Avg AND Price Moving
                    avg_vol = df['Volume'].iloc[-20:-1].mean()
                    cur_vol = df['Volume'].iloc[-1]
                    
                    if cur_vol > avg_vol * 3.0 and avg_vol > 10000: # Ignore illiquid trash
                        pct_move = (last_close - df['Open'].iloc[-1]) / df['Open'].iloc[-1]
                        if abs(pct_move) > 0.02: # Moving at least 2%
                            sig_key = f"{ticker}_VOL_{TimeUtils.now().hour}"
                            if sig_key not in last_signals:
                                direction = "UP" if pct_move > 0 else "DOWN"
                                send_alert(f"VOLUME EXPLOSION: {ticker} is moving {direction} ({pct_move*100:.1f}%) on 3x Volume!")
                                last_signals[sig_key] = True
                                
                except Exception:
                    continue

            # Sleep
            time.sleep(CHECK_INTERVAL)
            
            # Clean cache hourly
            if TimeUtils.now().minute == 0:
                last_signals = {}

    except KeyboardInterrupt:
        print(Fore.RED + "\n\n📯 WATCH ENDED.")

if __name__ == "__main__":
    live_watch()
