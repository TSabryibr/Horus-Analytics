from __future__ import annotations

import datetime
import math
import os
from typing import Any, Optional

import pandas as pd

from core.DataManager import DataManager
from database import SignalRecommendation, SignalRun
from .periods import _coerce_float


def _load_market_window(period_start: datetime.date, period_end: datetime.date) -> tuple[Optional[pd.DataFrame], str]:
    benchmark = os.getenv("ANALYSIS_REPORT_INDEX", "EGX30").strip().upper() or "EGX30"
    try:
        df = DataManager.get_stock_data(benchmark, limit=520)
    except Exception:
        return None, benchmark

    if df is None or df.empty:
        return None, benchmark

    data = df.copy()
    if "Date" not in data.columns:
        data = data.reset_index()
        if "Date" not in data.columns:
            idx_col = "index" if "index" in data.columns else data.columns[0]
            data = data.rename(columns={idx_col: "Date"})

    close_col = "Close" if "Close" in data.columns else ("close" if "close" in data.columns else None)
    if close_col is None:
        return None, benchmark

    data["Date"] = pd.to_datetime(data["Date"], errors="coerce").dt.date
    data[close_col] = pd.to_numeric(data[close_col], errors="coerce")
    data = data.dropna(subset=["Date", close_col]).sort_values("Date")
    window = data[(data["Date"] >= period_start) & (data["Date"] <= period_end)].copy()
    if window.empty:
        return None, benchmark

    if close_col != "Close":
        window = window.rename(columns={close_col: "Close"})
    return window, benchmark


def _aggregate_market_summary(
    runs: list[SignalRun],
    period_start: datetime.date,
    period_end: datetime.date,
) -> tuple[dict[str, Any], list[str]]:
    notes: list[str] = []
    summary: dict[str, Any] = {
        "regime_start": "NEUTRAL",
        "regime_end": "NEUTRAL",
        "period_return_pct": 0.0,
        "breadth_change_pct": 0.0,
        "volatility_context": "Insufficient benchmark data for volatility context.",
        "top_groups": [],
        "weak_groups": [],
        "key_shifts": [],
    }

    run_ids = [r.id for r in runs]
    if run_ids:
        regime_rows = list(
            SignalRecommendation.select(SignalRecommendation.regime, SignalRun.run_date)
            .join(SignalRun)
            .where(SignalRecommendation.run.in_(run_ids))
            .where(SignalRecommendation.regime.is_null(False))
            .order_by(SignalRun.run_date.asc(), SignalRecommendation.created_at.asc())
        )
        if regime_rows:
            first_regime = str(regime_rows[0].regime or "NEUTRAL").upper()
            last_regime = str(regime_rows[-1].regime or "NEUTRAL").upper()
            summary["regime_start"] = first_regime
            summary["regime_end"] = last_regime

    breadth_points = [
        (r.signals_count / r.universe_count) * 100.0
        for r in runs
        if _coerce_float(r.universe_count, 0.0) > 0
    ]
    if len(breadth_points) >= 2:
        summary["breadth_change_pct"] = round(breadth_points[-1] - breadth_points[0], 2)

    market_df, benchmark = _load_market_window(period_start, period_end)
    if market_df is not None and len(market_df) >= 2:
        start_close = _coerce_float(market_df["Close"].iloc[0], 0.0)
        end_close = _coerce_float(market_df["Close"].iloc[-1], 0.0)
        if start_close > 0:
            summary["period_return_pct"] = round(((end_close / start_close) - 1.0) * 100.0, 2)
        returns = market_df["Close"].pct_change().dropna()
        if not returns.empty:
            std_pct = _coerce_float(returns.std() * 100.0, default=float("nan"))
            if math.isfinite(std_pct):
                if std_pct < 1.0:
                    summary["volatility_context"] = f"{benchmark}: low volatility ({std_pct:.2f}% daily std)."
                elif std_pct < 2.5:
                    summary["volatility_context"] = f"{benchmark}: moderate volatility ({std_pct:.2f}% daily std)."
                else:
                    summary["volatility_context"] = f"{benchmark}: elevated volatility ({std_pct:.2f}% daily std)."
            else:
                summary["volatility_context"] = f"{benchmark}: limited benchmark history; volatility estimate unavailable."
    else:
        notes.append("Benchmark market return/volatility data is unavailable for the selected period.")

    if summary["regime_start"] != summary["regime_end"]:
        summary["key_shifts"].append(
            f"Regime shifted from {summary['regime_start']} to {summary['regime_end']} during the period."
        )
    if summary["breadth_change_pct"] >= 5:
        summary["key_shifts"].append("Breadth proxy improved materially over the period.")
    elif summary["breadth_change_pct"] <= -5:
        summary["key_shifts"].append("Breadth proxy deteriorated materially over the period.")
    if summary["period_return_pct"] >= 2:
        summary["key_shifts"].append("Benchmark finished the period with positive momentum.")
    elif summary["period_return_pct"] <= -2:
        summary["key_shifts"].append("Benchmark closed the period under pressure.")

    return summary, notes
