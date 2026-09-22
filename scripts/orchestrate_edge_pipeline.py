import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from core import DataManager
from core import Heimdall
from core import SignalEngine
from core import SignalAccuracyChecker

def setup_args():
    parser = argparse.ArgumentParser(description="Edge Pipeline Orchestrator (Horus Edition)")
    parser.add_argument("--output-dir", type=str, default="reports/edge_pipeline", help="Directory to save output")
    parser.add_argument("--symbols", type=str, help="Comma-separated list of symbols to scan")
    parser.add_argument("--as-of", type=str, help="Date to analyze (YYYY-MM-DD)")
    parser.add_argument("--backtest", action="store_true", help="Run historical validation for found tickets")
    return parser.parse_args()

def generate_pine_concept(ticket):
    """
    Synthesize Pine Script concept logic for a given ticket.
    (Simplified prototype for Stage 1)
    """
    ticker = ticket['ticker']
    edge_type = ticket['type']

    concept = {
        "concept_id": f"EG_{ticker}_{edge_type.replace(' ', '_').upper()}",
        "entry_rules": [],
        "pine_snippet": ""
    }

    if edge_type == "Whale Trap":
        concept["entry_rules"] = [
            "Price makes 20-day swing low",
            "Close sitting back above swing low (failed breakdown)",
            "OBV slope is positive over last 20 bars (Accumulation)"
        ]
        concept["pine_snippet"] = """
// Whale Trap Logic
swingLow = ta.lowest(low[1], 20)
isTrap = low < swingLow and close > swingLow
obv = ta.cum(math.sign(ta.change(close)) * volume)
isAccum = ta.linreg(obv, 20, 0) > 0
entry = isTrap and isAccum
"""
    elif edge_type == "Shadow Flow":
        concept["entry_rules"] = [
            "RSI below 30",
            "Price > 3 ATRs from EMA9",
            "RelVol > 1.5"
        ]
        concept["pine_snippet"] = """
// Shadow Flow Logic
isOversold = rsi < 30
ema9 = ta.ema(close, 9)
atr = ta.atr(14)
isStretched = (ema9 - close) > (atr * 3)
isLiquid = volume > ta.sma(volume, 20) * 1.5
entry = isOversold and isStretched and isLiquid
"""
    return concept

def run_auto_detect(output_dir, symbols=None, as_of=None):
    print(f"[*] Running auto_detect stage...")
    tickets = []

    if symbols:
        ticker_list = symbols.split(',')
    else:
        ticker_list = [f.stem for f in Path("data/EGX/history").glob("*.parquet")]

    print(f"[*] Scanning {len(ticker_list)} symbols for edges...")

    for ticker in ticker_list:
        df = DataManager.DataManager.get_stock_data(ticker)
        if df is None or len(df) < 50:
            continue

        df = SignalEngine.add_indicators(df)
        diag = Heimdall.diagnose_stock_optimized(ticker, df)

        if diag.get("trap_status") == "BEAR_TRAP" and diag.get("whale_activity") == "ACCUMULATION":
            tickets.append({
                "ticker": ticker,
                "type": "Whale Trap",
                "description": "Bear trap detected with smart money accumulation",
                "timestamp": df.index[-1].isoformat(),
                "price": float(df['Close'].iloc[-1]),
                "confidence": 0.85
            })

        trickster = SignalEngine.check_trickster_signal(df)
        if trickster:
            tickets.append({
                "ticker": ticker,
                "type": "Shadow Flow",
                "description": "Extreme mean reversion stretch with volume participation",
                "timestamp": df.index[-1].isoformat(),
                "price": float(df['Close'].iloc[-1]),
                "confidence": 0.75,
                "meta": trickster
            })

    tickets_path = Path(output_dir) / "tickets"
    tickets_path.mkdir(parents=True, exist_ok=True)

    market_summary = {
        "scan_date": as_of or datetime.now().strftime("%Y-%m-%d"),
        "total_scanned": len(ticker_list),
        "tickets_found": len(tickets)
    }

    with open(tickets_path / "market_summary.json", "w") as f:
        json.dump(market_summary, f, indent=2)

    for i, t in enumerate(tickets):
        with open(tickets_path / f"ticket_{t['ticker']}_{i}.yaml", "w") as f:
            yaml.dump(t, f)

    print(f"[+] auto_detect complete. Found {len(tickets)} potential edges.")
    return tickets

def run_backtest_validation(output_dir, tickets):
    print(f"[*] Running Stage 2: Historical Validation...")
    results_path = Path(output_dir) / "validation"
    results_path.mkdir(parents=True, exist_ok=True)

    validation_reports = []

    for ticket in tickets:
        ticker = ticket['ticker']
        print(f"[*] Validating edge for {ticker}...")

        # We run a 1-year lookback backtest for this specific ticker to see if this "Type" works
        # In a real scenario, we'd filter the backtest to only trigger on the specific edge logic
        # For now, we'll use SignalAccuracyChecker as a proxy

        # We'll simulate a focused backtest for the last 180 days
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (pd.to_datetime(end_date) - pd.Timedelta(days=180)).strftime("%Y-%m-%d")

        # Use existing checker (requires 'allowed_tickers' filter)
        report = SignalAccuracyChecker.run_accuracy_check(
            start_date=start_date,
            end_date=end_date,
            window_days=10,
            index_choice="ALL"
        )

        # Filter signals to only this ticker
        ticker_signals = [s for s in report['signals'] if s['ticker'] == ticker]

        ticker_summary = {
            "ticker": ticker,
            "edge_type": ticket['type'],
            "total_historical_signals": len(ticker_signals),
            "win_rate": 0,
            "avg_pnl": 0
        }

        if ticker_signals:
            wins = sum(1 for s in ticker_signals if s['outcome'] == 'TP_HIT')
            ticker_summary["win_rate"] = (wins / len(ticker_signals)) * 100
            ticker_summary["avg_pnl"] = np.mean([s['pnl_pct'] for s in ticker_signals])

        validation_reports.append(ticker_summary)

        with open(results_path / f"val_{ticker}.yaml", "w") as f:
            yaml.dump(ticker_summary, f)

    print(f"[DONE] Validation complete. {len(validation_reports)} reports generated.")
    return validation_reports

def main():
    args = setup_args()
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"=== Horus Edge Pipeline Orchestrator ===")

    # 1. Auto Detect
    tickets = run_auto_detect(args.output_dir, symbols=args.symbols, as_of=args.as_of)

    # 2. Synthesis (Pine Concepts)
    print(f"[*] Running Stage 1: Logic Synthesis...")
    concepts_path = output_path / "concepts"
    concepts_path.mkdir(parents=True, exist_ok=True)
    for ticket in tickets:
        concept = generate_pine_concept(ticket)
        with open(concepts_path / f"concept_{ticket['ticker']}.yaml", "w") as f:
            yaml.dump(concept, f)

    # 3. Backtest Validation
    if args.backtest:
        run_backtest_validation(args.output_dir, tickets)

    print(f"=== Pipeline Run Summary ===")
    print(f"[DONE] Outputs available in {output_path}")

if __name__ == "__main__":
    main()
