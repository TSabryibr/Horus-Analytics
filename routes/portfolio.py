from core.settings import settings
from core.exclusions import is_excluded_ticker, filter_excluded_from_payload, assert_ticker_allowed
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Response
from pydantic import BaseModel, Field, ValidationError, ConfigDict, model_validator
from typing import List, Optional
import os
import csv
import io
import datetime
from core.analyzers import TreasuryLedger
from core import RiskManager
from core import PositionTracker
from core import TimeUtils
from core import TelegramBot_Alerts
from core import WalkForwardValidation
from database import (
    Position,
    Trade,
    Portfolio,
    PortfolioSnapshot,
    ScannerStrategyProfile,
    SignalExecutionAttribution,
    db,
)
from routes.shared import SignalCardRequest

# Service layer — primary interface for portfolio business logic
from core.services import portfolio_service

# Low-level core imports (kept for routes not yet wired to the service)
from core.portfolio.commands import (
    seed_demo_portfolio_command as _portfolio_seed_demo_portfolio_command,
    batch_positions_command as _portfolio_batch_positions_command,
    apply_rebalancing_command as _portfolio_apply_rebalancing_command,
)
from core.portfolio.identity import (
    clear_default_system_portfolio_id as _identity_clear_default_system_portfolio_id,
    enforce_manual_entry_gate as _identity_enforce_manual_entry_gate,
    get_default_system_portfolio_id as _identity_get_default_system_portfolio_id,
    resolve_portfolio_id as _identity_resolve_portfolio_id,
    set_default_system_portfolio_id as _identity_set_default_system_portfolio_id,
    validation_error_detail as _identity_validation_error_detail,
)
from core.portfolio.import_export import (
    build_portfolio_export_response as _portfolio_build_portfolio_export_response,
    build_portfolio_excel_export_response as _portfolio_build_portfolio_excel_export_response,
    ensure_portfolio_snapshot_table as _portfolio_ensure_portfolio_snapshot_table,
    import_portfolio_csv_bytes as _portfolio_import_portfolio_csv_bytes,
    iso_or_empty as _portfolio_iso_or_empty,
    parse_bool_str as _portfolio_parse_bool_str,
    parse_date_str as _portfolio_parse_date_str,
    parse_datetime_str as _portfolio_parse_datetime_str,
    parse_float_str as _portfolio_parse_float_str,
    parse_int_str as _portfolio_parse_int_str,
)
from core.portfolio.template_generator import (
    build_subscriber_intake_excel_template as _build_subscriber_intake_excel_template,
    build_subscriber_intake_csv_template as _build_subscriber_intake_csv_template,
    parse_subscriber_intake_file as _parse_subscriber_intake_file,
)
from core.portfolio.management import (
    build_portfolio_management_report as _portfolio_build_portfolio_management_report,
    build_sandbox_management_report as _portfolio_build_sandbox_management_report,
    format_portfolio_management_report as _portfolio_format_portfolio_management_report,
    intake_portfolio_holdings_command as _portfolio_intake_portfolio_holdings_command,
    parse_holding_input as _portfolio_parse_holding_input,
    send_portfolio_management_report_command as _portfolio_send_portfolio_management_report_command,
    split_telegram_message as _portfolio_split_telegram_message,
    subscriber_import_command as _portfolio_subscriber_import_command,
    tp2_from_tp1 as _portfolio_tp2_from_tp1,
)
from core.portfolio.queries import (
    get_portfolio_metrics_query as _portfolio_get_portfolio_metrics_query,
    get_portfolio_report_query as _portfolio_get_portfolio_report_query,
    get_equity_curve_query as _portfolio_get_equity_curve_query,
    get_portfolio_analysis_query as _portfolio_get_portfolio_analysis_query,
)
from core.portfolio.performance import PerformanceTracker

from core.exclusions import (
    assert_ticker_allowed,
    filter_excluded_from_payload,
    is_excluded_ticker,
    normalize_ticker,
)

