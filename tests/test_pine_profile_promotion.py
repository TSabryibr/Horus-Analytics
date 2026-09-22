from fastapi.testclient import TestClient
import pandas as pd

from api import app
from core.pine_lab.executor import run_pine_backtest
from database import Portfolio, db


client = TestClient(app, raise_server_exceptions=False)


def test_pine_preflight_detects_strategy_entry_and_exit():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Breakout", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["compatibility_score"] > 0
    assert body["detected_entries"]
    assert body["detected_exits"]


def test_pine_preflight_returns_expression_plan_scaffolding_for_supported_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Plan Scaffold", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "READY"
    assert body["execution_mode"] == "LONG_ONLY"
    assert "ta.sma" in body["supported_nodes"]
    assert "ta.crossover" in body["supported_nodes"]
    assert body["blocked_reasons"] == []
    assert body["plan"]["execution_mode"] == "LONG_ONLY"
    assert set(body["plan"]["definitions"]) >= {"fast", "slow", "longCondition", "exitCondition"}
    assert body["plan"]["definitions"]["longCondition"]["node_type"] == "CALL"
    assert body["plan"]["entry_expression"]["node_type"] == "VARIABLE_REF"
    assert body["plan"]["entry_expression"]["name"] == "longCondition"
    assert body["plan"]["exit_expression"]["node_type"] == "VARIABLE_REF"
    assert body["plan"]["exit_expression"]["name"] == "exitCondition"


def test_pine_preflight_accepts_ema_crossover_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("EMA Breakout", overlay=true)
fast = ta.ema(close, 10)
slow = ta.ema(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["compatibility_score"] > 0


def test_pine_preflight_accepts_rsi_threshold_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("RSI Threshold", overlay=true)
rsiValue = ta.rsi(close, 2)
longCondition = rsiValue < 35
exitCondition = rsiValue > 60
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert "ta.rsi" in body["supported_nodes"]
    assert body["plan"]["definitions"]["longCondition"]["node_type"] == "COMPARE"
    assert body["plan"]["entry_expression"]["name"] == "longCondition"


def test_pine_preflight_accepts_macd_tuple_crossover_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("MACD Tuple", overlay=true)
[macdLine, signalLine, histLine] = ta.macd(close, 3, 6, 2)
longCondition = ta.crossover(macdLine, signalLine)
exitCondition = ta.crossunder(macdLine, signalLine)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert "ta.macd" in body["supported_nodes"]
    assert body["plan"]["definitions"]["macdLine"]["node_type"] == "TUPLE_ITEM"
    assert body["plan"]["definitions"]["signalLine"]["node_type"] == "TUPLE_ITEM"
    assert body["plan"]["entry_expression"]["name"] == "longCondition"


def test_pine_preflight_accepts_multiline_strategy_declaration():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
strategy(
    "Wrapped Header",
    shorttitle = "WH",
    overlay = true,
    pyramiding = 0
)
fast = ta.ema(close, 5)
slow = ta.ema(close, 10)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []


def test_pine_preflight_accepts_input_backed_lengths_in_reachable_signal_plan():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
strategy("Input Lengths", overlay=true)
fastLength = input.int(5, "Fast Length", minval=1)
slowLength = input.int(10, "Slow Length", minval=1)
fast = ta.ema(close, fastLength)
slow = ta.ema(close, slowLength)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["definitions"]["fastLength"]["node_type"] == "LITERAL"
    assert body["plan"]["definitions"]["fastLength"]["value"] == 5
    assert body["plan"]["definitions"]["slowLength"]["node_type"] == "LITERAL"
    assert body["plan"]["definitions"]["slowLength"]["value"] == 10


def test_pine_preflight_blocks_short_side_with_explicit_reason():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Short Side", overlay=true)
fast = ta.ema(close, 10)
slow = ta.ema(close, 20)
if ta.crossover(fast, slow)
    strategy.entry("Short", strategy.short)
if ta.crossunder(fast, slow)
    strategy.close("Short")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "BLOCKED"
    assert body["execution_mode"] == "LONG_ONLY"
    assert any("strategy.short" in reason for reason in body["blocked_reasons"])
    assert any("strategy.short" in feature for feature in body["unsupported_features"])
    assert body["plan"] is None


def test_pine_preflight_parses_inline_condition_using_actual_signal_variables():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Inline Condition", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
triggerFast = ta.sma(close, 5)
triggerSlow = ta.sma(close, 30)
if ta.crossover(triggerFast, triggerSlow)
    strategy.entry("Long", strategy.long)
if ta.crossunder(triggerFast, triggerSlow)
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "READY"
    assert body["plan"]["entry_expression"]["node_type"] == "CALL"
    assert body["plan"]["entry_expression"]["name"] == "ta.crossover"
    assert body["plan"]["entry_expression"]["args"][0]["name"] == "triggerFast"
    assert body["plan"]["entry_expression"]["args"][1]["name"] == "triggerSlow"


def test_pine_preflight_blocks_unresolved_variable_reference_in_condition():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Broken Condition", overlay=true)
fast = ta.sma(close, 10)
longCondition = ta.crossover(fast, ghostSignal)
if longCondition
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast, ta.sma(close, 20))
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "BLOCKED"
    assert any("ghostSignal" in reason for reason in body["blocked_reasons"])
    assert any("ghostSignal" in feature for feature in body["unsupported_features"])
    assert body["plan"] is None


def test_pine_preflight_blocks_visual_indicator_without_trade_signals():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
indicator("Visual RSI", overlay=false)
plot(ta.rsi(close, 14))
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "BLOCKED"
    assert body["unsupported_features"]


