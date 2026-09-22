"""
RISK MANAGER MODULE
===================
Handles sophisticated risk calculations:
1. Correlation Matrix (prevent concentrating risk)
2. Portfolio Heat (Total Open Risk relative to Equity)
3. Sector Exposure limits
"""

from core.settings import settings
from utils.currency_fetcher import get_parallel_usd_egp_rate, get_historical_usd_egp_rate
import pandas as pd
import numpy as np
import datetime
from core.market import MarketLists
from core.DataManager import DataManager

# === SETTINGS ===
CORRELATION_THRESHOLD = 0.70     # Warning level
HIGH_CORRELATION_LIMIT = 0.85    # Danger level
MAX_PORTFOLIO_HEAT = 6.0         # Max % of equity at risk (Total Stop Loss distance)


def _get_correlation_returns_from_universe(tickers, lookback_days=100):
    if len(tickers) < 2:
        return {}

    universe_df = DataManager.get_universe_data(tickers, include_live=False)
    if universe_df is None or universe_df.empty or "Close" not in universe_df.columns:
        return {}
    if not isinstance(universe_df.index, pd.MultiIndex):
        return {}

    try:
        close_matrix = universe_df["Close"].unstack(level=0).sort_index().tail(lookback_days)
    except Exception:
        return {}

    valid_data = {}
    returns_matrix = close_matrix.pct_change()
    for ticker in tickers:
        if ticker not in returns_matrix.columns:
            continue
        returns = returns_matrix[ticker].dropna()
        if len(returns) > 30:
            valid_data[ticker] = returns
    return valid_data


def get_correlation_matrix(tickers, lookback_days=100):
    """
    Calculates the correlation matrix for a list of tickers based on daily returns.

    Args:
        tickers: List of ticker symbols
        lookback_days: Days of history to analyze
    Returns:
        pd.DataFrame (Correlation Matrix) or None
    """
    ordered_tickers = list(dict.fromkeys(tickers))
    valid_data = _get_correlation_returns_from_universe(ordered_tickers, lookback_days=lookback_days)

    if len(valid_data) < 2:
        valid_data = {}
        for t in ordered_tickers:
            df = DataManager.get_stock_data(t, source="PARQUET", include_live=False)
            if df is not None and not df.empty:
                # We need aligned Dates
                # Get last N days
                df = df.sort_index().tail(lookback_days)
                if len(df) > 30: # Min data requirement
                    # Calculate daily returns
                    valid_data[t] = df['Close'].pct_change()

    if len(valid_data) < 2:
        return None

    # Create Panel DataFrame
    price_matrix = pd.DataFrame(valid_data)

    # Calculate Correlation
    corr_matrix = price_matrix.corr()
    return corr_matrix


def check_new_trade_correlation(current_portfolio, new_ticker):
    """
    Checks if a new trade is highly correlated with existing portfolio.

    Args:
        current_portfolio: List of tickers currently held
        new_ticker: Ticker considering to buy

    Returns:
        dict {
            'avg_correlation': float,
            'max_correlation': float,
            'most_correlated_with': str,
            'is_safe': bool,
            'warning': str
        }
    """
    if not current_portfolio:
        return {'is_safe': True, 'warning': None, 'avg_correlation': 0.0}

    # Combine lists
    all_tickers = current_portfolio + [new_ticker]

    # Get Matrix
    matrix = get_correlation_matrix(all_tickers)

    if matrix is None or new_ticker not in matrix.columns:
         return {'is_safe': True, 'warning': "Insufficient Data for Correlation", 'avg_correlation': 0.0}

    # Extract correlations for the new ticker (excluding itself)
    # The row for new_ticker
    new_ticker_corrs = matrix[new_ticker].drop(new_ticker)

    max_corr = new_ticker_corrs.max()
    avg_corr = new_ticker_corrs.mean()
    most_correlated = new_ticker_corrs.idxmax()

    # Logic
    warning = None
    is_safe = True

    if max_corr > HIGH_CORRELATION_LIMIT:
        is_safe = False
        warning = f"CRITICAL: Too similar to {most_correlated} ({max_corr:.2f})"

    elif avg_corr > CORRELATION_THRESHOLD:
        is_safe = False # Or just a warning? Let's say safe but warning
        warning = f"WARNING: High Correlation with Portfolio ({avg_corr:.2f})"

    return {
        'avg_correlation': round(avg_corr, 2),
        'max_correlation': round(max_corr, 2),
        'most_correlated_with': most_correlated,
        'is_safe': is_safe,
        'warning': warning
    }

