import time
import logging
import pandas as pd
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime

logger = logging.getLogger(__name__)

class MarketEventHandler(FileSystemEventHandler):
    def __init__(self, tickers, callback):
        self.tickers = tickers
        self.callback = callback
        # Keep track of file sizes to only read new data
        self.file_positions = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        ticker = file_path.stem
        
        # Filter for watched tickers (or all if tickers is None)
        if self.tickers and ticker not in self.tickers:
            return
            
        # Optional: Checking extension
        if file_path.suffix.lower() != '.csv':
            return

        try:
            self.process_update(file_path, ticker)
        except Exception as e:
            logger.warning("[Sentinel] Error reading ticker=%s err=%s", ticker, e)

    def process_update(self, file_path, ticker):
        """
        Reads only the new lines appended to the file.
        """
        current_size = file_path.stat().st_size
        last_pos = self.file_positions.get(ticker, 0)
        
        if current_size <= last_pos:
            # File didn't grow (or was reset), reset position if needed
            if current_size < last_pos:
                self.file_positions[ticker] = 0
            return

        with open(file_path, 'r') as f:
            f.seek(last_pos)
            new_lines = f.readlines()
            self.file_positions[ticker] = current_size
            
        if not new_lines:
            return

        # Parse the new lines
        # Expected CSV format: <DTYYYYMMDD>,<HHMMSS>,<OPEN>,<HIGH>,<LOW>,<CLOSE>,<VOL>
        # We need to handle potential partial lines or headers if it's a new file, 
        # but typically this is just data rows.
        
        for line in new_lines:
            line = line.strip()
            if not line or line.startswith('<'): # Skip empty or header
                continue
                
            parts = line.split(',')
            if len(parts) < 7:
                continue
                
            # Parse row
            try:
                # 0: Date, 1: Time, 2: Open, 3: High, 4: Low, 5: Close, 6: Vol
                dt_str = parts[0] + parts[1].zfill(6)
                timestamp = pd.to_datetime(dt_str, format='%Y%m%d%H%M%S')
                
                bar = {
                    'ticker': ticker,
                    'timestamp': timestamp,
                    'open': float(parts[2]),
                    'high': float(parts[3]),
                    'low': float(parts[4]),
                    'close': float(parts[5]),
                    'volume': float(parts[6])
                }
                
                # Send to Strategy
                self.callback(bar)
                
            except ValueError:
                continue

class MarketSentinel:
    def __init__(self, watch_dir):
        """
        Args:
            watch_dir: Path object to the Intraday CSV folder.
        """
        self.watch_dir = Path(watch_dir)
        self.observer = None
        self._running = False
        
    def start(self, tickers=None, on_data_callback=None):
        """
        Starts watching the folder.
        
        Args:
            tickers: List of tickers strings to watch (e.g. ['COMI', 'EGX30']). If None, watch all.
            on_data_callback: Function(bar_dict) to call when new data arrives.
        """
        if not self.watch_dir.exists():
            raise FileNotFoundError(f"Directory not found: {self.watch_dir}")
        if self._running:
            return

        self.observer = Observer()
        self._running = True

        event_handler = MarketEventHandler(tickers, on_data_callback)
        self.observer.schedule(event_handler, str(self.watch_dir), recursive=False)
        self.observer.start()
        logger.info("[Sentinel] Watching %s for updates", self.watch_dir)
        
        # Pre-fill file positions to end-of-file so we only get NEW data
        # (Otherwise it might read the whole history on first modify)
        for f in self.watch_dir.glob("*.csv"):
            if tickers and f.stem not in tickers:
                continue
            event_handler.file_positions[f.stem] = f.stat().st_size

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
            logger.info("[Sentinel] Stopped")
        finally:
            if self.observer:
                self.observer.join(timeout=5)

    def stop(self):
        self._running = False
        if self.observer:
            self.observer.stop()

if __name__ == "__main__":
    # Test Run
    def print_bar(bar):
        print(f"[LIVE] {bar['ticker']} @ {bar['timestamp'].time()} | Price: {bar['close']} | Vol: {bar['volume']}")

    # Use the hardcoded path from our project
    path = Path(r"C:\Users\TSabr\AppData\Roaming\MubasherTrade\PRO Egypt\UserData\847857994\MetaStock\Intraday\CASE")
    
    sentinel = MarketSentinel(path)
    # Watch COMI only for testing
    sentinel.start(tickers=['COMI'], on_data_callback=print_bar)
