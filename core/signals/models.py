from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any, Annotated
from datetime import datetime

class DailyRunRequest(BaseModel):
    run_date: Optional[str] = None  # YYYY-MM-DD
    scan_type: str = "DAILY"  # DAILY | INTRADAY | PRE_CLOSE
    run_key: Optional[str] = None
    force: bool = False
    notify: bool = False
    index: str = "EGX30"
    model_version: Optional[str] = None
    ignore_guard: bool = False


class PublishSignalsRequest(BaseModel):
    run_id: Optional[int] = Field(None, ge=1)
    portfolio_ids: Optional[List[Annotated[int, Field(ge=1)]]] = None
    retry_delivery_ids: Optional[List[Annotated[int, Field(ge=1)]]] = None
    channel: str = "TELEGRAM"
    service_tier: str = "SIGNALS_ONLY"
    operating_mode: str = "MANUAL"
    include_portfolios: bool = True
    include_subscribers: bool = True
    include_main_channel: bool = True
    dry_run: bool = False
    max_retries: int = Field(default=2, ge=0, le=5)
    backoff_ms: int = Field(default=500, ge=0, le=20000)
    enforce_window: bool = False
    ignore_guard: bool = False


class RetryFailedDeliveriesRequest(BaseModel):
    run_id: int = Field(..., ge=1)
    channel: str = "TELEGRAM"
    max_retries: int = Field(default=2, ge=0, le=5)
    backoff_ms: int = Field(default=500, ge=0, le=20000)
    enforce_window: bool = False


class RebuildOutcomesRequest(BaseModel):
    run_id: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class WalkforwardValidationRequest(BaseModel):
    window_days: int = Field(default=90, ge=7, le=3650)
    min_closed_signals: int = Field(default=20, ge=1, le=100000)
    min_win_rate_pct: float = Field(default=45.0, ge=0.0, le=100.0)
    min_avg_pnl_pct: float = Field(default=0.0, ge=-1000.0, le=1000.0)
    min_week_win_rate_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    max_consecutive_weak_weeks: int = Field(default=2, ge=1, le=52)
    auto_block: bool = True
    auto_unblock: bool = True


class GuardStateUpdateRequest(BaseModel):
    is_blocked: bool
    reason: Optional[str] = None
    source: str = "MANUAL"
    details: Optional[dict] = None


class SignalDeskModeUpdateRequest(BaseModel):
    operating_mode: str = Field(..., min_length=3, max_length=32)
    autopilot_armed: Optional[bool] = None
    publish_policy: Optional[dict] = None


class SignalDeskPromotionRequest(BaseModel):
    lane: str = Field(..., min_length=3, max_length=32)
    ticker: str = Field(..., min_length=1, max_length=32)
    side: str = Field(default="BUY", min_length=3, max_length=8)
    entry_price: float = Field(..., gt=0)
    stop_loss: float = Field(..., gt=0)
    target_price: float = Field(..., gt=0)
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    score: float = Field(default=0.0, ge=0.0)
    horizon_days: Optional[int] = Field(default=None, ge=1, le=365)
    source_module: Optional[str] = None
    rationale: Optional[dict] = None

    @model_validator(mode='after')
    def validate_price_levels(self):
        side_upper = self.side.upper()
        if side_upper == 'BUY':
            if not (self.stop_loss < self.entry_price < self.target_price):
                raise ValueError('For BUY signals, prices must be: stop_loss < entry_price < target_price')
        elif side_upper == 'SELL':
            if not (self.stop_loss > self.entry_price > self.target_price):
                raise ValueError('For SELL signals, prices must be: stop_loss > entry_price > target_price')
        return self


class SignalDeskAutopilotRequest(BaseModel):
    run_id: Optional[int] = Field(default=None, ge=1)
    dry_run: bool = False
    max_retries: int = Field(default=2, ge=0, le=5)
    backoff_ms: int = Field(default=500, ge=0, le=20000)
    enforce_window: bool = True
    ignore_guard: bool = False


class SignalLifecycleOverrideRequest(BaseModel):
    action: str = Field(..., min_length=3, max_length=64)
    notes: Optional[str] = None
    fill_price: Optional[float] = Field(default=None, gt=0)
    close_price: Optional[float] = Field(default=None, gt=0)
    target_state: Optional[str] = Field(default=None, min_length=3, max_length=32)


class SignalFollowUpActionRequest(BaseModel):
    action: str = Field(..., min_length=3, max_length=32)
    reason: Optional[str] = None
