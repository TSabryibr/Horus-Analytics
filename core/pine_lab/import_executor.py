from __future__ import annotations

import hashlib
import json
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import Any

import pandas as pd

from core.market import MarketLists
from core.simulation import PortfolioSimulator
from core.DataManager import DataManager

from .executor import (
    _build_equity_curve,
    _build_walk_forward_validation,
    _compute_max_drawdown,
    _compute_probabilistic_risk,
    _compute_quality_score,
    _estimate_alignment_score,
    _generate_signal_masks,
    _normalize_history_frame,
    _resolve_data_version,
    _simulate_ticker_trades,
)
from .import_validator import validate_import_backtest_request


def _build_horus_core_metrics(result: dict[str, Any]) -> dict[str, Any]:
    trades = list(result.get("trades") or [])
    starting_capital = float(result.get("starting_capital") or 0.0)
    final_value = float(result.get("final_value") or starting_capital)
    total_return = float(result.get("total_return") or 0.0)
    trade_count = len(trades)
    win_rate = (sum(1 for trade in trades if float(trade.get("pnl", 0.0) or 0.0) > 0) / trade_count) * 100.0 if trade_count else 0.0
    equity_curve = [
        {
            "date": str(point.get("date")),
            "equity": round(float(point.get("value") or starting_capital), 4),
        }
        for point in list(result.get("daily_values") or [])
        if point.get("date") is not None
    ]
    max_drawdown = _compute_max_drawdown(equity_curve)
    quality_score = _compute_quality_score(trades)
    return {
        "total_return": round(total_return, 4),
        "final_value": round(final_value, 4),
        "trade_count": trade_count,
        "win_rate": round(win_rate, 4),
        "max_drawdown": max_drawdown,
        "quality_score": quality_score,
    }


def _winner(imported_value: float, horus_value: float, *, lower_is_better: bool = False) -> str:
    if abs(float(imported_value) - float(horus_value)) < 1e-9:
        return "TIE"
    if lower_is_better:
        return "IMPORTED" if imported_value < horus_value else "HORUS_CORE"
    return "IMPORTED" if imported_value > horus_value else "HORUS_CORE"


def _run_horus_core_comparison(*, market: str, date_from: str, date_to: str, capital: float) -> dict[str, Any]:
    with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
        result = PortfolioSimulator.run_simulation(
            cap=capital,
            start_date=date_from,
            end_date=date_to,
            index_choice=market,
        )

    if not isinstance(result, dict):
        raise ValueError("Horus core comparison backtest did not return a result.")

    metrics = _build_horus_core_metrics(result)
    return {
        "status": "available",
        "metrics": metrics,
    }


