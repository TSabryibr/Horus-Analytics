"""
DRAUPNIR (THE TREASURY)
=======================
"Gold is heavy. Let me carry it for you."

The Central Treasury.
1. Tracks Live Positions (Updates prices in real-time).
2. Calculates Net Worth (Cash + Equity).
3. Manages the Ledger (Add/Close Trades).
4. Monitors Risk (Distance to Stop Loss).

API-First Refactor of the Legacy 'PortfolioManager'.
"""

from core.settings import settings
from utils.currency_fetcher import get_parallel_usd_egp_rate, get_historical_usd_egp_rate
import pandas as pd
import datetime
import os
import sys
import time
import json
from colorama import Fore, Style, init
from core import DataManager
from core import PositionTracker
import database
from core import Heimdall
from core import TimeUtils
from core.exclusions import is_excluded_ticker, normalize_ticker

init(autoreset=True)

def _now():
    """Safe time source to avoid runtime NameError or import issues."""
    try:
        from core import TimeUtils as _tu
        return _tu.now()
    except Exception:
        return datetime.datetime.now()

def genesis_protocol():
    """
    Runs to import initial account state.
    """
    print(Fore.MAGENTA + Style.BRIGHT + "\n✨ GENESIS PROTOCOL INITIATED ✨")
    print(Fore.WHITE + "Calibrating Treasury reserves and initial holdings.\n")
    
    # 1. SET CASH
    try:
        egp_input = input(Fore.YELLOW + "Enter starting AVAILABLE EGP: ").strip()
        starting_egp = float(egp_input.replace(',', ''))
        
        usd_input = input(Fore.YELLOW + "Enter starting AVAILABLE USD: ").strip()
        starting_usd = float(usd_input.replace(',', ''))
        
        # Update Global Settings
        settings.ACCOUNT_BALANCE = starting_egp
        settings.ACCOUNT_BALANCE_USD = starting_usd
        settings.STARTING_CAPITAL = starting_egp # Legacy support
        settings.save_settings()
        
        print(Fore.GREEN + f"   >> EGP Cash set to {starting_egp:,.2f}")
        print(Fore.GREEN + f"   >> USD Cash set to {starting_usd:,.2f}")
    except ValueError:
        print(Fore.RED + "Invalid amount. Setup cancelled.")
        return
        
    # 2. IMPORT HOLDINGS
    print(Fore.CYAN + "\nAdd existing stocks (Type 'DONE' to finish):")
    
    while True:
        ticker = input(Fore.CYAN + "Ticker (or DONE): ").strip().upper()
        if ticker == "DONE" or not ticker: break
        
        try:
            curr = detect_currency(ticker)
            shares = int(input(f"  Shares of {ticker} ({curr}): ").replace(',', ''))
            price = float(input(f"  Avg Entry Price in {curr}: ").replace(',', ''))
            
            # Add as EXISTING (No cash deduction)
            add_gold(ticker, shares, price, type="EXISTING")
            print(Fore.GREEN + f"   ✅ {ticker} added to Hoard.")
        except ValueError:
            print(Fore.RED + "   Invalid input. Ticker skipped.")
            
    # Create lock file
    with open("genesis.lock", "w") as f: f.write("LOCKED")
    print(Fore.MAGENTA + Style.BRIGHT + "\nGENESIS COMPLETE. THE TREASURY IS SEALED.\n")
    time.sleep(1)

def get_live_price(ticker):

    """
    Fetches the latest price using the DataManager (Universal/Local).
    """
    try:
        intra = DataManager.DataManager.get_intraday_data(ticker, limit=1)
        if intra is not None and not intra.empty:
            return float(intra['Close'].iloc[-1])
    except:
        pass
    try:
        df = DataManager.DataManager.get_stock_data(ticker)
        if df is not None and not df.empty:
            return float(df['Close'].iloc[-1])
    except:
        pass
    return 0.0

def detect_currency(ticker):
    """
    Auto-detects if a ticker is USD based on EGX common USD stocks.
    """
    usd_stocks = {
        'EGBE', 'TRTO', 'NAHO', 'GPPL', 'SAIB', 'NDRL', 'FAITA', 'EGSA', 'MOIL', 'CFGH', 'GTEX'
    }
    return "USD" if ticker.upper() in usd_stocks else "EGP"

