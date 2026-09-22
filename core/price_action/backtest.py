from __future__ import annotations
"""Backtesting and promotion helpers for EGX price-action strategies."""


import datetime
import hashlib
import json
from typing import Any

import pandas as pd
from peewee import IntegrityError

from core.market import MarketLists
from core import MonteCarlo
from core.DataManager import DataManager
from core.price_action.catalog import get_price_action_strategy
from core.price_action.executor import evaluate_price_action_strategy
from core.price_action.models import PriceActionSignalType, PriceActionStrategyFamily
from core.pine_lab.profiles import ensure_pine_scanner_profile_schema
from database import ScannerStrategyProfile, db

MIN_TRADES_FOR_PROMOTION = 30
MIN_EXPECTANCY_FOR_PROMOTION = 0.0
MIN_PROFIT_FACTOR_FOR_PROMOTION = 1.05
MAX_DRAWDOWN_FOR_PROMOTION = 35.0
MIN_LIQUIDITY_COVERAGE_FOR_PROMOTION = 0.5
MAX_WARNING_CONFLICT_RATE_FOR_PROMOTION = 0.6
MAX_RISK_OF_RUIN_FOR_PROMOTION = 1.0
MIN_OOS_TRADES_FOR_PROMOTION = 10
SAMPLED_INTRADAY_EXECUTION_MODE = "SAMPLED_INTRADAY"
FULL_EXECUTION_MODE = "FULL"

PROMOTION_THRESHOLDS = {
    "trade_count": MIN_TRADES_FOR_PROMOTION,
    "expectancy": MIN_EXPECTANCY_FOR_PROMOTION,
    "profit_factor": MIN_PROFIT_FACTOR_FOR_PROMOTION,
    "max_drawdown": MAX_DRAWDOWN_FOR_PROMOTION,
    "liquidity_coverage": MIN_LIQUIDITY_COVERAGE_FOR_PROMOTION,
    "warning_conflict_rate": MAX_WARNING_CONFLICT_RATE_FOR_PROMOTION,
    "risk_of_ruin_pct": MAX_RISK_OF_RUIN_FOR_PROMOTION,
    "oos_trade_count": MIN_OOS_TRADES_FOR_PROMOTION,
}


def _resolve_data_version() -> int:
    try:
        from routes import shared
        snapshot = shared.get_system_state_snapshot() or {}
        return int(snapshot.get("data_version", 0) or 0)
    except Exception:
        return 0


def _slice_frame(df: pd.DataFrame, date_from: str, date_to: str) -> pd.DataFrame:
    frame = df.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"])
        frame = frame.set_index("Date")
    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index)
    frame = frame.sort_index()
    return frame.loc[pd.Timestamp(date_from): pd.Timestamp(date_to)]


def _load_market_frame(
    ticker: str,
    *,
    family: PriceActionStrategyFamily,
    date_from: str,
    date_to: str,
) -> pd.DataFrame | None:
    if family is PriceActionStrategyFamily.INTRADAY:
        raw_df = DataManager.get_intraday_data(ticker, refresh_if_stale=False)
    else:
        raw_df = DataManager.get_stock_data(ticker, include_live=False)
    if raw_df is None or raw_df.empty:
        return None
    frame = _slice_frame(raw_df, date_from, date_to)
    return frame if not frame.empty else None


def _trim_recent_sessions(frame: pd.DataFrame, recent_sessions_only: int | None) -> pd.DataFrame:
    if recent_sessions_only is None or recent_sessions_only <= 0 or frame.empty:
        return frame
    normalized_dates = pd.Index(frame.index.normalize())
    unique_dates = normalized_dates.unique()
    if len(unique_dates) <= recent_sessions_only:
        return frame
    allowed_dates = set(unique_dates[-recent_sessions_only:])
    return frame.loc[normalized_dates.isin(allowed_dates)]


def _apply_intraday_sampling(
    frame: pd.DataFrame,
    *,
    max_bars_per_ticker: int | None,
    recent_sessions_only: int | None,
) -> pd.DataFrame:
    sampled = _trim_recent_sessions(frame, recent_sessions_only)
    if max_bars_per_ticker is not None and max_bars_per_ticker > 0 and len(sampled) > max_bars_per_ticker:
        sampled = sampled.tail(max_bars_per_ticker)
    return sampled


