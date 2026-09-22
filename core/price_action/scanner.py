from __future__ import annotations
"""Scanner runtime for promoted price-action profiles."""


import json
from typing import Any

import pandas as pd

from core.market import MarketLists
from core.DataManager import DataManager
from core.price_action.executor import evaluate_price_action_strategy
from core.price_action.models import PriceActionSignalType
from core.pine_lab.profiles import serialize_pine_scanner_profile
from database import ScannerStrategyProfile


def _load_profile_payload(profile: ScannerStrategyProfile) -> dict[str, Any]:
    try:
        payload = json.loads(profile.script_source or "{}")
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _normalize_history_frame(raw_df: pd.DataFrame | None) -> pd.DataFrame | None:
    if raw_df is None or raw_df.empty:
        return None
    frame = raw_df.copy()
    if "Date" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"])
        frame = frame.set_index("Date")
    if not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index)
    frame = frame.sort_index()
    return frame if not frame.empty else None


def _build_monitored_row(ticker: str, frame: pd.DataFrame) -> dict[str, Any]:
    latest = frame.iloc[-1]
    close = float(latest.get("Close", 0.0) or 0.0)
    open_price = float(latest.get("Open", close) or close)
    trend = "UP" if close >= open_price else "DOWN"
    return {
        "Ticker": ticker,
        "Close": round(close, 4),
        "Trend": trend,
        "Volume": float(latest.get("Volume", 0.0) or 0.0),
    }


def _build_signal_row(ticker: str, signal) -> dict[str, Any]:
    return {
        "Ticker": ticker,
        "Signal_Type": "BUY",
        "Signal_Setup": signal.strategy_id.upper(),
        "Conviction": "HIGH" if float(signal.score) >= 70 else "MODERATE",
        "Entry_Price": round(float(signal.entry_price or 0.0), 4),
        "Stop_Loss": round(float(signal.stop_loss or 0.0), 4),
        "Target_Price": round(float(signal.target_1 or 0.0), 4),
        "Target_Price_2": round(float(signal.target_2 or 0.0), 4) if signal.target_2 is not None else None,
        "Score": round(float(signal.score) / 10.0, 1),
        "RSI": None,
        "Volume_x": 0.0,
        "VSA_Valid": None,
        "Route_Profile": "PRICE_ACTION_PROFILE",
        "Routing_Reason": "price_action_profile_signal",
        "Scanner_Profile_Name": signal.setup_name,
        "Warnings": list(signal.warnings),
        "Avoidance_Flags": list(signal.avoidance_flags),
    }


def run_price_action_scanner_profile_scan(
    *,
    profile: ScannerStrategyProfile,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float, str, dict[str, Any]]:
    payload = _load_profile_payload(profile)
    strategy_id = str(payload.get("strategy_id") or "").strip().lower()
    if not strategy_id:
        raise ValueError("Selected price-action profile does not contain a strategy_id payload.")

    timeframe = str(profile.timeframe or "1D").strip().upper()
    if timeframe not in {"1D", "D", "DAILY"}:
        raise ValueError("Price-action scanner profiles currently support daily timeframe execution only.")

    tickers = sorted(MarketLists.get_market_list(profile.market) or set())
    if not tickers:
        tickers = sorted(DataManager.list_tickers() or [])

    signals: list[dict[str, Any]] = []
    monitored: list[dict[str, Any]] = []

    for ticker in tickers:
        frame = _normalize_history_frame(DataManager.get_stock_data(ticker, include_live=False))
        if frame is None or len(frame) < 8:
            continue
        monitored.append(_build_monitored_row(ticker, frame))
        signal = evaluate_price_action_strategy(
            frame,
            strategy_id=strategy_id,
            ticker=ticker,
            intraday_data_available=False,
        )
        if signal is None:
            continue
        if signal.signal_type in {PriceActionSignalType.BUY, PriceActionSignalType.BUY_CANDIDATE}:
            signals.append(_build_signal_row(ticker, signal))

    signals = sorted(signals, key=lambda item: float(item.get("Score", 0.0) or 0.0), reverse=True)
    total = len(monitored)
    bullish = sum(1 for item in monitored if item.get("Trend") == "UP")
    breadth = (bullish / total * 100.0) if total else 0.0
    regime = "BULLISH" if breadth > 50 else ("CAUTIOUS" if breadth > 30 else "BEARISH")
    return signals, monitored, round(breadth, 4), regime, serialize_pine_scanner_profile(profile)