def get_hoard_status(portfolio_id=1):
    """
    Returns the full status of the portfolio (The Hoard).
    Used by API and CLI.
    """
    # 1. Start with Empty Default
    result_template = {
        "status": "active",
        "portfolio_id": portfolio_id,
        "cash_egp": 0.0,
        "cash_usd": 0.0,
        "equity_egp": 0.0,
        "equity_usd": 0.0,
        "net_worth_egp": 0.0,
        "net_worth_usd": 0.0,
        "positions": [],
        "position_count": 0
    }

    # 2. Get Portfolio & Cash
    portfolio = database.Portfolio.get_or_none(database.Portfolio.id == portfolio_id)
    if not portfolio:
        # Fallback for CLI/Legacy
        if portfolio_id == 1: 
             # Try to find ANY User portfolio
             portfolio = database.Portfolio.get_or_none(type="USER")
        
    if not portfolio:
        return {"status": "error", "message": "Portfolio not found"}
        
    current_cash_egp = portfolio.cash_egp
    current_cash_usd = portfolio.cash_usd
    
    # 3. Get Ledger Data (Filtered by Portfolio)
    positions = database.Position.select().where(
        (database.Position.status == "OPEN") & 
        (database.Position.entry_date <= _now())
    )
    positions = positions.where(
        (database.Position.portfolio == portfolio.id) | (database.Position.portfolio.is_null())
    )
    
    total_equity_egp = 0.0
    total_equity_usd = 0.0
    position_list = []
    rate = get_parallel_usd_egp_rate()
    
    # 4. Process Positions
    for p in positions:
        curr_price = get_live_price(p.ticker)
        if curr_price == 0: curr_price = p.entry_price
        
        entry_rate = p.entry_usd_rate
        if entry_rate is None or entry_rate <= 0:
            entry_rate = get_historical_usd_egp_rate(p.entry_date)
        
        # Currency equivalents
        if p.currency == "USD":
            cost_usd = p.shares * p.entry_price
            cost_egp = cost_usd * entry_rate
            val_usd = p.shares * curr_price
            val_egp = val_usd * rate
        else:
            cost_egp = p.shares * p.entry_price
            cost_usd = cost_egp / entry_rate
            val_egp = p.shares * curr_price
            val_usd = val_egp / rate
            
        pnl_egp = val_egp - cost_egp
        pnl_usd = val_usd - cost_usd
        pnl_egp_pct = (pnl_egp / cost_egp) * 100 if cost_egp > 0 else 0
        pnl_usd_pct = (pnl_usd / cost_usd) * 100 if cost_usd > 0 else 0
        
        # Risk Calc
        dist_to_sl = ((curr_price - p.stop_loss) / curr_price) * 100 if curr_price != 0 else 0
        dist_to_tp = ((p.target_price - curr_price) / curr_price) * 100 if curr_price != 0 else 0
        
        devaluation_loss = getattr(settings, "DEVALUATION_HURDLE_ENABLED", True) and pnl_egp > 0 and pnl_usd < 0
        
        risk_status = "SAFE"
        if devaluation_loss:
            risk_status = "DEVALUATION_LOSS"
        elif dist_to_sl < 1.0:
            risk_status = "DANGER"
        elif dist_to_sl < 3.0:
            risk_status = "WARNING"
            
        pos_data = {
            "id": p.id,
            "ticker": p.ticker,
            "currency": p.currency,
            "shares": p.shares,
            "entry_price": p.entry_price,
            "current_price": curr_price,
            "entry_date": p.entry_date.isoformat() if p.entry_date else None,
            "exit_date": None,
            # Legacy fields (local currency)
            "market_value": round(val_usd if p.currency == "USD" else val_egp, 2),
            "pnl": round(pnl_usd if p.currency == "USD" else pnl_egp, 2),
            "pnl_pct": round(pnl_usd_pct if p.currency == "USD" else pnl_egp_pct, 2),
            # Hard-currency extensions
            "market_value_usd": round(val_usd, 2),
            "market_value_egp": round(val_egp, 2),
            "pnl_usd": round(pnl_usd, 2),
            "pnl_egp": round(pnl_egp, 2),
            "pnl_usd_pct": round(pnl_usd_pct, 2),
            "pnl_egp_pct": round(pnl_egp_pct, 2),
            "devaluation_loss": devaluation_loss,
            # Limits
            "stop_loss": p.stop_loss,
            "target_price": p.target_price,
            "risk_status": risk_status,
            "dist_to_sl": round(dist_to_sl, 2)
        }
        
        position_list.append(pos_data)
        total_equity_egp += val_egp
        total_equity_usd += val_usd
            
    # 5. Summary Stats
    total_cash_egp = current_cash_egp + current_cash_usd * rate
    total_cash_usd = current_cash_usd + current_cash_egp / rate
    total_net_worth_egp = total_cash_egp + total_equity_egp
    total_net_worth_usd = total_cash_usd + total_equity_usd
    
    status = "active"
    if len(position_list) == 0 and current_cash_egp == 0 and current_cash_usd == 0:
        status = "empty"

    return {
        "status": status,
        "portfolio_id": portfolio.id,
        "name": portfolio.name,
        "type": portfolio.type,
        "cash_egp": round(current_cash_egp, 2),
        "cash_usd": round(current_cash_usd, 2),
        "equity_egp": round(total_equity_egp, 2),
        "equity_usd": round(total_equity_usd, 2),
        "net_worth_egp": round(total_net_worth_egp, 2),
        "net_worth_usd": round(total_net_worth_usd, 2),
        "positions": position_list,
        "position_count": len(position_list)
    }

