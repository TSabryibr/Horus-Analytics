"""
HORUS ANALYTICS - PORTFOLIO & TRADING SCHEMAS
=============================================
Pydantic V2 schemas for portfolio management, trade execution, and position tracking.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import HorusBaseModel


class TradeCreateRequest(HorusBaseModel):
    """Payload for opening or appending a portfolio position."""

    ticker: str = Field(..., min_length=1, max_length=20, description="Asset ticker symbol")
    shares: float = Field(..., gt=0, description="Quantity of shares (positive float)")
    entry_price: float = Field(..., gt=0, description="Entry purchase price")
    entry_date: Optional[str] = Field(default=None, description="Date of entry (YYYY-MM-DD)")
    target_price: Optional[float] = Field(default=None, gt=0, description="Profit target price")
    stop_loss: Optional[float] = Field(default=None, gt=0, description="Stop loss price")
    strategy: Optional[str] = Field(default=None, description="Strategy name or signal trigger")
    notes: Optional[str] = Field(default=None, description="Trade rationale or notes")
    portfolio_id: Optional[int] = Field(default=None, description="Target portfolio ID")


class CloseTradeRequest(HorusBaseModel):
    """Payload for exiting an active position."""

    exit_price: float = Field(..., gt=0, description="Exit price per share")
    exit_date: Optional[str] = Field(default=None, description="Date of exit (YYYY-MM-DD)")
    exit_reason: Optional[str] = Field(default="MANUAL", description="Reason for trade exit")
    shares_to_close: Optional[float] = Field(default=None, gt=0, description="Partial exit share count")


class CreatePortfolioRequest(HorusBaseModel):
    """Payload for creating a new portfolio container."""

    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name")
    initial_cash: float = Field(default=100000.0, ge=0, description="Starting cash allocation")
    currency: str = Field(default="USD", max_length=10, description="Base currency")
    description: Optional[str] = Field(default=None, description="Portfolio description")


class SetDefaultPortfolioRequest(HorusBaseModel):
    """Payload for setting the system default portfolio."""

    portfolio_id: int = Field(..., description="Portfolio ID to mark default")


class RiskCheckRequest(HorusBaseModel):
    """Payload for pre-trade risk evaluation."""

    ticker: str = Field(..., min_length=1, max_length=20)
    proposed_shares: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    portfolio_id: Optional[int] = Field(default=None)


class GenesisHolding(HorusBaseModel):
    """Single position initialization item for portfolio seeding."""

    ticker: str = Field(..., min_length=1, max_length=20)
    shares: float = Field(..., gt=0)
    entry_price: float = Field(..., gt=0)
    entry_date: Optional[str] = Field(default=None)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    target_price: Optional[float] = Field(default=None, gt=0)


class GenesisRequest(HorusBaseModel):
    """Bulk portfolio seed request."""

    holdings: List[GenesisHolding] = Field(default_factory=list)
    initial_cash: Optional[float] = Field(default=100000.0, ge=0)
    portfolio_name: Optional[str] = Field(default="Default Portfolio")


class PositionResponse(HorusBaseModel):
    """Schema representing an active or closed position."""

    id: int
    ticker: str
    shares: float
    entry_price: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    status: str = "OPEN"
    entry_date: Optional[str] = None
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    realized_pnl: Optional[float] = None


class ManagedHoldingInput(HorusBaseModel):
    """Holding item for portfolio intake."""

    ticker: str
    shares: Optional[float] = Field(default=None, gt=0)
    entry_price: Optional[float] = Field(default=None, gt=0)
    total_cost: Optional[float] = Field(default=None, gt=0)
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    currency: Optional[str] = "EGP"
    sector: Optional[str] = None
    notes: Optional[str] = None


class PortfolioIntakeRequest(HorusBaseModel):
    """Request payload for bulk portfolio intake."""

    portfolio_id: Optional[int] = Field(default=None, ge=1)
    holdings: List[ManagedHoldingInput]
    refresh_prices: bool = True


class PortfolioReportSendRequest(HorusBaseModel):
    """Request payload to generate and send portfolio report."""

    portfolio_id: Optional[int] = Field(default=None, ge=1)
    include_positions: int = 15
    chat_id: Optional[str] = None
    refresh_prices: bool = True


class UpdateRequest(HorusBaseModel):
    """Request payload for updating an active position."""

    ticker: str = Field(..., min_length=1)
    sl: Optional[float] = None
    tp: Optional[float] = None
    tp2: Optional[float] = None
    shares: Optional[float] = Field(default=None, gt=0)
    price: Optional[float] = Field(default=None, gt=0)
    portfolio_id: Optional[int] = Field(default=1, ge=1)