LEGACY_SYSTEM_PORTFOLIOS = {"Daily Simulation"}

router = APIRouter(tags=["portfolio"])

def _resolve_portfolio_id(portfolio_id: Optional[int]) -> Optional[int]:
    return _identity_resolve_portfolio_id(portfolio_id)


def _get_default_system_portfolio():
    return portfolio_service.get_default_portfolio()


def _get_default_system_portfolio_id() -> Optional[int]:
    return _identity_get_default_system_portfolio_id()


def _set_default_system_portfolio_id(portfolio_id: int):
    return _identity_set_default_system_portfolio_id(portfolio_id)


def _enforce_manual_entry_gate(ticker: str):
    return _identity_enforce_manual_entry_gate(
        ticker,
        normalize_ticker_fn=normalize_ticker,
        assert_ticker_allowed_fn=assert_ticker_allowed,
        get_trade_permission_fn=WalkForwardValidation.get_trade_permission,
    )


def _validation_error_detail(exc: ValidationError) -> str:
    return _identity_validation_error_detail(exc)


def _select_first_portfolio_id() -> Optional[int]:
    portfolio = Portfolio.select().order_by(Portfolio.id.asc()).first()
    return portfolio.id if portfolio else None

class TradeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1)
    shares: int = Field(..., gt=0)
    price: float = Field(..., gt=0)
    type: str = "NEW"
    sl: Optional[float] = None
    tp: Optional[float] = None
    tp2: Optional[float] = None
    date: Optional[str] = None
    portfolio_id: Optional[int] = Field(1, ge=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_target_aliases(cls, data):
        if isinstance(data, dict):
            if data.get("tp") is None and data.get("target_price") is not None:
                data["tp"] = data.get("target_price")
            if data.get("tp2") is None and data.get("target_price_2") is not None:
                data["tp2"] = data.get("target_price_2")
        return data

class GenesisHolding(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1)
    shares: float = Field(..., gt=0)
    price: float = Field(..., gt=0)

class GenesisRequest(BaseModel):
    egp_balance: float = Field(0.0, ge=0)
    usd_balance: float = Field(0.0, ge=0)
    holdings: Optional[List[GenesisHolding]] = Field(default_factory=list)
    portfolio_id: Optional[int] = Field(1, ge=1)

class CloseTradeRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    shares: Optional[int] = Field(None, gt=0)
    portfolio_id: Optional[int] = Field(None, ge=1)

class CreatePortfolioRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1)
    auto_manage: bool = False


class SetDefaultPortfolioRequest(BaseModel):
    portfolio_id: int = Field(..., ge=1)

class RiskCheckRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str
    portfolio_id: Optional[int] = Field(1, ge=1)

class UpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1)
    sl: Optional[float] = None
    tp: Optional[float] = None
    tp2: Optional[float] = None
    shares: Optional[float] = Field(None, gt=0)
    price: Optional[float] = Field(None, gt=0)
    portfolio_id: Optional[int] = Field(1, ge=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_target_aliases(cls, data):
        if isinstance(data, dict):
            if data.get("tp") is None and data.get("target_price") is not None:
                data["tp"] = data.get("target_price")
            if data.get("tp2") is None and data.get("target_price_2") is not None:
                data["tp2"] = data.get("target_price_2")
        return data

    @model_validator(mode="after")
    def validate_update_fields(self):
        if all(value is None for value in (self.sl, self.tp, self.tp2, self.shares, self.price)):
            raise ValueError("At least one of sl, tp, tp2, shares, or price must be provided")
        return self

class ManagedHoldingInput(BaseModel):
    ticker: str
    shares: Optional[float] = Field(None, gt=0)
    entry_price: Optional[float] = Field(None, gt=0)
    total_cost: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = None
    target_price: Optional[float] = None
    currency: Optional[str] = "EGP"
    sector: Optional[str] = None
    notes: Optional[str] = None

class PortfolioIntakeRequest(BaseModel):
    portfolio_id: Optional[int] = Field(None, ge=1)
    holdings: List[ManagedHoldingInput]
    refresh_prices: bool = bool(getattr(settings, "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES", True))

class PortfolioReportSendRequest(BaseModel):
    portfolio_id: Optional[int] = Field(None, ge=1)
    include_positions: int = int(getattr(settings, "PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS", 15))
    chat_id: Optional[str] = None
    refresh_prices: bool = bool(getattr(settings, "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES", True))

@router.get("/api/v1/portfolio")
def get_portfolio(portfolio_id: Optional[int] = Query(None, ge=1)):
    return portfolio_service.get_portfolio(portfolio_id)

@router.get("/api/v1/portfolio/balance")
def get_portfolio_balance():
    return {
        "cash_egp": settings.ACCOUNT_BALANCE,
        "cash_usd": settings.ACCOUNT_BALANCE_USD
    }

@router.post("/api/v1/portfolio/genesis")
def initialize_portfolio_genesis(req: GenesisRequest):
    return portfolio_service.initialize_genesis(req)

@router.get("/api/v1/portfolio/open")
@router.get("/api/v1/positions")
def get_positions(portfolio_id: Optional[int] = Query(None, ge=1)):
    return portfolio_service.get_positions(portfolio_id)

@router.get("/api/v1/portfolio/trades")
@router.get("/api/v1/trades")
def get_trades(limit: int = Query(50, ge=1), portfolio_id: Optional[int] = Query(None, ge=1)):
    return portfolio_service.get_trades(portfolio_id, limit=limit)

@router.post("/api/v1/portfolio/add")
@router.post("/api/v1/trade/add")
def add_trade(req: TradeRequest):
    return portfolio_service.add_trade(req)

@router.post("/api/v1/portfolio/close")
@router.post("/api/v1/trade/close")
def close_trade(req: CloseTradeRequest):
    return portfolio_service.close_trade(req)

class PortfolioBatchActionRequest(BaseModel):
    portfolio_id: Optional[int] = None
    action: str
    tickers: List[str]


class PortfolioRebalanceApplyRequest(BaseModel):
    portfolio_id: Optional[int] = None
    model: str = "EQUAL_WEIGHT"


@router.post("/api/v1/portfolio/positions/batch")
def execute_batch_positions_action(req: PortfolioBatchActionRequest):
    return _portfolio_batch_positions_command(req, resolve_portfolio_id_fn=_resolve_portfolio_id)


@router.post("/api/v1/portfolio/update")
def update_trade(req: UpdateRequest):
    return portfolio_service.update_trade(req)

@router.get("/api/v1/portfolios")
def list_portfolios():
    return [
        row for row in Portfolio.select().dicts()
        if not (row.get("type") == "SYSTEM" and row.get("name") in LEGACY_SYSTEM_PORTFOLIOS)
    ]


@router.get("/api/v1/portfolio/strategies")
def list_strategy_portfolios():
    strategy_portfolios = list(
        Portfolio.select()
        .where(
            (Portfolio.type == "STRATEGY") |
            ((Portfolio.type == "USER") & (Portfolio.auto_manage == True))
        )
        .order_by(Portfolio.name.asc())
    )
    profile_rows = list(
        ScannerStrategyProfile.select()
        .where(ScannerStrategyProfile.profile_state == "ACTIVE")
        .order_by(ScannerStrategyProfile.profile_name.asc())
    )
    profiles_by_name: dict[str, list[dict]] = {}
    for profile in profile_rows:
        key = str(profile.profile_name or "").strip()
        if not key:
            continue
        profiles_by_name.setdefault(key, []).append({
            "profile_id": profile.id,
            "profile_name": profile.profile_name,
            "profile_state": profile.profile_state,
            "source_type": profile.source_type,
            "market": profile.market,
            "timeframe": profile.timeframe,
            "activated_at": profile.activated_at.isoformat() if profile.activated_at else None,
            "activation_count": int(profile.activation_count or 0),
        })

    payload = []
    for portfolio in strategy_portfolios:
        attached_profiles = profiles_by_name.get(str(portfolio.name or "").strip(), [])
        attribution_count = (
            SignalExecutionAttribution.select()
            .where(SignalExecutionAttribution.strategy_portfolio == portfolio.id)
            .count()
        )
        payload.append({
            "id": portfolio.id,
            "name": portfolio.name,
            "type": portfolio.type,
            "auto_manage": bool(portfolio.auto_manage),
            "description": portfolio.description,
            "attached_profiles": attached_profiles,
            "attribution_count": attribution_count,
        })

    return {"count": len(payload), "portfolios": payload}


@router.get("/api/v1/portfolios/default")
def get_default_portfolio():
    portfolio = _get_default_system_portfolio()
    return {
        "portfolio_id": portfolio.id if portfolio else None,
        "portfolio_name": portfolio.name if portfolio else None,
        "portfolio_type": portfolio.type if portfolio else None,
    }


@router.post("/api/v1/portfolios/default")
def set_default_portfolio(payload: dict):
    try:
        req = SetDefaultPortfolioRequest.model_validate(payload)
        portfolio = _set_default_system_portfolio_id(req.portfolio_id)
        return {
            "status": "updated",
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "portfolio_type": portfolio.type,
        }
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=_validation_error_detail(exc))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/v1/portfolios", operation_id="create_portfolio_legacy")
def create_portfolio(payload: dict):
    try:
        req = CreatePortfolioRequest.model_validate(payload)
        p = Portfolio.create(name=req.name, type="USER", auto_manage=req.auto_manage)
        return {"status": "created", "id": p.id}
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=_validation_error_detail(exc))
    except Exception as e: raise HTTPException(status_code=400, detail=str(e))