def add_gold(ticker, shares, price, type="NEW", sl=None, tp=None, tp2=None, date=None, portfolio_id=1, signal_id=None):
    """
    Executes a BUY order (Adds to Hoard).
    type: "NEW" (Deduct Cash) or "EXISTING" (Just Add Record)
    """
    ticker = normalize_ticker(ticker)
    if not ticker:
        return {"status": "error", "message": "Ticker required"}
    if is_excluded_ticker(ticker):
        return {
            "status": "blocked",
            "message": f"Ticker {ticker} is blacklisted and cannot be used.",
            "ticker": ticker,
            "reason": "blacklisted",
        }
    entry_type = str(type or "NEW").upper()

    # Manual execution deadbolt: allow importing existing holdings, block new entries when gated.
    if entry_type != "EXISTING":
        try:
            from core import WalkForwardValidation
            gate = WalkForwardValidation.get_trade_permission(ticker, fail_closed=True)
            if not gate.get("allowed", False):
                reason = gate.get("reason", "blocked")
                return {
                    "status": "blocked",
                    "message": f"WFA gate blocked {ticker}: {reason}",
                    "ticker": ticker,
                    "reason": reason,
                }
        except Exception as e:
            return {
                "status": "blocked",
                "message": f"WFA gate lookup failed for {ticker}: {e}",
                "ticker": ticker,
                "reason": "gate_lookup_error",
            }

    curr = detect_currency(ticker)
    cost = shares * price
    
    # 1. Get Portfolio
    portfolio = database.Portfolio.get_or_none(database.Portfolio.id == portfolio_id)
    if not portfolio:
        return {"status": "error", "message": f"Portfolio {portfolio_id} not found"}

    # 2. Cash Check (enforced against the portfolio's actual database cash balance)
    available_cash = portfolio.cash_egp if curr == "EGP" else portfolio.cash_usd
    if entry_type == "NEW":
        if cost > available_cash:
            return {"status": "error", "message": f"Insufficient {curr} Cash. Needed: {cost:.2f}, Has: {available_cash:.2f}"}
        
    # 3. DB Transaction
    existing = database.Position.get_or_none(
        ticker=ticker, 
        status="OPEN", 
        currency=curr,
        portfolio=portfolio_id
    )
    
    if existing:
        # Average Down/Up
        new_shares = existing.shares + shares
        new_avg_price = ((existing.shares * existing.entry_price) + (shares * price)) / new_shares
        
        # Weighted average entry exchange rate
        old_rate = existing.entry_usd_rate
        if old_rate is None or old_rate <= 0:
            old_rate = get_historical_usd_egp_rate(existing.entry_date)
        current_rate = get_parallel_usd_egp_rate()
        
        if curr == "USD":
            old_egp_cost = existing.shares * existing.entry_price * old_rate
            new_egp_cost = shares * price * current_rate
            total_egp_cost = old_egp_cost + new_egp_cost
            new_rate = total_egp_cost / (new_shares * new_avg_price) if new_shares * new_avg_price > 0 else current_rate
        else:
            old_usd_cost = (existing.shares * existing.entry_price) / old_rate if old_rate > 0 else 0
            new_usd_cost = (shares * price) / current_rate if current_rate > 0 else 0
            total_usd_cost = old_usd_cost + new_usd_cost
            new_rate = (new_shares * new_avg_price) / total_usd_cost if total_usd_cost > 0 else current_rate

        existing.entry_usd_rate = new_rate
        existing.shares = new_shares
        existing.entry_price = new_avg_price
        
        # ONLY overwrite SL/TP if explicitly requested during an average-down
        if sl is not None:
            existing.stop_loss = sl 
        if tp is not None:
            existing.target_price = tp
        if tp2 is not None:
            existing.target_price_2 = tp2
            
        existing.save()
        action = "updated"
    else:
        # New Position
        # Set default limits for NEW positions if missing
        if sl is None: sl = price * (1 - settings.SL_PCT/100)
        if tp is None: tp = price * (1 + settings.TP1_PCT/100)
        
        current_rate = get_parallel_usd_egp_rate()
        
        # Use PositionTracker but ensure it respects portfolio_id
        database.Position.create(
            portfolio=portfolio,
            ticker=ticker,
            shares=shares,
            entry_price=price,
            stop_loss=sl,
            target_price=tp,
            target_price_2=tp2,
            entries=1,
            current_price=price,
            status="OPEN",
            currency=curr,
            entry_usd_rate=current_rate,
            entry_date=date if date else _now(),
            signal_id=signal_id
        )
        action = "created"
            
    # 5. Update Cash
    if entry_type == "NEW":
        if curr == "EGP":
            portfolio.cash_egp -= cost
        else:
            portfolio.cash_usd -= cost
        portfolio.save()
        
    return {
        "status": "success",
        "action": action,
        "ticker": ticker,
        "cost": cost,
        "remaining_cash": portfolio.cash_egp if curr == "EGP" else portfolio.cash_usd
    }