def run_pine_import_backtest(
    *,
    rule_spec: dict[str, Any],
    operator_approved: bool,
    market: str,
    timeframe: str,
    date_from: str,
    date_to: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
) -> dict[str, Any]:
    validation = validate_import_backtest_request(rule_spec, operator_approved=operator_approved)
    execution_plan = dict(rule_spec.get("execution_plan") or {})

    tickers = sorted(MarketLists.get_market_list(market) or set())
    if not tickers:
        tickers = sorted(DataManager.list_tickers() or [])

    trade_notional = capital / max(1, min(10, len(tickers) or 1))
    ticker_frames: dict[str, pd.DataFrame] = {}
    trades: list[dict[str, Any]] = []
    start_ts = pd.Timestamp(date_from)
    end_ts = pd.Timestamp(date_to)

    for ticker in tickers:
        raw_df = DataManager.get_stock_data(ticker, include_live=False)
        df = _normalize_history_frame(raw_df)
        if df is None or df.empty:
            continue
        df = df.loc[(df.index >= start_ts) & (df.index <= end_ts)].copy()
        if df.empty:
            continue
        ticker_frames[ticker] = df
        entries, exits = _generate_signal_masks(df, execution_plan, base_timeframe=timeframe)
        trades.extend(
            _simulate_ticker_trades(
                ticker=ticker,
                df=df,
                entries=entries,
                exits=exits,
                trade_notional=trade_notional,
                commission_pct=commission_pct,
                slippage_pct=slippage_pct,
            )
        )

    equity_curve = _build_equity_curve(capital, trades, date_from, date_to)
    final_value = float(equity_curve[-1]["equity"]) if equity_curve else capital
    total_return = ((final_value - capital) / capital) * 100.0 if capital > 0 else 0.0
    trade_count = len(trades)
    win_rate = (sum(1 for trade in trades if float(trade["pnl"]) > 0) / trade_count) * 100.0 if trade_count else 0.0
    max_drawdown = _compute_max_drawdown(equity_curve)
    quality_score = _compute_quality_score(trades)
    probabilistic_risk = _compute_probabilistic_risk(trades, capital)
    walk_forward = _build_walk_forward_validation(trades, capital, date_from, date_to)
    alignment = _estimate_alignment_score(ticker_frames, trades)
    performance_score = max(0.0, min(100.0, 50.0 + total_return - max_drawdown + (win_rate * 0.2)))
    combined_score = round((performance_score * 0.7) + (alignment["alignment_score"] * 0.3), 4)

    imported_metrics = {
        "total_return": round(total_return, 4),
        "final_value": round(final_value, 4),
        "trade_count": trade_count,
        "win_rate": round(win_rate, 4),
        "max_drawdown": max_drawdown,
        "quality_score": quality_score,
        "risk_of_ruin_pct": probabilistic_risk["risk_of_ruin_pct"],
        "monte_carlo_pass": probabilistic_risk["monte_carlo_pass"],
        "walk_forward_pass": bool(walk_forward["pass"]),
        "oos_trade_count": int((walk_forward.get("out_of_sample") or {}).get("trade_count", 0)),
        "oos_total_return": float((walk_forward.get("out_of_sample") or {}).get("total_return", 0.0)),
    }
    artifacts = {
        "artifact_version": "promotion_v1",
        "date_from": date_from,
        "date_to": date_to,
        "market": market,
        "timeframe": timeframe,
        "tickers": sorted(ticker_frames.keys()),
        "data_version": _resolve_data_version(),
        "costs": {
            "commission_pct": float(commission_pct),
            "slippage_pct": float(slippage_pct),
        },
        "parameters": {
            "strategy_kind": str(execution_plan.get("strategy_kind") or "IMPORTED_EXPRESSION_PLAN"),
            "execution_mode": validation["execution_mode"],
        },
        "metrics": {
            "trade_count": trade_count,
            "total_return": round(total_return, 4),
            "max_drawdown": max_drawdown,
            "risk_of_ruin_pct": probabilistic_risk["risk_of_ruin_pct"],
        },
    }
    artifacts_hash = hashlib.sha256(json.dumps(artifacts, sort_keys=True).encode("utf-8")).hexdigest()
    artifacts["artifact_hash"] = artifacts_hash

    comparison: dict[str, Any] = {
        "imported": {"metrics": imported_metrics},
        "horus_core": {"status": "unavailable", "metrics": None},
        "winner_by_metric": {},
    }
    try:
        horus_core = _run_horus_core_comparison(
            market=market,
            date_from=date_from,
            date_to=date_to,
            capital=capital,
        )
    except Exception as exc:
        comparison["horus_core"] = {
            "status": "unavailable",
            "metrics": None,
            "warning": str(exc),
        }
    else:
        comparison["horus_core"] = horus_core
        horus_metrics = horus_core["metrics"]
        comparison["winner_by_metric"] = {
            "total_return": _winner(imported_metrics["total_return"], horus_metrics["total_return"]),
            "final_value": _winner(imported_metrics["final_value"], horus_metrics["final_value"]),
            "trade_count": _winner(imported_metrics["trade_count"], horus_metrics["trade_count"]),
            "win_rate": _winner(imported_metrics["win_rate"], horus_metrics["win_rate"]),
            "max_drawdown": _winner(imported_metrics["max_drawdown"], horus_metrics["max_drawdown"], lower_is_better=True),
            "quality_score": _winner(imported_metrics["quality_score"], horus_metrics["quality_score"]),
        }

    return {
        "status": "success",
        "import_mode": "LOGIC_IMPORT",
        "backtest_source": "IMPORTED_RULE_SPEC",
        "config": {
            "market": market,
            "timeframe": timeframe,
            "date_from": date_from,
            "date_to": date_to,
            "capital": capital,
            "execution_mode": validation["execution_mode"],
            "strategy_kind": str(execution_plan.get("strategy_kind") or "IMPORTED_EXPRESSION_PLAN"),
        },
        "metrics": imported_metrics,
        "assumptions": {
            "commission_pct": commission_pct,
            "slippage_pct": slippage_pct,
            "position_notional": round(trade_notional, 4),
            "execution_model": "close_to_close_simplified",
        },
        "monte_carlo": probabilistic_risk["monte_carlo"],
        "walk_forward": walk_forward,
        "promotion_artifacts": artifacts,
        "alignment": alignment,
        "rankings": {
            "performance_score": round(performance_score, 4),
            "alignment_score": alignment["alignment_score"],
            "combined_score": combined_score,
            "recommended": (combined_score >= performance_score) and bool(probabilistic_risk["monte_carlo_pass"]),
        },
        "equity_curve": equity_curve,
        "trades": trades,
        "import_metadata": {
            "operator_approved": True,
            "warnings": list(rule_spec.get("warnings") or []),
            "ignored_sections": list(rule_spec.get("ignored_sections") or []),
            "confidence": dict(rule_spec.get("confidence") or {}),
            "translation_mode": str((rule_spec.get("source") or {}).get("translation_mode") or "UNKNOWN"),
        },
        "comparison": comparison,
    }