@router.delete("/api/v1/portfolios/{portfolio_id}")
def delete_portfolio(portfolio_id: int):
    try:
        p = Portfolio.get_by_id(portfolio_id)
        if p.type == 'SYSTEM':
            raise HTTPException(status_code=400, detail="Cannot delete system portfolios")
        with db.atomic():
            if _get_default_system_portfolio_id() == p.id:
                _identity_clear_default_system_portfolio_id()
            Position.delete().where(Position.portfolio == portfolio_id).execute()
            Trade.delete().where(Trade.portfolio == portfolio_id).execute()
            p.delete_instance()
        return {"status": "deleted"}
    except Portfolio.DoesNotExist:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/api/v1/risk/check", operation_id="check_trade_risk_legacy")
def check_trade_risk(payload: dict):
    try:
        req = RiskCheckRequest.model_validate(payload)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=_validation_error_detail(exc))

    ticker = normalize_ticker(req.ticker)
    db_portfolio_id = req.portfolio_id
    if not ticker: raise HTTPException(status_code=400, detail="Ticker required")
    assert_ticker_allowed(ticker)
    current_positions = [p['ticker'] for p in Position.select().where((Position.status == 'OPEN') & (Position.portfolio == db_portfolio_id)).dicts()]
    warnings = []
    corr_res = RiskManager.check_new_trade_correlation(current_positions, ticker)
    if not corr_res['is_safe']: warnings.append(corr_res['warning'])
    safe_sector, sector_msg = RiskManager.check_sector_exposure(ticker, current_positions)
    if not safe_sector: warnings.append(sector_msg)
    return {"safe": len(warnings) == 0, "warnings": warnings, "details": {"correlation": corr_res.get('avg_correlation') if corr_res['is_safe'] else corr_res.get('max_correlation')}}

