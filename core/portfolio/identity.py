import datetime
from typing import Any, Callable, Optional

from fastapi import HTTPException
from pydantic import ValidationError

from database import Portfolio, PortfolioDefaultState
from core import WalkForwardValidation
from core.horus.identity import resolve_preferred_user_portfolio
from core.exclusions import assert_ticker_allowed, normalize_ticker

GLOBAL_DEFAULT_PORTFOLIO_STATE = "GLOBAL_DEFAULT"


def resolve_portfolio_id(portfolio_id: Optional[int]) -> Optional[int]:
    if portfolio_id:
        return portfolio_id

    preferred = resolve_preferred_user_portfolio()
    if preferred:
        return preferred.id

    return None


def _get_or_create_default_state() -> PortfolioDefaultState:
    state, _ = PortfolioDefaultState.get_or_create(name=GLOBAL_DEFAULT_PORTFOLIO_STATE)
    return state


def clear_default_system_portfolio_id() -> None:
    state = PortfolioDefaultState.get_or_none(PortfolioDefaultState.name == GLOBAL_DEFAULT_PORTFOLIO_STATE)
    if not state:
        return
    if state.portfolio_id is None:
        return
    state.portfolio = None
    state.updated_at = datetime.datetime.now()
    state.save()


def get_default_system_portfolio() -> Optional[Portfolio]:
    state = PortfolioDefaultState.get_or_none(PortfolioDefaultState.name == GLOBAL_DEFAULT_PORTFOLIO_STATE)
    if not state or state.portfolio_id is None:
        return None

    portfolio = Portfolio.get_or_none(Portfolio.id == state.portfolio_id)
    if portfolio is None or portfolio.type != "SYSTEM":
        clear_default_system_portfolio_id()
        return None

    return portfolio


def get_default_system_portfolio_id() -> Optional[int]:
    portfolio = get_default_system_portfolio()
    return portfolio.id if portfolio else None


def set_default_system_portfolio_id(portfolio_id: int) -> Portfolio:
    portfolio = Portfolio.get_or_none(Portfolio.id == portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if portfolio.type != "SYSTEM":
        raise HTTPException(status_code=400, detail="Only SYSTEM portfolios can be set as the global default")

    state = _get_or_create_default_state()
    state.portfolio = portfolio
    state.updated_at = datetime.datetime.now()
    state.save()
    return portfolio


def resolve_startup_portfolio_id() -> Optional[int]:
    default_system_id = get_default_system_portfolio_id()
    if default_system_id:
        return default_system_id

    first_system = Portfolio.select().where(Portfolio.type == "SYSTEM").order_by(Portfolio.id.asc()).first()
    if first_system:
        return first_system.id

    preferred = resolve_preferred_user_portfolio()
    if preferred:
        return preferred.id

    any_portfolio = Portfolio.select().order_by(Portfolio.id.asc()).first()
    return any_portfolio.id if any_portfolio else None


def enforce_manual_entry_gate(
    ticker: str,
    *,
    normalize_ticker_fn: Optional[Callable[[str], str]] = None,
    assert_ticker_allowed_fn: Optional[Callable[[str], Any]] = None,
    get_trade_permission_fn: Optional[Callable[..., dict[str, Any]]] = None,
) -> tuple[str, dict[str, Any]]:
    normalize_fn = normalize_ticker_fn or normalize_ticker
    assert_allowed_fn = assert_ticker_allowed_fn or assert_ticker_allowed
    get_permission_fn = get_trade_permission_fn or WalkForwardValidation.get_trade_permission

    symbol = normalize_fn(ticker)
    if not symbol:
        raise HTTPException(status_code=400, detail="Ticker is required")

    assert_allowed_fn(symbol)
    try:
        gate = get_permission_fn(symbol, fail_closed=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"WFA gate lookup failed for {symbol}: {exc}")

    if not gate.get("allowed", False):
        reason = gate.get("reason", "blocked")
        raise HTTPException(status_code=403, detail=f"WFA gate blocked {symbol}: {reason}")

    return symbol, gate


def validation_error_detail(exc: ValidationError) -> str:
    first_error = (exc.errors() or [{}])[0]
    field = ".".join(str(part) for part in first_error.get("loc", ()) if part != "body").strip()
    if field == "ticker":
        return "Ticker required"
    if field == "name":
        return "name is required"
    message = str(first_error.get("msg") or "Invalid request")
    return f"{field}: {message}" if field else message
