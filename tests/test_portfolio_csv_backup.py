import csv
import io
from fastapi.testclient import TestClient

from api import app
from database import Portfolio, Position, Trade, PortfolioSnapshot, db


client = TestClient(app, raise_server_exceptions=False)


def test_export_portfolio_csv_contains_full_record_types():
    p = Portfolio.create(
        name="CSV Export Full",
        type="USER",
        auto_manage=True,
        description="full export test",
        cash_egp=12345.67,
        cash_usd=890.12,
    )
    Position.create(
        portfolio=p.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        stop_loss=47.0,
        target_price=55.0,
        target_price_2=60.0,
        tp1_hit=False,
        current_price=52.0,
        status="OPEN",
        currency="EGP",
        sector="Banking",
        notes="note-a",
    )
    Trade.create(
        portfolio=p.id,
        ticker="COMI",
        shares=50,
        entry_price=45.0,
        exit_price=50.0,
        entry_date="2025-01-01",
        exit_date="2025-01-02",
        pnl=250.0,
        pnl_pct=11.11,
        reason="MANUAL",
        currency="EGP",
    )
    PortfolioSnapshot.create(
        portfolio=p.id,
        date="2025-01-03",
        equity_egp=13000.0,
        equity_usd=900.0,
        cash_egp=12000.0,
        cash_usd=850.0,
        position_count=1,
    )

    response = client.get(f"/api/v1/portfolio/export?portfolio_id={p.id}")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    assert "portfolio_backup_" in response.headers.get("content-disposition", "")

    rows = list(csv.DictReader(io.StringIO(response.text)))
    record_types = {str(r.get("record_type", "")).strip().upper() for r in rows}
    assert {"PROFILE", "POSITION", "TRADE", "SNAPSHOT"}.issubset(record_types)

    profile = next(r for r in rows if r.get("record_type") == "PROFILE")
    assert profile["portfolio_name"] == "CSV Export Full"
    assert profile["portfolio_cash_egp"] == "12345.67"
    assert profile["portfolio_cash_usd"] == "890.12"


