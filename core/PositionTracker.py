"""
POSITION TRACKER MODULE
=======================
Manages open positions and trade history using SQLite database.
Replaces legacy JSON implementation.
"""

from collections import defaultdict
import datetime
import json
from core import TimeUtils
from colorama import Fore, Style, init
from peewee import fn
import database
from database import Portfolio, Position, Trade, HorusExecution, db
from core.exclusions import is_excluded_ticker, normalize_ticker

init(autoreset=True)

def update_live_prices():
    """
    Fetch latest cached prices and update changed rows only.

    This path is used by portfolio read endpoints, so it must stay read-only
    with respect to market-data refreshes and avoid redundant database writes.
    """
    from core.DataManager import DataManager
    
    try:
        # Fetch as list to release read-lock immediately
        query = list(Position.select().where(Position.status == "OPEN"))
        count = 0
        for p in query:
            last_price = None

            # Request-path refreshes should use whatever the data layer already
            # has cached instead of triggering a fresh ingest synchronously.
            intra_df = DataManager.get_intraday_data(
                p.ticker,
                limit=1,
                refresh_if_stale=False,
            )
            if intra_df is not None and not intra_df.empty:
                last_price = float(intra_df.iloc[-1]['Close'])
            else:
                # Keep the fallback read-only too; include_live would recurse
                # into intraday reads that may attempt a refresh.
                df = DataManager.get_stock_data(p.ticker, include_live=False)
                if df is not None and not df.empty:
                    last_price = float(df.iloc[-1]['Close'])

            if last_price is not None:
                current_price = float(p.current_price) if p.current_price is not None else None
                if current_price is not None and abs(current_price - last_price) <= 1e-9:
                    continue
                p.current_price = last_price
                p.save()
                count += 1
        return count
    except Exception as e:
        import traceback
        print(f"Error updating live prices: {e}")
        # traceback.print_exc() 
        return 0


def load_positions(portfolio_id=None):
    """
    Returns a dictionary of open positions compatible with legacy format.
    Args:
        portfolio_id (int, optional): Filter by portfolio. If None, returns all.
    """
    positions = {}
    try:
        query = Position.select().where(Position.status == "OPEN")
        if portfolio_id:
            query = query.where(Position.portfolio == portfolio_id)
            
        for p in query:
            # Key is now unique per portfolio, but for legacy support keeping simple
            # If multiple portfolios span same ticker, this legacy function might overwrite.
            # But new UI will call APIs that handle this better.
            positions[p.ticker] = {
                "id": p.id,
                "portfolio_id": p.portfolio.id if p.portfolio else None,
                "shares": p.shares,
                "entry_price": p.entry_price,
                "date": p.entry_date.strftime("%Y-%m-%d"),
                "stop_loss": p.stop_loss,
                "target1": p.target_price,
                "target2": p.target_price_2,
                "tp1_hit": p.tp1_hit,
                "status": p.status,
                "sector": p.sector
            }
    except Exception as e:
        print(f"DB Error loading positions: {e}")
        
    return positions

def _cash_field_for_currency(currency):
    return "cash_usd" if str(currency or "").upper() == "USD" else "cash_egp"


