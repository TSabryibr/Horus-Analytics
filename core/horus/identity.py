from typing import Optional

from database import Portfolio


HORUS_PORTFOLIO_NAME = "Horus"


def get_horus_portfolio() -> Optional[Portfolio]:
    return Portfolio.get_or_none((Portfolio.type == "USER") & (Portfolio.name == HORUS_PORTFOLIO_NAME))


def get_horus_portfolio_id() -> Optional[int]:
    portfolio = get_horus_portfolio()
    return portfolio.id if portfolio else None


def resolve_preferred_user_portfolio() -> Optional[Portfolio]:
    horus = get_horus_portfolio()
    if horus:
        return horus

    preferred = Portfolio.get_or_none((Portfolio.type == "USER") & (Portfolio.name == "My Portfolio"))
    if preferred:
        return preferred

    return Portfolio.get_or_none(Portfolio.type == "USER")