def _calculate_drawdown_pct(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    running_peak = equity_curve[0]
    max_drawdown = 0.0
    for value in equity_curve:
        running_peak = max(running_peak, value)
        if running_peak <= 0:
            continue
        drawdown = (running_peak - value) / running_peak * 100.0
        max_drawdown = max(max_drawdown, drawdown)
    return round(max_drawdown, 4)


def _evaluate_readiness(metrics: dict[str, Any], *, compatibility_ready: bool) -> dict[str, Any]:
    failed_gates: list[str] = []
    trade_count = int(metrics.get("trade_count", 0) or 0)
    expectancy = float(metrics.get("expectancy", 0.0) or 0.0)
    profit_factor = float(metrics.get("profit_factor", 0.0) or 0.0)
    max_drawdown = float(metrics.get("max_drawdown", 0.0) or 0.0)
    liquidity_coverage = float(metrics.get("liquidity_coverage", 0.0) or 0.0)
    warning_conflict_rate = float(metrics.get("warning_conflict_rate", 0.0) or 0.0)
    risk_of_ruin_pct = float(metrics.get("risk_of_ruin_pct", 0.0) or 0.0)
    monte_carlo_pass = bool(metrics.get("monte_carlo_pass", False))
    walk_forward_pass = bool(metrics.get("walk_forward_pass", False))
    oos_trade_count = int(metrics.get("oos_trade_count", 0) or 0)

    if not compatibility_ready:
        failed_gates.append("readiness")
    if trade_count < MIN_TRADES_FOR_PROMOTION:
        failed_gates.append("trade_count")
    if expectancy <= MIN_EXPECTANCY_FOR_PROMOTION:
        failed_gates.append("expectancy")
    if profit_factor < MIN_PROFIT_FACTOR_FOR_PROMOTION:
        failed_gates.append("profit_factor")
    if max_drawdown > MAX_DRAWDOWN_FOR_PROMOTION:
        failed_gates.append("max_drawdown")
    if liquidity_coverage < MIN_LIQUIDITY_COVERAGE_FOR_PROMOTION:
        failed_gates.append("liquidity_coverage")
    if warning_conflict_rate > MAX_WARNING_CONFLICT_RATE_FOR_PROMOTION:
        failed_gates.append("warning_conflict_rate")
    if risk_of_ruin_pct > MAX_RISK_OF_RUIN_FOR_PROMOTION:
        failed_gates.append("risk_of_ruin_pct")
    if not monte_carlo_pass:
        failed_gates.append("monte_carlo")
    if not walk_forward_pass:
        failed_gates.append("walk_forward")
    if oos_trade_count < MIN_OOS_TRADES_FOR_PROMOTION:
        failed_gates.append("oos_trade_count")

    return {
        "profile_state": "READY" if not failed_gates else "DRAFT",
        "failed_gates": failed_gates,
        "thresholds": PROMOTION_THRESHOLDS,
        "actuals": {
            "trade_count": trade_count,
            "expectancy": round(expectancy, 6),
            "profit_factor": round(profit_factor, 6),
            "max_drawdown": round(max_drawdown, 4),
            "liquidity_coverage": round(liquidity_coverage, 4),
            "warning_conflict_rate": round(warning_conflict_rate, 4),
            "risk_of_ruin_pct": round(risk_of_ruin_pct, 4),
            "monte_carlo_pass": monte_carlo_pass,
            "walk_forward_pass": walk_forward_pass,
            "oos_trade_count": oos_trade_count,
            "readiness": "READY" if compatibility_ready else "BLOCKED",
        },
    }


def _compute_probabilistic_risk(trades: list[dict[str, Any]], capital: float) -> dict[str, Any]:
    if not trades:
        return {"risk_of_ruin_pct": 100.0, "monte_carlo_pass": False, "monte_carlo": None}
    simulations = int(max(500, min(3000, len(trades) * 120)))
    sample = [
        {
            "pnl": float(t.get("pnl", 0.0) or 0.0),
            "pnl_pct": (float(t.get("pnl", 0.0) or 0.0) / capital) * 100.0,
        }
        for t in trades
    ]
    mc = MonteCarlo.run_monte_carlo(sample, initial_equity=float(capital), simulations=simulations)
    if not isinstance(mc, dict):
        return {"risk_of_ruin_pct": 100.0, "monte_carlo_pass": False, "monte_carlo": None}
    risk_of_ruin_pct = float(mc.get("ruin_probability", 100.0) or 0.0)
    drawdown_50_prob = float(mc.get("drawdown_probability_50", 100.0) or 0.0)
    monte_carlo_pass = (risk_of_ruin_pct <= MAX_RISK_OF_RUIN_FOR_PROMOTION) and (drawdown_50_prob <= 5.0)
    return {
        "risk_of_ruin_pct": round(risk_of_ruin_pct, 4),
        "monte_carlo_pass": bool(monte_carlo_pass),
        "monte_carlo": {
            "simulations": int(mc.get("simulations", simulations)),
            "ruin_probability": round(risk_of_ruin_pct, 4),
            "drawdown_probability_20": round(float(mc.get("drawdown_probability_20", 0.0) or 0.0), 4),
            "drawdown_probability_50": round(drawdown_50_prob, 4),
            "median_max_drawdown": round(float(mc.get("median_max_drawdown", 0.0) or 0.0), 4),
            "worst_max_drawdown": round(float(mc.get("worst_max_drawdown", 0.0) or 0.0), 4),
        },
    }


def _compute_walk_forward_validation(trades: list[dict[str, Any]], capital: float, date_from: str, date_to: str) -> dict[str, Any]:
    if not trades:
        return {
            "method": "time_split_80_20",
            "split_date": date_to,
            "in_sample": {"trade_count": 0, "total_pnl": 0.0, "win_rate": 0.0},
            "out_of_sample": {"trade_count": 0, "total_pnl": 0.0, "win_rate": 0.0, "total_return": 0.0},
            "pass": False,
        }
    start_ts = pd.Timestamp(date_from)
    end_ts = pd.Timestamp(date_to)
    span_sec = max(0.0, (end_ts - start_ts).total_seconds())
    split_ts = start_ts + pd.to_timedelta(span_sec * 0.8, unit="s")
    in_sample = []
    out_sample = []
    for trade in trades:
        exit_ts = pd.Timestamp(trade.get("exit_date"))
        if exit_ts <= split_ts:
            in_sample.append(trade)
        else:
            out_sample.append(trade)

    def _summary(items: list[dict[str, Any]]) -> dict[str, Any]:
        count = len(items)
        total_pnl = float(sum(float(t.get("pnl", 0.0) or 0.0) for t in items))
        wins = sum(1 for t in items if float(t.get("pnl", 0.0) or 0.0) > 0)
        win_rate = (wins / count) * 100.0 if count else 0.0
        total_return = ((total_pnl / capital) * 100.0) if capital > 0 else 0.0
        return {
            "trade_count": count,
            "total_pnl": round(total_pnl, 4),
            "win_rate": round(win_rate, 4),
            "total_return": round(total_return, 4),
        }

    in_summary = _summary(in_sample)
    out_summary = _summary(out_sample)
    pass_flag = bool(out_summary["trade_count"] >= MIN_OOS_TRADES_FOR_PROMOTION and out_summary["total_pnl"] > 0)
    return {
        "method": "time_split_80_20",
        "split_date": split_ts.strftime("%Y-%m-%d"),
        "in_sample": {
            "trade_count": in_summary["trade_count"],
            "total_pnl": in_summary["total_pnl"],
            "win_rate": in_summary["win_rate"],
        },
        "out_of_sample": {
            "trade_count": out_summary["trade_count"],
            "total_pnl": out_summary["total_pnl"],
            "win_rate": out_summary["win_rate"],
            "total_return": out_summary["total_return"],
        },
        "pass": pass_flag,
    }


def _build_profile_payload(
    *,
    strategy_id: str,
    strategy_name: str,
    market: str,
    timeframe: str,
    family: PriceActionStrategyFamily,
    metrics: dict[str, Any],
    compatibility: dict[str, Any],
    ranking: dict[str, Any],
    execution: dict[str, Any],
    promotion_artifacts: dict[str, Any],
) -> str:
    payload = {
        "source_type": "PRICE_ACTION",
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "market": market,
        "timeframe": timeframe,
        "family": family.value,
        "metrics": metrics,
        "compatibility": compatibility,
        "ranking": ranking,
        "execution": execution,
        "promotion_artifacts": promotion_artifacts,
    }
    return json.dumps(payload, sort_keys=True)


def run_price_action_backtest(
    *,
    strategy_id: str,
    market: str,
    date_from: str,
    date_to: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
    ticker_limit: int | None = None,
    max_bars_per_ticker: int | None = None,
    max_trades: int | None = None,
    recent_sessions_only: int | None = None,
) -> dict[str, Any]:
    strategy = get_price_action_strategy(strategy_id)
    if strategy is None:
        raise ValueError(f"Unknown price-action strategy '{strategy_id}'")
    if strategy.warning_only:
        raise ValueError("Warning-only price-action strategies cannot be backtested as trade profiles.")

    tickers = sorted(MarketLists.get_market_list(market) or set())
    if not tickers:
        tickers = sorted(DataManager.list_tickers() or [])
    if not tickers:
        raise ValueError("No market tickers are available for the requested backtest.")
    requested_ticker_count = len(tickers)
    is_intraday = strategy.family is PriceActionStrategyFamily.INTRADAY
    sampled_intraday = is_intraday and any(
        value is not None for value in (ticker_limit, max_bars_per_ticker, max_trades, recent_sessions_only)
    )
    execution_mode = SAMPLED_INTRADAY_EXECUTION_MODE if sampled_intraday else FULL_EXECUTION_MODE
    if is_intraday and ticker_limit is not None and ticker_limit > 0:
        tickers = tickers[:ticker_limit]

    trade_notional = capital / max(1, min(10, len(tickers)))
    total_realized_pnl = 0.0
    total_gross_profit = 0.0
    total_gross_loss = 0.0
    warning_buy_count = 0
    triggered_buy_count = 0
    liquidity_ok_count = 0
    evaluated_ticker_count = 0
    scanned_bar_count = 0
    trades: list[dict[str, Any]] = []
    equity_curve = [capital]
    max_trades_reached = False

    for ticker in tickers:
        frame = _load_market_frame(
            ticker,
            family=strategy.family,
            date_from=date_from,
            date_to=date_to,
        )
        if frame is not None and is_intraday:
            frame = _apply_intraday_sampling(
                frame,
                max_bars_per_ticker=max_bars_per_ticker if sampled_intraday else None,
                recent_sessions_only=recent_sessions_only if sampled_intraday else None,
            )
        if frame is None or len(frame) < 8:
            continue
        evaluated_ticker_count += 1
        scanned_bar_count += len(frame)
        if float((frame["Close"] * frame["Volume"]).tail(20).mean()) >= 1_000.0:
            liquidity_ok_count += 1

        open_trade: dict[str, Any] | None = None
        i = 6
        while i < len(frame) - 1:
            window = frame.iloc[: i + 1]
            if open_trade is None:
                signal = evaluate_price_action_strategy(
                    window,
                    strategy_id=strategy_id,
                    ticker=ticker,
                    intraday_data_available=(strategy.family is PriceActionStrategyFamily.INTRADAY),
                )
                if signal is not None and signal.signal_type in {PriceActionSignalType.BUY, PriceActionSignalType.BUY_CANDIDATE}:
                    triggered_buy_count += 1
                    if signal.signal_type is PriceActionSignalType.BUY_CANDIDATE:
                        warning_buy_count += 1
                    next_bar = frame.iloc[i + 1]
                    entry_price = float(next_bar["Open"]) * (1.0 + commission_pct / 100.0 + slippage_pct / 100.0)
                    if entry_price <= 0:
                        i += 1
                        continue
                    shares = trade_notional / entry_price
                    open_trade = {
                        "entry_time": frame.index[i + 1],
                        "entry_price": entry_price,
                        "shares": shares,
                        "stop_loss": float(signal.stop_loss or 0.0),
                        "target_price": float(signal.target_1 or 0.0),
                        "signal_type": signal.signal_type.value,
                        "warning_count": len(signal.warnings),
                    }
                i += 1
                continue

            current_bar = frame.iloc[i + 1]
            exit_price = None
            exit_reason = None
            if float(current_bar["Low"]) <= open_trade["stop_loss"]:
                exit_price = open_trade["stop_loss"] * (1.0 - slippage_pct / 100.0)
                exit_reason = "STOP_LOSS"
            elif float(current_bar["High"]) >= open_trade["target_price"]:
                exit_price = open_trade["target_price"] * (1.0 - slippage_pct / 100.0)
                exit_reason = "TARGET_1"
            elif i + 1 == len(frame) - 1:
                exit_price = float(current_bar["Close"]) * (1.0 - commission_pct / 100.0 - slippage_pct / 100.0)
                exit_reason = "END_OF_TEST"

            if exit_price is not None:
                pnl = (exit_price - open_trade["entry_price"]) * open_trade["shares"]
                pnl_pct = ((exit_price / open_trade["entry_price"]) - 1.0) * 100.0
                total_realized_pnl += pnl
                total_gross_profit += max(pnl, 0.0)
                total_gross_loss += abs(min(pnl, 0.0))
                equity_curve.append(capital + total_realized_pnl)
                trades.append(
                    {
                        "ticker": ticker,
                        "entry_date": pd.Timestamp(open_trade["entry_time"]).strftime("%Y-%m-%d"),
                        "exit_date": pd.Timestamp(frame.index[i + 1]).strftime("%Y-%m-%d"),
                        "entry_price": round(open_trade["entry_price"], 4),
                        "exit_price": round(exit_price, 4),
                        "pnl": round(pnl, 4),
                        "pnl_pct": round(pnl_pct, 4),
                        "reason": exit_reason,
                        "signal_type": open_trade["signal_type"],
                    }
                )
                open_trade = None
                if max_trades is not None and max_trades > 0 and len(trades) >= max_trades:
                    max_trades_reached = True
                    break
            i += 1
        if max_trades_reached:
            break

    trade_count = len(trades)
    win_count = sum(1 for trade in trades if float(trade["pnl"]) > 0)
    final_value = capital + total_realized_pnl
    total_return = ((final_value / capital) - 1.0) * 100.0 if capital > 0 else 0.0
    profit_factor = (total_gross_profit / total_gross_loss) if total_gross_loss > 0 else (total_gross_profit if total_gross_profit > 0 else 0.0)
    expectancy = (total_realized_pnl / trade_count) if trade_count else 0.0
    liquidity_coverage = (liquidity_ok_count / evaluated_ticker_count) if evaluated_ticker_count else 0.0
    warning_conflict_rate = (warning_buy_count / triggered_buy_count) if triggered_buy_count else 0.0
    probabilistic_risk = _compute_probabilistic_risk(trades, capital)
    walk_forward = _compute_walk_forward_validation(trades, capital, date_from, date_to)
    compatibility_messages: list[str] = []
    compatibility_ready = True
    if is_intraday:
        compatibility_messages.append("Intraday EGX data is required and was used for this backtest.")
    else:
        compatibility_messages.append("Daily EGX OHLCV backtest completed without intraday dependency.")
    if sampled_intraday:
        compatibility_messages.append("Sampled intraday execution was used for research speed; this run is not promotion-eligible.")
    if trade_count == 0:
        compatibility_ready = False
        compatibility_messages.append("No trades were produced for the selected period and market.")

    metrics = {
        "trade_count": trade_count,
        "win_rate": round((win_count / trade_count) * 100.0, 4) if trade_count else 0.0,
        "total_return": round(total_return, 4),
        "final_value": round(final_value, 4),
        "max_drawdown": _calculate_drawdown_pct(equity_curve),
        "profit_factor": round(profit_factor, 6),
        "expectancy": round(expectancy, 6),
        "liquidity_coverage": round(liquidity_coverage, 4),
        "warning_conflict_rate": round(warning_conflict_rate, 4),
        "risk_of_ruin_pct": probabilistic_risk["risk_of_ruin_pct"],
        "monte_carlo_pass": probabilistic_risk["monte_carlo_pass"],
        "walk_forward_pass": bool(walk_forward["pass"]),
        "oos_trade_count": int((walk_forward.get("out_of_sample") or {}).get("trade_count", 0)),
        "oos_total_return": float((walk_forward.get("out_of_sample") or {}).get("total_return", 0.0)),
        "evaluated_tickers": evaluated_ticker_count,
    }
    execution = {
        "mode": execution_mode,
        "requested_tickers": requested_ticker_count,
        "scanned_tickers": evaluated_ticker_count,
        "scanned_bars": scanned_bar_count,
        "ticker_limit": ticker_limit if sampled_intraday else None,
        "max_bars_per_ticker": max_bars_per_ticker if sampled_intraday else None,
        "max_trades": max_trades if sampled_intraday else None,
        "recent_sessions_only": recent_sessions_only if sampled_intraday else None,
    }
    compatibility = {
        "readiness": "READY" if compatibility_ready else "BLOCKED",
        "compatibility_score": 85.0 if compatibility_ready else 40.0,
        "messages": compatibility_messages,
    }
    ranking = {
        "performance_score": max(0.0, min(100.0, 50.0 + metrics["total_return"])),
        "alignment_score": 80.0 if strategy.status.value in {"DRAFT", "READY"} else 65.0,
    }
    ranking["combined_score"] = round((ranking["performance_score"] * 0.6) + (ranking["alignment_score"] * 0.4), 4)
    ranking["recommended"] = (
        compatibility_ready
        and metrics["trade_count"] >= MIN_TRADES_FOR_PROMOTION
        and bool(metrics.get("monte_carlo_pass", False))
    )
    promotion_summary = _evaluate_readiness(metrics, compatibility_ready=compatibility_ready)
    promotion_artifacts = {
        "artifact_version": "promotion_v1",
        "date_from": date_from,
        "date_to": date_to,
        "market": market,
        "timeframe": "1D" if strategy.family is not PriceActionStrategyFamily.INTRADAY else "INTRADAY",
        "tickers": sorted(tickers),
        "data_version": _resolve_data_version(),
        "costs": {
            "commission_pct": float(commission_pct),
            "slippage_pct": float(slippage_pct),
        },
        "parameters": {
            "strategy_id": strategy.strategy_id,
            "ticker_limit": ticker_limit,
            "max_bars_per_ticker": max_bars_per_ticker,
            "max_trades": max_trades,
            "recent_sessions_only": recent_sessions_only,
        },
        "metrics": {
            "trade_count": trade_count,
            "total_return": round(total_return, 4),
            "max_drawdown": metrics["max_drawdown"],
            "risk_of_ruin_pct": metrics["risk_of_ruin_pct"],
        },
        "failed_gates": list(promotion_summary.get("failed_gates", [])),
    }
    promotion_artifacts_hash = hashlib.sha256(json.dumps(promotion_artifacts, sort_keys=True).encode("utf-8")).hexdigest()
    promotion_artifacts["artifact_hash"] = promotion_artifacts_hash

    return {
        "status": "success",
        "config": {
            "strategy_id": strategy.strategy_id,
            "strategy_name": strategy.display_name,
            "market": market,
            "timeframe": "1D" if strategy.family is not PriceActionStrategyFamily.INTRADAY else "INTRADAY",
            "date_from": date_from,
            "date_to": date_to,
            "capital": capital,
            "commission_pct": commission_pct,
            "slippage_pct": slippage_pct,
        },
        "strategy": strategy.to_dict(),
        "compatibility": compatibility,
        "metrics": metrics,
        "ranking": ranking,
        "promotion_summary": promotion_summary,
        "monte_carlo": probabilistic_risk["monte_carlo"],
        "walk_forward": walk_forward,
        "promotion_artifacts": promotion_artifacts,
        "execution": execution,
        "equity_curve": [round(value, 4) for value in equity_curve],
        "trades": trades,
    }


def promote_price_action_strategy(
    *,
    profile_name: str,
    strategy_id: str,
    market: str,
    date_from: str,
    date_to: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
    ticker_limit: int | None = None,
    max_bars_per_ticker: int | None = None,
    max_trades: int | None = None,
    recent_sessions_only: int | None = None,
) -> ScannerStrategyProfile:
    strategy = get_price_action_strategy(strategy_id)
    if strategy is None:
        raise ValueError(f"Unknown price-action strategy '{strategy_id}'")

    result = run_price_action_backtest(
        strategy_id=strategy_id,
        market=market,
        date_from=date_from,
        date_to=date_to,
        capital=capital,
        commission_pct=commission_pct,
        slippage_pct=slippage_pct,
        ticker_limit=ticker_limit,
        max_bars_per_ticker=max_bars_per_ticker,
        max_trades=max_trades,
        recent_sessions_only=recent_sessions_only,
    )
    if result.get("execution", {}).get("mode") == SAMPLED_INTRADAY_EXECUTION_MODE:
        raise ValueError("Sampled intraday backtests cannot be promoted; rerun a full backtest.")
    promotion_summary = result["promotion_summary"]
    if promotion_summary["profile_state"] != "READY":
        failed = ", ".join(promotion_summary["failed_gates"])
        raise ValueError(f"Price-action strategy did not pass promotion gates: {failed}")

    ensure_pine_scanner_profile_schema()
    script_source = _build_profile_payload(
        strategy_id=strategy.strategy_id,
        strategy_name=strategy.display_name,
        market=market,
        timeframe=result["config"]["timeframe"],
        family=strategy.family,
        metrics=result["metrics"],
        compatibility=result["compatibility"],
        ranking=result["ranking"],
        execution=result["execution"],
        promotion_artifacts=result.get("promotion_artifacts") or {},
    )
    script_hash = hashlib.sha256(f"PRICE_ACTION::{strategy.strategy_id}::{market}::{result['config']['timeframe']}".encode("utf-8")).hexdigest()
    ready_at = datetime.datetime.now()
    try:
        return ScannerStrategyProfile.create(
            profile_name=profile_name.strip(),
            source_type="PRICE_ACTION",
            script_source=script_source,
            script_hash=script_hash,
            market=market,
            timeframe=result["config"]["timeframe"],
            profile_state="READY",
            backtest_summary_json=json.dumps(result["metrics"], sort_keys=True),
            compatibility_summary_json=json.dumps(result["compatibility"], sort_keys=True),
            ranking_summary_json=json.dumps(result["ranking"], sort_keys=True),
            ready_at=ready_at,
            activation_count=0,
            activation_history_json="[]",
            import_rule_spec_json=json.dumps(
                {
                    "strategy_id": strategy.strategy_id,
                    "strategy_name": strategy.display_name,
                    "family": strategy.family.value,
                    "promotion_summary": promotion_summary,
                    "promotion_artifacts": result.get("promotion_artifacts") or {},
                },
                sort_keys=True,
            ),
        )
    except IntegrityError as exc:
        raise IntegrityError(exc)


def activate_price_action_profile(profile_id: int) -> ScannerStrategyProfile:
    ensure_pine_scanner_profile_schema()
    profile = ScannerStrategyProfile.get_or_none(ScannerStrategyProfile.id == int(profile_id))
    if profile is None:
        raise LookupError("Requested price-action scanner profile was not found.")
    if str(profile.source_type or "").upper() != "PRICE_ACTION":
        raise ValueError("Only PRICE_ACTION scanner profiles can be activated with this endpoint.")
    if profile.profile_state not in {"READY", "ACTIVE"}:
        raise ValueError("Only READY price-action scanner profiles can be activated.")
    if profile.profile_state == "ACTIVE":
        return profile

    activated_at = datetime.datetime.now()
    try:
        activation_history = json.loads(profile.activation_history_json or "[]")
    except json.JSONDecodeError:
        activation_history = []
    if not isinstance(activation_history, list):
        activation_history = []

    previous_active = (
        ScannerStrategyProfile.select()
        .where(
            (ScannerStrategyProfile.profile_state == "ACTIVE")
            & (ScannerStrategyProfile.id != profile.id)
        )
        .order_by(ScannerStrategyProfile.created_at.desc())
        .first()
    )
    activation_history.insert(
        0,
        {
            "event_type": "ACTIVATED",
            "activated_at": activated_at.isoformat(),
            "previous_state": profile.profile_state,
            "previous_active_profile_id": previous_active.id if previous_active else None,
            "previous_active_profile_name": previous_active.profile_name if previous_active else None,
        },
    )

    with db.atomic():
        (
            ScannerStrategyProfile.update(profile_state="READY")
            .where(
                (ScannerStrategyProfile.profile_state == "ACTIVE")
                & (ScannerStrategyProfile.id != profile.id)
            )
            .execute()
        )
        profile.profile_state = "ACTIVE"
        profile.ready_at = profile.ready_at or activated_at
        profile.activated_at = activated_at
        profile.activation_count = int(profile.activation_count or 0) + 1
        profile.activation_history_json = json.dumps(activation_history)
        profile.save()
    return profile
