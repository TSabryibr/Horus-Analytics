"""
Tests for Pydantic V2 Schemas in core/schemas.
"""

import pytest
from pydantic import ValidationError

from core.schemas import (
    CloseTradeRequest,
    CreatePortfolioRequest,
    GenesisRequest,
    HealthResponse,
    HolidayConfirmRequest,
    RiskCheckRequest,
    ScannerRunRequest,
    SignalCardRequest,
    StandardApiResponse,
    TradeCreateRequest,
)


def test_trade_create_request_validation():
    # Valid
    req = TradeCreateRequest(
        ticker="COMI.CA",
        shares=100.0,
        entry_price=55.50,
        stop_loss=50.0,
        target_price=65.0,
    )
    assert req.ticker == "COMI.CA"
    assert req.shares == 100.0
    assert req.entry_price == 55.50

    # Invalid shares <= 0
    with pytest.raises(ValidationError):
        TradeCreateRequest(ticker="COMI.CA", shares=0, entry_price=55.50)

    # Invalid entry_price <= 0
    with pytest.raises(ValidationError):
        TradeCreateRequest(ticker="COMI.CA", shares=10, entry_price=-5.0)


def test_close_trade_request_validation():
    req = CloseTradeRequest(exit_price=60.0, exit_reason="TARGET_HIT")
    assert req.exit_price == 60.0
    assert req.exit_reason == "TARGET_HIT"

    with pytest.raises(ValidationError):
        CloseTradeRequest(exit_price=0)


def test_signal_card_request_validation():
    req = SignalCardRequest(ticker="SWDY.CA", action="BUY", price=42.0, confidence=88.5)
    assert req.ticker == "SWDY.CA"
    assert req.confidence == 88.5

    # Out of range confidence
    with pytest.raises(ValidationError):
        SignalCardRequest(ticker="SWDY.CA", action="BUY", price=42.0, confidence=150.0)


def test_standard_api_envelope():
    resp = StandardApiResponse[dict](
        status="success",
        message="Operation completed",
        data={"items_processed": 5},
        request_id="req-999",
    )
    payload = resp.model_dump()
    assert payload["status"] == "success"
    assert payload["data"]["items_processed"] == 5
    assert payload["request_id"] == "req-999"