def add_position(ticker, shares, entry_price, sl=None, tp=None, tp2=None, sector=None, portfolio_id=1, currency="EGP", date=None, slippage_bps=None, latency_ms=None, signal_id=None):
    """Opens a new position in the database."""
    ticker = normalize_ticker(ticker)
    if not ticker:
        print(f"{Fore.RED}Ticker is required.")
        return False
    if is_excluded_ticker(ticker):
        print(f"{Fore.YELLOW}Blocked blacklisted ticker: {ticker}")
        return False
    
    # Check if exists in THAT portfolio
    if Position.select().where((Position.ticker == ticker) & (Position.status == "OPEN") & (Position.portfolio == portfolio_id)).exists():
        print(f"{Fore.YELLOW}Position for {ticker} already open in Portfolio {portfolio_id}. Skipping.")
        return False

    try:
        entry_date_val = TimeUtils.now()
        if date:
            try:
                # Expecting strings like "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS"
                if isinstance(date, str):
                    if len(date) == 10:
                        entry_date_val = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                    else:
                        entry_date_val = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                # If it's already a date object, use it (though specific to implementation)
                elif isinstance(date, (datetime.date, datetime.datetime)):
                     entry_date_val = date
            except Exception as e:
                print(f"Date parse error: {e}. Using NOW.")

        shares_i = int(round(float(shares)))
        entry_price_f = float(entry_price)
        if shares_i <= 0 or entry_price_f <= 0:
            print(f"{Fore.RED}Shares and entry price must be positive.")
            return False

        portfolio = Portfolio.get_or_none(Portfolio.id == portfolio_id) if portfolio_id else None
        cost = shares_i * entry_price_f
        cash_field = _cash_field_for_currency(currency)
        current_cash = float(getattr(portfolio, cash_field, 0.0) or 0.0) if portfolio else 0.0

        if portfolio and current_cash > 0:
            if cost > current_cash:
                print(f"{Fore.RED}Insufficient {currency} Cash in Portfolio {portfolio_id}. Needed: {cost:.2f}, Has: {current_cash:.2f}")
                return False

        with db.atomic():
            Position.create(
                portfolio=portfolio_id,
                ticker=ticker,
                shares=shares_i,
                entry_price=entry_price_f,
                stop_loss=sl or (entry_price_f * 0.985),
                target_price=tp or (entry_price_f * 1.04),
                target_price_2=tp2,
                tp1_hit=False,
                entry_date=entry_date_val,
                status="OPEN",
                sector=sector,
                currency=currency,
                slippage_bps=slippage_bps,
                execution_latency_ms=latency_ms,
                signal_id=signal_id
            )
            if portfolio and current_cash > 0:
                setattr(portfolio, cash_field, current_cash - cost)
                portfolio.save()
        print(f"{Fore.GREEN}Added {ticker}: {shares} shares @ {entry_price} (Port: {portfolio_id})")
        return True
    except Exception as e:
        print(f"{Fore.RED}Error adding position: {e}")
        return False

def close_position(ticker, exit_price, reason="MANUAL", portfolio_id=None, slippage_bps=None, latency_ms=None, partial_shares=None, signal_id=None):
    """Closes a position (or partially closes it) and logs the trade."""
    ticker = ticker.upper()
    
    try:
        query = (Position.ticker == ticker) & (Position.status == "OPEN")
        if portfolio_id:
            query &= (Position.portfolio == portfolio_id)
            
        p = Position.get_or_none(query)
        if not p:
            print(f"{Fore.RED}Ticker {ticker} not found/open in Portfolio {portfolio_id if portfolio_id else 'Any'}.")
            return False

        # Safety: only block automated exits for USER portfolios that are auto-managed
        try:
            if (
                p.portfolio
                and p.portfolio.type == "USER"
                and getattr(p.portfolio, "auto_manage", False)
                and reason in ("STOP_LOSS", "TARGET")
            ):
                print(f"{Fore.YELLOW}Blocked auto-close for USER portfolio {p.portfolio.id} ({ticker}, reason={reason}).")
                return False
        except Exception:
            pass
        
        # Calculate PnL
        original_shares = int(p.shares or 0)
        shares_to_close = partial_shares if partial_shares is not None else original_shares
        if shares_to_close > original_shares:
            shares_to_close = original_shares
            
        pnl = (exit_price - p.entry_price) * shares_to_close
        pnl_pct = ((exit_price - p.entry_price) / p.entry_price) * 100
        proceeds = exit_price * shares_to_close
        
        # Inherit signal_id from position if not explicitly passed
        resolved_signal_id = signal_id or getattr(p, "signal_id", None)

        # Atomic Transaction
        with db.atomic():
            # Create Trade Log
            trade = Trade.create(
                portfolio=p.portfolio,
                ticker=ticker,
                shares=shares_to_close,
                entry_price=p.entry_price,
                exit_price=exit_price,
                entry_date=p.entry_date,
                exit_date=TimeUtils.now(),
                pnl=pnl,
                pnl_pct=pnl_pct,
                reason=reason,
                currency=p.currency,
                slippage_bps=slippage_bps or p.slippage_bps,
                execution_latency_ms=latency_ms or p.execution_latency_ms,
                signal_id=resolved_signal_id
            )
            
            # Partial or Full Closure
            is_partial = bool(partial_shares and partial_shares < original_shares)
            if is_partial:
                p.shares -= partial_shares
                if str(reason or "").upper() in ("TARGET 1", "TARGET_1", "TP1", "TP1_HIT"):
                    p.tp1_hit = True
                    p.stop_loss = p.entry_price
                p.save()
            else:
                p.delete_instance()

            execution = (
                HorusExecution.select()
                .where(
                    (HorusExecution.portfolio == p.portfolio) &
                    (HorusExecution.ticker == ticker) &
                    (HorusExecution.state.in_(["OPEN", "UPDATED"]))
                )
                .order_by(HorusExecution.updated_at.desc(), HorusExecution.id.desc())
                .first()
            )
            if execution:
                details = {}
                try:
                    details = json.loads(execution.details_json or "{}")
                    if not isinstance(details, dict):
                        details = {}
                except Exception:
                    details = {}

                details["exit_price"] = float(exit_price)
                details["realized_pnl"] = float(pnl)
                details["realized_pnl_pct"] = float(pnl_pct)
                details["last_close_reason"] = str(reason or "")
                details["last_close_at"] = TimeUtils.now().isoformat()
                if is_partial and str(reason or "").upper() in ("TARGET 1", "TARGET_1", "TP1", "TP1_HIT"):
                    details["tp1_hit"] = True
                    execution.active_stop_loss = p.entry_price

                execution.details_json = json.dumps(details)
                execution.trade_id = trade.id if trade else execution.trade_id
                execution.close_reason = reason if not is_partial else execution.close_reason
                execution.state = "UPDATED" if is_partial else "CLOSED"
                execution.updated_at = TimeUtils.now()
                execution.save()

            if p.portfolio:
                cash_field = _cash_field_for_currency(p.currency)
                current_cash = float(getattr(p.portfolio, cash_field, 0.0) or 0.0)
                setattr(p.portfolio, cash_field, current_cash + proceeds)
                p.portfolio.save()
            
        p_port_id = p.portfolio.id if p.portfolio else None
        p_port_type = p.portfolio.type if p.portfolio else "UNKNOWN"
        print(f"{Fore.YELLOW}{'Partially ' if partial_shares else ''}Closed {ticker} at {exit_price} ({pnl:.2f} PnL) | port={p_port_id} type={p_port_type} reason={reason}")
        return True
        
    except Exception as e:
        print(f"{Fore.RED}Error closing position: {e}")
        return False

