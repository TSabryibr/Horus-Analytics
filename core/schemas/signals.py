"""
HORUS ANALYTICS - SIGNAL & SCANNER SCHEMAS
==========================================
Pydantic V2 schemas for signal generation, recommendations, deliveries, and scans.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import HorusBaseModel


class ScannerRunRequest(HorusBaseModel):
    """Payload to trigger a market scan."""

    strategy: Optional[str] = Field(default="ALL", description="Target strategy or ALL")
    tickers: Optional[List[str]] = Field(default=None, description="Specific ticker universe")
    force: bool = Field(default=False, description="Bypass rate limit or freshness restrictions if permitted")


class SignalPublishRequest(HorusBaseModel):
    """Payload to manually publish generated signals to subscribers."""

    signal_ids: Optional[List[int]] = Field(default=None, description="List of signal IDs to publish")
    channels: Optional[List[str]] = Field(default=None, description="Destination channels (e.g. telegram, discord, email)")
    run_id: Optional[str] = Field(default=None, description="Optional pipeline run ID")


class SignalPublishRetryRequest(HorusBaseModel):
    """Payload for retrying failed signal deliveries."""

    delivery_ids: Optional[List[int]] = Field(default=None, description="Delivery IDs to retry")
    max_retries: int = Field(default=3, ge=1, le=10)


class SignalCardRequest(HorusBaseModel):
    """Payload for generating branded visual signal cards."""

    ticker: str = Field(..., min_length=1, max_length=20)
    action: str = Field(..., description="BUY, SELL, HOLD, EXIT")
    price: float = Field(..., gt=0)
    strategy: Optional[str] = Field(default="HORUS_AI")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    stop_loss: Optional[float] = Field(default=None, gt=0)
    target_price: Optional[float] = Field(default=None, gt=0)
    timeframe: Optional[str] = Field(default="DAILY")
    notes: Optional[str] = Field(default=None)


class SignalRecommendationResponse(HorusBaseModel):
    """Schema representing an institutional signal recommendation."""

    id: int
    ticker: str
    action: str
    confidence_score: Optional[float] = None
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    risk_reward_ratio: Optional[float] = None
    strategy_name: Optional[str] = None
    market_regime: Optional[str] = None
    status: str = "ACTIVE"
    created_at: Optional[str] = None
