from typing import Any
from fastapi import HTTPException
import pandas as pd
from core.settings import settings
from core import TimeUtils
from core.DataManager import DataManager
from core.simulation import PortfolioSimulator
from core.price_action.models import PriceActionStrategyFamily, PriceActionStrategyStatus

VALID_INDEX_CHOICES = {
    "ALL": "ALL",
    "30": "EGX30",
    "70": "EGX70",
    "100": "EGX100",
    "EGX30": "EGX30",
    "EGX70": "EGX70",
    "EGX100": "EGX100",
}

NUMERIC_PARAM_RANGES = {
    "LOOKBACK": (1.0, 365.0),
    "VOL_SPIKE": (0.1, 50.0),
    "MOMENTUM": (0.0, 50.0),
    "RSI_MIN": (0.0, 100.0),
    "RSI_MAX": (0.0, 100.0),
    "SL_PCT": (0.1, 50.0),
    "TP1_PCT": (0.1, 200.0),
    "MIN_TURNOVER": (0.0, None),
    "TRICKSTER_RSI_MAX": (0.0, 100.0),
    "TRICKSTER_REL_VOL_MIN": (0.0, 20.0),
    "TRICKSTER_STRETCH_ATR": (0.0, 20.0),
    "MAX_POSITIONS": (1.0, 100.0),
    "MAX_DAILY_TRADES": (1.0, 100.0),
    "RISK_PER_TRADE": (0.1, 100.0),
    "MIN_RISK_REWARD": (0.0, 100.0),
    "MIN_SIGNAL_SCORE": (0.0, 10.0),
    "MIN_SIGNAL_CONFIDENCE": (0.0, 100.0),
    "MAX_PORTFOLIO_HEAT": (0.1, 100.0),
    "PENDING_ENTRY_MAX_GAP_PCT": (0.1, 100.0),
    "MAX_PER_SECTOR": (1.0, 100.0),
    "TRAILING_STOP_VALUE": (0.1, 100.0),
    "ATR_TP_MULTIPLIER": (0.1, 20.0),
    "ATR_SL_MULTIPLIER": (0.1, 20.0),
    "COMMISSION_PCT": (0.0, 100.0),
    "SLIPPAGE_PCT": (0.0, 100.0),
    "ACCOUNT_BALANCE": (1.0, None),
    "ACCOUNT_BALANCE_USD": (0.0, None),
}

INT_PARAMS = {"LOOKBACK", "MAX_POSITIONS", "MAX_DAILY_TRADES", "MAX_PER_SECTOR"}
BOOL_PARAMS = {
    "TRAILING_STOP_ENABLED",
    "REGIME_FILTER_ENABLED",
    "SECTOR_LIMIT_ENABLED",
    "USE_ATR_EXITS",
    "AUTO_TRADE_ENABLED",
}
ENUM_PARAMS = {
    "TRAILING_STOP_TYPE": {"PERCENT", "ATR", "FIXED"},
    "REGIME_MODE": {"AUTO", "BULLISH", "CAUTIOUS", "BEARISH"},
}

def _normalize_index_choice(index: Any) -> str:
    key = str(index or "ALL").strip().upper()
    normalized = VALID_INDEX_CHOICES.get(key)
    if normalized is None:
        allowed = ", ".join(sorted(set(VALID_INDEX_CHOICES.values())))
        raise HTTPException(status_code=400, detail=f"Invalid index '{index}'. Allowed: {allowed}")
    return normalized

