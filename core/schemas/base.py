"""
HORUS ANALYTICS - BASE PYDANTIC V2 SCHEMAS
==========================================
Foundation models and standard API envelopes with Pydantic V2 ConfigDict.
"""

from __future__ import annotations

from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, Field


class HorusBaseModel(BaseModel):
    """Base model with institutional serialization defaults."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="ignore",
        str_strip_whitespace=True,
        validate_assignment=True,
    )


T = TypeVar("T")


class StandardApiResponse(HorusBaseModel, Generic[T]):
    """Standard unified response wrapper for Horus API endpoints."""

    status: str = Field(default="success", description="Status string (success, error, degraded)")
    message: Optional[str] = Field(default=None, description="Human readable message or diagnostic")
    data: Optional[T] = Field(default=None, description="Typed payload data")
    request_id: Optional[str] = Field(default=None, description="Correlation trace ID")


class ErrorApiResponse(HorusBaseModel):
    """Unified error response model."""

    status: str = Field(default="error")
    message: str = Field(..., description="Error message description")
    error_id: Optional[str] = Field(default=None, description="Unique error or request ID")
    request_id: Optional[str] = Field(default=None, description="Correlation trace ID")
    error_type: Optional[str] = Field(default=None, description="Exception class name")
    method: Optional[str] = Field(default=None, description="HTTP method")
    path: Optional[str] = Field(default=None, description="HTTP request path")


class PaginationParams(HorusBaseModel):
    """Common pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number starting from 1")
    page_size: int = Field(default=50, ge=1, le=1000, description="Items per page")


class DateRangeFilter(HorusBaseModel):
    """Date filtering parameters."""

    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
