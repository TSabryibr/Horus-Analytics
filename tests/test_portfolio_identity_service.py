import pytest
from fastapi import HTTPException
from pydantic import BaseModel, Field, ValidationError

from database import Portfolio

from core.portfolio.identity import (
    enforce_manual_entry_gate,
    get_default_system_portfolio_id,
    resolve_portfolio_id,
    resolve_startup_portfolio_id,
    set_default_system_portfolio_id,
    validation_error_detail,
)


class _TickerPayload(BaseModel):
    ticker: str = Field(..., min_length=1)


class _NamePayload(BaseModel):
    name: str = Field(..., min_length=1)


def test_resolve_portfolio_id_returns_explicit_id():
    assert resolve_portfolio_id(7) == 7


def test_resolve_portfolio_id_prefers_horus_user():
    my_portfolio = Portfolio.create(name="My Portfolio", type="USER")
    horus = Portfolio.create(name="Horus", type="USER")

    assert resolve_portfolio_id(None) == horus.id
    assert my_portfolio.id != horus.id


def test_resolve_portfolio_id_falls_back_to_my_portfolio_user():
    other = Portfolio.create(name="Other User Portfolio", type="USER")
    preferred = Portfolio.create(name="My Portfolio", type="USER")

    assert resolve_portfolio_id(None) == preferred.id
    assert other.id != preferred.id


def test_resolve_portfolio_id_falls_back_to_any_user():
    user_portfolio = Portfolio.create(name="Fallback User Portfolio", type="USER")

    assert resolve_portfolio_id(None) == user_portfolio.id


def test_resolve_portfolio_id_returns_none_when_no_user_portfolio_exists():
    assert resolve_portfolio_id(None) is None


def test_set_default_system_portfolio_id_persists_system_portfolio():
    system_portfolio = Portfolio.create(name="System Default", type="SYSTEM")

    saved_portfolio = set_default_system_portfolio_id(system_portfolio.id)

    assert saved_portfolio.id == system_portfolio.id
    assert get_default_system_portfolio_id() == system_portfolio.id


def test_set_default_system_portfolio_id_rejects_user_portfolio():
    user_portfolio = Portfolio.create(name="User Default Attempt", type="USER")

    with pytest.raises(HTTPException) as exc_info:
        set_default_system_portfolio_id(user_portfolio.id)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Only SYSTEM portfolios can be set as the global default"


def test_resolve_startup_portfolio_id_prefers_persisted_default_system_portfolio():
    fallback_system = Portfolio.get(Portfolio.name == "Intraday Signals")
    preferred_system = Portfolio.create(name="Intraday Signals X", type="SYSTEM")
    Portfolio.create(name="Horus", type="USER")
    set_default_system_portfolio_id(preferred_system.id)

    assert resolve_startup_portfolio_id() == preferred_system.id
    assert fallback_system.id != preferred_system.id


def test_resolve_startup_portfolio_id_falls_back_to_any_system_before_user():
    system_portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    user_portfolio = Portfolio.create(name="Horus", type="USER")

    assert resolve_startup_portfolio_id() == system_portfolio.id
    assert system_portfolio.id != user_portfolio.id


def test_enforce_manual_entry_gate_returns_normalized_symbol_and_gate():
    symbol, gate = enforce_manual_entry_gate(
        "  comi  ",
        normalize_ticker_fn=lambda ticker: ticker.strip().upper(),
        assert_ticker_allowed_fn=lambda ticker: None,
        get_trade_permission_fn=lambda ticker, fail_closed=True: {"allowed": True, "reason": "ok"},
    )

    assert symbol == "COMI"
    assert gate == {"allowed": True, "reason": "ok"}


def test_enforce_manual_entry_gate_rejects_blank_symbol_after_normalization():
    with pytest.raises(HTTPException) as exc_info:
        enforce_manual_entry_gate(
            "   ",
            normalize_ticker_fn=lambda ticker: "",
            assert_ticker_allowed_fn=lambda ticker: None,
            get_trade_permission_fn=lambda ticker, fail_closed=True: {"allowed": True},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Ticker is required"


def test_enforce_manual_entry_gate_wraps_wfa_lookup_failure():
    with pytest.raises(HTTPException) as exc_info:
        enforce_manual_entry_gate(
            "COMI",
            normalize_ticker_fn=lambda ticker: ticker,
            assert_ticker_allowed_fn=lambda ticker: None,
            get_trade_permission_fn=lambda ticker, fail_closed=True: (_ for _ in ()).throw(RuntimeError("boom")),
        )

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "WFA gate lookup failed for COMI: boom"


def test_validation_error_detail_maps_ticker_field():
    with pytest.raises(ValidationError) as exc_info:
        _TickerPayload(ticker="")

    assert validation_error_detail(exc_info.value) == "Ticker required"


def test_validation_error_detail_maps_name_field():
    with pytest.raises(ValidationError) as exc_info:
        _NamePayload(name="")

    assert validation_error_detail(exc_info.value) == "name is required"
