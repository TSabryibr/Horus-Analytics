import csv
import io

import pytest
from fastapi import HTTPException

from database import Portfolio, Position, Trade, PortfolioSnapshot
from core.portfolio.import_export import (
    build_portfolio_export_response,
    import_portfolio_csv_bytes,
    parse_datetime_str,
    parse_int_str,
)


def test_parse_int_str_rejects_invalid_integer():
    with pytest.raises(ValueError) as exc_info:
        parse_int_str("abc", "position_shares", required=True)

    assert str(exc_info.value) == "position_shares must be a valid integer"


def test_parse_datetime_str_accepts_date_only():
    parsed = parse_datetime_str("2025-01-02", "trade_entry_date", required=True)
    assert parsed.year == 2025
    assert parsed.month == 1
    assert parsed.day == 2


def test_build_portfolio_export_response_contains_profile_and_trade_rows():
    portfolio = Portfolio.create(name="Service Export", type="USER", cash_egp=500.0, cash_usd=10.0)
    Trade.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=10,
        entry_price=10.0,
        exit_price=11.0,
        entry_date="2025-01-01",
        exit_date="2025-01-02",
        pnl=10.0,
        pnl_pct=10.0,
        currency="EGP",
    )

    response = build_portfolio_export_response(
        portfolio_id=portfolio.id,
        resolve_portfolio_id_fn=lambda current_id: portfolio.id,
        select_first_portfolio_id_fn=lambda: None,
        get_portfolio_fn=lambda current_id: portfolio,
        ensure_snapshot_table_fn=lambda: None,
        now_fn=lambda: parse_datetime_str("2026-03-17T12:00:00", "now"),
    )

    rows = list(csv.DictReader(io.StringIO(response.body.decode("utf-8"))))
    assert {row["record_type"] for row in rows} == {"PROFILE", "TRADE"}


def test_import_portfolio_csv_bytes_rejects_missing_record_type_schema():
    portfolio = Portfolio.create(name="Service Import", type="USER")

    with pytest.raises(HTTPException) as exc_info:
        import_portfolio_csv_bytes(
            raw=b"ticker\nCOMI\n",
            portfolio_id=portfolio.id,
            replace_existing=True,
            resolve_portfolio_id_fn=lambda current_id: portfolio.id,
            select_first_portfolio_id_fn=lambda: None,
            get_portfolio_fn=lambda current_id: portfolio,
            ensure_snapshot_table_fn=lambda: None,
            now_fn=lambda: parse_datetime_str("2026-03-17T12:00:00", "now"),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid CSV schema: missing record_type column"


def test_import_portfolio_csv_bytes_restores_snapshot_row():
    portfolio = Portfolio.create(name="Snapshot Import", type="USER")
    csv_text = "\n".join(
        [
            "record_type,schema_version,snapshot_date,snapshot_equity_egp,snapshot_equity_usd,snapshot_cash_egp,snapshot_cash_usd,snapshot_position_count",
            "SNAPSHOT,1,2025-01-31,52000.0,3000.0,50000.5,3000.25,1",
        ]
    )

    result = import_portfolio_csv_bytes(
        raw=csv_text.encode("utf-8"),
        portfolio_id=portfolio.id,
        replace_existing=True,
        resolve_portfolio_id_fn=lambda current_id: portfolio.id,
        select_first_portfolio_id_fn=lambda: None,
        get_portfolio_fn=lambda current_id: portfolio,
        ensure_snapshot_table_fn=lambda: None,
        now_fn=lambda: parse_datetime_str("2026-03-17T12:00:00", "now"),
    )

    assert result["status"] == "success"
    snapshot = PortfolioSnapshot.get(PortfolioSnapshot.portfolio == portfolio.id)
    assert snapshot.position_count == 1
