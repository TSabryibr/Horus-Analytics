from typing import Any

from database import Portfolio


def ensure_strategy_profile_portfolio(profile: Any) -> Portfolio:
    profile_name = str(getattr(profile, "profile_name", "") or "").strip()
    if not profile_name:
        raise ValueError("strategy profile name is required")

    description = (
        f"Auto-managed portfolio for strategy profile '{profile_name}'. "
        "Signals generated from this strategy profile are attributed here by default."
    )
    portfolio, created = Portfolio.get_or_create(
        name=profile_name,
        defaults={
            "type": "STRATEGY",
            "auto_manage": True,
            "description": description,
        },
    )
    if not created:
        changed = False
        if portfolio.type != "STRATEGY":
            portfolio.type = "STRATEGY"
            changed = True
        if not portfolio.auto_manage:
            portfolio.auto_manage = True
            changed = True
        if not portfolio.description:
            portfolio.description = description
            changed = True
        if changed:
            portfolio.save()
    return portfolio


def resolve_strategy_profile_portfolio(profile_name: str) -> Portfolio | None:
    normalized = str(profile_name or "").strip()
    if not normalized:
        return None
    return Portfolio.get_or_none(
        (Portfolio.name == normalized) &
        (
            (Portfolio.type == "STRATEGY") |
            ((Portfolio.type == "USER") & (Portfolio.auto_manage == True))
        )
    )


def serialize_strategy_profile_portfolio(portfolio: Portfolio) -> dict[str, Any]:
    return {
        "id": portfolio.id,
        "name": portfolio.name,
        "type": portfolio.type,
        "auto_manage": bool(portfolio.auto_manage),
    }