def _coerce_float(name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise HTTPException(status_code=400, detail=f"{name} must be numeric")
    try:
        return float(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"{name} must be numeric")

def _require_nonzero_cost_assumptions(payload: dict[str, Any]) -> tuple[float, float]:
    commission_pct = _coerce_float(
        "commission_pct",
        payload.get("commission_pct", getattr(settings, "COMMISSION_PCT", 0.0)),
    )
    slippage_pct = _coerce_float(
        "slippage_pct",
        payload.get("slippage_pct", getattr(settings, "SLIPPAGE_PCT", 0.0)),
    )
    if commission_pct <= 0:
        raise HTTPException(
            status_code=400,
            detail="commission_pct must be > 0 for realistic execution costs.",
        )
    if slippage_pct <= 0:
        raise HTTPException(
            status_code=400,
            detail="slippage_pct must be > 0 for realistic execution costs.",
        )
    return float(commission_pct), float(slippage_pct)

def _coerce_bool(name: str, value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    raise HTTPException(status_code=400, detail=f"{name} must be a boolean")

def _normalize_strategy_params(raw_params: Any) -> dict:
    if raw_params is None:
        return {}
    if not isinstance(raw_params, dict):
        raise HTTPException(status_code=400, detail="params must be an object")

    normalized: dict[str, Any] = {}
    for key, value in raw_params.items():
        param = str(key).strip().upper()
        if param in BOOL_PARAMS:
            normalized[param] = _coerce_bool(param, value)
            continue
        if param in ENUM_PARAMS:
            enum_value = str(value).strip().upper()
            if enum_value not in ENUM_PARAMS[param]:
                allowed = ", ".join(sorted(ENUM_PARAMS[param]))
                raise HTTPException(status_code=400, detail=f"{param} must be one of: {allowed}")
            normalized[param] = enum_value
            continue
        if param in NUMERIC_PARAM_RANGES:
            number = _coerce_float(param, value)
            min_value, max_value = NUMERIC_PARAM_RANGES[param]
            if number < min_value or (max_value is not None and number > max_value):
                upper = f" and <= {max_value}" if max_value is not None else ""
                raise HTTPException(status_code=400, detail=f"{param} must be >= {min_value}{upper}")
            if param in INT_PARAMS:
                normalized[param] = int(round(number))
            else:
                normalized[param] = number
            continue
        # Preserve unknown params to avoid breaking existing integrations.
        normalized[param] = value

    effective_rsi_min = float(normalized.get("RSI_MIN", getattr(settings, "RSI_MIN", 0.0)))
    effective_rsi_max = float(normalized.get("RSI_MAX", getattr(settings, "RSI_MAX", 100.0)))
    if effective_rsi_min >= effective_rsi_max:
        raise HTTPException(status_code=400, detail="RSI_MIN must be less than RSI_MAX")

    trailing_enabled = bool(normalized.get("TRAILING_STOP_ENABLED", getattr(settings, "TRAILING_STOP_ENABLED", False)))
    trailing_value = float(normalized.get("TRAILING_STOP_VALUE", getattr(settings, "TRAILING_STOP_VALUE", 0.0)))
    if trailing_enabled and trailing_value <= 0:
        raise HTTPException(status_code=400, detail="TRAILING_STOP_VALUE must be > 0 when trailing stop is enabled")

    return normalized

def _normalize_capital(value: Any) -> float:
    capital = _coerce_float("capital", value)
    if capital <= 0:
        raise HTTPException(status_code=400, detail="capital must be > 0")
    return capital

def _normalize_date_field(payload: dict[str, Any], field_name: str) -> str:
    raw = _require_text_field(payload, field_name)
    try:
        return pd.Timestamp(raw).strftime("%Y-%m-%d")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{field_name} must be a valid date") from exc

def _resolve_backtest_window(payload: dict[str, Any]) -> tuple[str, str]:
    start_provided = payload.get("start_date") is not None
    end_provided = payload.get("end_date") is not None

    if start_provided:
        start_ts = pd.Timestamp(_normalize_date_field(payload, "start_date"))
    else:
        baseline_start = str(getattr(PortfolioSimulator, "START_DATE", "2025-01-01"))
        start_ts = pd.Timestamp(baseline_start)

    if end_provided:
        end_ts = pd.Timestamp(_normalize_date_field(payload, "end_date"))
    else:
        end_ts = pd.Timestamp(TimeUtils.now().date())
        try:
            status = DataManager.get_data_status()
            last_updated_raw = status.get("last_updated") if isinstance(status, dict) else None
            if last_updated_raw:
                data_last_ts = pd.Timestamp(str(last_updated_raw)[:10])
                if not pd.isna(data_last_ts):
                    end_ts = min(end_ts, data_last_ts)
        except Exception:
            # Keep clock-based end date if freshness metadata is unavailable.
            pass

    if pd.isna(start_ts) or pd.isna(end_ts):
        raise HTTPException(status_code=400, detail="Backtest date window is invalid.")

    if start_ts > end_ts:
        raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date.")

    return start_ts.strftime("%Y-%m-%d"), end_ts.strftime("%Y-%m-%d")

def _normalize_optional_positive_int(payload: dict[str, Any], field_name: str) -> int | None:
    if field_name not in payload or payload.get(field_name) is None:
        return None
    raw_value = payload.get(field_name)
    if isinstance(raw_value, bool):
        raise HTTPException(status_code=400, detail=f"{field_name} must be numeric")
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"{field_name} must be numeric") from exc
    if value <= 0:
        raise HTTPException(status_code=400, detail=f"{field_name} must be > 0")
    return value

def _require_text_field(payload: dict[str, Any], field_name: str) -> str:
    value = str(payload.get(field_name) or "").strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{field_name} is required")
    return value

def _coerce_object(payload: dict[str, Any], field_name: str) -> dict[str, Any]:
    value = payload.get(field_name) or {}
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail=f"{field_name} must be an object")
    return value

