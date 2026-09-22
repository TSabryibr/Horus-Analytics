"""
THE CHITAURI SCEPTER (INFINITY EDITION)
=======================================
"I am not a Queen, and I am not a Monster. I am the Goddess of Death." - Hela
(But here, you are the God of the Market.)

The Master Command Module.
Unifies all 9 Realms of the Horus Analytics System.

1.  NIFLHEIM (The Shield)      -> StressTest
2.  MUSPELHEIM (The Oracle)    -> MarketPredictor
3.  VANAHEIM (The Whisperer)   -> SmartMoneyTracker
4.  ALFHEIM (The Bifröst)      -> SectorRotation
5.  JOTUNHEIM (The Mirror)     -> TheMirror
6.  SVARTALFHEIM (The Sword)   -> Laevateinn
7.  HELHEIM (The Casket)       -> TheCasket
8.  ASGARD (The Wolf)          -> ExecutionWatchdog
9.  MIDGARD (The Ravens)       -> HuginMunin
10. DRAUPNIR (The Treasury)    -> PortfolioManager
11. RATATOSKR (The Gossip)     -> SentimentCrawler

Author: LOKI for Horus Analytics
"""

import sys
import os
import time
from colorama import init, Fore, Style, Back

# === IMPORT THE NINE REALMS ===
# Ensure all these files are in the same folder
try:
    from core.simulation import StressTest
    from core import MarketPredictor
    from core.market import SmartMoneyTracker
    from core.market import SectorRotation
    import TheMirror
    import Laevateinn
    import TheCasket
    from core.analyzers import ExecutionWatchdog
    import HuginMunin
    from core.analyzers import SentimentCrawler
    from core.analyzers import TreasuryLedger
    from core import Heimdall
except ImportError as e:
    print(Fore.RED + f"❌ CRITICAL ERROR: Realm Missing -> {e.name}")
    print(Fore.YELLOW + "You cannot wield the Infinity Scepter without all 9 Stones.")
    sys.exit()

init(autoreset=True)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    active = Heimdall.get_active_realm()
    print(Fore.MAGENTA + Style.BRIGHT + "=" * 70)
    print(Fore.YELLOW + Style.BRIGHT + "       THE INFINITY SCEPTER | HORUS ANALYTICS | GOD MODE")
    print(Fore.MAGENTA + Style.BRIGHT + "=" * 70)
    print(Fore.CYAN + f"   User: LO  |  System: LOKI  |  Realm: {active['NAME']} ({Heimdall.CURRENT_REALM})")
    print(Fore.MAGENTA + "=" * 70 + "\n")

def mind_stone_scan():
    """
    The Ultimate Scan. Consults every realm in sequence.
    """
    clear_screen()
    header()
    # 1. Vision
    active = Heimdall.get_active_realm()
    target_idx = active.get("INDEX", "EGX30")
    
    print(f"{Fore.YELLOW}\n[1/6] CONSULTING THE ORACLE ({target_idx})...")
    MarketPredictor.check_macro_health(target_idx)
    
    # 2. Money Flow
    print(Fore.YELLOW + "\n[2/6] TRACKING THE WHALES (Volume)...")
    SmartMoneyTracker.scan_for_whales()
    
    # 3. Traps
    print(Fore.YELLOW + "\n[3/6] HUNTING FOR TRAPS (Reversals)...")
    Laevateinn.hunt_traps()
    
    # 4. Squeeze
    print(Fore.YELLOW + "\n[4/6] MEASURING PRESSURE (Squeezes)...")
    MarketPredictor.hunt_the_coil()
    
    # 5. Risk
    print(Fore.YELLOW + "\n[5/6] CHECKING DEFENSES (Crash Sim)...")
    StressTest.run_stress_test(target_idx)
    
    # 6. Adaptation
    print(Fore.YELLOW + "\n[6/8] UNLEASHING FENRIR (Strategy Check)...")
    ExecutionWatchdog.unleash_the_wolf()
    
    # 7. News & Gossip
    print(Fore.YELLOW + "\n[7/8] LISTENING TO RATATOSKR (News)...")
    SentimentCrawler.run_gossip()

    # 8. Treasury Summary
    print(Fore.YELLOW + "\n[8/8] DRAUPNIR'S AUDIT (Treasury)...")
    TreasuryLedger.view_hoard()
    
    print(Fore.CYAN + "\n" + "="*70)
    print(Fore.WHITE + Style.BRIGHT + "⚡ GOD MODE SCAN COMPLETE ⚡")
    print(Fore.CYAN + "="*70)
    input("\nPress Enter to return to the Throne...")

