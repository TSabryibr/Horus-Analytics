from __future__ import annotations
from core.settings import settings

import json
import math
import re
import hashlib
from typing import Any

import numpy as np
import pandas as pd

from core.market import MarketLists
from core import SignalEngine
from core import MonteCarlo
from core.DataManager import DataManager
from database import ScannerStrategyProfile
from .expression_eval import evaluate_signal_plan
from .parser import build_pine_execution_plan, preflight_pine_script
from .profiles import build_promotion_summary


def _normalize_history_frame(df: pd.DataFrame) -> pd.DataFrame | None:
    if df is None or df.empty:
        return None

    normalized = df.copy()
    if "Date" in normalized.columns:
        normalized["Date"] = pd.to_datetime(normalized["Date"], errors="coerce")
        normalized = normalized.set_index("Date")

    if not isinstance(normalized.index, pd.DatetimeIndex):
        return None

    normalized.index = pd.to_datetime(normalized.index, errors="coerce")
    normalized = normalized.sort_index()
    normalized = normalized[~normalized.index.duplicated(keep="last")]
    required_cols = {"Open", "High", "Low", "Close", "Volume"}
    if not required_cols.issubset(set(normalized.columns)):
        return None
    return normalized


def _resample_runtime_frame(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    token = str(timeframe or "").strip().upper()
    if not re.fullmatch(r"\d+", token):
        return df
    minutes = int(token)
    if minutes < 1:
        return df
    resampled = df.resample(f"{minutes}min", label="right", closed="right").agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }
    )
    return resampled.dropna(subset=["Open", "High", "Low", "Close"]).copy()


def _is_intraday_strategy_timeframe(timeframe: str) -> bool:
    token = str(timeframe or "").strip().upper()
    return bool(re.fullmatch(r"\d+", token)) and int(token) > 0


def _generate_signal_masks(
    df: pd.DataFrame,
    strategy_spec: dict[str, Any],
    *,
    base_timeframe: str = "1D",
    source_df: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.Series]:
    if strategy_spec.get("entry_expression") and strategy_spec.get("exit_expression"):
        return evaluate_signal_plan(df, strategy_spec, base_timeframe=base_timeframe, source_df=source_df)

    close = df["Close"].astype(float)
    kind = strategy_spec["strategy_kind"]
    signal_family = str(strategy_spec.get("signal_family", "SMA")).upper()

    def build_ma_series(length: int) -> pd.Series:
        if signal_family == "EMA":
            return close.ewm(span=length, adjust=False).mean()
        return close.rolling(length).mean()

    if kind in {"SMA_CROSSOVER", "EMA_CROSSOVER"}:
        fast = build_ma_series(strategy_spec["fast_length"])
        slow = build_ma_series(strategy_spec["slow_length"])
        entries = (fast.shift(1) <= slow.shift(1)) & (fast > slow)
        exits = (fast.shift(1) >= slow.shift(1)) & (fast < slow)
        return entries.fillna(False), exits.fillna(False)

    signal = build_ma_series(strategy_spec["signal_length"])
    entries = (close.shift(1) <= signal.shift(1)) & (close > signal)
    exits = (close.shift(1) >= signal.shift(1)) & (close < signal)
    return entries.fillna(False), exits.fillna(False)


