"""
HORUS ANALYTICS - SYSTEM & TELEMETRY SCHEMAS
============================================
Pydantic V2 schemas for health checks, system status, diagnostics, and holidays.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import Field
from .base import HorusBaseModel


class HealthResponse(HorusBaseModel):
    """Health check payload for container orchestration and uptime monitors."""

    status: str = Field(default="ok")
    pipeline_state: str = Field(default="FRESH")
    bootstrap_complete: bool = Field(default=True)
    version: Optional[str] = Field(default=None)
    timestamp: Optional[str] = Field(default=None)
    details: Optional[Dict[str, Any]] = Field(default=None)


class HolidayConfirmRequest(HorusBaseModel):
    """Payload for registering or confirming a market holiday."""

    date: str = Field(..., description="Date of holiday (YYYY-MM-DD)")
    name: str = Field(..., min_length=1, max_length=100, description="Holiday description/name")
    market: Optional[str] = Field(default="EGX", description="Target market exchange")


class SystemStatusResponse(HorusBaseModel):
    """Comprehensive system status payload."""

    status: str = "READY"
    pipeline_state: str = "FRESH"
    bootstrap_complete: bool = True
    active_portfolios: int = 0
    total_positions: int = 0
    db_connected: bool = True
    session_mode: str = "LIVE"
    market_regime: Optional[str] = None
    last_sync: Optional[str] = None
    message: Optional[str] = None