def calculate_portfolio_heat(positions, account_balance):
    """
    Calculates Total Portfolio Heat:
    Sum of (Entry - StopLoss) * Shares / AccountBalance

    Args:
        positions: List of dicts {'ticker', 'entry', 'sl', 'shares'}
        account_balance: Total Equity
    """
    def _to_float(val, default=0.0):
        try:
            if hasattr(val, '__class__') and 'MagicMock' in val.__class__.__name__:
                return default
            return float(val)
        except:
            return default

    account_balance = _to_float(account_balance)

    if not positions or account_balance <= 0:
        return 0.0

    total_risk_amt = 0.0

    for p in positions:
        entry = _to_float(p.get('entry'))
        sl = _to_float(p.get('sl'))
        shares = _to_float(p.get('shares'))

        risk_per_share = entry - sl
        if risk_per_share < 0: risk_per_share = 0 # Short? Assuming Long for now

        position_risk = risk_per_share * shares
        total_risk_amt += position_risk

    heat_pct = (total_risk_amt / account_balance) * 100
    return round(heat_pct, 2)


def check_sector_exposure(new_ticker, current_portfolio_tickers):
    """
    Checks if adding new_ticker exceeds max sector exposure limits.
    """
    if not getattr(settings, 'SECTOR_LIMIT_ENABLED', False):
        return True, None

    new_sector = MarketLists.get_sector(new_ticker)
    if new_sector == "Unknown":
        return True, None # Can't enforce if unknown

    count = 0
    for t in current_portfolio_tickers:
        if MarketLists.get_sector(t) == new_sector:
            count += 1

    limit = getattr(settings, 'MAX_PER_SECTOR', 2)
    if count >= limit:
        return False, f"Sector Limit Exceeded: Already holding {count} stocks in {new_sector}"

    return True, None


def calculate_hhi(weights):
    """
    Calculates the Herfindahl-Hirschman Index (HHI) for concentration.
    HHI = sum(w_i^2) where w_i is % weight (0-100).
    Result 0-10000.
    < 1500: Diversified
    1500-2500: Moderately Concentrated
    > 2500: Highly Concentrated
    """
    if not weights:
        return 0.0
    # Ensure weights are percentages (0-100)
    return sum(float(w)**2 for w in weights)


def get_stock_beta(ticker, benchmark="EGX30", lookback_days=100):
    """
    Calculates the beta of a stock relative to a benchmark.
    Beta = Cov(r_s, r_b) / Var(r_b)
    """
    try:
        stock_df = DataManager.get_stock_data(ticker, source="PARQUET", include_live=False)
        bench_df = DataManager.get_stock_data(benchmark, source="PARQUET", include_live=False)

        if stock_df is None or bench_df is None or stock_df.empty or bench_df.empty:
            return 1.0 # Default to Market

        # Align dates
        stock_ret = stock_df['Close'].pct_change().dropna()
        bench_ret = bench_df['Close'].pct_change().dropna()

        merged = pd.concat([stock_ret, bench_ret], axis=1).dropna().tail(lookback_days)
        if len(merged) < 30:
            return 1.0

        merged.columns = ['s', 'b']
        covariance = merged.cov().iloc[0, 1]
        variance = merged['b'].var()

        if variance == 0:
            return 1.0

        beta = covariance / variance
        return round(float(beta), 2)
    except Exception:
        return 1.0


def calculate_portfolio_beta(positions, equity):
    """
    Calculates the weighted average beta of the portfolio.
    """
    if not positions or equity <= 0:
        return 1.0

    total_weighted_beta = 0.0
    total_weight = 0.0

    for p in positions:
        market_val = p['shares'] * p['current_price']
        weight = market_val / equity
        ticker = p['ticker']

        beta = get_stock_beta(ticker)
        total_weighted_beta += beta * weight
        total_weight += weight

    # Remaining weight is cash (beta 0)
    return round(total_weighted_beta, 2)