def melt_gold(ticker, shares, price, portfolio_id=1, signal_id=None):
    """
    Executes a SELL order (Removes from Hoard).
    """
    ticker = str(ticker).upper()
    p = database.Position.get_or_none(ticker=ticker, status="OPEN", portfolio=portfolio_id)
    
    if not p:
        return {"status": "error", "message": "Position not found in this portfolio"}

    try:
        price_f = float(price)
    except Exception:
        return {"status": "error", "message": "Invalid price"}
    if price_f <= 0:
        return {"status": "error", "message": "Price must be > 0"}

    # If shares is omitted, default to full close.
    if shares is None:
        shares_i = int(p.shares)
    else:
        try:
            shares_i = int(round(float(shares)))
        except Exception:
            return {"status": "error", "message": "Invalid shares"}

    if shares_i <= 0:
        return {"status": "error", "message": "Shares must be > 0"}
    
    current_shares = p.shares if p.shares is not None else 0
    if shares_i > current_shares:
         return {"status": "error", "message": f"Not enough shares. Has: {current_shares}, Requested: {shares_i}"}

    proceeds = shares_i * price_f
    curr = p.currency
    
    # Get Portfolio to update cash
    portfolio = p.portfolio
    
    # Generate PnL values for this exact quantity
    pnl = proceeds - (shares_i * p.entry_price)
    
    # Fetch/calculate exchange rates
    entry_rate = p.entry_usd_rate
    if entry_rate is None or entry_rate <= 0:
        entry_rate = get_historical_usd_egp_rate(p.entry_date)
    exit_rate = get_parallel_usd_egp_rate()

    # Create the Trade Record (even for partial sells)
    resolved_signal_id = signal_id or getattr(p, "signal_id", None)
    database.Trade.create(
        portfolio=portfolio,
        ticker=ticker,
        shares=shares_i,
        entry_price=p.entry_price,
        exit_price=price_f,
        entry_date=p.entry_date,
        exit_date=_now(),
        pnl=pnl,
        pnl_pct=((price_f - p.entry_price) / p.entry_price) * 100,
        currency=curr,
        entry_usd_rate=entry_rate,
        exit_usd_rate=exit_rate,
        reason="PARTIAL_SELL_API" if shares_i < p.shares else "MANUAL_API",
        signal_id=resolved_signal_id
    )
    
    # If partial sell
    if shares_i < p.shares:
        # Just reduce quantity, keeping avg price same
        p.shares -= shares_i
        p.save()
        
        # Calculate proceeds from this partial sale
        # Update Cash
        if curr == "EGP":
            portfolio.cash_egp += proceeds
        else:
            portfolio.cash_usd += proceeds
            
        portfolio.save()
        
        return {
            "status": "success", 
            "ticker": ticker,
            "action": "partial_sell",
            "proceeds": proceeds,
            "pnl": pnl,
            "remaining_shares": p.shares
        }
    
    # FULL CLOSE
    # We will close the whole position for now.
    p.delete_instance()
    
    # Update Cash
    if curr == "EGP":
        portfolio.cash_egp += proceeds
    else:
        portfolio.cash_usd += proceeds
        
    portfolio.save()
    
    return {
        "status": "success", 
        "ticker": ticker,
        "proceeds": proceeds,
        "pnl": proceeds - (shares_i * p.entry_price)
    }

