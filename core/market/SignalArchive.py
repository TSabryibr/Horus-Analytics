"""
SIGNAL ARCHIVE MODULE
=====================
Saves all generated signals to JSON for compliance and tracking.

Author: Horus Analytics - EGX
Date: 2026-01-17
"""

import json
import os
import datetime
from core import TimeUtils
ARCHIVE_FILE = os.path.join(os.path.dirname(__file__), "signal_archive.json")

def load_archive():
    """Load existing signal archive."""
    if os.path.exists(ARCHIVE_FILE):
        try:
            with open(ARCHIVE_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_archive(archive):
    """Save archive to file."""
    with open(ARCHIVE_FILE, 'w') as f:
        json.dump(archive, f, indent=2, default=str)

def archive_signals(signals, scan_date=None):
    """
    Archive a list of signals with metadata.
    
    Args:
        signals: List of signal dicts from DailyScanner
        scan_date: Date of scan (defaults to today)
    """
    if not signals:
        return
    
    archive = load_archive()
    scan_date = scan_date or TimeUtils.today().strftime("%Y-%m-%d")
    
    for sig in signals:
        entry = {
            'archived_at': TimeUtils.now().isoformat(),
            'scan_date': scan_date,
            'ticker': sig.get('Ticker'),
            'signal_type': sig.get('Signal_Type', 'BUY'),
            'entry_price': sig.get('Entry_Price'),
            'stop_loss': sig.get('Stop_Loss'),
            'target_price': sig.get('Target_Price'),
            'rsi': sig.get('RSI'),
            'volume_x': sig.get('Volume_x'),
            'sector': sig.get('Sector'),
            'score': sig.get('Score'),
            'outcome': None,  # To be filled later (TP_HIT, SL_HIT, EXPIRED)
            'outcome_date': None
        }
        archive.append(entry)
    
    save_archive(archive)
    return len(signals)

def update_outcome(ticker, scan_date, outcome, outcome_date=None):
    """
    Update the outcome of a previously archived signal.
    
    Args:
        ticker: Stock ticker
        scan_date: Original scan date
        outcome: 'TP_HIT', 'SL_HIT', or 'EXPIRED'
        outcome_date: Date outcome occurred
    """
    archive = load_archive()
    
    for entry in archive:
        if entry['ticker'] == ticker and entry['scan_date'] == scan_date:
            entry['outcome'] = outcome
            entry['outcome_date'] = outcome_date or TimeUtils.today().strftime("%Y-%m-%d")
            break
    
    save_archive(archive)

def get_performance_summary():
    """Get summary statistics from archive."""
    archive = load_archive()
    
    total = len(archive)
    with_outcome = [a for a in archive if a['outcome']]
    tp_hits = sum(1 for a in with_outcome if a['outcome'] == 'TP_HIT')
    sl_hits = sum(1 for a in with_outcome if a['outcome'] == 'SL_HIT')
    
    return {
        'total_signals': total,
        'resolved': len(with_outcome),
        'tp_hits': tp_hits,
        'sl_hits': sl_hits,
        'win_rate': round(tp_hits / len(with_outcome) * 100, 1) if with_outcome else 0
    }

if __name__ == "__main__":
    print("Signal Archive Module")
    print(f"Archive file: {ARCHIVE_FILE}")
    summary = get_performance_summary()
    print(f"Stats: {summary}")
