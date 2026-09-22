"""
INTRADAY WATCHER
================
Monitors MetaStock intraday folder for file changes and triggers
signal detection + Telegram alerts on new data.

Author: Horus Analytics - EGX
Date: 2026-01-16
"""

from core.settings import settings
from core.exclusions import get_all_exclusions
import os
import glob
import time
import json
import threading
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Callable

from core.adapters.MetaStockAdapter import  read_dat_file, METASTOCK_INTRADAY
from core import TelegramBot_Alerts
from core import TimeUtils
class IntradayWatcher:
    """
    Monitors intraday folder for file changes and triggers callbacks.
    Uses polling-based approach (more reliable on Windows than watchdog).
    """
    
    def __init__(self, 
                 intraday_folder: str = None,
                 poll_interval: float = None,
                 on_update: Callable = None):
        """
        Args:
            intraday_folder: Path to intraday MetaStock folder
            poll_interval: Seconds between file checks (default from GlobalSettings)
            on_update: Callback function(ticker, df) called when data updates
        """
        self.folder = intraday_folder or settings.METASTOCK_INTRADAY_FOLDER
        
        # Use GlobalSettings for default poll interval (mins to seconds)
        if poll_interval is None:
            interval_mins = getattr(settings, "INTRADAY_INTERVAL_MINS", 5)
            self.poll_interval = float(interval_mins * 60)
        else:
            self.poll_interval = poll_interval
            
        self.on_update = on_update
        
        self.last_modified = {}
        self._running = False
        self._thread = None
        
        # Initial scan
        self._scan_files()
    
    def _scan_files(self):
        """Record modification times of all CSV files"""
        for path in glob.glob(os.path.join(self.folder, "*.csv")):
            self.last_modified[path] = os.path.getmtime(path)
    
    def check_updates(self) -> List[tuple]:
        """
        Check for updated files.
        Returns: List of (ticker, file_path) tuples for files that changed
        """
        changed = []
        
        for path in glob.glob(os.path.join(self.folder, "*.csv")):
            mtime = os.path.getmtime(path)
            
            # Extract ticker from filename (e.g., COMI.csv -> COMI)
            ticker = os.path.basename(path).replace('.csv', '').upper()
            
            # Skip index files and non-stock files
            if ticker.isdigit() or ticker.startswith('EG') or ticker.startswith('REOPEN'):
                continue

            # Check Global Exclusions
            if ticker in get_all_exclusions():
                continue
            
            if path not in self.last_modified:
                # New file
                self.last_modified[path] = mtime
                changed.append((ticker, path))
                
            elif mtime > self.last_modified[path]:
                # Modified file
                self.last_modified[path] = mtime
                changed.append((ticker, path))
        
        return changed
    
    def _poll_loop(self):
        """Main polling loop (runs in background thread)"""
        print(f"[IntradayWatcher] Started monitoring: {self.folder}")
        print(f"[IntradayWatcher] Poll interval: {self.poll_interval}s")
        
        while self._running:
            try:
                updated = self.check_updates()
                
                for ticker, path in updated:
                    try:
                        # Read data using MubasherAdapter from INTRADAY folder
                        from core.adapters.MubasherAdapter import  MubasherAdapter, MUBASHER_INTRADAY
                        
                        # Use intraday folder 
                        df = MubasherAdapter.get_intraday_data(ticker, MUBASHER_INTRADAY)
                        
                        if df is not None and not df.empty:
                            # Reset index to have Date/Time as column if needed, but get_intraday_data sets index
                            # LiveFeedManager expects df
                            
                            print(f"[{TimeUtils.now().strftime('%H:%M:%S')}] Update: {ticker} ({len(df)} bars)")
                            
                            # Check for signal
                            signal = check_signal(ticker, df)
                            
                            # Store in LiveFeedManager for Dashboard access
                            try:
                                from core.market import LiveFeedManager
                                LiveFeedManager.update_ticker(ticker, df, signal)
                            except Exception as lfm_err:
                                pass  # Silent fail if manager not available
                            
                            # Call callback if provided
                            if self.on_update:
                                self.on_update(ticker, df)
                    except Exception as e:
                        print(f"[IntradayWatcher] Error processing {ticker}: {e}")
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                print(f"[IntradayWatcher] Poll error: {e}")
                time.sleep(self.poll_interval)
        
        print("[IntradayWatcher] Stopped.")
    
    def start(self):
        """Start the watcher in background thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the watcher"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
    
    @property
    def is_running(self) -> bool:
        return self._running


def check_signal(ticker: str, df: pd.DataFrame) -> Optional[dict]:
    """
    Check if latest data represents a buy signal.
    DEPRECATED: Real-time intraday monitoring has moved to LiveFeedManager
    with 5-minute candle aggregation and multi-tick persistence.
    """
    import warnings
    warnings.warn(
        "IntradayWatcher.check_signal is deprecated. LiveFeedManager is the active engine.",
        DeprecationWarning,
        stacklevel=2,
    )
    if df is None or len(df) < 60:
        return None
    
    try:
        # Normalize columns
        if 'Closed' in df.columns and 'Close' not in df.columns:
            df = df.rename(columns={'Closed': 'Close'})
        df.columns = df.columns.str.strip().str.title()
        
        # Calculate indicators
        df['RSI'] = df.ta.rsi(length=14)
        df['ATR'] = df.ta.atr(length=14)
        df['EFI'] = df.ta.efi(length=13)
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        df['Avg_Vol'] = df['Volume'].rolling(20).mean()
        df['Rel_Vol'] = df['Volume'] / df['Avg_Vol'].replace(0, float('nan'))
        df['Move'] = ((df['Close'] - df['Open']) / df['Open'].replace(0, float('nan'))) * 100
        df['Turnover'] = df['Close'] * df['Volume']
        df['Avg_Turnover'] = df['Turnover'].rolling(20).mean()
        
        # True daily resistance if available, fallback to rolling high
        daily_res = None
        try:
            from core.market.LiveFeedManager import LiveFeedManager
            daily_res = LiveFeedManager._resistance_cache.get(ticker, {}).get('R20')
        except Exception:
            pass
        if daily_res and not pd.isna(daily_res) and daily_res > 0:
            df['Res'] = float(daily_res)
        else:
            df['Res'] = df['High'].rolling(settings.LOOKBACK).max().shift(1)
        
        last = df.iloc[-1]
        
        # Scale daily turnover requirement to 5-minute bar expectation (~54 bars per EGX session)
        intraday_min_turnover = float(settings.MIN_TURNOVER) / 54.0
        
        # Signal conditions
        is_liquid = last['Avg_Turnover'] > intraday_min_turnover
        is_momentum = (last['Rel_Vol'] > settings.VOL_SPIKE and 
                       last['Move'] >= settings.MOMENTUM and
                       settings.RSI_MIN < last['RSI'] < settings.RSI_MAX)
        breakout = last['Close'] > last['Res']
        power_positive = last['EFI'] > 0
        above_ema = last['Close'] > last['EMA9']
        
        # Score
        score = 0
        if breakout and power_positive: score += 3
        if is_liquid and is_momentum: score += 5
        if last['Rel_Vol'] > 1.5: score += 1
        if settings.RSI_MIN < last['RSI'] < 70: score += 1
        if above_ema: score += 1
        
        if score >= 6:
            return {
                'ticker': ticker,
                'price': last['Close'],
                'score': score,
                'rsi': last['RSI'],
                'volume_ratio': last['Rel_Vol'],
                'time': TimeUtils.now()
            }
        
        return None
        
    except Exception as e:
        return None



# Global cache for alert deduplication (Persistent)
ALERTS_LOG_FILE = os.path.join(os.path.dirname(__file__), "daily_alerts.json")
ALERT_COOLDOWN = 900  # 15 minutes in seconds (still useful for same-day repeats if logic changes)
LAST_ALERTS_CACHE = {} # Runtime cache for watchlist alert cooldowns

def load_alert_log():
    """Load persistent alert log from disk."""
    if os.path.exists(ALERTS_LOG_FILE):
        try:
            with open(ALERTS_LOG_FILE, 'r') as f:
                data = json.load(f)
                # Auto-reset if date changed
                if data.get('date') != TimeUtils.today().strftime('%Y-%m-%d'):
                    return {'date': TimeUtils.today().strftime('%Y-%m-%d'), 'alerts': {}}
                return data
        except:
            pass
    return {'date': TimeUtils.today().strftime('%Y-%m-%d'), 'alerts': {}}

def save_alert_log(log_data):
    """Save alert log to disk."""
    try:
        with open(ALERTS_LOG_FILE, 'w') as f:
            json.dump(log_data, f, indent=2)
    except Exception as e:
        print(f"Error saving alert log: {e}")

def on_intraday_update(ticker: str, df: pd.DataFrame):
    """Callback when intraday data updates - check for signals and watchlist alerts"""
    if TimeUtils.is_simulating():
        return # Silent in simulation mode
    
    # 1. Check for new signals
    signal = check_signal(ticker, df)
    
    if signal:
        # Load persistent log
        log_data = load_alert_log()
        alerts = log_data.get('alerts', {})
        
        # Check if already alerted TODAY
        if ticker not in alerts:
            
            # Format message
            msg = f"""