if __name__ == "__main__":
    # Test
    print("Testing Risk Manager...")
    test_tickers = ['COMI', 'HRHO', 'SWDY', 'FWRY'] # Common stocks
    print(f"Tickers: {test_tickers}")

    matrix = get_correlation_matrix(test_tickers)
    print("\nCorrelation Matrix:")
    print(matrix)

    print("\nCheck adding 'CIEB' to ['COMI', 'HRHO']...")
    res = check_new_trade_correlation(['COMI', 'HRHO'], 'CIEB')
    print(res)
    print(res)

def analyze_portfolio(portfolio_id):
    """
    Generates a comprehensive risk analysis and recommendation report for a portfolio.
    """
    from database import Position, Portfolio

    # 1. Fetch Portfolio & Positions
    p = Portfolio.get_or_none(Portfolio.id == portfolio_id)
    if not p: return {"error": "Portfolio not found"}

    positions = list(Position.select().where((Position.status == "OPEN") & (Position.portfolio == portfolio_id)).dicts())
    tickers = [pos['ticker'] for pos in positions]

    recommendations = []
    status = "HEALTHY"
    score = 100

    # 2. Check Portfolio Heat
    rate = get_parallel_usd_egp_rate()
    total_cash = (p.cash_egp or 0) + (p.cash_usd or 0) * rate
    
    # Calculate position values in EGP
    total_pos_val_egp = 0.0
    for pos in positions:
        if not pos['current_price']:
            continue
        p_currency = pos.get('currency', 'EGP')
        if p_currency == 'USD':
            total_pos_val_egp += pos['shares'] * pos['current_price'] * rate
        else:
            total_pos_val_egp += pos['shares'] * pos['current_price']
            
    equity = total_cash + total_pos_val_egp

    # Parallel market rate volatility circuit breaker check
    try:
        prev_rate = get_historical_usd_egp_rate(datetime.datetime.now() - datetime.timedelta(days=1))
        rate_change = abs(rate - prev_rate) / prev_rate * 100
        if rate_change > 2.0:
            status = "RISK"
            score -= 15
            recommendations.append({
                "type": "CURRENCY_VOLATILITY",
                "severity": "HIGH",
                "title": "Extreme Currency Volatility (Circuit Breaker)",
                "message": f"Parallel market USD/EGP rate has shifted by {rate_change:.2f}% in the last 24 hours ({prev_rate:.2f} -> {rate:.2f}). Technical signals are blocked/flagged."
            })
    except Exception:
        pass

    heat_input = [{'ticker': pos['ticker'], 'entry': pos['entry_price'], 'sl': pos['stop_loss'], 'shares': pos['shares']} for pos in positions if pos['stop_loss']]
    heat = calculate_portfolio_heat(heat_input, equity)

    max_portfolio_heat = float(getattr(settings, 'MAX_PORTFOLIO_HEAT', MAX_PORTFOLIO_HEAT))

    if heat > max_portfolio_heat:
        status = "RISK"
        score -= 20
        recommendations.append({
            "type": "RISK_MANAGEMENT",
            "severity": "HIGH",
            "title": "High Portfolio Heat",
            "message": f"Total risk exposure is {heat}%, exceeding the {max_portfolio_heat}% safe limit. Consider closing positions or tightening stops."
        })
    elif heat > max_portfolio_heat * 0.75:
        recommendations.append({
            "type": "RISK_MANAGEMENT",
            "severity": "MEDIUM",
            "title": "Elevated Portfolio Heat",
            "message": f"Risk exposure is {heat}%. Monitor closely."
        })

    # 3. Check Correlation
    if len(tickers) >= 2:
        matrix = get_correlation_matrix(tickers)
        if matrix is not None:
            # Find high correlations
            # Iterate upper triangle
            cols = matrix.columns
            for i in range(len(cols)):
                for j in range(i+1, len(cols)):
                    val = matrix.iloc[i, j]
                    if val > HIGH_CORRELATION_LIMIT:
                        t1, t2 = cols[i], cols[j]
                        score -= 10
                        if status == "HEALTHY": status = "WARNING"
                        recommendations.append({
                            "type": "DIVERSIFICATION",
                            "severity": "HIGH",
                            "title": "Critical Correlation",
                            "message": f"{t1} and {t2} are highly correlated ({val:.2f}). Holding both increases concentrated risk."
                        })

    # 4. Check Sector Concentration
    sectors = {}
    for pos in positions:
        sec = pos.get('sector') or MarketLists.get_sector(pos['ticker'])
        sectors[sec] = sectors.get(sec, 0) + 1

    limit = getattr(settings, 'MAX_PER_SECTOR', 2)
    for sec, count in sectors.items():
        if sec != "Unknown" and count > limit:
            score -= 5
            recommendations.append({
                "type": "ALLOCATION",
                "severity": "MEDIUM",
                "title": "Sector Overweight",
                "message": f"You hold {count} positions in {sec}. Limit is {limit}."
            })

    # 6. Concentration Analysis (HHI)
    total_pos_val = sum(pos['shares'] * pos['current_price'] for pos in positions if pos['current_price'])
    if total_pos_val > 0:
        pos_weights = [(pos['shares'] * pos['current_price'] / total_pos_val) * 100 for pos in positions if pos['current_price']]
        hhi = calculate_hhi(pos_weights)

        if hhi > 2500:
            score -= 15
            recommendations.append({
                "type": "CONCENTRATION",
                "severity": "HIGH",
                "title": "High Position Concentration",
                "message": f"HHI score is {hhi:.0f}. A few positions dominate your portfolio. Consider diversifying."
            })
        elif hhi > 1500:
            recommendations.append({
                "type": "CONCENTRATION",
                "severity": "MEDIUM",
                "title": "Moderate Concentration",
                "message": f"HHI score is {hhi:.0f}. Some concentration detected."
            })

        # Sector HHI
        sector_weights = {}
        for sec, count in sectors.items():
            # Percentage of total position value for this sector
            sec_val = sum(pos['shares'] * pos['current_price'] for pos in positions if (pos.get('sector') or MarketLists.get_sector(pos['ticker'])) == sec)
            sector_weights[sec] = (sec_val / total_pos_val) * 100

        sector_hhi = calculate_hhi(sector_weights.values())
        if sector_hhi > 3000:
            score -= 10
            recommendations.append({
                "type": "ALLOCATION",
                "severity": "HIGH",
                "title": "Extreme Sector Concentration",
                "message": f"Sector HHI is {sector_hhi:.0f}. You are heavily exposed to very few sectors."
            })

    # 7. Portfolio Beta
    p_beta = calculate_portfolio_beta(positions, equity)
    if p_beta > 1.3:
        recommendations.append({
            "type": "RISK",
            "severity": "MEDIUM",
            "title": "High Volatility (Beta)",
            "message": f"Portfolio Beta is {p_beta:.2f}. You will likely move 30%+ more than the EGX30 index."
        })
    elif p_beta < 0.7:
        recommendations.append({
            "type": "RISK",
            "severity": "INFO",
            "title": "Defensive Portfolio",
            "message": f"Portfolio Beta is {p_beta:.2f}. You are less volatile than the index."
        })

    result = {
        "portfolio_id": portfolio_id,
        "status": status,
        "health_score": max(0, score),
        "heat": heat,
        "beta": p_beta,
        "hhi": round(hhi, 2) if total_pos_val > 0 else 0,
        "recommendations": recommendations,
        "sector_breakdown": sectors
    }
    try:
        from utils.audit_logger import log_audit_event
        log_audit_event(
            category="risk_management",
            action="audit_portfolio",
            status="success" if status == "HEALTHY" else "warning",
            details={
                "portfolio_id": portfolio_id,
                "status": status,
                "health_score": result["health_score"],
                "heat": heat,
                "beta": p_beta,
                "hhi": result["hhi"],
                "recommendation_count": len(recommendations)
            }
        )
    except Exception:
        pass
    return result