def test_pine_preflight_promotes_indicator_with_named_long_and_exit_conditions():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Indicator Signal Promotion", overlay=true)
fast = ta.ema(close, 5)
slow = ta.ema(close, 10)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
plot(close)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EMA_CROSSOVER"
    assert body["plan"]["entry_expression"]["name"] == "longCondition"
    assert body["plan"]["exit_expression"]["name"] == "exitCondition"
    assert body["detected_entries"] == ["indicator.signal.longCondition"]
    assert body["detected_exits"] == ["indicator.signal.exitCondition"]


def test_pine_preflight_promotes_indicator_with_entry_and_exit_signal_names():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Indicator Signal Aliases", overlay=true)
rsiValue = ta.rsi(close, 14)
entrySignal = rsiValue < 35
exitSignal = rsiValue > 60
plot(rsiValue)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["plan"]["entry_expression"]["name"] == "entrySignal"
    assert body["plan"]["exit_expression"]["name"] == "exitSignal"
    assert body["detected_entries"] == ["indicator.signal.entrySignal"]
    assert body["detected_exits"] == ["indicator.signal.exitSignal"]


def test_pine_preflight_promotes_indicator_with_buy_and_sell_cond_aliases():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Indicator Buy Sell Cond", overlay=true)
fast = ta.ema(close, 5)
slow = ta.ema(close, 10)
buyCond = ta.crossover(fast, slow)
sellCond = ta.crossunder(fast, slow)
plot(close)
""",
            "market": "EGX30",
            "timeframe": "15",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EMA_CROSSOVER"
    assert body["detected_entries"] == ["indicator.signal.buyCond"]
    assert body["detected_exits"] == ["indicator.signal.sellCond"]


def test_pine_preflight_promotes_indicator_with_new_buy_and_sell_signal_aliases():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Indicator New Buy Sell", overlay=true)
fast = ta.ema(close, 5)
slow = ta.ema(close, 10)
newBuySignal = ta.crossover(fast, slow)
newSellSignal = ta.crossunder(fast, slow)
plot(close)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EMA_CROSSOVER"
    assert body["detected_entries"] == ["indicator.signal.newBuySignal"]
    assert body["detected_exits"] == ["indicator.signal.newSellSignal"]


def test_pine_preflight_promotes_indicator_with_snake_case_signal_aliases():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Indicator Snake Case", overlay=true)
rsiValue = ta.rsi(close, 14)
buy_signal = rsiValue < 35
sell_signal = rsiValue > 60
plot(rsiValue)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["detected_entries"] == ["indicator.signal.buy_signal"]
    assert body["detected_exits"] == ["indicator.signal.sell_signal"]


def test_pine_preflight_promotes_indicator_with_arithmetic_and_stdev_signal_chain():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Arithmetic Signal Chain", overlay=true)
price = input(close, "Source")
length = input.int(20, "Length")
smooth = input.int(3, "Smooth")
mult = input.float(0.3, "Width")
sd_len = input.int(5, "SD Length")
baseline = ta.wma(price, sd_len)
dev = mult * ta.stdev(price, sd_len)
upper = baseline + dev
lower = baseline - dev
cprice = price > upper ? upper : price < lower ? lower : price
rema = ta.wma(ta.wma(cprice, length), smooth)
remaUp = rema > rema[1]
newBuySignal = remaUp and not remaUp[1] and barstate.isconfirmed
newSellSignal = not remaUp and remaUp[1] and barstate.isconfirmed
plot(rema)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert "ta.stdev" in body["supported_nodes"]
    assert body["blocked_reasons"] == []
    assert body["detected_entries"] == ["indicator.signal.newBuySignal"]
    assert body["detected_exits"] == ["indicator.signal.newSellSignal"]


def test_pine_preflight_accepts_multiline_input_assignment_in_signal_chain():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Multiline Input Assignment", overlay=true)
price = input(close, "Source")
mult = input.float(0.3,
  minval=0.05,
  title="Width")
sd_len = input.int(5,
  minval=1,
  title="Length")
baseline = ta.wma(price, sd_len)
dev = mult * ta.stdev(price, sd_len)
upper = baseline + dev
lower = baseline - dev
remaUp = price > upper and price[1] <= upper[1]
newBuySignal = remaUp and barstate.isconfirmed
newSellSignal = price < lower and barstate.isconfirmed
plot(price)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["definitions"]["sd_len"]["value"] == 5
    assert body["plan"]["definitions"]["mult"]["value"] == 0.3


def test_pine_preflight_blocks_strategy_that_is_not_supported_by_runtime():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Stoch Trend", overlay=true)
stochValue = ta.stoch(close, high, low, 14)
if ta.crossover(stochValue, 50)
    strategy.entry("Long", strategy.long)
if ta.crossunder(stochValue, 50)
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "BLOCKED"
    assert body["compatibility_score"] == 0
    assert any("ta.stoch" in feature for feature in body["unsupported_features"])


def test_pine_preflight_ignores_commented_strategy_markers_in_indicator_script():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
indicator("Commented Strategy Noise", overlay=true)
visualMode = switch "A"
    "A" => 1
    => 0
// strategy.entry("Long", strategy.long)
// strategy.close("Long")
plot(close)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "BLOCKED"
    assert "Indicator script does not expose executable entry and exit behavior." in body["unsupported_features"]


def test_pine_preflight_ignores_unreachable_unsupported_indicator_helper():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Unused Indicator Helper", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
unusedBand = ta.bb(close, 20, 2)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "SMA_CROSSOVER"


def test_pine_preflight_ignores_unreachable_unsupported_custom_helper_call():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Unused Custom Helper", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
unusedVisual = custom_helper(close)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "SMA_CROSSOVER"


def test_pine_preflight_ignores_unreachable_unresolved_reference_helper():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Unused Unresolved Helper", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
unusedVisual = ghostSignal
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "SMA_CROSSOVER"


def test_pine_preflight_blocks_reachable_unsupported_indicator_helper():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Reachable Indicator Helper", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
bandBasis = ta.bb(close, 20, 2)
longCondition = ta.crossover(fast, slow) and close > bandBasis
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "BLOCKED"
    assert any("ta.bb" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_accepts_core_indicator_nodes_while_still_blocking_strategy_exit():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Core Indicator Mix", overlay=true)
atrValue = ta.atr(14)
weighted = ta.wma(close, 10)
volumeWeighted = ta.vwma(close, 20)
ceiling = ta.highest(high, 20)
floor = ta.lowest(low, 20)
longCondition = close > weighted and close > volumeWeighted and close < ceiling and close > floor and atrValue > 1
if longCondition
    strategy.entry("Long", strategy.long)
strategy.exit("Risk", "Long", stop=close - atrValue * 2)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "BLOCKED"
    assert {"ta.atr", "ta.wma", "ta.vwma", "ta.highest", "ta.lowest"}.issubset(set(body["supported_nodes"]))
    assert any("strategy.exit" in reason for reason in body["blocked_reasons"])
    assert not any("ta.atr" in reason for reason in body["blocked_reasons"])
    assert not any("ta.wma" in reason for reason in body["blocked_reasons"])
    assert not any("ta.vwma" in reason for reason in body["blocked_reasons"])
    assert not any("ta.highest" in reason for reason in body["blocked_reasons"])
    assert not any("ta.lowest" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_accepts_core_indicator_nodes_in_algox_style_script_while_preserving_real_blockers():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("ALGOX", overlay=true)
rp_security(_symbol, _res, _src) =>
    request.security(_symbol, _res, _src[barstate.isrealtime ? 1 : 0])
variant(type, src, len, offSig, offALMA) =>
    v1 = ta.sma(src, len)
    v2 = ta.ema(src, len)
    v5 = ta.wma(src, len)
    v6 = ta.vwma(src, len)
    v9 = ta.linreg(src, len, offSig)
    v10 = ta.alma(src, len, offALMA, offSig)
    type == 'ALMA' ? v10 : type == 'VWMA' ? v6 : v5
ema = ta.ema(close, 20)
i_atrValue = ta.atr(14)
i_maxHistoricalATR = ta.highest(i_atrValue, 20)
i_minHistoricalATR = ta.lowest(i_atrValue, 20)
weighted = variant('ALMA', close, 2, 5, 0.85)
remoteClose = rp_security("EGX:COMI", "30", close)
longCondition = close > weighted and close > remoteClose and i_atrValue > 1
if longCondition
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ema)
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "BLOCKED"
    assert {"ta.atr", "ta.highest", "ta.lowest", "ta.wma", "ta.vwma", "ta.linreg", "ta.alma", "ta.crossunder"}.issubset(set(body["supported_nodes"]))
    assert any("request.security" in reason for reason in body["blocked_reasons"])
    assert not any("ta.atr" in reason for reason in body["blocked_reasons"])
    assert not any("ta.highest" in reason for reason in body["blocked_reasons"])
    assert not any("ta.lowest" in reason for reason in body["blocked_reasons"])
    assert not any("ta.wma" in reason for reason in body["blocked_reasons"])
    assert not any("ta.vwma" in reason for reason in body["blocked_reasons"])
    assert not any("ta.linreg" in reason for reason in body["blocked_reasons"])
    assert not any("ta.alma" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_accepts_supported_core_indicator_signal_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Core Signal Runtime", overlay=true)
atrValue = ta.atr(2)
weighted = ta.wma(close, 2)
volumeWeighted = ta.vwma(close, 2)
ceiling = ta.highest(high, 2)
floor = ta.lowest(low, 2)
longCondition = close > weighted and close > volumeWeighted and high >= ceiling and atrValue > 1
exitCondition = close < weighted and low <= floor
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert {"ta.atr", "ta.highest", "ta.lowest", "ta.wma", "ta.vwma"}.issubset(set(body["supported_nodes"]))
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["plan"]["entry_expression"]["name"] == "longCondition"
    assert body["plan"]["exit_expression"]["name"] == "exitCondition"


def test_pine_preflight_accepts_supported_linreg_and_alma_signal_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Smoothing Signal Runtime", overlay=true)
linregTrend = ta.linreg(close, 3, 0)
almaTrend = ta.alma(close, 3, 0.85, 6)
longCondition = close > linregTrend and close > almaTrend
exitCondition = close < linregTrend or close < almaTrend
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert {"ta.linreg", "ta.alma"}.issubset(set(body["supported_nodes"]))
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["plan"]["entry_expression"]["name"] == "longCondition"
    assert body["plan"]["exit_expression"]["name"] == "exitCondition"


def test_pine_preflight_accepts_same_symbol_higher_timeframe_request_security_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("HTF Close Import", overlay=true)
htfClose = request.security(syminfo.tickerid, "1W", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert "request.security" in body["supported_nodes"]
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["plan"]["definitions"]["htfClose"]["name"] == "request.security"


def test_pine_preflight_accepts_passthrough_request_security_wrapper_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Wrapped HTF Close Import", overlay=true)
security_passthrough(sym, res, expr) => request.security(sym, res, expr)
htfClose = security_passthrough(syminfo.tickerid, "1W", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert "request.security" in body["supported_nodes"]
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["plan"]["definitions"]["htfClose"]["name"] == "request.security"


def test_pine_preflight_accepts_input_timeframe_request_security_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Input TF Import", overlay=true)
tf = input.timeframe("1W", "Trend TF")
htfClose = request.security(syminfo.tickerid, tf, close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert "request.security" in body["supported_nodes"]
    assert body["blocked_reasons"] == []
    assert body["plan"]["definitions"]["tf"]["node_type"] == "LITERAL"
    assert body["plan"]["definitions"]["tf"]["value"] == "1W"


def test_pine_preflight_accepts_multiline_request_security_helper_indicator():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Helper Trend", overlay=true)
getTrend(tf) =>
    ema50 = request.security(syminfo.tickerid, tf, ta.ema(close, 50))
    current_close = request.security(syminfo.tickerid, tf, close)
    current_close > ema50 ? 1 : current_close < ema50 ? -1 : 0
trend_m5 = getTrend("5")
trend_m15 = getTrend("15")
final_buy = trend_m5 == 1 and trend_m15 == 1
final_sell = trend_m5 == -1 and trend_m15 == -1
""",
            "market": "EGX30",
            "timeframe": "15",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["detected_entries"] == ["indicator.signal.final_buy"]
    assert body["detected_exits"] == ["indicator.signal.final_sell"]
    assert body["blocked_reasons"] == []


