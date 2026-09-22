from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


_SERIES_COLUMNS = {
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
}

_TIMEFRAME_RULES = {
    "1D": ("D", 1),
    "D": ("D", 1),
    "DAILY": ("D", 1),
    "1W": ("W-FRI", 2),
    "W": ("W-FRI", 2),
    "WEEKLY": ("W-FRI", 2),
    "1M": ("ME", 3),
    "M": ("ME", 3),
    "1MO": ("ME", 3),
    "MONTHLY": ("ME", 3),
}


def _constant_series(index: pd.Index, value: Any) -> pd.Series:
    return pd.Series([value] * len(index), index=index)


def _ensure_series(value: pd.Series | int | float | bool, index: pd.Index) -> pd.Series:
    if isinstance(value, pd.Series):
        return value.reindex(index)
    return _constant_series(index, value)


def _compute_rsi(series: pd.Series, length: int) -> pd.Series:
    delta = series.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)
    avg_gain = gains.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = losses.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    relative_strength = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + relative_strength))
    rsi = rsi.where(avg_loss != 0, 100.0)
    rsi = rsi.where(avg_gain != 0, 0.0)
    return rsi.astype(float)


def _compute_macd(series: pd.Series, fast_length: int, slow_length: int, signal_length: int) -> tuple[pd.Series, pd.Series, pd.Series]:
    fast_ema = series.ewm(span=fast_length, adjust=False).mean()
    slow_ema = series.ewm(span=slow_length, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_length, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line.astype(float), signal_line.astype(float), histogram.astype(float)


def _normalize_length(value: pd.Series | int | float | bool, index: pd.Index) -> int:
    length = int(_ensure_series(value, index).iloc[0])
    if length < 1:
        raise ValueError(f"Unsupported rolling length: {length}")
    return length


def _compute_wma(series: pd.Series, length: int) -> pd.Series:
    weights = np.arange(1, length + 1, dtype=float)
    weight_sum = float(weights.sum())
    return series.rolling(length, min_periods=length).apply(lambda values: float(np.dot(values, weights) / weight_sum), raw=True)


def _compute_vwma(series: pd.Series, volume: pd.Series, length: int) -> pd.Series:
    numerator = (series * volume).rolling(length, min_periods=length).sum()
    denominator = volume.rolling(length, min_periods=length).sum().replace(0, np.nan)
    return (numerator / denominator).astype(float)


def _compute_stdev(series: pd.Series, length: int) -> pd.Series:
    return series.rolling(length, min_periods=length).std(ddof=0).astype(float)


def _compute_true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    previous_close = close.shift(1)
    components = pd.concat(
        [
            (high - low).abs(),
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    )
    return components.max(axis=1).astype(float)


def _compute_rma(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(alpha=1 / length, min_periods=length, adjust=False).mean().astype(float)


def _compute_atr(df: pd.DataFrame, length: int) -> pd.Series:
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    close = df["Close"].astype(float)
    true_range = _compute_true_range(high, low, close)
    return _compute_rma(true_range, length)


def _compute_linreg(series: pd.Series, length: int, offset: float) -> pd.Series:
    x = np.arange(length, dtype=float)
    x_mean = float(x.mean())
    denominator = float(np.sum((x - x_mean) ** 2))
    projection_index = (length - 1) - float(offset)

    def project(values: np.ndarray) -> float:
        y = np.asarray(values, dtype=float)
        y_mean = float(y.mean())
        slope = float(np.dot(x - x_mean, y - y_mean) / denominator) if denominator else 0.0
        intercept = y_mean - (slope * x_mean)
        return intercept + (slope * projection_index)

    return series.rolling(length, min_periods=length).apply(project, raw=True).astype(float)


def _compute_alma(series: pd.Series, length: int, offset: float, sigma: float) -> pd.Series:
    sigma_value = float(sigma)
    if sigma_value <= 0:
        raise ValueError(f"Unsupported ALMA sigma: {sigma}")
    m = offset * (length - 1)
    s = length / sigma_value
    weights = np.exp(-((np.arange(length, dtype=float) - m) ** 2) / (2 * s * s))
    weights = weights / weights.sum()
    return series.rolling(length, min_periods=length).apply(lambda values: float(np.dot(values, weights)), raw=True).astype(float)


def _compute_supertrend(source: pd.Series, factor: float, atr: pd.Series) -> tuple[pd.Series, pd.Series]:
    index = source.index
    upper_band = (source + (factor * atr)).astype(float)
    lower_band = (source - (factor * atr)).astype(float)
    trend_line = pd.Series(index=index, dtype=float)
    direction = pd.Series(index=index, dtype=float)

    for position in range(len(index)):
        if position == 0:
            direction.iloc[position] = 1.0
            trend_line.iloc[position] = upper_band.iloc[position]
            continue

        previous_lower = lower_band.iloc[position - 1] if pd.notna(lower_band.iloc[position - 1]) else lower_band.iloc[position]
        previous_upper = upper_band.iloc[position - 1] if pd.notna(upper_band.iloc[position - 1]) else upper_band.iloc[position]

        current_lower = lower_band.iloc[position]
        current_upper = upper_band.iloc[position]
        previous_close = source.iloc[position - 1]

        if pd.notna(previous_lower) and not (current_lower > previous_lower or previous_close < previous_lower):
            current_lower = previous_lower
        if pd.notna(previous_upper) and not (current_upper < previous_upper or previous_close > previous_upper):
            current_upper = previous_upper

        lower_band.iloc[position] = current_lower
        upper_band.iloc[position] = current_upper

        previous_trend_line = trend_line.iloc[position - 1]
        if pd.isna(atr.iloc[position - 1]):
            current_direction = 1.0
        elif previous_trend_line == previous_upper:
            current_direction = -1.0 if source.iloc[position] > current_upper else 1.0
        else:
            current_direction = 1.0 if source.iloc[position] < current_lower else -1.0

        direction.iloc[position] = current_direction
        trend_line.iloc[position] = current_lower if current_direction == -1.0 else current_upper

    return trend_line.astype(float), direction.astype(float)


def _normalize_timeframe_config(value: str | None) -> tuple[str, int] | None:
    token = str(value or "").strip().upper()
    if token in _TIMEFRAME_RULES:
        return _TIMEFRAME_RULES.get(token)
    if token.isdigit():
        minutes = int(token)
        if minutes < 1:
            return None
        return (f"{minutes}min", minutes)
    return None


def _is_intraday_timeframe(value: str | None) -> bool:
    token = str(value or "").strip().upper()
    return token.isdigit() and int(token) > 0


def _infer_intraday_step_minutes(df: pd.DataFrame) -> int | None:
    if df is None or df.empty or not isinstance(df.index, pd.DatetimeIndex) or len(df.index) < 2:
        return None
    deltas = df.index.to_series().diff().dropna()
    if deltas.empty:
        return None
    median_delta = deltas.median()
    if pd.isna(median_delta):
        return None
    minutes = int(round(median_delta.total_seconds() / 60.0))
    return minutes if minutes > 0 else None


def _extract_literal_value(expression: dict[str, Any], definitions: dict[str, dict[str, Any]], stack: tuple[str, ...] = ()) -> Any:
    node_type = expression.get("node_type")
    if node_type == "LITERAL":
        return expression.get("value")
    if node_type == "VARIABLE_REF":
        name = str(expression.get("name") or "")
        if name in stack or name not in definitions:
            raise ValueError("request.security only supports literal symbol/timeframe arguments in this phase.")
        return _extract_literal_value(definitions[name], definitions, (*stack, name))
    raise ValueError("request.security only supports literal symbol/timeframe arguments in this phase.")


def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    resampled = df.resample(rule, label="right", closed="right").agg(
        {
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum",
        }
    )
    return resampled.dropna(subset=["Open", "High", "Low", "Close"]).copy()


def evaluate_expression_node(
    expression: dict[str, Any],
    df: pd.DataFrame,
    definitions: dict[str, dict[str, Any]],
    cache: dict[str, pd.Series] | None = None,
    *,
    base_timeframe: str = "1D",
    source_df: pd.DataFrame | None = None,
) -> pd.Series:
    cache = cache if cache is not None else {}
    index = df.index
    node_type = expression.get("node_type")

    if node_type == "SERIES_REF":
        column = _SERIES_COLUMNS.get(str(expression.get("name") or "").lower())
        if column is None or column not in df.columns:
            raise ValueError(f'Unsupported series reference "{expression.get("name")}".')
        return df[column].astype(float)

    if node_type == "VARIABLE_REF":
        name = str(expression.get("name") or "")
        if name in cache:
            return cache[name]
        if name not in definitions:
            raise ValueError(f'Blocked: condition depends on unresolved variable "{name}".')
        resolved = evaluate_expression_node(definitions[name], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df)
        cache[name] = resolved
        return resolved

    if node_type == "HISTORY_REF":
        source = _ensure_series(
            evaluate_expression_node(expression.get("source") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        )
        bars_ago_value = expression.get("bars_ago")
        if isinstance(bars_ago_value, dict):
            bars_ago = int(_ensure_series(evaluate_expression_node(bars_ago_value, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df), index).iloc[0])
        else:
            bars_ago = int(bars_ago_value or 0)
        if bars_ago < 0:
            raise ValueError(f"Unsupported history offset: {bars_ago}")
        return source.shift(bars_ago)

    if node_type == "LITERAL":
        return _constant_series(index, expression.get("value"))

    if node_type == "IF_EXPR":
        condition = _ensure_series(
            evaluate_expression_node(expression.get("condition") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        ).fillna(False).astype(bool)
        when_true = _ensure_series(
            evaluate_expression_node(expression.get("when_true") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        )
        when_false = _ensure_series(
            evaluate_expression_node(expression.get("when_false") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        )
        return when_true.where(condition, when_false)

    if node_type == "STATE_VAR":
        initial = _ensure_series(
            evaluate_expression_node(expression.get("initial") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        )
        updates = [
            (
                _ensure_series(
                    evaluate_expression_node(update.get("condition") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
                    index,
                ).fillna(False).astype(bool),
                _ensure_series(
                    evaluate_expression_node(update.get("value") or {}, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
                    index,
                ),
            )
            for update in expression.get("updates", [])
        ]
        state = pd.Series(index=index, dtype=object)
        for position in range(len(index)):
            current = initial.iloc[position] if position == 0 else state.iloc[position - 1]
            for condition_series, value_series in updates:
                if bool(condition_series.iloc[position]):
                    current = value_series.iloc[position]
            state.iloc[position] = current
        return state

    if node_type == "TUPLE_ITEM":
        source = expression.get("source") or {}
        source_name = str(source.get("name") or "")
        if source.get("node_type") != "CALL" or source_name not in {"ta.macd", "horus.supertrend"}:
            raise ValueError(f"Unsupported tuple source: {source_name or source.get('node_type')}")
        cache_key = f"__tuple__{repr(source)}"
        if cache_key not in cache:
            args = [evaluate_expression_node(arg, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df) for arg in source.get("args", [])]
            if source_name == "ta.macd":
                input_series = _ensure_series(args[0], index).astype(float)
                fast_length = int(_ensure_series(args[1], index).iloc[0])
                slow_length = int(_ensure_series(args[2], index).iloc[0])
                signal_length = int(_ensure_series(args[3], index).iloc[0])
                cache[cache_key] = _compute_macd(input_series, fast_length, slow_length, signal_length)
            else:
                input_series = _ensure_series(args[0], index).astype(float)
                factor = float(_ensure_series(args[1], index).iloc[0])
                atr_length = int(_ensure_series(args[2], index).iloc[0])
                atr = _compute_atr(df, atr_length)
                cache[cache_key] = _compute_supertrend(input_series, factor, atr)
        tuple_values = cache[cache_key]
        return tuple_values[int(expression.get("index", 0))]

    if node_type == "CALL":
        name = str(expression.get("name") or "")
        raw_args = list(expression.get("args") or [])
        if name == "request.security":
            if len(raw_args) < 3:
                raise ValueError("Blocked: wrapped request.security helper patterns are not supported in this phase.")

            symbol_value = str(_extract_literal_value(raw_args[0], definitions) or "").strip()
            timeframe_value = str(_extract_literal_value(raw_args[1], definitions) or "").strip()
            if symbol_value.lower() != "syminfo.tickerid":
                raise ValueError("Blocked: request.security only supports same-symbol imports in this phase.")

            base_config = _normalize_timeframe_config(base_timeframe)
            request_config = _normalize_timeframe_config(timeframe_value)
            if base_config is None or request_config is None:
                raise ValueError("Blocked: request.security deterministic MTF runtime is not available yet.")

            _, base_rank = base_config
            request_rule, request_rank = request_config
            if request_rank < base_rank:
                if not (_is_intraday_timeframe(timeframe_value) and _is_intraday_timeframe(base_timeframe)):
                    raise ValueError("Blocked: request.security lower-timeframe imports are only supported for intraday strategies in this phase.")
                upstream_df = source_df if source_df is not None else df
                source_step_minutes = _infer_intraday_step_minutes(upstream_df)
                if source_step_minutes is None or source_step_minutes > request_rank:
                    raise ValueError("Blocked: request.security deterministic MTF runtime is not available yet.")
            elif request_rank == base_rank and str(timeframe_value).strip().upper() != str(base_timeframe or "").strip().upper():
                raise ValueError("Blocked: request.security only supports higher-timeframe imports in this phase.")

            cache_key = f"__request_security__{base_timeframe}__{request_rule}__{repr(expression)}"
            if cache_key in cache:
                return cache[cache_key]

            upstream_df = source_df if source_df is not None else df
            resampled_df = upstream_df if request_rank == base_rank else _resample_ohlcv(upstream_df, request_rule)
            imported = evaluate_expression_node(
                raw_args[2],
                resampled_df,
                definitions,
                {},
                base_timeframe=timeframe_value,
                source_df=upstream_df,
            )
            aligned = imported.reindex(index, method="ffill")
            cache[cache_key] = aligned
            return aligned

        args = [evaluate_expression_node(arg, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df) for arg in raw_args]
        if name == "ta.sma":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return source.rolling(length).mean()
        if name == "ta.ema":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return source.ewm(span=length, adjust=False).mean()
        if name == "ta.rsi":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return _compute_rsi(source, length)
        if name == "ta.stdev":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return _compute_stdev(source, length)
        if name == "ta.atr":
            length = _normalize_length(args[0], index)
            return _compute_atr(df, length)
        if name == "ta.highest":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return source.rolling(length, min_periods=length).max()
        if name == "ta.lowest":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return source.rolling(length, min_periods=length).min()
        if name == "ta.macd":
            raise ValueError("ta.macd tuple outputs must be unpacked before evaluation.")
        if name == "ta.wma":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            return _compute_wma(source, length)
        if name == "ta.vwma":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            volume = df["Volume"].astype(float)
            return _compute_vwma(source, volume, length)
        if name == "ta.linreg":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            offset = float(_ensure_series(args[2], index).iloc[0])
            return _compute_linreg(source, length, offset)
        if name == "ta.alma":
            source = _ensure_series(args[0], index).astype(float)
            length = _normalize_length(args[1], index)
            offset = float(_ensure_series(args[2], index).iloc[0])
            sigma = float(_ensure_series(args[3], index).iloc[0])
            return _compute_alma(source, length, offset, sigma)
        if name == "math.abs":
            source = _ensure_series(args[0], index)
            return source.abs()
        if name == "math.floor":
            source = _ensure_series(args[0], index).astype(float)
            return np.floor(source)
        if name == "horus.supertrend":
            raise ValueError("horus.supertrend tuple outputs must be unpacked before evaluation.")
        if name == "ta.crossover":
            left = _ensure_series(args[0], index).astype(float)
            right = _ensure_series(args[1], index).astype(float)
            return ((left.shift(1) <= right.shift(1)) & (left > right)).fillna(False)
        if name == "ta.crossunder":
            left = _ensure_series(args[0], index).astype(float)
            right = _ensure_series(args[1], index).astype(float)
            return ((left.shift(1) >= right.shift(1)) & (left < right)).fillna(False)
        raise ValueError(f"Unsupported expression call: {name}")

    if node_type == "COMPARE":
        left = _ensure_series(evaluate_expression_node(expression["left"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df), index)
        right = _ensure_series(evaluate_expression_node(expression["right"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df), index)
        operator = expression.get("operator")
        operations = {
            ">": left > right,
            ">=": left >= right,
            "<": left < right,
            "<=": left <= right,
            "==": left == right,
            "!=": left != right,
        }
        result = operations.get(operator)
        if result is None:
            raise ValueError(f"Unsupported comparison operator: {operator}")
        return result.fillna(False)

    if node_type == "BINARY_OP":
        left = _ensure_series(
            evaluate_expression_node(expression["left"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        ).astype(float)
        right = _ensure_series(
            evaluate_expression_node(expression["right"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df),
            index,
        ).astype(float)
        operator = expression.get("operator")
        operations = {
            "+": left + right,
            "-": left - right,
            "*": left * right,
            "/": left / right.replace(0, np.nan),
        }
        result = operations.get(operator)
        if result is None:
            raise ValueError(f"Unsupported binary operator: {operator}")
        return result

    if node_type == "BOOL_OP":
        operands = [
            _ensure_series(evaluate_expression_node(operand, df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df), index).fillna(False).astype(bool)
            for operand in expression.get("operands", [])
        ]
        if not operands:
            return _constant_series(index, False)
        result = operands[0]
        operator = expression.get("operator")
        for operand in operands[1:]:
            if operator == "and":
                result = result & operand
            elif operator == "or":
                result = result | operand
            else:
                raise ValueError(f"Unsupported boolean operator: {operator}")
        return result.fillna(False)

    if node_type == "UNARY_OP":
        operand = _ensure_series(evaluate_expression_node(expression["operand"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df), index).fillna(False).astype(bool)
        if expression.get("operator") != "not":
            raise ValueError(f'Unsupported unary operator: {expression.get("operator")}')
        return (~operand).fillna(False)

    raise ValueError(f"Unsupported expression node type: {node_type}")


def evaluate_signal_plan(
    df: pd.DataFrame,
    plan: dict[str, Any],
    *,
    base_timeframe: str = "1D",
    source_df: pd.DataFrame | None = None,
) -> tuple[pd.Series, pd.Series]:
    definitions = dict(plan.get("definitions") or {})
    cache: dict[str, pd.Series] = {}
    entries = evaluate_expression_node(plan["entry_expression"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df).fillna(False).astype(bool)
    exits = evaluate_expression_node(plan["exit_expression"], df, definitions, cache, base_timeframe=base_timeframe, source_df=source_df).fillna(False).astype(bool)
    return entries, exits
