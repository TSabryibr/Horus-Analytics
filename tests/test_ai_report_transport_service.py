import pytest
from core.ai_report.transport import (
    _sanitize_telegram_text,
    build_ai_report_telegram_message,
)

def test_sanitize_telegram_text():
    assert _sanitize_telegram_text("`*test*`") == "test"
    assert _sanitize_telegram_text("Hello [World]") == "Hello World"
    assert _sanitize_telegram_text("Multiple   Spaces") == "Multiple Spaces"

def test_build_ai_report_telegram_message():
    payload = {
        "market_direction": {"label": "BULLISH", "confidence": 85.5},
        "execution_profile": {"mode": "AGGRESSIVE", "selectivity": "LOW", "max_risk_per_trade_pct": 2.0},
        "daily_report": {"summary": ["Market is mooning"]},
        "recommendations": [{"ticker": "BTC", "action": "BUY", "confidence": 90, "entry_zone": "50k", "stop_loss": "48k", "take_profit": "60k"}],
        "risk_warnings": ["Volatility is high"]
    }
    msg = build_ai_report_telegram_message(payload)
    assert "HORUS AI DAILY MARKET REPORT" in msg
    assert "BULLISH" in msg
    assert "85.5%" in msg
    assert "BTC" in msg
    assert "BUY" in msg
    assert "Volatility is high" in msg


def test_build_ai_report_telegram_message_formats_status_labels():
    payload = {
        "market_direction": {"label": "NEUTRAL", "confidence": 52.0},
        "execution_profile": {
            "mode": "CAPITAL_PRESERVATION",
            "selectivity": "VERY_HIGH",
            "max_risk_per_trade_pct": 0.5,
        },
        "daily_report": {"summary": ["Risk first"]},
        "recommendations": [],
        "risk_warnings": [],
    }

    msg = build_ai_report_telegram_message(payload)

    assert "CAPITAL PRESERVATION" in msg
    assert "VERY HIGH" in msg
    assert "CAPITALPRESERVATION" not in msg
    assert "VERYHIGH" not in msg


def test_build_ai_report_telegram_message_separates_cash_stance_from_setups():
    payload = {
        "market_direction": {"label": "NEUTRAL", "confidence": 52.0},
        "execution_profile": {"mode": "CAPITAL_PRESERVATION", "selectivity": "VERY_HIGH"},
        "daily_report": {"summary": ["Preserve capital"]},
        "recommendations": [
            {"ticker": "CASH", "action": "HOLD", "confidence": 75},
            {
                "ticker": "ORWE",
                "action": "WATCH",
                "confidence": 52,
                "entry_zone": "23.75 - 24.00",
                "stop_loss": "22.35",
                "take_profit": "26.07",
            },
        ],
        "risk_warnings": [],
    }

    msg = build_ai_report_telegram_message(payload)

    assert "Execution Stance" in msg
    assert "CASH" in msg
    assert msg.index("CASH") < msg.index("Top Setups")
    top_setups = msg.split("*Top Setups*", 1)[1]
    assert "ORWE" in top_setups
    assert "CASH" not in top_setups
