"""
HORUS ANALYTICS - PORTFOLIO DOMAIN SERVICE
==========================================
Clean service layer encapsulating portfolio queries, trade execution,
risk checks, performance tracking, and snapshots.

All methods delegate to the respective core command / query with
their built-in dependency-injection defaults, so routes no longer
need to wire explicit _fn arguments.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import logging

from core.portfolio.commands import (
    add_trade_command,
    close_trade_command,
    initialize_portfolio_genesis_command,
    seed_demo_portfolio_command,
    update_trade_command,
)
from core.portfolio.identity import (
    clear_default_system_portfolio_id,
    get_default_system_portfolio,
    get_default_system_portfolio_id,
    resolve_portfolio_id,
    resolve_startup_portfolio_id,
    set_default_system_portfolio_id,
)
from core.portfolio.queries import (
    get_equity_curve_query,
    get_portfolio_analysis_query,
    get_portfolio_metrics_query,
    get_portfolio_query,
    get_portfolio_report_query,
    get_positions_query,
    get_trades_query,
)
from core.portfolio.management import (
    build_portfolio_management_report,
    get_portfolio_rebalancing_command,
    intake_portfolio_holdings_command,
    trigger_portfolio_snapshot_command,
)

logger = logging.getLogger("horus.services.portfolio")


class PortfolioService:
    """Institutional portfolio domain service.

    Provides a stable, mockable interface over the raw command/query
    layer.  All dependency-injection wiring is handled by the underlying
    core functions via their default parameter values.
    """

    # ------------------------------------------------------------------
    # Identity helpers
    # ------------------------------------------------------------------

    def resolve_id(self, portfolio_id: Optional[int] = None) -> Optional[int]:
        """Resolves target portfolio ID or returns system default."""
        return resolve_portfolio_id(portfolio_id)

    def get_default_portfolio(self) -> Optional[Any]:
        """Retrieves the default system portfolio entity."""
        return get_default_system_portfolio()

    def set_default_portfolio(self, portfolio_id: int) -> Any:
        """Updates the default system portfolio."""
        return set_default_system_portfolio_id(portfolio_id)

    # ------------------------------------------------------------------
    # Read queries — all DI defaults are baked into the query functions
    # ------------------------------------------------------------------

    def get_portfolio(self, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """Retrieves portfolio summary, holdings, and cash balance.

        Raises HTTPException 404 when no portfolio exists.
        """
        return get_portfolio_query(portfolio_id=portfolio_id)

    def get_positions(self, portfolio_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieves all currently open positions."""
        return get_positions_query(portfolio_id=portfolio_id)

    def get_trades(
        self,
        portfolio_id: Optional[int] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieves trade audit ledger (most-recent first)."""
        return get_trades_query(limit=limit, portfolio_id=portfolio_id)

    def get_metrics(self, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """Calculates institutional portfolio metrics (Sharpe, Drawdown, Win Rate)."""
        return get_portfolio_metrics_query(portfolio_id=portfolio_id)

    def get_equity_curve(self, portfolio_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Generates historical equity curve time-series."""
        return get_equity_curve_query(portfolio_id=portfolio_id)

    def get_report(
        self,
        portfolio_id: Optional[int] = None,
        trades_limit: int = 20,
    ) -> Dict[str, Any]:
        """Returns a combined metrics + curve + trades report."""
        return get_portfolio_report_query(
            portfolio_id=portfolio_id,
            trades_limit=trades_limit,
        )

    def get_analysis(self, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """Returns risk/correlation analysis for the portfolio."""
        return get_portfolio_analysis_query(portfolio_id=portfolio_id)

    # ------------------------------------------------------------------
    # Write commands — accept the validated Pydantic request model
    # (same interface the route handlers receive from FastAPI)
    # ------------------------------------------------------------------

    def add_trade(self, req: Any) -> Dict[str, Any]:
        """Executes a new trade / position-open command.

        Args:
            req: A Pydantic model with fields: ticker, shares, price,
                 type, sl, tp, tp2, date, portfolio_id.
        """
        return add_trade_command(req)

    def close_trade(self, req: Any) -> Dict[str, Any]:
        """Closes an active position and calculates realized PnL.

        Args:
            req: A Pydantic model with fields: ticker, price, shares,
                 portfolio_id.
        """
        return close_trade_command(req)

    def update_trade(self, req: Any) -> Dict[str, Any]:
        """Updates stop-loss / take-profit levels on an open position.

        Args:
            req: A Pydantic model with fields: ticker, sl, tp, tp2,
                 shares, price, portfolio_id.
        """
        return update_trade_command(req)

    def initialize_genesis(self, req: Any) -> Dict[str, Any]:
        """Seeds a portfolio from a genesis holdings manifest.

        Args:
            req: A Pydantic GenesisRequest model.
        """
        return initialize_portfolio_genesis_command(req)

    # ------------------------------------------------------------------
    # Operational commands
    # ------------------------------------------------------------------

    def trigger_snapshot(self, portfolio_id: Optional[int] = None) -> Dict[str, Any]:
        """Captures an immutable portfolio equity snapshot.

        Raises HTTPException 404 when portfolio doesn't exist.
        """
        return trigger_portfolio_snapshot_command(portfolio_id=portfolio_id)

    def get_rebalancing(
        self,
        portfolio_id: Optional[int] = None,
        model: str = "EQUAL_WEIGHT",
    ) -> Dict[str, Any]:
        """Returns position-level rebalancing recommendations."""
        return get_portfolio_rebalancing_command(
            portfolio_id=portfolio_id,
            model=model,
        )


# Singleton service instance consumed by route handlers
portfolio_service = PortfolioService()
