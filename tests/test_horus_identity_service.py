from database import Portfolio

from core.horus.identity import (
    get_horus_portfolio,
    get_horus_portfolio_id,
    resolve_preferred_user_portfolio,
)


def test_get_horus_portfolio_returns_none_when_missing():
    assert get_horus_portfolio() is None
    assert get_horus_portfolio_id() is None


def test_get_horus_portfolio_returns_horus_user_portfolio():
    horus = Portfolio.create(name="Horus", type="USER")

    assert get_horus_portfolio() == horus
    assert get_horus_portfolio_id() == horus.id


def test_resolve_preferred_user_portfolio_prefers_horus_then_my_portfolio_then_any_user():
    fallback = Portfolio.create(name="Fallback", type="USER")
    assert resolve_preferred_user_portfolio() == fallback

    my_portfolio = Portfolio.create(name="My Portfolio", type="USER")
    assert resolve_preferred_user_portfolio() == my_portfolio

    horus = Portfolio.create(name="Horus", type="USER")
    assert resolve_preferred_user_portfolio() == horus