@router.get("/api/v1/portfolio/metrics", operation_id="get_portfolio_metrics_legacy")
@router.get("/api/v1/portfolio-metrics", operation_id="get_portfolio_metrics")
def get_portfolio_metrics(portfolio_id: Optional[int] = Query(None, ge=1)):
    return _portfolio_get_portfolio_metrics_query(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        update_live_prices_fn=PositionTracker.update_live_prices,
        now_fn=TimeUtils.now,
    )

@router.get("/api/v1/portfolio/report")
def get_portfolio_report(
    portfolio_id: Optional[int] = Query(None, ge=1),
    trades_limit: int = Query(20, ge=1, le=100),
):
    return _portfolio_get_portfolio_report_query(
        portfolio_id=portfolio_id,
        trades_limit=trades_limit,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        update_live_prices_fn=PositionTracker.update_live_prices,
        now_fn=TimeUtils.now,
    )

@router.get("/api/v1/portfolio/curve")
def get_equity_curve(portfolio_id: Optional[int] = Query(None, ge=1)):
    return _portfolio_get_equity_curve_query(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        now_fn=TimeUtils.now,
        get_portfolio_metrics_query_fn=lambda **kwargs: _portfolio_get_portfolio_metrics_query(
            portfolio_id=kwargs.get("portfolio_id"),
            resolve_portfolio_id_fn=_resolve_portfolio_id,
            select_first_portfolio_id_fn=_select_first_portfolio_id,
            update_live_prices_fn=PositionTracker.update_live_prices,
            now_fn=TimeUtils.now,
        ),
    )

_PORTFOLIO_BACKUP_SCHEMA_VERSION = "1"
_PORTFOLIO_BACKUP_FIELDS = [
    "record_type",
    "schema_version",
    "exported_at",
    "portfolio_id",
    "portfolio_name",
    "portfolio_type",
    "portfolio_auto_manage",
    "portfolio_description",
    "portfolio_cash_egp",
    "portfolio_cash_usd",
    "portfolio_created_at",
    "position_id",
    "position_ticker",
    "position_shares",
    "position_entry_price",
    "position_stop_loss",
    "position_target_price",
    "position_target_price_2",
    "position_tp1_hit",
    "position_current_price",
    "position_entry_date",
    "position_status",
    "position_currency",
    "position_sector",
    "position_notes",
    "position_risk_amount",
    "position_slippage_bps",
    "position_execution_latency_ms",
    "trade_id",
    "trade_ticker",
    "trade_shares",
    "trade_entry_price",
    "trade_exit_price",
    "trade_entry_date",
    "trade_exit_date",
    "trade_pnl",
    "trade_pnl_pct",
    "trade_reason",
    "trade_currency",
    "trade_slippage_bps",
    "trade_execution_latency_ms",
    "snapshot_id",
    "snapshot_date",
    "snapshot_equity_egp",
    "snapshot_equity_usd",
    "snapshot_cash_egp",
    "snapshot_cash_usd",
    "snapshot_position_count",
]


def _iso_or_empty(value) -> str:
    return _portfolio_iso_or_empty(value)


def _parse_bool_str(value: str, default: bool = False) -> bool:
    return _portfolio_parse_bool_str(value, default=default)


def _parse_int_str(value: str, field_name: str, *, required: bool = False, default: int = 0) -> int:
    return _portfolio_parse_int_str(value, field_name, required=required, default=default)


def _parse_float_str(value: str, field_name: str, *, required: bool = False, default: float = 0.0) -> float:
    return _portfolio_parse_float_str(value, field_name, required=required, default=default)


def _parse_datetime_str(value: str, field_name: str, *, required: bool = True) -> Optional[datetime.datetime]:
    return _portfolio_parse_datetime_str(value, field_name, required=required)


def _parse_date_str(value: str, field_name: str, *, required: bool = True) -> Optional[datetime.date]:
    return _portfolio_parse_date_str(value, field_name, required=required)


def _ensure_portfolio_snapshot_table() -> None:
    return _portfolio_ensure_portfolio_snapshot_table()


