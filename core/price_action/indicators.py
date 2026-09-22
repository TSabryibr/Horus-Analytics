from __future__ import annotations
"""Shared OHLCV feature helpers for price-action evaluation."""


import pandas as pd
import numpy as np


REQUIRED_OHLCV_COLUMNS = ("Open", "High", "Low", "Close", "Volume")


def validate_ohlcv_frame(frame: pd.DataFrame) -> None:
    if frame is None or frame.empty:
        raise ValueError("price-action evaluation requires a non-empty OHLCV frame")
    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"price-action evaluation is missing OHLCV columns: {', '.join(missing)}")


def add_price_action_features(frame: pd.DataFrame, *, volume_window: int = 20, atr_window: int = 14) -> pd.DataFrame:
    validate_ohlcv_frame(frame)
    df = frame.copy()
    prev_close = df["Close"].shift(1)
    true_range = np.fmax.reduce(
        [
            (df["High"] - df["Low"]).to_numpy(),
            (df["High"] - prev_close).abs().to_numpy(),
            (df["Low"] - prev_close).abs().to_numpy(),
        ]
    )
    df["ATR"] = pd.Series(true_range, index=df.index).rolling(atr_window, min_periods=1).mean()
    df["Avg_Volume"] = df["Volume"].rolling(volume_window, min_periods=1).mean()
    df["Rel_Volume"] = (df["Volume"] / df["Avg_Volume"]).fillna(0.0)
    df["Turnover"] = df["Close"] * df["Volume"]
    df["Avg_Turnover"] = df["Turnover"].rolling(volume_window, min_periods=1).mean()
    return df
