import json
import os
import datetime
import pandas as pd
from core import TimeUtils
from colorama import Fore, Style, init

init(autoreset=True)

JOURNAL_FILE = "journal.json"

def load_journal():
    if not os.path.exists(JOURNAL_FILE):
        return []
    with open(JOURNAL_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_journal(journal):
    with open(JOURNAL_FILE, "w") as f:
        json.dump(journal, f, indent=4)

def log_trade(ticker, entry_price, exit_price, shares, entry_date, exit_date, reason, tag="General", mae=0.0, mfe=0.0):
    """
    Logs a completed trade with advanced metadata.
    
    Args:
        ticker (str): Stock symbol
        entry_price (float): Entry
        exit_price (float): Exit
        shares (int): Qty
        entry_date (str): YYYY-MM-DD
        exit_date (str): YYYY-MM-DD
        reason (str): Text description
        tag (str): Strategy tag e.g. "Breakout", "Reversal", "FOMO"
        mae (float): Max Adverse Excursion (Lowest price price hit while in trade)
        mfe (float): Max Favorable Excursion (Highest price hit while in trade)
    """
    journal = load_journal()
    
    ticker = ticker.upper()
    total_fees = (entry_price * shares * 0.003) + (exit_price * shares * 0.003) # 0.3% fee
    pnl = ((exit_price - entry_price) * shares) - total_fees
    pnl_pct = (pnl / (entry_price * shares)) * 100
    
    # Calculate Efficiency if MAE/MFE provided
    # MAE Efficiency: Did we withstand too much heat? (Drawdown vs PnL)
    # MFE Efficiency: Did we capture the move? (PnL vs Max Potential)
    
    trade = {
        "ticker": ticker,
        "entry_date": entry_date,
        "entry_price": entry_price,
        "exit_date": exit_date,
        "exit_price": exit_price,
        "shares": shares,
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 2),
        "reason": reason,
        "tag": tag, 
        "mae": mae,
        "mfe": mfe,
        "logged_at": TimeUtils.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    journal.append(trade)
    save_journal(journal)
    print(f"{Fore.GREEN}Logged trade for {ticker}: {pnl_pct:+.2f}% P&L [Tag: {tag}]")

def delete_trade(index):
    """Delete a trade from journal by index"""
    journal = load_journal()
    if 0 <= index < len(journal):
        removed = journal.pop(index)
        save_journal(journal)
        print(f"{Fore.YELLOW}Deleted trade: {removed['ticker']}")
        return True
    return False

def update_trade(index, **kwargs):
    """Update a trade's details by index"""
    journal = load_journal()
    if 0 <= index < len(journal):
        for key, value in kwargs.items():
            if key in journal[index]:
                journal[index][key] = value
            # Allow adding new keys (Schema Migration)
            else:
                 journal[index][key] = value
        save_journal(journal)
        return True
    return False

def get_journal_dataframe():
    """Returns Pandas DataFrame of the journal with safe defaults"""
    journal = load_journal()
    if not journal:
        return pd.DataFrame()
    
    df = pd.DataFrame(journal)
    
    # Backfill new columns if missing
    if 'tag' not in df.columns: df['tag'] = "General"
    if 'mae' not in df.columns: df['mae'] = 0.0
    if 'mfe' not in df.columns: df['mfe'] = 0.0
    
    # Fill specific row NaNs
    df['tag'] = df['tag'].fillna("General")
    df['mae'] = df['mae'].fillna(0.0)
    df['mfe'] = df['mfe'].fillna(0.0)
    
    return df

def show_summary():
    df = get_journal_dataframe()
    if df.empty:
        print(f"{Fore.CYAN}Journal is empty.")
        return
    
    total_pnl = df['pnl'].sum()
    win_rate = (df['pnl'] > 0).mean() * 100
    
    print(f"\n{Style.BRIGHT}{Fore.YELLOW}TRADE JOURNAL SUMMARY (SMART)")
    print("=" * 30)
    print(f"Total Trades:      {len(df)}")
    print(f"Total Net P&L:     {Fore.GREEN if total_pnl >= 0 else Fore.RED}{total_pnl:,.2f} EGP")
    print(f"Win Rate:          {win_rate:.1f}%")
    
    # Tag Breakdown
    if 'tag' in df.columns:
        print(f"\n{Style.BRIGHT}BY STRATEGY TAG:")
        tag_grp = df.groupby('tag')['pnl'].sum()
        for tag, pnl in tag_grp.items():
             print(f"  {tag:<10}: {Fore.GREEN if pnl >=0 else Fore.RED}{pnl:,.0f} EGP")

    print("-" * 30)
    print(f"\n{Style.BRIGHT}{'TICKER':<8} {'TAG':<10} {'P&L %':>8} {'P&L EGP':>11} {'MFE':>7}")
    for _, row in df.tail(10).iterrows():
        color = Fore.GREEN if row['pnl'] > 0 else Fore.RED
        print(f"{row['ticker']:<8} {row['tag']:<10} {color}{row['pnl_pct']:>7.2f}% {color}{row['pnl']:>11,.0f} {row['mfe']:>7}")

if __name__ == "__main__":
    import sys
    # Basic CLI
    if len(sys.argv) > 1 and sys.argv[1].lower() == "summary":
        show_summary()
    else:
        show_summary()