def test_pine_preflight_accepts_stateful_indicator_signals_with_multiline_conditions():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
indicator("Stateful Signals", overlay=true)
length = input.int(5, "Length")
lag = math.floor((length - 1) / 2)
z = ta.ema(close + (close - close[lag]), length)
var int trend = 0
if ta.crossover(close, z)
    trend := 1
if ta.crossunder(close, z)
    trend := -1
advancedBullishEntry = ta.crossover(close, z) and trend == 1 and trend[1] == 1 and
   close > open
advancedBearishEntry = ta.crossunder(close, z) and trend == -1 and trend[1] == -1 and
   close < open
""",
            "market": "EGX30",
            "timeframe": "15",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["detected_entries"] == ["indicator.signal.advancedBullishEntry"]
    assert body["detected_exits"] == ["indicator.signal.advancedBearishEntry"]
    assert body["blocked_reasons"] == []


def test_pine_preflight_accepts_known_supertrend_helper_indicator():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
indicator("Simple Supertrend", overlay=true)
supertrend(src, factor, atrLen) =>
    atr = ta.atr(atrLen)
    upperBand = src + factor * atr
    lowerBand = src - factor * atr
    prevLowerBand = nz(lowerBand[1])
    prevUpperBand = nz(upperBand[1])
    lowerBand := lowerBand > prevLowerBand or close[1] < prevLowerBand ? lowerBand : prevLowerBand
    upperBand := upperBand < prevUpperBand or close[1] > prevUpperBand ? upperBand : prevUpperBand
    var int direction = na
    var float superTrend = na
    prevSuperTrend = nz(superTrend[1])
    if na(atr[1])
        direction := 1
    else if prevSuperTrend == prevUpperBand
        direction := close > upperBand ? -1 : 1
    else
        direction := close < lowerBand ? 1 : -1
    superTrend := direction == -1 ? lowerBand : upperBand
    [superTrend, direction]
[supertrend_line, direction] = supertrend(close, 3.0, 10)
buy_signal = ta.crossover(close, supertrend_line)
sell_signal = ta.crossunder(close, supertrend_line)
""",
            "market": "EGX30",
            "timeframe": "15",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "INDICATOR"
    assert body["readiness"] == "READY"
    assert body["detected_entries"] == ["indicator.signal.buy_signal"]
    assert body["detected_exits"] == ["indicator.signal.sell_signal"]
    assert body["blocked_reasons"] == []