def take_snapshot(portfolio_id=1):
    """
    Records a snapshot of the portfolio's current net worth.
    """
    status = get_hoard_status(portfolio_id)
    if status['status'] == "error":
        return status
        
    try:
        if not database.PortfolioSnapshot.table_exists():
            database.db.create_tables([database.PortfolioSnapshot], safe=True)
        snapshot = database.PortfolioSnapshot.create(
            portfolio=portfolio_id,
            equity_egp=status['net_worth_egp'],
            equity_usd=status['net_worth_usd'],
            cash_egp=status['cash_egp'],
            cash_usd=status['cash_usd'],
            position_count=status['position_count']
        )
        return {"status": "success", "id": snapshot.id, "net_worth": status['net_worth_egp']}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_rebalancing_recommendations(portfolio_id=1, target_model="EQUAL_WEIGHT"):
    """
    Suggests trades to reach a target allocation based on the specified model:
    - EQUAL_WEIGHT: Equal target percentage across all holdings
    - RISK_PARITY: Weights inversely proportional to risk distance / ATR
    - KELLY_WEIGHTED: Weights based on conviction and reward-risk profiles
    """
    status = get_hoard_status(portfolio_id)
    if status.get('status') == "error":
        return []

    equity = float(status.get('net_worth_egp', 0.0))
    if equity <= 0:
        return []

    raw_positions = status.get('positions', [])
    if not raw_positions:
        return []

    rate = get_parallel_usd_egp_rate() or 50.0
    if rate <= 0:
        rate = 50.0

    # 1. Consolidate individual trade lots into unified unique ticker positions with currency awareness
    consolidated_map = {}
    for p in raw_positions:
        ticker = str(p.get('ticker') or '').upper().strip()
        if not ticker:
            continue

        currency = str(p.get('currency') or detect_currency(ticker)).upper()
        is_usd = (currency == "USD")

        shares = int(p.get('shares') or 0)
        curr_price_native = float(p.get('current_price') or p.get('entry_price') or 1.0)
        entry_price_native = float(p.get('entry_price') or curr_price_native)

        # Calculate market value in EGP and in native currency
        if is_usd:
            mval_usd = float(p.get('market_value_usd', shares * curr_price_native))
            mval_egp = float(p.get('market_value_egp', mval_usd * rate))
            price_egp = curr_price_native * rate
        else:
            mval_egp = float(p.get('market_value_egp', shares * curr_price_native))
            mval_usd = mval_egp / rate
            price_egp = curr_price_native

        sl = float(p.get('stop_loss') or (curr_price_native * 0.95))
        tp = float(p.get('target_price') or (curr_price_native * 1.10))

        if ticker not in consolidated_map:
            consolidated_map[ticker] = {
                "ticker": ticker,
                "currency": currency,
                "is_usd": is_usd,
                "shares": shares,
                "current_price": curr_price_native,
                "current_price_egp": price_egp,
                "total_cost_native": shares * entry_price_native,
                "market_value_native": mval_usd if is_usd else mval_egp,
                "market_value_egp": mval_egp,
                "market_value_usd": mval_usd,
                "stop_loss": sl,
                "target_price": tp,
            }
        else:
            c = consolidated_map[ticker]
            c["shares"] += shares
            c["total_cost_native"] += (shares * entry_price_native)
            c["market_value_native"] += (mval_usd if is_usd else mval_egp)
            c["market_value_egp"] += mval_egp
            c["market_value_usd"] += mval_usd
            c["current_price"] = curr_price_native
            c["current_price_egp"] = price_egp
            if sl > 0:
                c["stop_loss"] = min(c["stop_loss"], sl) if c["stop_loss"] > 0 else sl
            if tp > 0:
                c["target_price"] = max(c["target_price"], tp)

    positions = list(consolidated_map.values())
    count = len(positions)
    if count == 0:
        return []

    model_upper = str(target_model or "EQUAL_WEIGHT").upper()
    targets = {}

    if model_upper == "RISK_PARITY":
        # Compute inverse risk weights: risk_dist = (price - stop_loss) / price
        inv_risks = []
        for p in positions:
            price = float(p.get('current_price') or 1.0)
            sl = float(p.get('stop_loss') or (price * 0.95))
            risk_pct = max((price - sl) / price, 0.02)  # min 2% risk
            inv_risk = 1.0 / risk_pct
            inv_risks.append((p['ticker'], inv_risk))
        total_inv = sum(r for _, r in inv_risks) or 1.0
        for ticker, r in inv_risks:
            targets[ticker] = (r / total_inv) * 100.0

    elif model_upper in ["KELLY_WEIGHTED", "CONFLUENCE_WEIGHTED"]:
        # Base weights on upside reward-risk ratio modulated by Confluence Conviction
        from core.confluence import ConfluenceEngine
        from routes.shared import SECTOR_CACHE, WHALE_CACHE, TRAP_CACHE, ORACLE_CACHE
        
        sector_data = SECTOR_CACHE.get("data")
        whale_data = WHALE_CACHE.get("data")
        trap_data = TRAP_CACHE.get("data")
        oracle_data = ORACLE_CACHE.get("data")

        rr_weights = []
        for p in positions:
            price = float(p.get('current_price') or 1.0)
            sl = float(p.get('stop_loss') or (price * 0.95))
            tp = float(p.get('target_price') or (price * 1.10))
            risk = max(price - sl, 0.0001)
            reward = max(tp - price, 0.0001)
            rr = min(max(reward / risk, 0.5), 5.0)
            
            try:
                conf = ConfluenceEngine.evaluate_ticker(
                    ticker=p['ticker'],
                    sector_data=sector_data if isinstance(sector_data, dict) else None,
                    whale_data=whale_data if isinstance(whale_data, dict) else None,
                    trap_data=trap_data if isinstance(trap_data, dict) else None,
                    oracle_data=oracle_data if isinstance(oracle_data, dict) else None,
                )
                stars = conf.get("stars", 3)
                multiplier = 0.6 + (stars * 0.15)  # 1★ -> 0.75x, 3★ -> 1.05x, 5★ -> 1.35x
            except Exception:
                multiplier = 1.0
                
            rr_weights.append((p['ticker'], rr * multiplier))
        total_rr = sum(w for _, w in rr_weights) or 1.0
        for ticker, w in rr_weights:
            targets[ticker] = (w / total_rr) * 100.0

    else:  # EQUAL_WEIGHT default
        target_pct = 100.0 / count
        for p in positions:
            targets[p['ticker']] = target_pct

    recs = []
    for p in positions:
        ticker = p['ticker']
        currency = p['currency']
        is_usd = p['is_usd']
        curr_price_native = p['current_price']
        curr_price_egp = p['current_price_egp']
        curr_mval_egp = p['market_value_egp']
        curr_mval_native = p['market_value_native']

        current_pct = (curr_mval_egp / equity) * 100.0 if equity > 0 else 0.0
        target_pct = targets.get(ticker, 100.0 / count)
        drift = current_pct - target_pct
        target_val_egp = (target_pct / 100.0) * equity
        delta_val_egp = target_val_egp - curr_mval_egp
        delta_val_native = (delta_val_egp / rate) if is_usd else delta_val_egp

        action = "HOLD"
        shares_delta = 0
        if drift > 2.0:
            action = "TRIM"
            shares_delta = int(abs(delta_val_native) / curr_price_native) if curr_price_native > 0 else 0
        elif drift < -2.0:
            action = "ADD"
            shares_delta = int(abs(delta_val_native) / curr_price_native) if curr_price_native > 0 else 0

        target_shares = int(target_val_egp / curr_price_egp) if curr_price_egp > 0 else int(p.get('shares', 0))

        recs.append({
            "ticker": ticker,
            "currency": currency,
            "is_usd": is_usd,
            "action": action,
            "current_pct": round(current_pct, 2),
            "target_pct": round(target_pct, 2),
            "drift_pct": round(drift, 2),
            "current_shares": int(p.get('shares', 0)),
            "target_shares": target_shares,
            "shares_delta": shares_delta,
            "delta_value_native": round(delta_val_native, 2),
            "delta_value_egp": round(delta_val_egp, 2),
            "current_price": round(curr_price_native, 4 if is_usd else 2),
            "current_price_egp": round(curr_price_egp, 2),
            "usd_rate": round(rate, 2),
            "reason": f"{'Overweight' if drift > 0 else 'Underweight'} ({abs(drift):.1f}% drift from {model_upper} target)",
            "model": model_upper,
        })

    return recs