🔔 **LIVE SIGNAL DETECTED**

📈 **{signal['ticker']}** @ {signal['price']:.2f}
⭐ Score: {signal['score']}/11
📊 RSI: {signal['rsi']:.1f}
📦 Vol Ratio: {signal['volume_ratio']:.1f}x
⏰ {signal['time'].strftime('%H:%M:%S')}
"""
            print(msg)
            
            # Send Telegram alert
            try:
                if settings.ENABLE_INTRADAY_ALERTS:
                    TelegramBot_Alerts.send_message(msg)
                
                # Update and Save Log
                alerts[ticker] = datetime.now().isoformat()
                log_data['alerts'] = alerts
                save_alert_log(log_data)
                
            except Exception as e:
                print(f"Telegram alert failed: {e}")
        else:
            # Already alerted today
            pass
    
    # 2. Check Watchlist price levels (Entry/SL hit)
    try:
        from core.market import Watchlist
        watchlist = Watchlist.load_watchlist()
        
        current_price = df['Close'].iloc[-1] if not df.empty else None
        
        if current_price and ticker in [w.get('ticker', '').upper() for w in watchlist]:
            for item in watchlist:
                if item.get('ticker', '').upper() == ticker.upper():
                    entry = item.get('entry_price', 0)
                    sl = item.get('stop_loss', 0)
                    tp = item.get('target_price', 0)
                    
                    alert_type = None
                    alert_msg = ""
                    
                    # Check conditions
                    if entry and abs(current_price - entry) / entry < 0.005:
                        alert_type = "ENTRY"
                        alert_msg = f"🎯 **ENTRY HIT**: {ticker} @ {current_price:.2f} (Target: {entry:.2f})"
                    elif sl and current_price <= sl:
                        alert_type = "SL"
                        alert_msg = f"🚨 **STOP LOSS HIT**: {ticker} @ {current_price:.2f} (SL: {sl:.2f})"
                    elif tp and current_price >= tp:
                        alert_type = "TP"
                        alert_msg = f"✅ **TARGET HIT**: {ticker} @ {current_price:.2f} (TP: {tp:.2f})"
                    
                    # Send alert with cooldown per type
                    if alert_type:
                        key = f"{ticker}_{alert_type}"
                        last_wl_time = LAST_ALERTS_CACHE.get(key)
                        now = TimeUtils.now()
                        
                        if last_wl_time is None or (now - last_wl_time).total_seconds() > ALERT_COOLDOWN:
                            print(alert_msg)
                            
                            # Generate Premium Card
                            try:
                                if settings.ENABLE_INTRADAY_ALERTS:
                                    from core import ReportGenerator
                                    reason = "TARGET" if alert_type == "TP" else "STOP_LOSS" if alert_type == "SL" else "ENTRY"
                                    if entry > 0:
                                        pnl_pct = (current_price - entry) / entry * 100
                                        card_buf = ReportGenerator.create_exit_card(ticker, current_price, entry, pnl_pct, reason)
                                        TelegramBot_Alerts.send_image(card_buf, caption=alert_msg)
                                    else:
                                        TelegramBot_Alerts.send_message(alert_msg)
                            except Exception as img_err:
                                print(f"Failed to generate exit card: {img_err}")
                                if settings.ENABLE_INTRADAY_ALERTS:
                                    TelegramBot_Alerts.send_message(alert_msg)

                            LAST_ALERTS_CACHE[key] = now
                        
                    break
    except Exception as e:
        pass  # Watchlist not available or error



# === STANDALONE RUNNER ===
if __name__ == "__main__":
    print("=" * 60)
    print("INTRADAY WATCHER - LIVE MODE")
    print("=" * 60)
    print(f"Folder: {settings.METASTOCK_INTRADAY_FOLDER}")
    print("Press Ctrl+C to stop\n")
    
    watcher = IntradayWatcher(
        poll_interval=5.0,
        on_update=on_intraday_update
    )
    watcher.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        watcher.stop()
        print("Done!")
