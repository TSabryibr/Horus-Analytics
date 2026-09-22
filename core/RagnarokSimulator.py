from __future__ import annotations
"""
RAGNAROK MONTE CARLO SIMULATOR
==============================
Simulates multiple market paths to estimate portfolio loss and ruin risk.
"""

from core.settings import settings

import numpy as np
import pandas as pd

from core.DataManager import DataManager


def _prepare_returns(portfolio_tickers: list[str]) -> pd.DataFrame:
    """Collect clean daily return series for provided tickers."""
    returns_data: dict[str, pd.Series] = {}

    for raw_ticker in portfolio_tickers:
        ticker = str(raw_ticker).strip().upper()
        if not ticker:
            continue

        df = DataManager.get_stock_data(ticker, include_live=False)
        if df is None or df.empty or "Close" not in df.columns:
            continue

        series = pd.to_numeric(df["Close"], errors="coerce").pct_change().dropna()
        if len(series) > 5:
            returns_data[ticker] = series

    if not returns_data:
        return pd.DataFrame()

    returns_df = pd.DataFrame(returns_data).dropna(how="all")
    valid_cols = [col for col in returns_df.columns if returns_df[col].dropna().shape[0] > 5]
    if not valid_cols:
        return pd.DataFrame()

    return returns_df[valid_cols].dropna()


def _resolve_starting_value(starting_value: float | None) -> float:
    if starting_value is not None:
        try:
            resolved = float(starting_value)
            if resolved > 0:
                return resolved
        except Exception:
            pass
    fallback = float(getattr(settings, "ACCOUNT_BALANCE", 0.0) or 0.0)
    return fallback if fallback > 0 else 1_000_000.0


def _resolve_weights(assets_used: list[str], weights: dict[str, float] | None) -> np.ndarray:
    if not assets_used:
        return np.array([])
    if not weights:
        return np.ones(len(assets_used), dtype=float) / float(len(assets_used))

    resolved = []
    for ticker in assets_used:
        try:
            resolved.append(float(weights.get(ticker, 0.0)))
        except Exception:
            resolved.append(0.0)

    vec = np.array(resolved, dtype=float)
    vec = np.clip(vec, 0.0, None)
    total = float(vec.sum())
    if total <= 0:
        return np.ones(len(assets_used), dtype=float) / float(len(assets_used))
    return vec / total


def run_ragnarok_simulation(
    portfolio_tickers: list[str],
    iterations: int = 1000,
    days: int = 20,
    starting_value: float | None = None,
    ruin_threshold_pct: float = 50.0,
    weights: dict[str, float] | None = None,
) -> dict:
    """
    Simulate potential portfolio outcomes using multivariate normal returns.
    """
    if not portfolio_tickers:
        raise ValueError("No tickers provided for Ragnarok simulation.")
    if iterations < 100:
        raise ValueError("Iterations must be at least 100.")
    if days < 1:
        raise ValueError("Days must be at least 1.")

    returns_df = _prepare_returns(portfolio_tickers)
    if returns_df.empty:
        raise ValueError("Not enough historical data to run Ragnarok simulation.")

    mean_returns = returns_df.mean().values
    cov_matrix = returns_df.cov().values + np.eye(returns_df.shape[1]) * 1e-10
    starting_value_resolved = _resolve_starting_value(starting_value)

    try:
        ruin_threshold_pct = float(ruin_threshold_pct)
    except Exception:
        ruin_threshold_pct = 50.0
    ruin_threshold_pct = min(99.9, max(0.0, ruin_threshold_pct))
    ruin_floor = starting_value_resolved * (1.0 - ruin_threshold_pct / 100.0)

    assets_used = list(returns_df.columns)
    weight_vec = _resolve_weights(assets_used, weights)

    random_returns = np.random.multivariate_normal(mean_returns, cov_matrix, size=(iterations, days))
    daily_portfolio_returns = np.einsum("ija,a->ij", random_returns, weight_vec)
    cumulative_returns = np.cumprod(1 + daily_portfolio_returns, axis=1)
    final_values = starting_value_resolved * cumulative_returns[:, -1]

    results_array = np.array(final_values, dtype=float)
    var_95 = float(np.percentile(results_array, 5))
    loss_probability = float((results_array < starting_value_resolved).sum() / iterations * 100.0)
    ruin_probability = float((results_array < ruin_floor).sum() / iterations * 100.0)
    expected_outcome = float(np.mean(results_array))
    min_outcome = float(np.min(results_array))
    max_outcome = float(np.max(results_array))

    return {
        "expected_value": expected_outcome,
        "var_95": var_95,
        "loss_probability": loss_probability,
        "ruin_probability": ruin_probability,
        "ruin_threshold_pct": ruin_threshold_pct,
        "ruin_floor": float(ruin_floor),
        "starting_value": starting_value_resolved,
        "min_outcome": min_outcome,
        "max_outcome": max_outcome,
        "iterations": int(iterations),
        "days": int(days),
        "assets_count": int(len(assets_used)),
        "assets_used": assets_used,
        "weights_used": {assets_used[i]: float(weight_vec[i]) for i in range(len(assets_used))},
        "plot_paths": (starting_value_resolved * cumulative_returns[:50]).tolist(),
    }