def test_pine_preflight_accepts_same_symbol_lower_timeframe_request_security_for_intraday_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
strategy("LTF RSI Import", overlay=true)
ltfRsi = request.security(syminfo.tickerid, "5", ta.rsi(close, 14))
longCondition = ltfRsi > 55
exitCondition = ltfRsi < 45
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "15",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["script_type"] == "STRATEGY"
    assert body["readiness"] == "READY"
    assert "request.security" in body["supported_nodes"]
    assert body["blocked_reasons"] == []
    assert body["plan"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert body["plan"]["definitions"]["ltfRsi"]["name"] == "request.security"


def test_pine_preflight_blocks_lower_timeframe_request_security_for_daily_strategy():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=6
strategy("Daily LTF RSI Import", overlay=true)
ltfRsi = request.security(syminfo.tickerid, "5", ta.rsi(close, 14))
longCondition = ltfRsi > 55
exitCondition = ltfRsi < 45
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "BLOCKED"
    assert "request.security" in body["supported_nodes"]
    assert any("lower-timeframe imports are only supported for intraday strategies" in reason for reason in body["blocked_reasons"])
    assert not any("deterministic MTF runtime is not available yet" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_accepts_request_security_when_timeframe_matches_base():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Same Timeframe Import", overlay=true)
htfClose = request.security(syminfo.tickerid, "1D", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "READY"
    assert "request.security" in body["supported_nodes"]
    assert body["blocked_reasons"] == []


def test_pine_preflight_blocks_cross_symbol_request_security_with_precise_reason():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Cross Symbol Import", overlay=true)
htfClose = request.security("EGX:COMI", "1D", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "BLOCKED"
    assert "request.security" in body["supported_nodes"]
    assert any("same-symbol imports in this phase" in reason for reason in body["blocked_reasons"])
    assert not any("request.security is not supported" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_blocks_request_security_lookahead_with_precise_reason():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Lookahead Import", overlay=true)
htfClose = request.security(syminfo.tickerid, "1D", close, gaps=barmerge.gaps_off, lookahead=barmerge.lookahead_on)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "BLOCKED"
    assert "request.security" in body["supported_nodes"]
    assert any("lookahead/repaint behavior is not supported" in reason for reason in body["blocked_reasons"])
    assert not any("request.security is not supported" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_keeps_repaint_request_security_wrapper_blocked():
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": """
//@version=5
strategy("Wrapped Repaint Import", overlay=true)
rp_security(sym, res, expr) => request.security(sym, res, expr[barstate.isrealtime ? 1 : 0])
htfClose = rp_security(syminfo.tickerid, "1W", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["readiness"] == "BLOCKED"
    assert "request.security" in body["supported_nodes"]
    assert any("lookahead/repaint behavior is not supported" in reason for reason in body["blocked_reasons"])
    assert any("wrapped request.security helper patterns are not supported" in reason for reason in body["blocked_reasons"])


def test_pine_backtest_supports_ema_crossover_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=8, freq="D"),
            "Open": [100, 99, 98, 99, 101, 104, 103, 101],
            "High": [101, 100, 99, 100, 102, 105, 104, 102],
            "Low": [99, 98, 97, 98, 100, 103, 102, 100],
            "Close": [100, 99, 98, 99, 101, 104, 103, 101],
            "Volume": [1000, 1000, 1000, 1000, 1000, 1000, 1000, 1000],
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.check_buy_signal",
        lambda *_args, **_kwargs: False,
    )

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("EMA Runtime", overlay=true)
fast = ta.ema(close, 2)
slow = ta.ema(close, 3)
if ta.crossover(fast, slow)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast, slow)
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-08",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["config"]["strategy_kind"] == "EMA_CROSSOVER"
    assert "metrics" in result


def test_pine_backtest_supports_same_symbol_higher_timeframe_request_security_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=15, freq="D"),
            "Open": [100, 101, 102, 103, 104, 106, 108, 110, 112, 114, 115, 113, 111, 108, 104],
            "High": [101, 102, 103, 104, 105, 107, 109, 111, 113, 115, 116, 114, 112, 109, 105],
            "Low": [99, 100, 101, 102, 103, 105, 107, 109, 111, 113, 114, 112, 110, 107, 103],
            "Close": [100, 101, 102, 103, 104, 106, 108, 110, 112, 114, 115, 113, 111, 108, 104],
            "Volume": [1000] * 15,
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("HTF Close Import", overlay=true)
htfClose = request.security(syminfo.tickerid, "1W", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-15",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["config"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert result["compatibility"]["readiness"] == "READY"
    assert result["metrics"]["trade_count"] >= 1


def test_pine_backtest_supports_passthrough_request_security_wrapper_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=15, freq="D"),
            "Open": [100, 101, 102, 103, 104, 106, 108, 110, 112, 114, 115, 113, 111, 108, 104],
            "High": [101, 102, 103, 104, 105, 107, 109, 111, 113, 115, 116, 114, 112, 109, 105],
            "Low": [99, 100, 101, 102, 103, 105, 107, 109, 111, 113, 114, 112, 110, 107, 103],
            "Close": [100, 101, 102, 103, 104, 106, 108, 110, 112, 114, 115, 113, 111, 108, 104],
            "Volume": [1000] * 15,
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("Wrapped HTF Close Import", overlay=true)
security_passthrough(sym, res, expr) => request.security(sym, res, expr)
htfClose = security_passthrough(syminfo.tickerid, "1W", close)
longCondition = close > htfClose
exitCondition = close < htfClose
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-15",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["config"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert result["compatibility"]["readiness"] == "READY"
    assert result["metrics"]["trade_count"] >= 1


def test_pine_backtest_supports_intraday_lower_timeframe_request_security_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01 09:00:00", periods=90, freq="min"),
            "Open": [100 + (i * 0.08) for i in range(90)],
            "High": [100.2 + (i * 0.08) for i in range(90)],
            "Low": [99.8 + (i * 0.08) for i in range(90)],
            "Close": [100 + (i * 0.08) for i in range(90)],
            "Volume": [1000 + (i * 10) for i in range(90)],
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_intraday_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=6
strategy("Intraday LTF RSI Runtime", overlay=true)
ltfRsi = request.security(syminfo.tickerid, "5", ta.rsi(close, 2))
longCondition = ltfRsi > 55
exitCondition = ltfRsi < 45
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="15",
        date_from="2025-01-01 09:00:00",
        date_to="2025-01-01 10:29:00",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["config"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert result["compatibility"]["readiness"] == "READY"


def test_pine_backtest_supports_rsi_threshold_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=9, freq="D"),
            "Open": [100, 94, 88, 92, 97, 103, 108, 102, 98],
            "High": [101, 95, 89, 93, 98, 104, 109, 103, 99],
            "Low": [99, 93, 87, 91, 96, 102, 107, 101, 97],
            "Close": [100, 94, 88, 92, 97, 103, 108, 102, 98],
            "Volume": [1000] * 9,
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("RSI Runtime", overlay=true)
rsiValue = ta.rsi(close, 2)
longCondition = rsiValue < 35
exitCondition = rsiValue > 60
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-09",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["metrics"]["trade_count"] >= 1


def test_pine_backtest_supports_boolean_rsi_and_ema_condition(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=10, freq="D"),
            "Open": [100, 96, 90, 92, 95, 99, 104, 107, 103, 100],
            "High": [101, 97, 91, 93, 96, 100, 105, 108, 104, 101],
            "Low": [99, 95, 89, 91, 94, 98, 103, 106, 102, 99],
            "Close": [100, 96, 90, 92, 95, 99, 104, 107, 103, 100],
            "Volume": [1000] * 10,
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("RSI EMA Runtime", overlay=true)
rsiValue = ta.rsi(close, 2)
emaFast = ta.ema(close, 2)
longCondition = rsiValue < 45 and close > emaFast
exitCondition = rsiValue > 65
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-10",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["metrics"]["trade_count"] >= 0


def test_pine_backtest_supports_macd_tuple_crossover_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=12, freq="D"),
            "Open": [100, 99, 98, 97, 98, 100, 103, 106, 109, 107, 104, 101],
            "High": [101, 100, 99, 98, 99, 101, 104, 107, 110, 108, 105, 102],
            "Low": [99, 98, 97, 96, 97, 99, 102, 105, 108, 106, 103, 100],
            "Close": [100, 99, 98, 97, 98, 100, 103, 106, 109, 107, 104, 101],
            "Volume": [1000] * 12,
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("MACD Runtime", overlay=true)
[macdLine, signalLine, histLine] = ta.macd(close, 3, 6, 2)
longCondition = ta.crossover(macdLine, signalLine)
exitCondition = ta.crossunder(macdLine, signalLine)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-12",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["metrics"]["trade_count"] >= 0


def test_pine_backtest_supports_core_indicator_signal_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=9, freq="D"),
            "Open": [10.0, 10.4, 11.2, 12.3, 13.0, 14.0, 13.2, 11.4, 10.2],
            "High": [10.8, 11.5, 12.6, 13.7, 14.8, 15.6, 13.9, 11.9, 10.6],
            "Low": [9.7, 10.1, 10.9, 12.0, 12.8, 13.7, 12.4, 10.8, 9.8],
            "Close": [10.2, 11.0, 12.1, 13.3, 14.2, 15.0, 12.9, 11.0, 10.0],
            "Volume": [100, 130, 150, 170, 210, 240, 180, 140, 120],
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("Core Signal Runtime", overlay=true)
atrValue = ta.atr(2)
weighted = ta.wma(close, 2)
volumeWeighted = ta.vwma(close, 2)
ceiling = ta.highest(high, 2)
floor = ta.lowest(low, 2)
longCondition = close > weighted and close > volumeWeighted and high >= ceiling and atrValue > 1
exitCondition = close < weighted and low <= floor
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-09",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["config"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert result["compatibility"]["readiness"] == "READY"
    assert result["metrics"]["trade_count"] >= 1


def test_pine_backtest_supports_linreg_and_alma_signal_strategy(monkeypatch):
    history = pd.DataFrame(
        {
            "Date": pd.date_range("2025-01-01", periods=10, freq="D"),
            "Open": [10.0, 10.1, 10.3, 10.8, 11.6, 12.4, 12.9, 12.0, 11.0, 10.4],
            "High": [10.2, 10.4, 10.8, 11.4, 12.1, 12.9, 13.2, 12.3, 11.3, 10.6],
            "Low": [9.8, 9.9, 10.1, 10.6, 11.3, 12.1, 12.5, 11.6, 10.7, 10.1],
            "Close": [10.0, 10.2, 10.6, 11.2, 11.9, 12.7, 13.0, 11.8, 10.9, 10.2],
            "Volume": [100, 105, 115, 130, 145, 160, 170, 150, 130, 120],
        }
    )

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.executor.DataManager.get_stock_data", lambda *_args, **_kwargs: history)
    monkeypatch.setattr(
        "core.pine_lab.executor.SignalEngine.add_indicators",
        lambda df, **_kwargs: df.assign(EMA9=df["Close"], ATR=1.0, Volume_Ratio=1.0, RSI=50.0),
    )
    monkeypatch.setattr("core.pine_lab.executor.SignalEngine.check_buy_signal", lambda *_args, **_kwargs: False)

    result = run_pine_backtest(
        script_source="""
//@version=5
strategy("Smoothing Signal Runtime", overlay=true)
linregTrend = ta.linreg(close, 3, 0)
almaTrend = ta.alma(close, 3, 0.85, 6)
longCondition = close > linregTrend and close > almaTrend
exitCondition = close < linregTrend or close < almaTrend
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
        market="EGX30",
        timeframe="1D",
        date_from="2025-01-01",
        date_to="2025-01-10",
        capital=100000,
        commission_pct=0.05,
        slippage_pct=0.1,
    )

    assert result["status"] == "success"
    assert result["config"]["strategy_kind"] == "EXPRESSION_PLAN"
    assert result["compatibility"]["readiness"] == "READY"
    assert result["metrics"]["trade_count"] >= 1


def test_create_and_list_pine_scanner_profiles():
    create_response = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Promoted", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "EGX Breakout Pine",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 18.2,
                "trade_count": 34,
                "max_drawdown": 7.1,
                "walk_forward_pass": True,
                "oos_trade_count": 12,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
            "compatibility_summary": {
                "compatibility_score": 92,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 88,
                "alignment_score": 71,
                "combined_score": 82,
                "recommended": True,
            },
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "success"
    assert created["profile_name"] == "EGX Breakout Pine"
    assert created["profile_state"] == "READY"
    assert created["profile_id"]
    assert created["created_at"]
    assert created["ready_at"]
    assert created["activated_at"] is None
    assert created["activation_count"] == 0
    assert created["activation_history"] == []

    list_response = client.get("/api/v1/strategy/pine/scanner-profiles")

    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["status"] == "success"
    assert listed["active_profile_id"] is None
    assert len(listed["profiles"]) == 1
    assert listed["profiles"][0]["profile_name"] == "EGX Breakout Pine"
    assert listed["profiles"][0]["profile_state"] == "READY"
    assert listed["profiles"][0]["ready_at"]
    assert listed["profiles"][0]["activated_at"] is None
    assert listed["profiles"][0]["activation_count"] == 0
    assert listed["profiles"][0]["activation_history"] == []


def test_create_pine_scanner_profile_recovers_when_profile_table_is_missing():
    db.execute_sql("DROP TABLE scannerstrategyprofile")

    create_response = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Recover Missing Table", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "Recover Missing Table Pine",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 14.8,
                "trade_count": 9,
                "max_drawdown": 5.2,
            },
            "compatibility_summary": {
                "compatibility_score": 92,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 84,
                "alignment_score": 70,
                "combined_score": 79,
                "recommended": True,
            },
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["status"] == "success"
    assert created["profile_name"] == "Recover Missing Table Pine"

    list_response = client.get("/api/v1/strategy/pine/scanner-profiles")
    assert list_response.status_code == 200
    listed = list_response.json()
    assert len(listed["profiles"]) == 1
    assert listed["profiles"][0]["profile_name"] == "Recover Missing Table Pine"


def test_get_pine_scanner_profile_detail_returns_script_source():
    created = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Profile Detail", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "Profile Detail Pine",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 12.0,
                "trade_count": 8,
                "max_drawdown": 5.0,
            },
            "compatibility_summary": {
                "compatibility_score": 92,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 80,
                "alignment_score": 68,
                "combined_score": 74,
                "recommended": True,
            },
        },
    ).json()

    response = client.get(f"/api/v1/strategy/pine/scanner-profile/{created['profile_id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["profile"]["profile_id"] == created["profile_id"]
    assert body["profile"]["profile_name"] == "Profile Detail Pine"
    assert "strategy(\"Profile Detail\"" in body["script_source"]


def test_activate_pine_scanner_profile_promotes_ready_profile():
    first_profile = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Promoted One", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "EGX Breakout Pine One",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 18.2,
                "trade_count": 36,
                "max_drawdown": 7.1,
                "walk_forward_pass": True,
                "oos_trade_count": 12,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
            "compatibility_summary": {
                "compatibility_score": 92,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 88,
                "alignment_score": 71,
                "combined_score": 82,
                "recommended": True,
            },
        },
    ).json()
    second_profile = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Promoted Two", overlay=true)
if ta.crossover(close, ta.sma(close, 10))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 10))
    strategy.close("Long")
""",
            "profile_name": "EGX Breakout Pine Two",
            "market": "EGX70",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 12.2,
                "trade_count": 31,
                "max_drawdown": 6.4,
                "walk_forward_pass": True,
                "oos_trade_count": 11,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
            "compatibility_summary": {
                "compatibility_score": 88,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 76,
                "alignment_score": 68,
                "combined_score": 73,
                "recommended": True,
            },
        },
    ).json()

    activate_response = client.post(
        "/api/v1/strategy/pine/activate-scanner-profile",
        json={"profile_id": first_profile["profile_id"]},
    )

    assert activate_response.status_code == 200
    activated = activate_response.json()
    assert activated["status"] == "success"
    assert activated["profile_id"] == first_profile["profile_id"]
    assert activated["profile_state"] == "ACTIVE"
    assert activated["activated_at"]
    assert activated["activation_count"] == 1
    assert len(activated["activation_history"]) == 1
    assert activated["activation_history"][0]["event_type"] == "ACTIVATED"
    assert activated["activation_history"][0]["previous_active_profile_id"] is None

    list_response = client.get("/api/v1/strategy/pine/scanner-profiles")

    assert list_response.status_code == 200
    listed = list_response.json()
    assert listed["active_profile_id"] == first_profile["profile_id"]
    by_id = {profile["profile_id"]: profile for profile in listed["profiles"]}
    assert by_id[first_profile["profile_id"]]["profile_state"] == "ACTIVE"
    assert by_id[first_profile["profile_id"]]["activated_at"]
    assert by_id[first_profile["profile_id"]]["activation_count"] == 1
    assert len(by_id[first_profile["profile_id"]]["activation_history"]) == 1
    assert by_id[second_profile["profile_id"]]["profile_state"] == "READY"