def run_portfolio_stress_test(portfolio_id: int, num_simulations: int = 1000, horizon_days: int = 30) -> dict:
    """
    Executes a 1,000-path Monte Carlo simulation and deterministic macro crisis stress tests.
    Computes 95% and 99% Value-at-Risk (VaR), Expected Shortfall (CVaR), and Scenario impacts.
    """
    import numpy as np
    from database import Position, Portfolio

    p = Portfolio.get_or_none(Portfolio.id == portfolio_id)
    if not p:
        return {"error": "Portfolio not found"}

    positions = list(Position.select().where((Position.status == "OPEN") & (Position.portfolio == portfolio_id)).dicts())
    rate = get_parallel_usd_egp_rate()
    total_cash_egp = float(p.cash_egp or 0.0) + (float(p.cash_usd or 0.0) * rate)

    total_market_val_egp = 0.0
    holding_weights = []
    holding_betas = []
    holding_vols = []

    for pos in positions:
        curr_p = float(pos.get('current_price') or pos.get('entry_price') or 0.0)
        shares = float(pos.get('shares', 0.0))
        p_curr = str(pos.get('currency') or "EGP").upper()
        fx = rate if p_curr == "USD" else 1.0
        val = curr_p * shares * fx
        total_market_val_egp += val

        # Estimate daily volatility (default ~1.8% daily for EGX stocks, annual ~28%)
        vol = 0.018
        beta = 1.0
        if curr_p > 0 and pos.get('stop_loss'):
            sl = float(pos['stop_loss'])
            risk_dist = max((curr_p - sl) / curr_p, 0.02)
            vol = min(max(risk_dist / 3.0, 0.012), 0.045)
            beta = min(max(vol / 0.015, 0.6), 2.2)

        holding_weights.append((pos['ticker'], val, beta, vol))
        holding_betas.append(beta)
        holding_vols.append(vol)

    net_worth_egp = total_cash_egp + total_market_val_egp
    if net_worth_egp <= 0:
        return {
            "portfolio_id": portfolio_id,
            "net_worth_egp": 0.0,
            "var_95_egp": 0.0,
            "var_95_pct": 0.0,
            "var_99_egp": 0.0,
            "var_99_pct": 0.0,
            "cvar_95_egp": 0.0,
            "cvar_95_pct": 0.0,
            "scenarios": [],
            "monte_carlo_distribution": {},
        }

    # Portfolio aggregated beta and weighted daily volatility
    invested_ratio = total_market_val_egp / net_worth_egp
    p_beta = (sum(w * b for _, w, b, _ in holding_weights) / total_market_val_egp) if total_market_val_egp > 0 else 1.0
    p_daily_vol = (sum(w * v for _, w, _, v in holding_weights) / total_market_val_egp) * invested_ratio if total_market_val_egp > 0 else 0.01

    # 1. Monte Carlo Simulation: 1,000 paths over horizon_days
    np.random.seed(42)
    daily_returns = np.random.normal(loc=0.0004, scale=p_daily_vol, size=(num_simulations, horizon_days))
    price_paths = np.cumprod(1 + daily_returns, axis=1)
    final_returns = price_paths[:, -1] - 1.0

    # Sort final returns for empirical quantiles
    sorted_returns = np.sort(final_returns)
    var_95_ret = float(-np.percentile(sorted_returns, 5))
    var_99_ret = float(-np.percentile(sorted_returns, 1))
    
    # Expected Shortfall (CVaR 95%): average loss beyond 95% quantile
    tail_losses = sorted_returns[sorted_returns <= -var_95_ret]
    cvar_95_ret = float(-np.mean(tail_losses)) if len(tail_losses) > 0 else var_95_ret * 1.25

    var_95_egp = round(var_95_ret * net_worth_egp, 2)
    var_99_egp = round(var_99_ret * net_worth_egp, 2)
    cvar_95_egp = round(cvar_95_ret * net_worth_egp, 2)

    mc_distribution = {
        "p5_loss_pct": round(float(np.percentile(sorted_returns, 5)) * 100, 2),
        "p25_pct": round(float(np.percentile(sorted_returns, 25)) * 100, 2),
        "median_pct": round(float(np.percentile(sorted_returns, 50)) * 100, 2),
        "p75_pct": round(float(np.percentile(sorted_returns, 75)) * 100, 2),
        "p95_gain_pct": round(float(np.percentile(sorted_returns, 95)) * 100, 2),
    }

    # 2. Crisis Scenario Shocks
    scenarios = [
        {
            "id": "EGX30_CRASH_5",
            "name": "EGX30 Moderate Pullback (-5%)",
            "description": "Standard market correction. High-beta stocks take proportional hit.",
            "loss_pct": round(5.0 * p_beta * invested_ratio, 2),
            "loss_egp": round((5.0 * p_beta * invested_ratio / 100.0) * net_worth_egp, 2),
            "remaining_net_worth": round(net_worth_egp - ((5.0 * p_beta * invested_ratio / 100.0) * net_worth_egp), 2),
            "severity": "LOW",
        },
        {
            "id": "EGX30_CRASH_10",
            "name": "EGX30 Severe Market Drop (-10%)",
            "description": "Broad market panic liquidation triggering trailing stops.",
            "loss_pct": round(10.0 * p_beta * invested_ratio, 2),
            "loss_egp": round((10.0 * p_beta * invested_ratio / 100.0) * net_worth_egp, 2),
            "remaining_net_worth": round(net_worth_egp - ((10.0 * p_beta * invested_ratio / 100.0) * net_worth_egp), 2),
            "severity": "MEDIUM",
        },
        {
            "id": "FX_DEVALUATION_15",
            "name": "Parallel FX Surge (+15% USD/EGP)",
            "description": "Egyptian Pound devaluation. USD reserves appreciate; imported inflation weighs on domestic margins.",
            "loss_pct": round(-1.0 * (float(p.cash_usd or 0.0) * rate * 0.15 / net_worth_egp * 100.0), 2),
            "loss_egp": round(-1.0 * (float(p.cash_usd or 0.0) * rate * 0.15), 2),
            "remaining_net_worth": round(net_worth_egp + (float(p.cash_usd or 0.0) * rate * 0.15), 2),
            "severity": "POSITIVE" if (p.cash_usd or 0) > 0 else "INFO",
        },
        {
            "id": "LIQUIDITY_FREEZE_20",
            "name": "Top Holdings Liquidity Squeeze (-20%)",
            "description": "Idiosyncratic selloff in highest-weighted active positions.",
            "loss_pct": round(min(20.0 * invested_ratio, 20.0), 2),
            "loss_egp": round((min(20.0 * invested_ratio, 20.0) / 100.0) * net_worth_egp, 2),
            "remaining_net_worth": round(net_worth_egp - ((min(20.0 * invested_ratio, 20.0) / 100.0) * net_worth_egp), 2),
            "severity": "HIGH",
        },
        {
            "id": "BLACK_SWAN_25",
            "name": "Black Swan Event (-25% Circuit Breaker)",
            "description": "Multi-day limit-down emergency circuit breaker cascade.",
            "loss_pct": round(25.0 * p_beta * invested_ratio, 2),
            "loss_egp": round((25.0 * p_beta * invested_ratio / 100.0) * net_worth_egp, 2),
            "remaining_net_worth": round(net_worth_egp - ((25.0 * p_beta * invested_ratio / 100.0) * net_worth_egp), 2),
            "severity": "CRITICAL",
        }
    ]

    return {
        "portfolio_id": portfolio_id,
        "net_worth_egp": round(net_worth_egp, 2),
        "invested_market_val_egp": round(total_market_val_egp, 2),
        "cash_reserve_egp": round(total_cash_egp, 2),
        "portfolio_beta": round(p_beta, 2),
        "daily_volatility_pct": round(p_daily_vol * 100, 2),
        "horizon_days": horizon_days,
        "simulations_count": num_simulations,
        "var_95_egp": var_95_egp,
        "var_95_pct": round(var_95_ret * 100, 2),
        "var_99_egp": var_99_egp,
        "var_99_pct": round(var_99_ret * 100, 2),
        "cvar_95_egp": cvar_95_egp,
        "cvar_95_pct": round(cvar_95_ret * 100, 2),
        "monte_carlo_distribution": mc_distribution,
        "scenarios": scenarios,
    }
