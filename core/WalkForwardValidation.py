from __future__ import annotations
"""
MIMIR WALK-FORWARD ANALYZER (MIND STONE MODULE)
================================================
Walk-Forward Analysis (WFA) coordinator that evolves strategy parameters
through rolling train/validation windows.
"""


import json
import os
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from core.simulation import Optimizer
from core import SignalEngine
from core.DataManager import DataManager

from core.settings import settings
WFA_GATE_PATH = Path(settings.DATA_ROOT) / "wfa" / "trade_gate.json"

_GATE_CACHE: dict[str, tuple[float, dict]] = {}


def _load_trade_gate(path=None, return_error=False):
    gate_path = Path(path) if path else WFA_GATE_PATH
    gate_str = str(gate_path)
    if not gate_path.exists():
        if return_error:
            return {}, None
        return {}
    try:
        current_mtime = gate_path.stat().st_mtime
        cached = _GATE_CACHE.get(gate_str)
        if cached is not None and cached[0] == current_mtime:
            state = cached[1]
        else:
            state = json.loads(gate_path.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                if return_error:
                    return {}, "gate_root_not_object"
                return {}
            _GATE_CACHE[gate_str] = (current_mtime, state)

        if return_error:
            return state, None
        return state
    except Exception as exc:
        if return_error:
            return {}, str(exc)
        return {}


def _save_trade_gate(state, path=None):
    gate_path = Path(path) if path else WFA_GATE_PATH
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    return str(gate_path)


def set_trade_permission(ticker, allowed, reason="unspecified", details=None, path=None):
    symbol = str(ticker).upper()
    state = _load_trade_gate(path=path)
    state[symbol] = {
        "allowed": bool(allowed),
        "reason": str(reason),
        "details": details or {},
        "updated_at": pd.Timestamp.utcnow().isoformat(),
    }
    saved_to = _save_trade_gate(state, path=path)
    return state[symbol], saved_to


def get_trade_permission(ticker, path=None, fail_closed=False):
    symbol = str(ticker).upper()
    state, gate_error = _load_trade_gate(path=path, return_error=True)
    if gate_error and fail_closed:
        return {
            "allowed": False,
            "reason": "gate_unreadable",
            "details": {"error": gate_error},
            "updated_at": None,
        }
    item = state.get(symbol)
    if item is None:
        return {"allowed": True, "reason": "no_gate", "details": {}, "updated_at": None}
    if not isinstance(item, dict):
        if fail_closed:
            return {
                "allowed": False,
                "reason": "gate_malformed",
                "details": {"ticker": symbol},
                "updated_at": None,
            }
        return {"allowed": True, "reason": "no_gate", "details": {}, "updated_at": None}
    return item


def _merge_with_global_defaults(strategy_settings):
    """Fallback for missing settings during validation."""
    if strategy_settings is None: return {}
    res = strategy_settings.copy()
    for key, val in settings.__dict__.items():
        if key not in res and not key.startswith("_"):
            res[key] = val
    return res

def _validate_window_settings(ticker, strategy_settings, start, end, df_override):
    """
    Validate optimized settings on out-of-sample data.
    Standalone version for ProcessPoolExecutor.
    """
    merged_settings = _merge_with_global_defaults(strategy_settings)
    lookback = int(merged_settings.get("LOOKBACK", settings.LOOKBACK))
    resistance_col = f"Res_{lookback}"

    df = df_override
    if df is None or df.empty:
        return {
            "total_return_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": 0,
            "bars": 0,
            "win_rate_pct": 0.0,
            "reason": "missing_data",
            "trade_allowed": False,
        }

    valid_mask = (df.index >= start) & (df.index < end)
    test_df = df.loc[valid_mask]

    if len(test_df) < 5:
        return {
            "total_return_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": 0,
            "bars": 0,
            "win_rate_pct": 0.0,
            "reason": "insufficient_data",
            "trade_allowed": False,
        }

    # Vectorized validation using SignalEngine logic
    from core import SignalEngine
    # We need a proper settings object, not just a dict
    class Bag: pass
    set_obj = Bag()
    for k, v in merged_settings.items(): setattr(set_obj, k, v)
    
    signals = SignalEngine.vectorize_signals(test_df, set_obj, resistance_col=resistance_col)
    if signals is None or not signals.any():
        return {
            "total_return_pct": 0.0,
            "sharpe": 0.0,
            "max_drawdown_pct": 0.0,
            "trades": 0,
            "bars": 0,
            "win_rate_pct": 0.0,
            "reason": "no_signals",
            "trade_allowed": False,
        }

    # Extract returns for signals
    trades = signals.sum()
    rets = test_df['Close'].pct_change().shift(-1).fillna(0)
    signal_rets = rets[signals]
    
    total_ret = (1 + signal_rets).prod() - 1
    sharpe = (signal_rets.mean() / signal_rets.std() * np.sqrt(252)) if len(signal_rets) > 1 and signal_rets.std() > 0 else 0
    mdd = (1 - (1 + signal_rets).cumprod() / (1 + signal_rets).cumprod().cummax()).max() if not signal_rets.empty else 0

    return {
        "total_return_pct": float(total_ret * 100),
        "sharpe": float(sharpe),
        "max_drawdown_pct": float(mdd * 100),
        "trades": int(trades),
        "bars": len(test_df),
        "win_rate_pct": float((signal_rets > 0).mean() * 100) if trades > 0 else 0.0,
        "reason": "ok",
        "trade_allowed": total_ret > 0,
    }



class WalkForwardForge:
    def __init__(
        self,
        ticker,
        train_months=6,
        val_months=1,
        step_months=None,
        dynamic_windows=True,
        chaos_factor=0.6,
        atr_lookback_days=30,
        atr_chaos_threshold=0.035,
        min_train_days=75,
        min_val_days=20,
    ):
        if train_months <= 0:
            raise ValueError("train_months must be > 0")
        if val_months <= 0:
            raise ValueError("val_months must be > 0")
        if step_months is not None and step_months <= 0:
            raise ValueError("step_months must be > 0 when provided")
        if not (0 < float(chaos_factor) <= 1):
            raise ValueError("chaos_factor must be in (0, 1]")
        if atr_lookback_days < 5:
            raise ValueError("atr_lookback_days must be >= 5")
        if atr_chaos_threshold <= 0:
            raise ValueError("atr_chaos_threshold must be > 0")

        self.ticker = str(ticker).upper()
        self.train_window = timedelta(days=int(train_months * 30))
        self.val_window = timedelta(days=int(val_months * 30))
        self.step_window = timedelta(days=int((step_months or val_months) * 30))
        self._explicit_step = step_months is not None
        self.dynamic_windows = bool(dynamic_windows)
        self.chaos_factor = float(chaos_factor)
        self.atr_lookback_days = int(atr_lookback_days)
        self.atr_chaos_threshold = float(atr_chaos_threshold)
        self.min_train_days = int(min_train_days)
        self.min_val_days = int(min_val_days)
        self.best_params_history = []
        self._cached_df = None
        self._volatility_df = None

    def run_forge(self, start_date, end_date):
        """
        Rolling forge:
        1) optimize on train window
        2) validate on next unseen window
        3) step forward and repeat
        """
        start_ts = pd.to_datetime(start_date)
        end_ts = pd.to_datetime(end_date)
        if pd.isna(start_ts) or pd.isna(end_ts):
            raise ValueError("start_date and end_date must be valid dates")
        if start_ts >= end_ts:
            raise ValueError("start_date must be earlier than end_date")

        self.best_params_history = []
        current_train_start = start_ts
        self._cached_df = DataManager.get_stock_data(self.ticker, include_live=False)
        self._volatility_df = self._build_volatility_frame(self._cached_df)

        # Pre-calculate ALL indicators for the full history once
        full_lookbacks = Optimizer.PARAM_GRID.get('LOOKBACK', [settings.LOOKBACK])
        indicator_data = {}
        for lb in full_lookbacks:
             indicator_data[lb] = SignalEngine.add_indicators(self._cached_df.copy(), lookback=lb)
        
        # Prepare window schedules
        windows = []
        while True:
            train_span, val_span, atr_ratio, chaos_mode = self._resolve_windows(current_train_start)
            train_end = current_train_start + train_span
            val_end = train_end + val_span
            if val_end > end_ts:
                break
            
            windows.append({
                 "train_start": current_train_start,
                 "train_end": train_end,
                 "val_start": train_end,
                 "val_end": val_end,
                 "atr_ratio": atr_ratio,
                 "chaos_mode": chaos_mode,
                 "train_days": train_span.days,
                 "val_days": val_span.days,
                 "train_span": train_span,
                 "val_span": val_span,
            })
            
            if chaos_mode and not self._explicit_step:
                step_span = val_span
            else:
                step_span = self.step_window
            current_train_start += step_span

        # 4. Execute Serial Window Loop
        results = []
        import time
        cycle_start = time.time()
        
        print(f"Starting WFA Optimization Cycle for {self.ticker} ({len(windows)} windows)...")
        
        for i, win in enumerate(windows):
            win_start = time.time()
            print(f"  Scoring Window {i+1}/{len(windows)}: {win['train_start'].date()} to {win['train_end'].date()}...")
            
            # --- CRITICAL: Slicing for Optimizer ---
            # We need to provide extra buffer for indicators (60 bars before) and post-trade window (30 bars after)
            pad_start = win['train_start'] - timedelta(days=90)
            pad_end = win['train_end'] + timedelta(days=60)
            
            # Extract lookbacks from grid
            lb_grid = Optimizer.PARAM_GRID.get('LOOKBACK', [10, 30, 60])
            
            # Build data pool for this window
            window_stock_data = {
                 'ticker': self.ticker,
                 'index': self._cached_df.index # Replaced below by slice
            }
            
            first_lb = lb_grid[0] if lb_grid else 30
            base_df = indicator_data[first_lb]
            
            # Common columns slice
            mask = (base_df.index >= pad_start) & (base_df.index <= pad_end)
            if mask.sum() < 60:
                 print(f"    Window {i+1} FAILED (Insufficient History Coverage).")
                 continue
                 
            win_base = base_df.loc[mask]
            window_stock_data['index'] = win_base.index
            window_stock_data['length'] = len(win_base)
            
            common_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Move', 'RSI', 'Rel_Vol', 'Avg_Turnover', 'ATR', 'EMA9', 'EFI']
            for col in common_cols:
                 if col in win_base.columns:
                      window_stock_data[col] = win_base[col].to_numpy()
            
            # Lookback-specific columns
            for lb in lb_grid:
                 lb_df = indicator_data.get(lb)
                 if lb_df is not None:
                      win_lb = lb_df.loc[mask]
                      if f'Res_{lb}' in win_lb.columns:
                           window_stock_data[f'Res_{lb}'] = win_lb[f'Res_{lb}'].to_numpy()
                      if f'Sup_{lb}' in win_lb.columns:
                           window_stock_data[f'Sup_{lb}'] = win_lb[f'Sup_{lb}'].to_numpy()
            
            # Run Individual Window Optimization
            best_settings = Optimizer.run_brute_force(
                self.ticker,
                start=win['train_start'],
                end=win['train_end'],
                data_override=[window_stock_data],
                max_workers=None # Uses all cores for chunks
            )
            
            duration = time.time() - win_start
            if best_settings:
                lb = int(best_settings.get("LOOKBACK", settings.LOOKBACK))
                win_df = indicator_data.get(lb, self._cached_df)
                validation = self.validate_settings(best_settings, win["train_end"], win["val_end"], df_override=win_df)
                
                win["params"] = best_settings
                win["val_perf"] = validation
                results.append(win)
                print(f"    Window {i+1} complete in {duration:.1f}s. Profit: {validation.get('total_return_pct', 0):.1f}%")
            else:
                print(f"    Window {i+1} FAILED (No solutions) in {duration:.1f}s.")
                
        total_duration = time.time() - cycle_start
        print(f"WFA Cycle Complete in {total_duration:.1f}s.")
        self.best_params_history = results
        return self.best_params_history

    def validate_settings(self, settings, start, end, df_override=None):
        return _validate_window_settings(self.ticker, settings, start, end, df_override)

    def _merge_with_global_defaults(self, settings):
        return _merge_with_global_defaults(settings)

    @property
    def latest_params(self):
        for item in reversed(self.best_params_history):
            params = item.get("params")
            if params:
                return params
        return None

    @property
    def latest_cycle(self):
        if not self.best_params_history:
            return None
        return self.best_params_history[-1]

    @property
    def latest_trade_allowed(self):
        cycle = self.latest_cycle
        if not cycle:
            return False
        val_perf = cycle.get("val_perf", {})
        return bool(val_perf.get("trade_allowed", False))

    def to_dataframe(self):
        rows = []
        for item in self.best_params_history:
            val_perf = item.get("val_perf", {})
            rows.append(
                {
                    "train_start": item.get("train_start"),
                    "train_end": item.get("train_end"),
                    "val_start": item.get("val_start"),
                    "val_end": item.get("val_end"),
                    "train_days": item.get("train_days"),
                    "val_days": item.get("val_days"),
                    "atr_ratio": item.get("atr_ratio"),
                    "chaos_mode": item.get("chaos_mode"),
                    "params": item.get("params"),
                    "total_return_pct": val_perf.get("total_return_pct", 0.0),
                    "sharpe": val_perf.get("sharpe", 0.0),
                    "max_drawdown_pct": val_perf.get("max_drawdown_pct", 0.0),
                    "trades": val_perf.get("trades", 0),
                    "win_rate_pct": val_perf.get("win_rate_pct", 0.0),
                    "trade_allowed": val_perf.get("trade_allowed", False),
                    "reason": val_perf.get("reason", "unknown"),
                }
            )
        return pd.DataFrame(rows)

    def save_history(self, path=None):
        target = Path(path) if path else Path(settings.DATA_ROOT) / "wfa" / f"{self.ticker}_wfa_history.json"
        target.parent.mkdir(parents=True, exist_ok=True)

        serializable = []
        for item in self.best_params_history:
            serializable.append(
                {
                    "train_start": pd.to_datetime(item["train_start"]).isoformat(),
                    "train_end": pd.to_datetime(item["train_end"]).isoformat(),
                    "val_start": pd.to_datetime(item["val_start"]).isoformat(),
                    "val_end": pd.to_datetime(item["val_end"]).isoformat(),
                    "train_days": item.get("train_days"),
                    "val_days": item.get("val_days"),
                    "atr_ratio": item.get("atr_ratio"),
                    "chaos_mode": item.get("chaos_mode"),
                    "params": item.get("params"),
                    "val_perf": item.get("val_perf"),
                }
            )

        with target.open("w", encoding="utf-8") as f:
            import json
            json.dump(serializable, f, indent=2)

        return str(target)

    def _build_volatility_frame(self, base_df):
        if base_df is None or base_df.empty:
            return None
        try:
            vol_df = base_df.copy()
            if "ATR" not in vol_df.columns:
                vol_df = SignalEngine.add_indicators(vol_df, lookback=max(14, settings.LOOKBACK))
            return vol_df
        except Exception:
            return None

    def _atr_ratio_at(self, anchor_ts):
        if self._volatility_df is None or self._volatility_df.empty:
            return None
        start = anchor_ts - timedelta(days=self.atr_lookback_days)
        window = self._volatility_df.loc[(self._volatility_df.index >= start) & (self._volatility_df.index < anchor_ts)]
        if len(window) < 5:
            fallback_end = anchor_ts + timedelta(days=self.atr_lookback_days)
            window = self._volatility_df.loc[(self._volatility_df.index >= anchor_ts) & (self._volatility_df.index <= fallback_end)]
        if len(window) < 5 or "ATR" not in window.columns or "Close" not in window.columns:
            return None
        ratio = (window["ATR"] / window["Close"]).replace([np.inf, -np.inf], np.nan).dropna()
        if ratio.empty:
            return None
        return float(ratio.tail(self.atr_lookback_days).mean())

    def _resolve_windows(self, current_train_start):
        train_span = self.train_window
        val_span = self.val_window
        atr_ratio = self._atr_ratio_at(current_train_start)
        chaos_mode = False
        if self.dynamic_windows and atr_ratio is not None and atr_ratio >= self.atr_chaos_threshold:
            chaos_mode = True
            train_days = max(self.min_train_days, int(round(train_span.days * self.chaos_factor)))
            val_days = max(self.min_val_days, int(round(val_span.days * self.chaos_factor)))
            train_span = timedelta(days=train_days)
            val_span = timedelta(days=val_days)
        return train_span, val_span, atr_ratio, chaos_mode


def apply_evolved_params(
    ticker,
    start_date,
    end_date,
    train_months=6,
        val_months=1,
        step_months=None,
        dynamic_windows=True,
        chaos_factor=0.6,
        atr_lookback_days=30,
        atr_chaos_threshold=0.035,
        preset_name=None,
        persist_history=True,
        gate_path=None,
):
    """
    Run WFA, then apply the latest evolved parameters to 
    """
    forge = WalkForwardForge(
        ticker=ticker,
        train_months=train_months,
        val_months=val_months,
        step_months=step_months,
        dynamic_windows=dynamic_windows,
        chaos_factor=chaos_factor,
        atr_lookback_days=atr_lookback_days,
        atr_chaos_threshold=atr_chaos_threshold,
    )
    history = forge.run_forge(start_date, end_date)
    latest_cycle = forge.latest_cycle
    latest = forge.latest_params
    history_path = forge.save_history() if persist_history else None

    if not latest_cycle or not latest:
        gate_record, gate_file = set_trade_permission(
            ticker=ticker,
            allowed=False,
            reason="no_evolved_params",
            details={"history_points": len(history)},
            path=gate_path,
        )
        return {
            "applied": False,
            "reason": "no_evolved_params",
            "history_points": len(history),
            "history_path": history_path,
            "gate": gate_record,
            "gate_path": gate_file,
        }

    latest_val = latest_cycle.get("val_perf", {})
    if not bool(latest_val.get("trade_allowed", False)):
        gate_record, gate_file = set_trade_permission(
            ticker=ticker,
            allowed=False,
            reason=latest_val.get("reason", "validation_loss_blocked"),
            details=latest_val,
            path=gate_path,
        )
        return {
            "applied": False,
            "reason": latest_val.get("reason", "validation_loss_blocked"),
            "history_points": len(history),
            "history_path": history_path,
            "latest_validation": latest_val,
            "gate": gate_record,
            "gate_path": gate_file,
        }

    keys_to_apply = (
        "LOOKBACK",
        "VOL_SPIKE",
        "MOMENTUM",
        "RSI_MIN",
        "RSI_MAX",
        "SL_PCT",
        "TP1_PCT",
        "MIN_TURNOVER",
        "TRAILING_STOP_ENABLED",
        "TRAILING_STOP_TYPE",
        "TRAILING_STOP_VALUE",
        "USE_ATR_EXITS",
        "ATR_TP_MULTIPLIER",
        "ATR_SL_MULTIPLIER",
        "TRICKSTER_RSI_MAX",
        "TRICKSTER_REL_VOL_MIN",
        "TRICKSTER_STRETCH_ATR",
    )

    merged_latest = forge._merge_with_global_defaults(latest)
    applied = {}
    for key in keys_to_apply:
        if key not in merged_latest or not hasattr(settings, key):
            continue

        current = getattr(settings, key)
        value = merged_latest[key]
        if isinstance(current, bool):
            casted = bool(value)
        elif isinstance(current, int) and not isinstance(current, bool):
            casted = int(value)
        elif isinstance(current, float):
            casted = float(value)
        else:
            casted = value

        setattr(settings, key, casted)
        applied[key] = casted

    preset = preset_name or f"WFA_{str(ticker).upper()}"
    if applied:
        settings.save_settings(preset_name=preset)

    gate_record, gate_file = set_trade_permission(
        ticker=ticker,
        allowed=True,
        reason="validation_profitable",
        details=latest_val,
        path=gate_path,
    )
    return {
        "applied": bool(applied),
        "applied_params": applied,
        "history_points": len(history),
        "history_path": history_path,
        "latest_validation": latest_val,
        "gate": gate_record,
        "gate_path": gate_file,
        "preset_name": preset,
    }
