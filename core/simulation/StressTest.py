from __future__ import annotations
"""
STRESS TEST SIMULATOR (RAGNAROK MODULE)
=======================================
Identifies the worst market crash dates and simulates
their effect on market prices.
"""


from datetime import date, datetime, timedelta
import sys

import pandas as pd

from core.market import MarketLists
from core import DataManager

# Configuration defaults
LOOKBACK_DAYS = 365
SIMULATION_DAYS = 5
FINANCIAL_SECTORS = ["Banks", "Non-bank Financial Services", "Basic Resources"]


def _resolve_symbol(name: str, fallback: any) -> any:
    mod = sys.modules.get("StressTest")
    if mod and hasattr(mod, name):
        return getattr(mod, name)
    mod2 = sys.modules.get("core.simulation.StressTest")
    if mod2 and hasattr(mod2, name):
        return getattr(mod2, name)
    return fallback


def get_sector_tickers(sector_list):
    """Filter tickers by sector list."""
    data_mgr = _resolve_symbol("DataManager", DataManager)
    mkt_lists = _resolve_symbol("MarketLists", MarketLists)
    all_tickers = data_mgr.DataManager.list_tickers()
    valid_tickers = []
    for ticker in all_tickers:
        sector = mkt_lists.get_sector(ticker)
        if sector in sector_list:
            valid_tickers.append(ticker)
    return valid_tickers