def test_activating_new_profile_records_previous_active_profile_in_history():
    first_profile = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Primary", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "Primary Pine",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 18.2,
                "trade_count": 35,
                "max_drawdown": 7.1,
                "walk_forward_pass": True,
                "oos_trade_count": 12,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
            "compatibility_summary": {
                "compatibility_score": 92,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 88,
                "alignment_score": 71,
                "combined_score": 82,
                "recommended": True,
            },
        },
    ).json()
    second_profile = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Secondary", overlay=true)
if ta.crossover(close, ta.sma(close, 10))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 10))
    strategy.close("Long")
""",
            "profile_name": "Secondary Pine",
            "market": "EGX70",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 14.4,
                "trade_count": 33,
                "max_drawdown": 5.4,
                "walk_forward_pass": True,
                "oos_trade_count": 11,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
            "compatibility_summary": {
                "compatibility_score": 89,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 81,
                "alignment_score": 69,
                "combined_score": 76,
                "recommended": True,
            },
        },
    ).json()

    client.post(
        "/api/v1/strategy/pine/activate-scanner-profile",
        json={"profile_id": first_profile["profile_id"]},
    )
    second_activation = client.post(
        "/api/v1/strategy/pine/activate-scanner-profile",
        json={"profile_id": second_profile["profile_id"]},
    )

    assert second_activation.status_code == 200
    activated = second_activation.json()
    assert activated["profile_state"] == "ACTIVE"
    assert activated["activation_count"] == 1
    assert len(activated["activation_history"]) == 1
    assert activated["activation_history"][0]["previous_active_profile_id"] == first_profile["profile_id"]
    assert activated["activation_history"][0]["previous_active_profile_name"] == "Primary Pine"

    listed = client.get("/api/v1/strategy/pine/scanner-profiles").json()
    by_id = {profile["profile_id"]: profile for profile in listed["profiles"]}
    assert by_id[first_profile["profile_id"]]["profile_state"] == "READY"
    assert by_id[first_profile["profile_id"]]["activation_count"] == 1
    assert by_id[second_profile["profile_id"]]["profile_state"] == "ACTIVE"
    assert by_id[second_profile["profile_id"]]["activation_history"][0]["previous_active_profile_id"] == first_profile["profile_id"]


def test_activating_ready_pine_profile_provisions_named_portfolio():
    created = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Portfolio Bound", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "EGX Profile Portfolio",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 11.2,
                "trade_count": 32,
                "max_drawdown": 4.1,
                "walk_forward_pass": True,
                "oos_trade_count": 10,
                "commission_pct": 0.05,
                "slippage_pct": 0.1,
            },
            "compatibility_summary": {"compatibility_score": 91, "readiness": "READY"},
            "ranking_summary": {"combined_score": 78, "recommended": True},
        },
    ).json()

    response = client.post(
        "/api/v1/strategy/pine/activate-scanner-profile",
        json={"profile_id": created["profile_id"]},
    )

    assert response.status_code == 200
    body = response.json()
    portfolio = Portfolio.get_or_none(Portfolio.name == "EGX Profile Portfolio")
    assert portfolio is not None
    assert portfolio.type == "STRATEGY"
    assert portfolio.auto_manage is True
    assert "strategy profile" in (portfolio.description or "").lower()
    assert body["portfolio"]["id"] == portfolio.id
    assert body["portfolio"]["name"] == "EGX Profile Portfolio"


def test_create_pine_scanner_profile_returns_draft_gate_reasons():
    create_response = client.post(
        "/api/v1/strategy/pine/create-scanner-profile",
        json={
            "script_source": """