def _simulate_ticker_trades(
    ticker: str,
    df: pd.DataFrame,
    entries: pd.Series,
    exits: pd.Series,
    trade_notional: float,
    commission_pct: float,
    slippage_pct: float,
) -> list[dict[str, Any]]:
    trades: list[dict[str, Any]] = []
    in_position = False
    entry_price_gross = 0.0
    entry_date = None
    shares = 0.0
    combined_cost_pct = (commission_pct + slippage_pct) / 100.0

    for ts, row in df.iterrows():
        if not in_position and bool(entries.loc[ts]):
            raw_entry = float(row["Close"])
            entry_price_gross = raw_entry * (1 + combined_cost_pct)
            if entry_price_gross <= 0:
                continue
            shares = trade_notional / entry_price_gross
            entry_date = ts
            in_position = True
            continue

        if in_position and bool(exits.loc[ts]):
            raw_exit = float(row["Close"])
            exit_price_net = raw_exit * (1 - combined_cost_pct)
            pnl = shares * (exit_price_net - entry_price_gross)
            pnl_pct = (pnl / trade_notional) * 100 if trade_notional > 0 else 0.0
            trades.append(
                {
                    "ticker": ticker,
                    "entry_date": entry_date.strftime("%Y-%m-%d"),
                    "exit_date": ts.strftime("%Y-%m-%d"),
                    "entry_price": round(entry_price_gross, 4),
                    "exit_price": round(exit_price_net, 4),
                    "pnl": round(pnl, 4),
                    "pnl_pct": round(pnl_pct, 4),
                    "reason": "SIGNAL_EXIT",
                }
            )
            in_position = False
            entry_date = None
            shares = 0.0

    if in_position and entry_date is not None:
        final_ts = df.index[-1]
        raw_exit = float(df.iloc[-1]["Close"])
        exit_price_net = raw_exit * (1 - combined_cost_pct)
        pnl = shares * (exit_price_net - entry_price_gross)
        pnl_pct = (pnl / trade_notional) * 100 if trade_notional > 0 else 0.0
        trades.append(
            {
                "ticker": ticker,
                "entry_date": entry_date.strftime("%Y-%m-%d"),
                "exit_date": final_ts.strftime("%Y-%m-%d"),
                "entry_price": round(entry_price_gross, 4),
                "exit_price": round(exit_price_net, 4),
                "pnl": round(pnl, 4),
                "pnl_pct": round(pnl_pct, 4),
                "reason": "TIME_EXIT",
            }
        )

    return trades


def _compute_max_drawdown(equity_curve: list[dict[str, Any]]) -> float:
    if not equity_curve:
        return 0.0
    equities = [float(point["equity"]) for point in equity_curve]
    peak = equities[0]
    max_drawdown = 0.0
    for equity in equities:
        peak = max(peak, equity)
        if peak <= 0:
            continue
        drawdown = ((peak - equity) / peak) * 100.0
        max_drawdown = max(max_drawdown, drawdown)
    return round(max_drawdown, 4)


def _build_equity_curve(capital: float, trades: list[dict[str, Any]], date_from: str, date_to: str) -> list[dict[str, Any]]:
    if not trades:
        return [
            {"date": date_from, "equity": round(capital, 4)},
            {"date": date_to, "equity": round(capital, 4)},
        ]

    curve = [{"date": date_from, "equity": round(capital, 4)}]
    running = capital
    for trade in sorted(trades, key=lambda item: (item["exit_date"], item["ticker"])):
        running += float(trade["pnl"])
        curve.append({"date": trade["exit_date"], "equity": round(running, 4)})
    return curve


def _estimate_alignment_score(ticker_frames: dict[str, pd.DataFrame], trades: list[dict[str, Any]]) -> dict[str, Any]:
    if not trades:
        return {
            "alignment_score": 0.0,
            "matched_entries": 0,
            "pine_entries": 0,
            "method": "entry_overlap_same_day",
        }

    horus_entries: dict[str, set[str]] = {}
    for ticker, base_df in ticker_frames.items():
        try:
            indicator_df = SignalEngine.add_indicators(base_df.copy(), lookback=settings.LOOKBACK)
        except Exception:
            continue
        entry_dates: set[str] = set()
        resistance_col = f"Res_{settings.LOOKBACK}"
        for _, row in indicator_df.iterrows():
            signal = SignalEngine.check_buy_signal(row, settings, resistance_col=resistance_col)
            if signal:
                entry_dates.add(pd.Timestamp(row.name).strftime("%Y-%m-%d"))
        horus_entries[ticker] = entry_dates

    matched_entries = 0
    for trade in trades:
        if trade["entry_date"] in horus_entries.get(trade["ticker"], set()):
            matched_entries += 1

    pine_entries = len(trades)
    alignment_score = (matched_entries / pine_entries) * 100.0 if pine_entries else 0.0
    return {
        "alignment_score": round(alignment_score, 4),
        "matched_entries": matched_entries,
        "pine_entries": pine_entries,
        "method": "entry_overlap_same_day",
    }