def test_export_portfolio_csv_recreates_missing_snapshot_table():
    p = Portfolio.create(name="CSV Export Missing Snapshot", type="USER", cash_egp=100.0, cash_usd=0.0)
    Trade.create(
        portfolio=p.id,
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

    db.drop_tables([PortfolioSnapshot], safe=True)
    assert not PortfolioSnapshot.table_exists()

    response = client.get(f"/api/v1/portfolio/export?portfolio_id={p.id}")
    assert response.status_code == 200
    assert PortfolioSnapshot.table_exists()

    rows = list(csv.DictReader(io.StringIO(response.text)))
    record_types = {str(r.get("record_type", "")).strip().upper() for r in rows}
    assert "PROFILE" in record_types
    assert "TRADE" in record_types


def test_import_portfolio_csv_restores_full_profile_and_replaces_existing():
    p = Portfolio.create(name="CSV Import Full", type="USER", cash_egp=1.0, cash_usd=2.0)
    Position.create(
        portfolio=p.id,
        ticker="OLD1",
        shares=10,
        entry_price=10.0,
        stop_loss=9.0,
        target_price=12.0,
        current_price=10.5,
        status="OPEN",
    )
    Trade.create(
        portfolio=p.id,
        ticker="OLD1",
        shares=10,
        entry_price=10.0,
        exit_price=11.0,
        entry_date="2025-01-01",
        exit_date="2025-01-02",
        pnl=10.0,
        pnl_pct=10.0,
    )
    PortfolioSnapshot.create(
        portfolio=p.id,
        date="2025-01-02",
        equity_egp=100.0,
        equity_usd=0.0,
        cash_egp=50.0,
        cash_usd=0.0,
        position_count=1,
    )

    fieldnames = [
        "record_type",
        "schema_version",
        "portfolio_name",
        "portfolio_type",
        "portfolio_auto_manage",
        "portfolio_description",
        "portfolio_cash_egp",
        "portfolio_cash_usd",
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
        "snapshot_date",
        "snapshot_equity_egp",
        "snapshot_equity_usd",
        "snapshot_cash_egp",
        "snapshot_cash_usd",
        "snapshot_position_count",
    ]
    csv_buffer = io.StringIO(newline="")
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(
        {
            "record_type": "PROFILE",
            "schema_version": "1",
            "portfolio_name": "Imported Profile",
            "portfolio_type": "USER",
            "portfolio_auto_manage": "1",
            "portfolio_description": "restored",
            "portfolio_cash_egp": "50000.5",
            "portfolio_cash_usd": "3000.25",
        }
    )
    writer.writerow(
        {
            "record_type": "POSITION",
            "schema_version": "1",
            "position_ticker": "COMI",
            "position_shares": "120",
            "position_entry_price": "72.5",
            "position_stop_loss": "70.0",
            "position_target_price": "80.0",
            "position_target_price_2": "86.0",
            "position_tp1_hit": "0",
            "position_current_price": "74.0",
            "position_entry_date": "2025-02-01T10:00:00",
            "position_status": "OPEN",
            "position_currency": "EGP",
            "position_sector": "Banking",
            "position_notes": "restored position",
        }
    )
    writer.writerow(
        {
            "record_type": "TRADE",
            "schema_version": "1",
            "trade_ticker": "COMI",
            "trade_shares": "50",
            "trade_entry_price": "65.0",
            "trade_exit_price": "70.0",
            "trade_entry_date": "2025-01-10T09:00:00",
            "trade_exit_date": "2025-01-20T13:00:00",
            "trade_pnl": "250.0",
            "trade_pnl_pct": "7.69",
            "trade_reason": "RESTORE",
            "trade_currency": "EGP",
        }
    )
    writer.writerow(
        {
            "record_type": "SNAPSHOT",
            "schema_version": "1",
            "snapshot_date": "2025-01-31",
            "snapshot_equity_egp": "52000.0",
            "snapshot_equity_usd": "3000.0",
            "snapshot_cash_egp": "50000.5",
            "snapshot_cash_usd": "3000.25",
            "snapshot_position_count": "1",
        }
    )
    csv_text = csv_buffer.getvalue()

    response = client.post(
        f"/api/v1/portfolio/import?portfolio_id={p.id}&replace_existing=true",
        files={"file": ("portfolio_backup.csv", csv_text, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["imported"] == {"profile": 1, "positions": 1, "trades": 1, "snapshots": 1}

    p_db = Portfolio.get_by_id(p.id)
    assert p_db.name == "Imported Profile"
    assert p_db.type == "USER"
    assert bool(p_db.auto_manage) is True
    assert float(p_db.cash_egp) == 50000.5
    assert float(p_db.cash_usd) == 3000.25

    pos = list(Position.select().where(Position.portfolio == p.id))
    trades = list(Trade.select().where(Trade.portfolio == p.id))
    snaps = list(PortfolioSnapshot.select().where(PortfolioSnapshot.portfolio == p.id))

    assert len(pos) == 1
    assert pos[0].ticker == "COMI"
    assert pos[0].shares == 120
    assert len(trades) == 1
    assert trades[0].ticker == "COMI"
    assert len(snaps) == 1
    assert snaps[0].position_count == 1


def test_import_portfolio_csv_rejects_non_positive_portfolio_id():
    zero_response = client.post(
        "/api/v1/portfolio/import?portfolio_id=0&replace_existing=true",
        files={"file": ("portfolio_backup.csv", "record_type\n", "text/csv")},
    )
    negative_response = client.post(
        "/api/v1/portfolio/import?portfolio_id=-1&replace_existing=true",
        files={"file": ("portfolio_backup.csv", "record_type\n", "text/csv")},
    )

    assert zero_response.status_code == 422
    assert negative_response.status_code == 422