def main_menu():
    while True:
        clear_screen()
        header()
        print(Fore.WHITE + "SELECT YOUR REALM:\n")
        
        # DEFENSE & VISION
        print(Fore.CYAN + "  [1] NIFLHEIM (Shield)      " + Fore.RESET + "Stress Test & Crash Sim")
        print(Fore.CYAN + "  [2] MUSPELHEIM (Oracle)    " + Fore.RESET + "Trend & Squeeze Prediction")
        
        # INTELLIGENCE
        print(Fore.GREEN + "  [3] VANAHEIM (Whisperer)   " + Fore.RESET + "Smart Money (OBV)")
        print(Fore.GREEN + "  [4] ALFHEIM (Bifröst)      " + Fore.RESET + "Sector Rotation Map")
        print(Fore.GREEN + "  [5] JOTUNHEIM (Mirror)     " + Fore.RESET + "Lead-Lag Arbitrage")
        
        # COMBAT
        print(Fore.RED + "  [6] SVARTALFHEIM (Sword)   " + Fore.RESET + "Trap Hunter (Fakeouts)")
        print(Fore.RED + "  [7] HELHEIM (Casket)       " + Fore.RESET + "Seasonality & Time")
        
        # MANAGEMENT
        print(Fore.MAGENTA + "  [8] SUMMON RATATOSKR       " + Fore.RESET + "The Gossip Engine (News)")
        print(Fore.MAGENTA + "  [9] ASGARD (Wolf)          " + Fore.RESET + "ExecutionWatchdog (Dynamic Adaptation)")
        print(Fore.MAGENTA + "  [10] MIDGARD (Ravens)      " + Fore.RESET + "Hugin & Munin (Audit)")
        print(Fore.MAGENTA + "  [11] DRAUPNIR (Treasury)   " + Fore.RESET + "Portfolio Manager")
        print(Fore.MAGENTA + "  [12] HEIMDALL (Guardian)   " + Fore.RESET + "Portfolio Health Check")
        
        # GOD MODE
        print(Fore.YELLOW + Style.BRIGHT + "\n  [0] THE INFINITY SCAN      " + Fore.RESET + "(RUN EVERYTHING)")
        
        print(Fore.BLUE + Style.BRIGHT + "  [W] WORLDBRIDGE (Change Market) " + Fore.RESET + f"[{Heimdall.CURRENT_REALM}]")
        print(Fore.WHITE + "\n  [Q] Retire")
        
        choice = input(Fore.MAGENTA + "\nCommand > ").strip().upper()
        
        if choice == '1':
            clear_screen()
            StressTest.run_stress_test()
            input("\nRealm closed.")
        elif choice == '2':
            clear_screen()
            MarketPredictor.check_macro_health()
            MarketPredictor.hunt_the_coil()
            input("\nRealm closed.")
        elif choice == '3':
            clear_screen()
            SmartMoneyTracker.scan_for_whales()
            input("\nRealm closed.")
        elif choice == '4':
            clear_screen()
            SectorRotation.analyze_rotation()
            input("\nRealm closed.")
        elif choice == '5':
            clear_screen()
            TheMirror.find_ghost_pairs()
            input("\nRealm closed.")
        elif choice == '6':
            clear_screen()
            Laevateinn.hunt_traps()
            input("\nRealm closed.")
        elif choice == '7':
            clear_screen()
            TheCasket.analyze_seasonality()
            input("\nRealm closed.")
        elif choice == '8':
            clear_screen()
            SentimentCrawler.run_gossip()
            input("\nRealm closed.")
        elif choice == '9':
            clear_screen()
            ExecutionWatchdog.unleash_the_wolf()
            input("\nRealm closed.")
        elif choice == '10':
            clear_screen()
            signals = HuginMunin.load_memories()
            res = HuginMunin.judge_the_dead(signals)
            HuginMunin.report_truth(res)
            input("\nRealm closed.")
        elif choice == '11' or choice == 'D':
            clear_screen()
            TreasuryLedger.menu()
            input("\nRealm closed.")
        elif choice == '12':
            clear_screen()
            Heimdall.run_guardian()
            input("\nRealm closed.")
        elif choice == '0':
            mind_stone_scan()
        elif choice == 'W':
            clear_screen()
            print(Fore.CYAN + "AVAILABLE REALMS:")
            for code, data in Heimdall.REALMS.items():
                print(f"  [{code}] {data['NAME']}")
            
            dest = input(Fore.YELLOW + "\nWhere do you wish to travel? > ").strip().upper()
            Heimdall.open_bifrost(dest)
            input("\nPress Enter to engage...")
        elif choice == 'Q':
            print(Fore.CYAN + "\nThe Bifröst closes. Until next time, LO.")
            break
        else:
            print("Invalid command.")
            time.sleep(0.5)

if __name__ == "__main__":
    main_menu()