def _compute_quality_score(trades: list[dict[str, Any]]) -> float:
    if not trades:
        return 0.0
    pnl_pcts = np.array([float(trade["pnl_pct"]) for trade in trades], dtype=float)
    mean = float(np.mean(pnl_pcts))
    std = float(np.std(pnl_pcts))
    if std <= 0:
        return round(mean, 4)
    return round((mean / std) * math.sqrt(len(pnl_pcts)), 4)


def _resolve_data_version() -> int:
    try:
        from routes import shared
        snapshot = shared.get_system_state_snapshot() or {}
        return int(snapshot.get("data_version", 0) or 0)
    except Exception:
        return 0


def _build_walk_forward_validation(trades: list[dict[str, Any]], capital: float, date_from: str, date_to: str) -> dict[str, Any]:
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
    pass_flag = bool(out_summary["trade_count"] >= 10 and out_summary["total_pnl"] > 0)
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


def _compute_probabilistic_risk(trades: list[dict[str, Any]], capital: float) -> dict[str, Any]:
    if not trades:
        return {
            "risk_of_ruin_pct": 100.0,
            "monte_carlo": None,
            "monte_carlo_pass": False,
        }
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
        return {
            "risk_of_ruin_pct": 100.0,
            "monte_carlo": None,
            "monte_carlo_pass": False,
        }
    risk_of_ruin_pct = float(mc.get("ruin_probability", 100.0) or 0.0)
    drawdown_50_prob = float(mc.get("drawdown_probability_50", 100.0) or 0.0)
    monte_carlo_pass = (risk_of_ruin_pct <= 1.0) and (drawdown_50_prob <= 5.0)
    return {
        "risk_of_ruin_pct": round(risk_of_ruin_pct, 4),
        "monte_carlo": {
            "simulations": int(mc.get("simulations", simulations)),
            "ruin_probability": round(risk_of_ruin_pct, 4),
            "drawdown_probability_20": round(float(mc.get("drawdown_probability_20", 0.0) or 0.0), 4),
            "drawdown_probability_50": round(drawdown_50_prob, 4),
            "median_max_drawdown": round(float(mc.get("median_max_drawdown", 0.0) or 0.0), 4),
            "worst_max_drawdown": round(float(mc.get("worst_max_drawdown", 0.0) or 0.0), 4),
        },
        "monte_carlo_pass": bool(monte_carlo_pass),
    }