def update_position(ticker, shares=None, entry_price=None, sl=None, tp=None, tp2=None, tp1_hit=None, portfolio_id=None):
    """Update an existing position."""
    ticker = ticker.upper()
    try:
        query = (Position.ticker == ticker) & (Position.status == "OPEN")
        if portfolio_id:
            query &= (Position.portfolio == portfolio_id)
            
        p = Position.get_or_none(query)
        if p:
            if shares is not None: p.shares = shares
            if entry_price is not None: p.entry_price = entry_price
            if sl is not None: p.stop_loss = sl
            if tp is not None: p.target_price = tp
            if tp2 is not None: p.target_price_2 = tp2
            if tp1_hit is not None: p.tp1_hit = tp1_hit
            p.save()
            print(f"{Fore.GREEN}Updated {ticker}")
            return True
        else:
            print(f"{Fore.RED}Ticker {ticker} not found.")
            return False
    except Exception as e:
        print(f"{Fore.RED}Error updating: {e}")
        return False

def list_positions():
    """Print positions table."""
    positions = load_positions()
    if not positions:
        print(f"{Fore.CYAN}No open positions.")
        return

    print(f"\n{Style.BRIGHT}{'TICKER':<10} {'SHARES':<10} {'ENTRY':<10} {'SL':<10} {'TP1':<10} {'DATE'}")
    print("-" * 65)
    for t, p in positions.items():
        print(f"{Fore.WHITE}{t:<10} {p['shares']:<10} {p['entry_price']:<10.2f} {Fore.RED}{p['stop_loss']:<10.2f} {Fore.GREEN}{p['target1']:<10.2f} {Style.DIM}{p['date']}")

if __name__ == "__main__":
    import sys
    # Initialize DB ensures tables exist
    database.initialize_db()
    
    if len(sys.argv) < 2:
        list_positions()
    else:
        cmd = sys.argv[1].lower()
        if cmd == "add" and len(sys.argv) >= 4:
            # add TICKER SHARES ENTRY [SL] [TP]
            sl = float(sys.argv[5]) if len(sys.argv) >= 6 else None
            tp = float(sys.argv[6]) if len(sys.argv) >= 7 else None
            add_position(sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sl, tp)
        elif cmd == "close" and len(sys.argv) >= 4:
            # close TICKER PRICE [REASON]
            reason = sys.argv[4] if len(sys.argv) >= 5 else "MANUAL"
            close_position(sys.argv[2], float(sys.argv[3]), reason)
        elif cmd == "list":
            list_positions()
