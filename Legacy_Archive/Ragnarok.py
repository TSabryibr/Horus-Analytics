"""
RAGNAROK (THE CLEANER)
======================
"The old world must burn to make way for the new."

Organizes your workspace:
1. Preserves the SKELETON (Data/Settings).
2. Preserves the NINE REALMS (Loki's Code).
3. Banishes the OLD LOGIC to 'Legacy_Archive'.

Author: LOKI
"""

import os
import shutil
from colorama import init, Fore, Style

init(autoreset=True)

# 1. THE SACRED TEXTS (DO NOT TOUCH)
# These are required dependencies or the new divine modules.
KEEP_LIST = [
    # The Skeleton
    "DataManager.py",
    "MarketLists.py",
    "py",
    "AutoTrader.py",          # Keep execution logic for now
    "MubasherAdapter.py",     # Keep API adapters
    "MetaStockAdapter.py",
    "ReportGenerator.py",     # Useful util
    
    # The Nine Realms
    "ChitauriScepter.py",
    "StressTest.py",
    "MarketPredictor.py",
    "SmartMoneyTracker.py",
    "SectorRotation.py",
    "TheMirror.py",
    "Laevateinn.py",
    "TheCasket.py",
    "Fenrir.py",
    "HuginMunin.py",
    
    # Self
    "Ragnarok.py"
]

# 2. THE OLD GODS (TO BE ARCHIVED)
# These are the files being replaced by the Nine Realms.
ARCHIVE_LIST = [
    "SignalEngine.py",
    "DailyScanner.py",
    "IntradayWatcher.py",
    "IntradayRealism.py",
    "SignalAccuracyChecker.py", # Replaced by HuginMunin
    "PortfolioSimulator.py",    # Replaced by Fenrir/Hugin logic (mostly)
    "RiskManager.py",           # Replaced by Fenrir
    "SectorAnalysis.py"         # Replaced by SectorRotation
]

def clean_house():
    print(Fore.RED + Style.BRIGHT + "🔥 INITIATING RAGNAROK PROTOCOL...")
    
    # Create the Crypt
    archive_dir = "Legacy_Archive"
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        print(Fore.YELLOW + f"  Created crypt: {archive_dir}/")
    
    # Move the Old Gods
    moved_count = 0
    for file in ARCHIVE_LIST:
        if os.path.exists(file):
            try:
                shutil.move(file, os.path.join(archive_dir, file))
                print(Fore.WHITE + f"  Banished: {file} -> {archive_dir}/")
                moved_count += 1
            except Exception as e:
                print(Fore.RED + f"  Failed to banish {file}: {e}")
    
    print(Fore.CYAN + "-" * 50)
    print(Fore.GREEN + f"  Ragnarok Complete. {moved_count} old files archived.")
    print(Fore.GREEN + "  The Nine Realms now rule this folder.")
    print(Fore.CYAN + "-" * 50)

if __name__ == "__main__":
    confirm = input(Fore.RED + "Are you sure you want to clean up the old Horus files? (Y/N): ")
    if confirm.upper() == 'Y':
        clean_house()
    else:
        print("Mercy shown. The old files remain.")