//@version=5
strategy("Weak Pine", overlay=true)
if ta.crossover(close, ta.sma(close, 20))
    strategy.entry("Long", strategy.long)
if ta.crossunder(close, ta.sma(close, 20))
    strategy.close("Long")
""",
            "profile_name": "Weak EGX Pine",
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": -2.0,
                "trade_count": 1,
                "max_drawdown": 41.5,
            },
            "compatibility_summary": {
                "compatibility_score": 61,
                "readiness": "READY",
            },
            "ranking_summary": {
                "performance_score": 40,
                "alignment_score": 30,
                "combined_score": 45,
                "recommended": False,
            },
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["profile_state"] == "DRAFT"
    assert created["promotion_summary"]["failed_gates"]
    assert "combined_score" in created["promotion_summary"]["failed_gates"]
    assert "compatibility_score" in created["promotion_summary"]["failed_gates"]
    assert "trade_count" in created["promotion_summary"]["failed_gates"]


def test_pine_backtest_returns_normalized_result_payload(monkeypatch):
    dates = pd.date_range("2025-01-01", periods=10, freq="D")
    df = pd.DataFrame(
        {
            "Open": [10, 10, 10, 10.5, 11.5, 12.5, 12.2, 11.5, 10.5, 9.5],
            "High": [10.2, 10.2, 10.3, 11.2, 12.2, 13.2, 12.4, 11.7, 10.7, 9.7],
            "Low": [9.8, 9.8, 9.9, 10.3, 11.3, 12.3, 12.0, 11.2, 10.2, 9.2],
            "Close": [10, 10, 10, 11, 12, 13, 12, 11, 10, 9],
            "Volume": [1000] * 10,
        },
        index=dates,
    )
    df.index.name = "Date"

    monkeypatch.setattr("core.pine_lab.executor.MarketLists.get_market_list", lambda choice: {"COMI"})
    monkeypatch.setattr("core.DataManager.DataManager.get_stock_data", lambda ticker, include_live=False: df.copy())

    response = client.post(
        "/api/v1/strategy/pine/backtest",
        json={
            "script_source": """
