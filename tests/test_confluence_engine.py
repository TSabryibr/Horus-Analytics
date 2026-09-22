import pytest
from core.confluence import ConfluenceEngine

def test_confluence_engine_evaluation():
    # Test neutral ticker
    res = ConfluenceEngine.evaluate_ticker("COMI")
    assert "ticker" in res
    assert res["ticker"] == "COMI"
    assert 1 <= res["stars"] <= 5
    assert "rating" in res
    assert isinstance(res["tags"], list)

def test_confluence_engine_bullish_tailwinds():
    mock_oracle = {"status": "BULLISH", "forecast": "UP"}
    mock_whales = {"candidates": [{"Ticker": "COMI", "Signal": "ACCUMULATION"}]}
    mock_traps = {"bull_traps": [], "bear_traps": [{"Ticker": "COMI", "Signal": "BEAR TRAP (BUY)"}]}
    mock_sectors = {"sectors": [{"Sector": "Banking", "Trend": "LEADING", "Rotation_Score": 105}]}

    res = ConfluenceEngine.evaluate_ticker(
        "COMI",
        sector_data=mock_sectors,
        whale_data=mock_whales,
        trap_data=mock_traps,
        oracle_data=mock_oracle
    )

    assert res["stars"] >= 4
    assert res["rating"] in ["HIGH_CONVICTION_BUY", "ACCUMULATE"]
    assert "WHALE_ACCUMULATION" in res["tags"]
    assert "SPRING_REVERSAL" in res["tags"]

def test_confluence_engine_defensive_warnings():
    mock_whales = {"candidates": [{"Ticker": "COMI", "Signal": "DISTRIBUTION"}]}
    mock_traps = {"bull_traps": [{"Ticker": "COMI", "Signal": "BULL TRAP (SELL)"}], "bear_traps": []}

    res = ConfluenceEngine.evaluate_ticker(
        "COMI",
        whale_data=mock_whales,
        trap_data=mock_traps
    )

    assert len(res["warnings"]) > 0
    assert any("Bull Trap" in w or "Whale" in w for w in res["warnings"])
