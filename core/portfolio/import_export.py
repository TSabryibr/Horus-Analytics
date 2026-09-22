import csv
import datetime
import io
from typing import Any, Callable, Optional

from fastapi import HTTPException
from fastapi.responses import Response

from core import TimeUtils
from database import Portfolio, PortfolioSnapshot, Position, Trade, db
from core.exclusions import normalize_ticker

from .identity import resolve_portfolio_id


PORTFOLIO_BACKUP_SCHEMA_VERSION = "1"
PORTFOLIO_BACKUP_FIELDS = [
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


def iso_or_empty(value) -> str:
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    return str(value)


def parse_bool_str(value: str, default: bool = False) -> bool:
    txt = str(value or "").strip().lower()
    if not txt:
        return default
    return txt in {"1", "true", "yes", "y", "on"}


def parse_int_str(value: str, field_name: str, *, required: bool = False, default: int = 0) -> int:
    txt = str(value or "").strip()
    if not txt:
        if required:
            raise ValueError(f"{field_name} is required")
        return default
    try:
        return int(float(txt))
    except Exception:
        raise ValueError(f"{field_name} must be a valid integer")


def parse_float_str(value: str, field_name: str, *, required: bool = False, default: float = 0.0) -> float:
    txt = str(value or "").strip()
    if not txt:
        if required:
            raise ValueError(f"{field_name} is required")
        return default
    try:
        return float(txt)
    except Exception:
        raise ValueError(f"{field_name} must be a valid number")


def parse_datetime_str(value: str, field_name: str, *, required: bool = True) -> Optional[datetime.datetime]:
    txt = str(value or "").strip()
    if not txt:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    try:
        return datetime.datetime.fromisoformat(txt.replace("Z", "+00:00"))
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(txt, fmt)
        except Exception:
            continue
    raise ValueError(f"{field_name} has unsupported datetime format")


def parse_date_str(value: str, field_name: str, *, required: bool = True) -> Optional[datetime.date]:
    txt = str(value or "").strip()
    if not txt:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    try:
        return datetime.date.fromisoformat(txt)
    except Exception:
        pass
    try:
        return datetime.datetime.fromisoformat(txt.replace("Z", "+00:00")).date()
    except Exception:
        pass
    raise ValueError(f"{field_name} has unsupported date format")


def ensure_portfolio_snapshot_table() -> None:
    try:
        if not PortfolioSnapshot.table_exists():
            db.create_tables([PortfolioSnapshot], safe=True)
    except Exception:
        db.create_tables([PortfolioSnapshot], safe=True)


def _select_first_portfolio_id() -> Optional[int]:
    any_portfolio = Portfolio.select().order_by(Portfolio.id.asc()).first()
    return any_portfolio.id if any_portfolio else None


def _resolve_existing_portfolio_id(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]],
    select_first_portfolio_id_fn: Callable[[], Optional[int]],
) -> Optional[int]:
    target_id = resolve_portfolio_id_fn(portfolio_id)
    if target_id:
        return target_id
    return select_first_portfolio_id_fn()