//@version=5
strategy("Fast Slow", overlay=true)
fast = ta.sma(close, 2)
slow = ta.sma(close, 3)
if ta.crossover(fast, slow)
    strategy.entry("Long", strategy.long)
if ta.crossunder(fast, slow)
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-01-31",
            "capital": 100000,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["config"]["market"] == "EGX30"
    assert body["config"]["capital"] == 100000
    assert body["metrics"]["trade_count"] >= 1
    assert "final_value" in body["metrics"]
    assert "compatibility" in body
    assert body["compatibility"]["readiness"] == "READY"
    assert "alignment" in body
    assert "rankings" in body
    assert "performance_score" in body["rankings"]
    assert "combined_score" in body["rankings"]
    assert body["equity_curve"]
    assert body["trades"]


def test_pine_backtest_rejects_blocked_script():
    response = client.post(
        "/api/v1/strategy/pine/backtest",
        json={
            "script_source": """
//@version=5
indicator("Visual RSI", overlay=false)
plot(ta.rsi(close, 14))
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
            "capital": 100000,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
        },
    )

    assert response.status_code == 400
    assert "blocked" in response.json()["detail"].lower()


def test_pine_backtest_rejects_indicator_with_only_commented_strategy_markers():
    response = client.post(
        "/api/v1/strategy/pine/backtest",
        json={
            "script_source": """
//@version=5
indicator("Commented Strategy Noise", overlay=true)
visualMode = switch "A"
    "A" => 1
    => 0
// strategy.entry("Long", strategy.long)
// strategy.close("Long")
plot(close)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
            "capital": 100000,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
        },
    )

    assert response.status_code == 400
    assert "blocked" in response.json()["detail"].lower()