# === CLI ADAPTERS ===
def view_hoard_cli():
    # Trigger Genesis if no lock AND no positions AND no balances
    has_positions = database.Position.select().exists()
    has_balances = settings.ACCOUNT_BALANCE > 0 or settings.ACCOUNT_BALANCE_USD > 0
    
    if not os.path.exists("genesis.lock") and not has_positions and not has_balances:
        genesis_protocol()

    data = get_hoard_status()
    if data['status'] == "empty":
        return

    print(Fore.YELLOW + Style.BRIGHT + "\n💰 DRAUPNIR'S HOARD (LIVE PORTFOLIO)")
    print(Fore.YELLOW + "=" * 80)
    
    print(f"💵 EGP CASH: {Fore.WHITE}{data['cash_egp']:,.2f} | {Fore.CYAN}USD CASH: {data['cash_usd']:,.2f}")
    print(f"🏛️  EGP STOCK: {Fore.WHITE}{data['equity_egp']:,.2f} | {Fore.CYAN}USD STOCK: {data['equity_usd']:,.2f}")
    print(f"💎 NET EGP:   {Fore.YELLOW}{Style.BRIGHT}{data['net_worth_egp']:,.2f} | {Fore.YELLOW}NET USD: {data['net_worth_usd']:,.2f}")
    print("-" * 80)
    
    print(f"{'TICKER':<10} {'SHARES':<10} {'PRICE':<10} {'PnL':<15} {'RISK':<10}")
    print("-" * 80)
    for p in data['positions']:
        c = Fore.GREEN if p['pnl'] >= 0 else Fore.RED
        print(f"{p['ticker']:<10} {p['shares']:<10} {p['current_price']:<10.2f} {c}{p['pnl']:<15,.2f}{Fore.RESET} {p['risk_status']}")
    print("-" * 80)

if __name__ == "__main__":
    if "--reset" in sys.argv:
        confirm = input(Fore.RED + "CRITICAL: Wipe all portfolio data? (y/n): ").lower()
        if confirm == 'y':
            database.clear_portfolio_data()
            genesis_protocol()
        sys.exit()
        
    view_hoard_cli()