def build_portfolio_export_response(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    get_portfolio_fn: Callable[[int], Any] = lambda current_id: Portfolio.get_or_none(Portfolio.id == current_id),
    ensure_snapshot_table_fn: Callable[[], None] = ensure_portfolio_snapshot_table,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(status_code=404, detail="No portfolio found")

    portfolio = get_portfolio_fn(target_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    ensure_snapshot_table_fn()

    positions = list(Position.select().where(Position.portfolio == portfolio.id).order_by(Position.ticker.asc(), Position.id.asc()))
    trades = list(Trade.select().where(Trade.portfolio == portfolio.id).order_by(Trade.exit_date.asc(), Trade.id.asc()))
    snapshots = list(
        PortfolioSnapshot.select()
        .where(PortfolioSnapshot.portfolio == portfolio.id)
        .order_by(PortfolioSnapshot.date.asc(), PortfolioSnapshot.id.asc())
    )

    exported_at = now_fn().isoformat()
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=PORTFOLIO_BACKUP_FIELDS)
    writer.writeheader()
    writer.writerow(
        {
            "record_type": "PROFILE",
            "schema_version": PORTFOLIO_BACKUP_SCHEMA_VERSION,
            "exported_at": exported_at,
            "portfolio_id": portfolio.id,
            "portfolio_name": portfolio.name,
            "portfolio_type": portfolio.type,
            "portfolio_auto_manage": int(bool(portfolio.auto_manage)),
            "portfolio_description": portfolio.description or "",
            "portfolio_cash_egp": float(portfolio.cash_egp or 0.0),
            "portfolio_cash_usd": float(portfolio.cash_usd or 0.0),
            "portfolio_created_at": iso_or_empty(portfolio.created_at),
        }
    )

    for pos in positions:
        writer.writerow(
            {
                "record_type": "POSITION",
                "schema_version": PORTFOLIO_BACKUP_SCHEMA_VERSION,
                "exported_at": exported_at,
                "portfolio_id": portfolio.id,
                "position_id": pos.id,
                "position_ticker": pos.ticker,
                "position_shares": pos.shares,
                "position_entry_price": pos.entry_price,
                "position_stop_loss": pos.stop_loss,
                "position_target_price": pos.target_price,
                "position_target_price_2": "" if pos.target_price_2 is None else pos.target_price_2,
                "position_tp1_hit": int(bool(pos.tp1_hit)),
                "position_current_price": "" if pos.current_price is None else pos.current_price,
                "position_entry_date": iso_or_empty(pos.entry_date),
                "position_status": pos.status or "OPEN",
                "position_currency": pos.currency or "EGP",
                "position_sector": pos.sector or "",
                "position_notes": pos.notes or "",
                "position_risk_amount": "" if pos.risk_amount is None else pos.risk_amount,
                "position_slippage_bps": "" if pos.slippage_bps is None else pos.slippage_bps,
                "position_execution_latency_ms": "" if pos.execution_latency_ms is None else pos.execution_latency_ms,
            }
        )

    for trade in trades:
        writer.writerow(
            {
                "record_type": "TRADE",
                "schema_version": PORTFOLIO_BACKUP_SCHEMA_VERSION,
                "exported_at": exported_at,
                "portfolio_id": portfolio.id,
                "trade_id": trade.id,
                "trade_ticker": trade.ticker,
                "trade_shares": trade.shares,
                "trade_entry_price": trade.entry_price,
                "trade_exit_price": trade.exit_price,
                "trade_entry_date": iso_or_empty(trade.entry_date),
                "trade_exit_date": iso_or_empty(trade.exit_date),
                "trade_pnl": trade.pnl,
                "trade_pnl_pct": trade.pnl_pct,
                "trade_reason": trade.reason or "MANUAL",
                "trade_currency": trade.currency or "EGP",
                "trade_slippage_bps": "" if trade.slippage_bps is None else trade.slippage_bps,
                "trade_execution_latency_ms": "" if trade.execution_latency_ms is None else trade.execution_latency_ms,
            }
        )

    for snap in snapshots:
        writer.writerow(
            {
                "record_type": "SNAPSHOT",
                "schema_version": PORTFOLIO_BACKUP_SCHEMA_VERSION,
                "exported_at": exported_at,
                "portfolio_id": portfolio.id,
                "snapshot_id": snap.id,
                "snapshot_date": iso_or_empty(snap.date),
                "snapshot_equity_egp": snap.equity_egp,
                "snapshot_equity_usd": snap.equity_usd,
                "snapshot_cash_egp": snap.cash_egp,
                "snapshot_cash_usd": snap.cash_usd,
                "snapshot_position_count": snap.position_count,
            }
        )

    filename = f"portfolio_backup_{portfolio.id}_{now_fn().strftime('%Y%m%d_%H%M%S')}.csv"
    response = Response(content=stream.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
    return response


def build_portfolio_excel_export_response(
    *,
    portfolio_id: Optional[int],
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(status_code=404, detail="No portfolio found")

    from core.reports.portfolio_excel import build_portfolio_excel_report

    try:
        raw_xlsx = build_portfolio_excel_report(target_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate Excel report: {e}")

    filename = f"portfolio_audit_{target_id}_{now_fn().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response = Response(
        content=raw_xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.headers["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
    return response


def import_portfolio_csv_bytes(
    *,
    raw: bytes,
    portfolio_id: Optional[int],
    replace_existing: bool,
    resolve_portfolio_id_fn: Callable[[Optional[int]], Optional[int]] = resolve_portfolio_id,
    select_first_portfolio_id_fn: Callable[[], Optional[int]] = _select_first_portfolio_id,
    get_portfolio_fn: Callable[[int], Any] = lambda current_id: Portfolio.get_or_none(Portfolio.id == current_id),
    ensure_snapshot_table_fn: Callable[[], None] = ensure_portfolio_snapshot_table,
    now_fn: Callable[[], datetime.datetime] = TimeUtils.now,
):
    target_id = _resolve_existing_portfolio_id(
        portfolio_id=portfolio_id,
        resolve_portfolio_id_fn=resolve_portfolio_id_fn,
        select_first_portfolio_id_fn=select_first_portfolio_id_fn,
    )
    if not target_id:
        raise HTTPException(status_code=404, detail="No portfolio found")

    portfolio = get_portfolio_fn(target_id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    if not raw:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    # 1. Check if uploaded file is an Excel spreadsheet (.xlsx binary) or Subscriber Template
    is_excel = raw.startswith(b"PK")
    is_subscriber_template = False
    subscriber_holdings = []

    if is_excel:
        from core.portfolio.template_generator import parse_subscriber_intake_file
        try:
            subscriber_holdings = parse_subscriber_intake_file(raw, "subscriber_template.xlsx")
            is_subscriber_template = True
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel Subscriber Template: {exc}")

    if not is_excel:
        text = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")

        reader = csv.DictReader(io.StringIO(text), skipinitialspace=True)
        if reader.fieldnames and "record_type" in reader.fieldnames:
            # Standard Horus CSV Backup
            pass
        else:
            # Check if it's a Subscriber Template CSV (must have valid shares > 0 and entry_price > 0)
            from core.portfolio.template_generator import parse_subscriber_intake_file
            try:
                raw_parsed = parse_subscriber_intake_file(raw, "subscriber_template.csv")
                valid_holdings = [
                    h for h in raw_parsed
                    if h.get("ticker") and float(h.get("shares") or 0) > 0 and float(h.get("entry_price") or 0) > 0
                ]
                if valid_holdings:
                    subscriber_holdings = valid_holdings
                    is_subscriber_template = True
                else:
                    raise HTTPException(status_code=400, detail="Invalid CSV schema: missing record_type column")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid CSV schema: missing record_type column")

    if is_subscriber_template:
        if not subscriber_holdings:
            raise HTTPException(status_code=400, detail="No valid holdings found in Subscriber Template")

        from core.portfolio.template_generator import resolve_ticker_alias

        with db.atomic():
            if replace_existing:
                Position.delete().where(Position.portfolio == portfolio.id).execute()

            for h in subscriber_holdings:
                raw_sym = str(h.get("ticker") or "").strip().upper()
                norm_sym = normalize_ticker(resolve_ticker_alias(raw_sym))
                if not norm_sym:
                    continue
                shares = int(h.get("shares", 0))
                if shares <= 0:
                    continue
                entry_price = float(h.get("entry_price", 0.0))
                if entry_price <= 0:
                    continue
                stop_loss = float(h.get("stop_loss", 0.0)) if h.get("stop_loss") else round(entry_price * 0.95, 2)
                target_price = float(h.get("target_price", 0.0)) if h.get("target_price") else round(entry_price * 1.10, 2)
                target_price_2 = float(h.get("target_price_2", 0.0)) if h.get("target_price_2") else None
                curr = str(h.get("currency") or "EGP").strip().upper() or "EGP"

                existing = None if replace_existing else Position.get_or_none(
                    (Position.portfolio == portfolio.id) & (Position.ticker == norm_sym)
                )
                if existing:
                    existing.shares = shares
                    existing.entry_price = entry_price
                    existing.stop_loss = stop_loss
                    existing.target_price = target_price
                    existing.target_price_2 = target_price_2
                    existing.currency = curr
                    if h.get("sector"):
                        existing.sector = h["sector"]
                    if h.get("notes"):
                        existing.notes = h["notes"]
                    existing.save()
                else:
                    Position.create(
                        portfolio=portfolio.id,
                        ticker=norm_sym,
                        shares=shares,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        target_price=target_price,
                        target_price_2=target_price_2,
                        current_price=entry_price,
                        status="OPEN",
                        currency=curr,
                        sector=h.get("sector"),
                        notes=h.get("notes") or "Subscriber template import",
                        entry_date=now_fn(),
                    )

        try:
            from core.PositionTracker import PositionTracker
            PositionTracker.update_live_prices()
        except Exception:
            pass

        return {
            "status": "success",
            "portfolio_id": portfolio.id,
            "replace_existing": bool(replace_existing),
            "imported": {
                "profile": 1,
                "positions": len(subscriber_holdings),
                "trades": 0,
                "snapshots": 0,
            },
            "message": f"Successfully imported {len(subscriber_holdings)} position(s) from Subscriber Template.",
        }

    rows = [row for row in reader if any(str(value or "").strip() for value in row.values())]
    if not rows:
        raise HTTPException(status_code=400, detail="CSV has no data rows")

    profile_rows = [row for row in rows if str(row.get("record_type", "")).strip().upper() == "PROFILE"]
    position_rows = [row for row in rows if str(row.get("record_type", "")).strip().upper() == "POSITION"]
    trade_rows = [row for row in rows if str(row.get("record_type", "")).strip().upper() == "TRADE"]
    snapshot_rows = [row for row in rows if str(row.get("record_type", "")).strip().upper() == "SNAPSHOT"]

    if not profile_rows and not position_rows and not trade_rows and not snapshot_rows:
        raise HTTPException(status_code=400, detail="No supported record types found in CSV")

    ensure_snapshot_table_fn()

    try:
        with db.atomic():
            if replace_existing:
                Position.delete().where(Position.portfolio == portfolio.id).execute()
                Trade.delete().where(Trade.portfolio == portfolio.id).execute()
                PortfolioSnapshot.delete().where(PortfolioSnapshot.portfolio == portfolio.id).execute()

            if profile_rows:
                profile = profile_rows[0]
                imported_name = str(profile.get("portfolio_name") or "").strip()
                if imported_name and imported_name != portfolio.name:
                    duplicate = Portfolio.get_or_none((Portfolio.name == imported_name) & (Portfolio.id != portfolio.id))
                    if duplicate is None:
                        portfolio.name = imported_name
                imported_type = str(profile.get("portfolio_type") or "").strip().upper()
                if imported_type in {"USER", "SYSTEM"}:
                    portfolio.type = imported_type
                portfolio.auto_manage = parse_bool_str(profile.get("portfolio_auto_manage", ""), default=bool(portfolio.auto_manage))
                imported_desc = str(profile.get("portfolio_description") or "").strip()
                portfolio.description = imported_desc or None
                portfolio.cash_egp = parse_float_str(profile.get("portfolio_cash_egp", ""), "portfolio_cash_egp", required=False, default=0.0)
                portfolio.cash_usd = parse_float_str(profile.get("portfolio_cash_usd", ""), "portfolio_cash_usd", required=False, default=0.0)
                portfolio.save()

            for row in position_rows:
                ticker = normalize_ticker(row.get("position_ticker"))
                if not ticker:
                    raise ValueError("position_ticker is required")
                shares = parse_int_str(row.get("position_shares", ""), "position_shares", required=True)
                if shares <= 0:
                    raise ValueError("position_shares must be > 0")
                entry_price = parse_float_str(row.get("position_entry_price", ""), "position_entry_price", required=True)
                if entry_price <= 0:
                    raise ValueError("position_entry_price must be > 0")
                stop_loss = parse_float_str(row.get("position_stop_loss", ""), "position_stop_loss", required=False, default=entry_price)
                target_price = parse_float_str(row.get("position_target_price", ""), "position_target_price", required=False, default=entry_price)
                Position.create(
                    portfolio=portfolio.id,
                    ticker=ticker,
                    shares=shares,
                    entry_price=entry_price,
                    stop_loss=stop_loss,
                    target_price=target_price,
                    target_price_2=parse_float_str(row.get("position_target_price_2", ""), "position_target_price_2", required=False, default=0.0) if str(row.get("position_target_price_2", "")).strip() else None,
                    tp1_hit=parse_bool_str(row.get("position_tp1_hit", ""), default=False),
                    current_price=parse_float_str(row.get("position_current_price", ""), "position_current_price", required=False, default=0.0) if str(row.get("position_current_price", "")).strip() else None,
                    entry_date=parse_datetime_str(row.get("position_entry_date", ""), "position_entry_date", required=False) or now_fn(),
                    status=str(row.get("position_status") or "OPEN").strip() or "OPEN",
                    currency=str(row.get("position_currency") or "EGP").strip().upper() or "EGP",
                    sector=str(row.get("position_sector") or "").strip() or None,
                    notes=str(row.get("position_notes") or "").strip() or None,
                    risk_amount=parse_float_str(row.get("position_risk_amount", ""), "position_risk_amount", required=False, default=0.0) if str(row.get("position_risk_amount", "")).strip() else None,
                    slippage_bps=parse_float_str(row.get("position_slippage_bps", ""), "position_slippage_bps", required=False, default=0.0) if str(row.get("position_slippage_bps", "")).strip() else None,
                    execution_latency_ms=parse_int_str(row.get("position_execution_latency_ms", ""), "position_execution_latency_ms", required=False, default=0) if str(row.get("position_execution_latency_ms", "")).strip() else None,
                )

            for row in trade_rows:
                ticker = normalize_ticker(row.get("trade_ticker"))
                if not ticker:
                    raise ValueError("trade_ticker is required")
                shares = parse_int_str(row.get("trade_shares", ""), "trade_shares", required=True)
                if shares <= 0:
                    raise ValueError("trade_shares must be > 0")
                entry_price = parse_float_str(row.get("trade_entry_price", ""), "trade_entry_price", required=True)
                exit_price = parse_float_str(row.get("trade_exit_price", ""), "trade_exit_price", required=True)
                if entry_price <= 0 or exit_price <= 0:
                    raise ValueError("trade_entry_price and trade_exit_price must be > 0")
                Trade.create(
                    portfolio=portfolio.id,
                    ticker=ticker,
                    shares=shares,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    entry_date=parse_datetime_str(row.get("trade_entry_date", ""), "trade_entry_date", required=True),
                    exit_date=parse_datetime_str(row.get("trade_exit_date", ""), "trade_exit_date", required=True),
                    pnl=parse_float_str(row.get("trade_pnl", ""), "trade_pnl", required=True),
                    pnl_pct=parse_float_str(row.get("trade_pnl_pct", ""), "trade_pnl_pct", required=True),
                    reason=str(row.get("trade_reason") or "MANUAL").strip() or "MANUAL",
                    currency=str(row.get("trade_currency") or "EGP").strip().upper() or "EGP",
                    slippage_bps=parse_float_str(row.get("trade_slippage_bps", ""), "trade_slippage_bps", required=False, default=0.0) if str(row.get("trade_slippage_bps", "")).strip() else None,
                    execution_latency_ms=parse_int_str(row.get("trade_execution_latency_ms", ""), "trade_execution_latency_ms", required=False, default=0) if str(row.get("trade_execution_latency_ms", "")).strip() else None,
                )

            for row in snapshot_rows:
                PortfolioSnapshot.create(
                    portfolio=portfolio.id,
                    date=parse_date_str(row.get("snapshot_date", ""), "snapshot_date", required=True),
                    equity_egp=parse_float_str(row.get("snapshot_equity_egp", ""), "snapshot_equity_egp", required=True),
                    equity_usd=parse_float_str(row.get("snapshot_equity_usd", ""), "snapshot_equity_usd", required=True),
                    cash_egp=parse_float_str(row.get("snapshot_cash_egp", ""), "snapshot_cash_egp", required=True),
                    cash_usd=parse_float_str(row.get("snapshot_cash_usd", ""), "snapshot_cash_usd", required=True),
                    position_count=parse_int_str(row.get("snapshot_position_count", ""), "snapshot_position_count", required=True),
                )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Import failed: {exc}")

    return {
        "status": "success",
        "portfolio_id": portfolio.id,
        "replace_existing": bool(replace_existing),
        "imported": {
            "profile": 1 if profile_rows else 0,
            "positions": len(position_rows),
            "trades": len(trade_rows),
            "snapshots": len(snapshot_rows),
        },
    }