def _coerce_ref_date(value: str | date | datetime | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def _coerce_positive_int(value: int | None, default: int) -> int:
    try:
        coerced = int(value) if value is not None else default
    except Exception:
        return default
    return coerced if coerced > 0 else default


def find_worst_day(
    tickers,
    name: str = "Index",
    ref_date: date | None = None,
    lookback_days: int = LOOKBACK_DAYS,
):
    """Find the single worst trading day for a list of tickers."""
    data_mgr = _resolve_symbol("DataManager", DataManager)
    returns_dict = {}
    normalized_ref_date = _coerce_ref_date(ref_date)
    effective_lookback_days = _coerce_positive_int(lookback_days, LOOKBACK_DAYS)

    start_date = None
    end_date = None
    if normalized_ref_date is not None:
        end_date = normalized_ref_date
        start_date = end_date - timedelta(days=effective_lookback_days)

    for ticker in tickers:
        df = data_mgr.DataManager.get_stock_data(ticker, include_live=False)
        if df is not None and not df.empty and "Change" in df.columns:
            change_series = pd.to_numeric(df["Change"], errors="coerce").dropna()
            if not isinstance(change_series.index, pd.DatetimeIndex):
                change_series.index = pd.to_datetime(change_series.index)
            if start_date is not None and end_date is not None:
                change_series = change_series.loc[
                    (change_series.index >= pd.Timestamp(start_date)) & (change_series.index <= pd.Timestamp(end_date))
                ]
            if not change_series.empty:
                returns_dict[ticker] = change_series

    if not returns_dict:
        return None

    all_returns = pd.DataFrame(returns_dict)
    all_returns["AVG_CHANGE"] = all_returns.mean(axis=1)
    worst_date = all_returns["AVG_CHANGE"].idxmin()
    return worst_date, all_returns


def run_stress_test(
    target_index="EGX30",
    ref_date: str | date | datetime | None = None,
    initial_capital: float = 1_000_000.0,
    lookback_days: int = LOOKBACK_DAYS,
    simulation_days: int = SIMULATION_DAYS,
):
    """
    Run full stress test on the chosen index.
    Simulates portfolio drop if worst day happened today.
    """
    mkt_lists = _resolve_symbol("MarketLists", MarketLists)
    data_mgr = _resolve_symbol("DataManager", DataManager)
    worst_day_fn = _resolve_symbol("find_worst_day", find_worst_day)

    normalized_ref_date = _coerce_ref_date(ref_date)
    effective_lookback_days = _coerce_positive_int(lookback_days, LOOKBACK_DAYS)
    effective_simulation_days = _coerce_positive_int(simulation_days, SIMULATION_DAYS)
    try:
        effective_capital = float(initial_capital) if initial_capital is not None else 1_000_000.0
    except Exception:
        effective_capital = 1_000_000.0
    if effective_capital <= 0:
        effective_capital = 1_000_000.0

    if target_index == "EGX30":
        tickers = list(mkt_lists.get_market_list("30"))
    elif target_index == "EGX70":
        tickers = list(mkt_lists.get_market_list("70"))
    elif target_index == "FINANCIALS":
        tickers = get_sector_tickers(FINANCIAL_SECTORS)
    else:
        tickers = list(mkt_lists.get_market_list("ALL"))

    result = worst_day_fn(
        tickers,
        target_index,
        ref_date=normalized_ref_date,
        lookback_days=effective_lookback_days,
    )
    if not result:
        return None

    crash_date, all_returns = result
    try:
        loc = all_returns.index.get_loc(crash_date)
    except Exception:
        return None

    ticker_cols = [col for col in all_returns.columns if col != "AVG_CHANGE"]
    end_loc = min(loc + effective_simulation_days, len(all_returns))
    crash_sequence = all_returns.iloc[loc:end_loc][ticker_cols]

    current_portfolio = []
    for ticker in tickers:
        df = data_mgr.DataManager.get_stock_data(ticker, include_live=False)
        if df is None or df.empty or "Close" not in df.columns:
            continue
        close_series = pd.to_numeric(df["Close"], errors="coerce").dropna()
        if close_series.empty:
            continue
        if not isinstance(close_series.index, pd.DatetimeIndex):
            close_series.index = pd.to_datetime(close_series.index)
        close_series = close_series.sort_index()

        if normalized_ref_date is not None:
            ref_slice = close_series.loc[close_series.index <= pd.Timestamp(normalized_ref_date)]
            if ref_slice.empty:
                continue
            last_price = float(ref_slice.iloc[-1])
            snapshot_date = ref_slice.index[-1]
        else:
            last_price = float(close_series.iloc[-1])
            snapshot_date = close_series.index[-1]

        if ticker in crash_sequence.columns:
            drops = crash_sequence[ticker].values
        else:
            drops = all_returns.iloc[loc:end_loc]["AVG_CHANGE"].values

        simulated_prices = [last_price]
        for d in drops:
            simulated_prices.append(simulated_prices[-1] * (1 + (d / 100)))

        total_simulated_drop = (simulated_prices[-1] - last_price) / last_price * 100

        date_str = snapshot_date.strftime("%Y-%m-%d") if hasattr(snapshot_date, "strftime") else str(snapshot_date)[:10]
        current_portfolio.append(
            {
                "Ticker": ticker,
                "Current_Price": last_price,
                "Current_Price_Date": date_str,
                "Snapshot_Date": date_str,
                "Simulated_Price": simulated_prices[-1],
                "Simulated_Drop_Pct": total_simulated_drop,
                "Price_Path": simulated_prices,
            }
        )

    if not current_portfolio:
        return None

    df_results = pd.DataFrame(current_portfolio)
    df_results = df_results.sort_values(by="Simulated_Drop_Pct", ascending=True)

    avg_drop = df_results["Simulated_Drop_Pct"].mean()
    most_affected = df_results.head(5).to_dict(orient="records")
    least_affected = df_results.tail(5).to_dict(orient="records")
    estimated_loss_egp = max(0.0, float(effective_capital * (abs(avg_drop) / 100.0))) if avg_drop < 0 else 0.0
    ending_capital = max(0.0, float(effective_capital * (1.0 + (avg_drop / 100.0))))

    return {
        "target_index": target_index,
        "historical_crash_date": crash_date.strftime("%Y-%m-%d"),
        "historical_drop_pct": all_returns.loc[crash_date, "AVG_CHANGE"],
        "projected_portfolio_drop_pct": avg_drop,
        "most_affected": most_affected,
        "least_affected": least_affected,
        "full_data": df_results.to_dict(orient="records"),
        "estimated_loss_egp": estimated_loss_egp,
        "ending_capital": ending_capital,
        "initial_capital": effective_capital,
        "lookback_days": effective_lookback_days,
        "simulation_days": effective_simulation_days,
        "ref_date": normalized_ref_date.isoformat() if normalized_ref_date else None,
    }