@router.get("/api/v1/portfolio/export")
def export_portfolio_report(portfolio_id: Optional[int] = Query(None, ge=1)):
    return _portfolio_build_portfolio_export_response(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        get_portfolio_fn=lambda current_id: Portfolio.get_or_none(Portfolio.id == current_id),
        ensure_snapshot_table_fn=_ensure_portfolio_snapshot_table,
        now_fn=TimeUtils.now,
    )


@router.get("/api/v1/portfolio/export/excel")
def export_portfolio_excel(portfolio_id: Optional[int] = Query(None, ge=1)):
    return _portfolio_build_portfolio_excel_export_response(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        now_fn=TimeUtils.now,
    )


@router.get("/api/v1/portfolio/template")
def download_portfolio_intake_template(format: str = Query("xlsx", regex="^(xlsx|csv)$")):
    if format == "csv":
        content = _build_subscriber_intake_csv_template()
        response = Response(content=content, media_type="text/csv")
        response.headers["Content-Disposition"] = 'attachment; filename="subscriber_portfolio_intake_template.csv"'
        return response
    else:
        content = _build_subscriber_intake_excel_template()
        response = Response(
            content=content,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response.headers["Content-Disposition"] = 'attachment; filename="subscriber_portfolio_intake_template.xlsx"'
        return response


@router.post("/api/v1/portfolio/import")
def import_portfolio_report_csv(
    file: UploadFile = File(...),
    portfolio_id: Optional[int] = Query(None, ge=1),
    replace_existing: bool = True,
):
    raw = file.file.read()
    return _portfolio_import_portfolio_csv_bytes(
        raw=raw,
        portfolio_id=portfolio_id,
        replace_existing=replace_existing,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        get_portfolio_fn=lambda current_id: Portfolio.get_or_none(Portfolio.id == current_id),
        ensure_snapshot_table_fn=_ensure_portfolio_snapshot_table,
        now_fn=TimeUtils.now,
    )


@router.post("/api/v1/portfolio/management/intake/file")
def intake_portfolio_holdings_file(
    file: UploadFile = File(...),
    portfolio_id: Optional[int] = Query(None, ge=1),
    refresh_prices: bool = True,
):
    try:
        raw_bytes = file.file.read()
        parsed_holdings = _parse_subscriber_intake_file(raw_bytes, file.filename or "intake.xlsx")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded file: {exc}")

    if not parsed_holdings:
        raise HTTPException(status_code=400, detail="No valid holding rows found in uploaded file")

    holdings_inputs = [ManagedHoldingInput.model_validate(h) for h in parsed_holdings]
    intake_req = PortfolioIntakeRequest(
        portfolio_id=portfolio_id,
        holdings=holdings_inputs,
        refresh_prices=refresh_prices,
    )
    return _portfolio_intake_portfolio_holdings_command(
        intake_req,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        parse_holding_input_fn=_parse_holding_input,
        get_trade_permission_fn=WalkForwardValidation.get_trade_permission,
        update_live_prices_fn=PositionTracker.update_live_prices,
        build_report_fn=_build_portfolio_management_report,
        now_fn=TimeUtils.now,
    )


@router.post("/api/v1/portfolio/subscriber/import")
def subscriber_portfolio_import(
    file: UploadFile = File(...),
    portfolio_name: Optional[str] = Query(None),
    mode: str = Query("create_new", regex="^(create_new|sandbox|overwrite)$"),
    portfolio_id: Optional[int] = Query(None, ge=1),
    starting_cash_egp: float = Query(0.0, ge=0.0),
    starting_cash_usd: float = Query(0.0, ge=0.0),
    refresh_prices: bool = True,
):
    try:
        raw_bytes = file.file.read()
        return _portfolio_subscriber_import_command(
            file_bytes=raw_bytes,
            filename=file.filename or "subscriber_intake.xlsx",
            portfolio_name=portfolio_name,
            mode=mode,
            portfolio_id=portfolio_id,
            starting_cash_egp=starting_cash_egp,
            starting_cash_usd=starting_cash_usd,
            refresh_prices=refresh_prices,
            parse_file_fn=_parse_subscriber_intake_file,
            parse_holding_input_fn=_parse_holding_input,
            get_trade_permission_fn=WalkForwardValidation.get_trade_permission,
            update_live_prices_fn=PositionTracker.update_live_prices,
            build_report_fn=_build_portfolio_management_report,
            resolve_portfolio_id_fn=_resolve_portfolio_id,
            now_fn=TimeUtils.now,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to import subscriber portfolio: {exc}")


@router.post("/api/v1/portfolio/seed")
def seed_portfolio_demo(portfolio_id: int = Query(..., ge=1)):
    return _portfolio_seed_demo_portfolio_command(
        portfolio_id=portfolio_id,
        get_portfolio_fn=lambda candidate_id: Portfolio.get_or_none(Portfolio.id == candidate_id),
        is_excluded_ticker_fn=is_excluded_ticker,
        create_position_fn=Position.create,
    )

def _tp2_from_tp1(tp1: float) -> float:
    return _portfolio_tp2_from_tp1(tp1, env_get_fn=os.getenv)

def _parse_holding_input(row: ManagedHoldingInput):
    return _portfolio_parse_holding_input(
        row,
        normalize_ticker_fn=normalize_ticker,
        is_excluded_ticker_fn=is_excluded_ticker,
        sl_pct=settings.SL_PCT,
        tp1_pct=settings.TP1_PCT,
    )

def _build_portfolio_management_report(
    portfolio_id: Optional[int],
    refresh_prices: bool = bool(getattr(settings, "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES", True)),
):
    return _portfolio_build_portfolio_management_report(
        portfolio_id=portfolio_id,
        refresh_prices=refresh_prices,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        get_portfolio_fn=lambda target_id: Portfolio.get_or_none(Portfolio.id == target_id),
        update_live_prices_fn=PositionTracker.update_live_prices,
        is_excluded_ticker_fn=is_excluded_ticker,
        analyze_portfolio_fn=RiskManager.analyze_portfolio,
        now_fn=TimeUtils.now,
        tp2_from_tp1_fn=_tp2_from_tp1,
    )

def _format_portfolio_management_report(
    report: dict,
    include_positions: int = int(getattr(settings, "PORTFOLIO_MGMT_DEFAULT_INCLUDE_POSITIONS", 15)),
):
    return _portfolio_format_portfolio_management_report(report, include_positions=include_positions)


def _split_telegram_message(text: str, max_len: int = 3500):
    return _portfolio_split_telegram_message(text, max_len=max_len)

@router.post("/api/v1/portfolio/management/intake")
def intake_portfolio_holdings(req: PortfolioIntakeRequest):
    return _portfolio_intake_portfolio_holdings_command(
        req,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        parse_holding_input_fn=_parse_holding_input,
        get_trade_permission_fn=WalkForwardValidation.get_trade_permission,
        update_live_prices_fn=PositionTracker.update_live_prices,
        build_report_fn=_build_portfolio_management_report,
        now_fn=TimeUtils.now,
    )

@router.get("/api/v1/portfolio/management/report")
def get_portfolio_management_report(
    portfolio_id: Optional[int] = Query(None, ge=1),
    refresh_prices: bool = bool(getattr(settings, "PORTFOLIO_MGMT_DEFAULT_REFRESH_PRICES", True)),
):
    return _build_portfolio_management_report(portfolio_id=portfolio_id, refresh_prices=refresh_prices)

@router.post("/api/v1/portfolio/management/report/send")
def send_portfolio_management_report(req: PortfolioReportSendRequest):
    if req.include_positions < 1 or req.include_positions > 100:
        raise HTTPException(status_code=400, detail="include_positions must be between 1 and 100")

    report = _build_portfolio_management_report(req.portfolio_id, refresh_prices=req.refresh_prices)
    return _portfolio_send_portfolio_management_report_command(
        report=report,
        include_positions=req.include_positions,
        chat_id=req.chat_id,
        format_report_fn=_format_portfolio_management_report,
        split_message_fn=_split_telegram_message,
        send_message_fn=TelegramBot_Alerts.send_message,
    )

@router.get("/api/v1/portfolio/rebalance")
def get_portfolio_rebalancing(portfolio_id: Optional[int] = Query(None, ge=1), model: str = "EQUAL_WEIGHT"):
    return portfolio_service.get_rebalancing(portfolio_id, model=model)

@router.post("/api/v1/portfolio/snapshot")
def trigger_portfolio_snapshot(portfolio_id: Optional[int] = Query(None, ge=1)):
    return portfolio_service.trigger_snapshot(portfolio_id)

@router.get("/api/v1/portfolio/analysis")
def get_portfolio_analysis(portfolio_id: Optional[int] = Query(None, ge=1)):
    return _portfolio_get_portfolio_analysis_query(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=_resolve_portfolio_id,
        select_first_portfolio_id_fn=_select_first_portfolio_id,
        update_live_prices_fn=PositionTracker.update_live_prices,
        analyze_portfolio_fn=RiskManager.analyze_portfolio,
    )
@router.post("/api/v1/portfolio/rebalance/apply")
def apply_portfolio_rebalancing(req: PortfolioRebalanceApplyRequest):
    return _portfolio_apply_rebalancing_command(req, resolve_portfolio_id_fn=_resolve_portfolio_id)


@router.get("/api/v1/portfolio/stress-test")
def get_portfolio_stress_test(
    portfolio_id: Optional[int] = Query(None, ge=1),
    simulations: int = Query(1000, ge=100, le=10000),
    days: int = Query(30, ge=5, le=365),
):
    target_id = _resolve_portfolio_id(portfolio_id) or _select_first_portfolio_id()
    if not target_id:
        raise HTTPException(404, "Portfolio not found")
    return RiskManager.run_portfolio_stress_test(target_id, num_simulations=simulations, horizon_days=days)


@router.get("/api/v1/market/rate")
def get_market_parallel_rate():
    rate = RiskManager.get_parallel_usd_egp_rate()
    return {
        "rate": rate,
        "base": "USD",
        "target": "EGP",
        "timestamp": TimeUtils.now().isoformat(),
    }


@router.get("/api/v1/portfolio/performance/{portfolio_id}")
@router.get("/performance/{portfolio_id}")
async def get_portfolio_performance(portfolio_id: int, days: int = 90):
    """Get detailed performance metrics for a specific portfolio."""
    try:
        return PerformanceTracker.get_portfolio_performance(portfolio_id, days)
    except Portfolio.DoesNotExist:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/v1/portfolio/strategy-performance/{portfolio_id}")
async def get_strategy_portfolio_performance(portfolio_id: int, days: int = 90):
    try:
        portfolio = Portfolio.get_by_id(portfolio_id)
    except Portfolio.DoesNotExist:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if str(portfolio.type or "").upper() not in {"STRATEGY", "USER"} or not bool(portfolio.auto_manage):
        raise HTTPException(status_code=400, detail="Portfolio is not a strategy portfolio")

    try:
        return PerformanceTracker.get_portfolio_performance(portfolio_id, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/portfolio/system-comparison")
@router.get("/system-comparison")
async def get_system_portfolio_comparison():
    """Get performance comparison across all SYSTEM portfolios."""
    try:
        return PerformanceTracker.get_system_comparison()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/portfolio/execution-history/{portfolio_id}")
@router.get("/execution-history/{portfolio_id}")
async def get_execution_history(portfolio_id: int, limit: int = 50):
    """Get detailed execution audit history for a portfolio."""
    try:
        return PerformanceTracker.get_execution_history(portfolio_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
