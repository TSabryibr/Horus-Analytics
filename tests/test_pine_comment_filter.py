from fastapi.testclient import TestClient

import core.pine_lab.capabilities as pine_capabilities
from api import app


client = TestClient(app, raise_server_exceptions=False)


def _preflight(script_source: str) -> dict:
    response = client.post(
        "/api/v1/strategy/pine/preflight",
        json={
            "script_source": script_source,
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_pine_preflight_ignores_full_line_commented_strategy_short():
    body = _preflight(
        """
//@version=5
strategy("Commented Short", overlay=true)
// strategy.entry("Short", strategy.short)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("strategy.short" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_trailing_commented_strategy_short():
    body = _preflight(
        """
//@version=5
strategy("Trailing Short", overlay=true)
fast = ta.sma(close, 10) // strategy.entry("Short", strategy.short)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("strategy.short" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_commented_strategy_exit():
    body = _preflight(
        """
//@version=5
strategy("Commented Exit", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
// strategy.exit("Risk", "Long", stop=close * 0.95)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("strategy.exit" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_commented_unsafe_request_security():
    body = _preflight(
        """
//@version=5
strategy("Commented Security", overlay=true)
// htfClose = request.security("EGX:COMI", "1D", close, gaps=barmerge.gaps_off, lookahead=barmerge.lookahead_on)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("request.security" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_full_line_block_commented_strategy_short():
    body = _preflight(
        """
//@version=5
strategy("Block Commented Short", overlay=true)
/* strategy.entry("Short", strategy.short) */
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("strategy.short" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_inline_block_commented_strategy_short():
    body = _preflight(
        """
//@version=5
strategy("Inline Block Short", overlay=true)
fast = ta.sma(close, 10) /* strategy.entry("Short", strategy.short) */
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("strategy.short" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_block_commented_strategy_exit():
    body = _preflight(
        """
//@version=5
strategy("Block Commented Exit", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
/* strategy.exit("Risk", "Long", stop=close * 0.95) */
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("strategy.exit" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_multiline_block_commented_unsafe_request_security():
    body = _preflight(
        """
//@version=5
strategy("Block Commented Security", overlay=true)
/*
htfClose = request.security("EGX:COMI", "1D", close, gaps=barmerge.gaps_off, lookahead=barmerge.lookahead_on)
*/
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"
    assert not any("request.security" in reason for reason in body["blocked_reasons"])


def test_pine_preflight_ignores_inline_block_comment_assignment_tail():
    body = _preflight(
        """
//@version=5
strategy("Inline Assignment Tail", overlay=true)
fast = ta.sma(close, 10) /* helper = ta.bb(close, 20, 2) */
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
"""
    )

    assert body["readiness"] == "READY"


def test_strip_pine_comments_preserves_double_slash_inside_strings():
    sanitized = pine_capabilities._strip_pine_comments('note = "http://example.com" // strategy.short\n')

    assert sanitized == 'note = "http://example.com" \n'


def test_strip_pine_comments_preserves_block_comment_markers_inside_strings():
    sanitized = pine_capabilities._strip_pine_comments('note = "literal /* not a comment */ text" /* strategy.short */\n')

    assert sanitized == 'note = "literal /* not a comment */ text" \n'