def _load_profile_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _load_profile_json_list(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _build_profile_metadata(profile: ScannerStrategyProfile) -> dict[str, Any]:
    backtest_summary = _load_profile_json(getattr(profile, "backtest_summary_json", None))
    compatibility_summary = _load_profile_json(getattr(profile, "compatibility_summary_json", None))
    ranking_summary = _load_profile_json(getattr(profile, "ranking_summary_json", None))
    return {
        "profile_id": profile.id,
        "profile_name": profile.profile_name,
        "source_type": profile.source_type,
        "market": profile.market,
        "timeframe": profile.timeframe,
        "profile_state": profile.profile_state,
        "created_at": profile.created_at.isoformat() if profile.created_at else None,
        "ready_at": profile.ready_at.isoformat() if profile.ready_at else None,
        "activated_at": profile.activated_at.isoformat() if profile.activated_at else None,
        "activation_count": int(profile.activation_count or 0),
        "activation_history": _load_profile_json_list(getattr(profile, "activation_history_json", None)),
        "backtest_summary": backtest_summary,
        "compatibility_summary": compatibility_summary,
        "ranking_summary": ranking_summary,
        "promotion_summary": build_promotion_summary(
            backtest_summary=backtest_summary,
            compatibility_summary=compatibility_summary,
            ranking_summary=ranking_summary,
        ),
    }


def _build_monitored_row(ticker: str, row: pd.Series) -> dict[str, Any]:
    close = float(row.get("Close", 0.0) or 0.0)
    ema9_raw = row.get("EMA9")
    ema9 = float(ema9_raw) if pd.notna(ema9_raw) else close
    rsi = row.get("RSI")
    return {
        "Ticker": ticker,
        "Close": round(close, 4),
        "Trend": "UP" if close >= ema9 else "DOWN",
        "RSI": round(float(rsi), 4) if pd.notna(rsi) else None,
    }


def _build_pine_scanner_signal(
    *,
    ticker: str,
    row: pd.Series,
    profile: ScannerStrategyProfile,
) -> dict[str, Any]:
    close = float(row.get("Close", 0.0) or 0.0)
    atr = float(row.get("ATR", 0.0) or 0.0) if pd.notna(row.get("ATR")) else 0.0
    if getattr(settings, "USE_ATR_EXITS", False) and atr > 0:
        stop_loss = close - (atr * float(getattr(settings, "ATR_SL_MULTIPLIER", 1.5)))
        target_price = close + (atr * float(getattr(settings, "ATR_TP_MULTIPLIER", 2.0)))
    else:
        stop_loss = close * (1 - float(getattr(settings, "SL_PCT", 1.5)) / 100.0)
        target_price = close * (1 + float(getattr(settings, "TP1_PCT", 4.0)) / 100.0)
    target_price_2 = target_price * 1.04

    ranking_summary = _load_profile_json(profile.ranking_summary_json)
    combined_score = float(ranking_summary.get("combined_score", 80.0) or 80.0)
    score = round(max(1.0, min(5.0, combined_score / 20.0)), 1)
    rel_vol = row.get("Rel_Vol")
    rsi = row.get("RSI")

    return {
        "Ticker": ticker,
        "Signal_Type": "BUY",
        "Signal_Setup": "PINE_CROSSOVER",
        "Conviction": "HIGH" if score >= 4.0 else "MODERATE",
        "Entry_Price": round(close, 4),
        "Stop_Loss": round(stop_loss, 4),
        "Target_Price": round(target_price, 4),
        "Target_Price_2": round(target_price_2, 4),
        "Score": score,
        "RSI": round(float(rsi), 4) if pd.notna(rsi) else None,
        "Volume_x": round(float(rel_vol), 4) if pd.notna(rel_vol) else 0.0,
        "VSA_Valid": None,
        "Route_Profile": "PINE_PROFILE",
        "Routing_Reason": "pine_profile_signal",
        "Scanner_Profile_Name": profile.profile_name,
    }


def run_pine_scanner_profile_scan(
    *,
    profile: ScannerStrategyProfile,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, str, dict[str, Any]]:
    timeframe = str(profile.timeframe or "1D").strip().upper()
    if timeframe not in {"1D", "D", "DAILY"}:
        raise ValueError("Pine scanner profiles currently support daily timeframe execution only.")

    preflight = preflight_pine_script(profile.script_source, timeframe=timeframe)
    if preflight["readiness"] != "READY":
        raise ValueError("Selected Pine scanner profile is not ready for scanner execution.")

    strategy_spec = preflight.get("plan") or build_pine_execution_plan(profile.script_source)
    tickers = sorted(MarketLists.get_market_list(profile.market) or set())
    if not tickers:
        tickers = sorted(DataManager.list_tickers() or [])

    signals: list[dict[str, Any]] = []
    monitored: list[dict[str, Any]] = []

    for ticker in tickers:
        raw_df = DataManager.get_stock_data(ticker, include_live=False)
        df = _normalize_history_frame(raw_df)
        if df is None or df.empty:
            continue
        indicator_df = SignalEngine.add_indicators(df.copy(), lookback=settings.LOOKBACK)
        if indicator_df is None or indicator_df.empty:
            continue
        latest_row = indicator_df.iloc[-1]
        monitored.append(_build_monitored_row(ticker, latest_row))

        entries, exits = _generate_signal_masks(indicator_df, strategy_spec, base_timeframe=timeframe)
        latest_entry = bool(entries.iloc[-1]) if len(entries) else False
        latest_exit = bool(exits.iloc[-1]) if len(exits) else False
        if latest_entry and not latest_exit:
            signals.append(_build_pine_scanner_signal(ticker=ticker, row=latest_row, profile=profile))

    signals = sorted(signals, key=lambda item: float(item.get("Score", 0) or 0), reverse=True)
    total = len(monitored)
    above_trend = sum(1 for item in monitored if item.get("Trend") == "UP")
    breadth = (above_trend / total * 100.0) if total else 0.0
    if breadth > 50:
        regime = "BULLISH"
    elif breadth > 30:
        regime = "CAUTIOUS"
    else:
        regime = "BEARISH"

    return signals, monitored, round(breadth, 4), regime, _build_profile_metadata(profile)


def run_pine_backtest(
    *,
    script_source: str,
    market: str,
    timeframe: str,
    date_from: str,
    date_to: str,
    capital: float,
    commission_pct: float,
    slippage_pct: float,
) -> dict[str, Any]:
    preflight = preflight_pine_script(script_source, timeframe=timeframe)
    if preflight["readiness"] != "READY":
        raise ValueError("Pine preflight blocked this script from backtest execution.")

    strategy_spec = preflight.get("plan") or build_pine_execution_plan(script_source)
    tickers = sorted(MarketLists.get_market_list(market) or set())
    if not tickers:
        tickers = sorted(DataManager.list_tickers() or [])

    trade_notional = capital / max(1, min(10, len(tickers) or 1))
    ticker_frames: dict[str, pd.DataFrame] = {}
    trades: list[dict[str, Any]] = []
    start_ts = pd.Timestamp(date_from)
    end_ts = pd.Timestamp(date_to)

    for ticker in tickers:
        if _is_intraday_strategy_timeframe(timeframe):
            raw_df = DataManager.get_intraday_data(ticker, refresh_if_stale=False)
        else:
            raw_df = DataManager.get_stock_data(ticker, include_live=False)
        df = _normalize_history_frame(raw_df)
        if df is None or df.empty:
            continue
        df = df.loc[(df.index >= start_ts) & (df.index <= end_ts)].copy()
        if df.empty:
            continue
        base_df = _resample_runtime_frame(df, timeframe)
        if base_df.empty:
            continue
        ticker_frames[ticker] = base_df
        entries, exits = _generate_signal_masks(base_df, strategy_spec, base_timeframe=timeframe, source_df=df)
        ticker_trades = _simulate_ticker_trades(
            ticker=ticker,
            df=base_df,
            entries=entries,
            exits=exits,
            trade_notional=trade_notional,
            commission_pct=commission_pct,
            slippage_pct=slippage_pct,
        )
        trades.extend(ticker_trades)

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
            "strategy_kind": strategy_spec["strategy_kind"],
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

    return {
        "status": "success",
        "config": {
            "market": market,
            "timeframe": timeframe,
            "date_from": date_from,
            "date_to": date_to,
            "capital": capital,
            "strategy_kind": strategy_spec["strategy_kind"],
        },
        "metrics": {
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
        },
        "assumptions": {
            "commission_pct": commission_pct,
            "slippage_pct": slippage_pct,
            "position_notional": round(trade_notional, 4),
            "execution_model": "close_to_close_simplified",
        },
        "monte_carlo": probabilistic_risk["monte_carlo"],
        "walk_forward": walk_forward,
        "promotion_artifacts": artifacts,
        "compatibility": {
            "script_type": preflight["script_type"],
            "readiness": preflight["readiness"],
            "compatibility_score": preflight["compatibility_score"],
            "messages": preflight["messages"],
        },
        "alignment": alignment,
        "rankings": {
            "performance_score": round(performance_score, 4),
            "alignment_score": alignment["alignment_score"],
            "combined_score": combined_score,
            "recommended": (combined_score >= performance_score) and bool(probabilistic_risk["monte_carlo_pass"]),
        },
        "equity_curve": equity_curve,
        "trades": trades,
    }