def _normalize_backtest_summary_payload(backtest_payload: dict[str, Any]) -> dict[str, Any]:
    metrics = backtest_payload.get("metrics")
    if not isinstance(metrics, dict):
        return dict(backtest_payload or {})

    assumptions = backtest_payload.get("assumptions") if isinstance(backtest_payload.get("assumptions"), dict) else {}
    config = backtest_payload.get("config") if isinstance(backtest_payload.get("config"), dict) else {}
    walk_forward = backtest_payload.get("walk_forward") if isinstance(backtest_payload.get("walk_forward"), dict) else {}
    promotion_artifacts = backtest_payload.get("promotion_artifacts") if isinstance(backtest_payload.get("promotion_artifacts"), dict) else {}
    promotion_summary = backtest_payload.get("promotion_summary") if isinstance(backtest_payload.get("promotion_summary"), dict) else {}

    normalized = dict(metrics)
    normalized["commission_pct"] = float(assumptions.get("commission_pct", 0.0) or 0.0)
    normalized["slippage_pct"] = float(assumptions.get("slippage_pct", 0.0) or 0.0)
    normalized["costs"] = {
        "commission_pct": normalized["commission_pct"],
        "slippage_pct": normalized["slippage_pct"],
    }
    normalized["date_from"] = config.get("date_from")
    normalized["date_to"] = config.get("date_to")
    normalized["market"] = config.get("market")
    normalized["timeframe"] = config.get("timeframe")
    normalized["walk_forward_pass"] = bool(walk_forward.get("pass", normalized.get("walk_forward_pass", False)))
    oos = walk_forward.get("out_of_sample") if isinstance(walk_forward.get("out_of_sample"), dict) else {}
    normalized["oos_trade_count"] = int(oos.get("trade_count", normalized.get("oos_trade_count", 0)) or 0)
    normalized["oos_total_return"] = float(oos.get("total_return", normalized.get("oos_total_return", 0.0)) or 0.0)
    if promotion_artifacts:
        normalized["promotion_artifacts"] = promotion_artifacts
    if isinstance(promotion_summary.get("failed_gates"), list):
        normalized["failed_gates"] = list(promotion_summary.get("failed_gates") or [])
    return normalized

def _normalize_price_action_family(value: Any) -> PriceActionStrategyFamily:
    normalized = str(value or "").strip().upper()
    try:
        return PriceActionStrategyFamily(normalized)
    except ValueError as exc:
        allowed = ", ".join(family.value for family in PriceActionStrategyFamily)
        raise HTTPException(status_code=400, detail=f"family must be one of: {allowed}") from exc

def _normalize_price_action_status(value: Any) -> PriceActionStrategyStatus:
    normalized = str(value or "").strip().upper()
    try:
        return PriceActionStrategyStatus(normalized)
    except ValueError as exc:
        allowed = ", ".join(status.value for status in PriceActionStrategyStatus)
        raise HTTPException(status_code=400, detail=f"status must be one of: {allowed}") from exc
