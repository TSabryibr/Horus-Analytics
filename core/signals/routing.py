from typing import Optional
from database import Portfolio

ROUTING_MAP = {
    "INTRADAY": "Intraday Signals",
    "PRE_CLOSE": "Swing Signals",
    "DAILY": "Swing Signals",
    "DAILY_NEXT_OPEN": "Swing Signals",
    "WEEKLY": "Position Signals",
}

def resolve_target_portfolio(scan_type: str) -> Optional[Portfolio]:
    """Maps a scan type to its target portfolio, respecting settings override and default system portfolio."""
    from core.settings import settings
    target_name = getattr(settings, "AUTO_TRADE_TARGET_PORTFOLIO_NAME", None)
    if target_name:
        port = Portfolio.get_or_none(Portfolio.name == target_name)
        if port:
            return port

    from core.portfolio.identity import get_default_system_portfolio
    try:
        default_port = get_default_system_portfolio()
        if default_port:
            return default_port
    except Exception:
        pass

    name = ROUTING_MAP.get(scan_type.upper())
    if not name:
        return None
    return Portfolio.get_or_none(
        (Portfolio.name == name) & (Portfolio.type == "SYSTEM")
    )

def resolve_target_portfolio_name(scan_type: str) -> Optional[str]:
    """Returns the target portfolio name for a given scan type."""
    from core.settings import settings
    target_name = getattr(settings, "AUTO_TRADE_TARGET_PORTFOLIO_NAME", None)
    if target_name:
        return target_name

    from core.portfolio.identity import get_default_system_portfolio
    try:
        default_port = get_default_system_portfolio()
        if default_port:
            return default_port.name
    except Exception:
        pass

    return ROUTING_MAP.get(scan_type.upper())
