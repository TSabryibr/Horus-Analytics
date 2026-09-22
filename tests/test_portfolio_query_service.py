import datetime

import pytest
from fastapi import HTTPException

from database import Portfolio, Position, Trade
from core.portfolio.queries import (
    get_equity_curve_query,
    get_portfolio_analysis_query,
    get_portfolio_metrics_query,
    get_portfolio_report_query,
    get_portfolio_query,
    get_positions_query,
    get_trades_query,
)


def test_get_portfolio_query_raises_when_no_user_portfolio():
    with pytest.raises(HTTPException) as exc_info:
        get_portfolio_query(
            portfolio_id=None,
            resolve_portfolio_id_fn=lambda portfolio_id: None,
            get_hoard_status_fn=lambda **kwargs: {"status": "success"},
            filter_payload_fn=lambda payload: payload,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No user portfolio found"


def test_get_portfolio_query_maps_error_payload_to_http_400():
    portfolio = Portfolio.create(name="Query Portfolio", type="USER")

    with pytest.raises(HTTPException) as exc_info:
        get_portfolio_query(
            portfolio_id=portfolio.id,
            resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
            get_hoard_status_fn=lambda **kwargs: {"status": "error", "message": "lookup failed"},
            filter_payload_fn=lambda payload: payload,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "lookup failed"


def test_get_portfolio_query_filters_success_payload():
    portfolio = Portfolio.create(name="Filtered Portfolio", type="USER")

    payload = get_portfolio_query(
        portfolio_id=portfolio.id,
        resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
        get_hoard_status_fn=lambda **kwargs: {"status": "success", "positions": ["COMI"]},
        filter_payload_fn=lambda current_payload: {"wrapped": current_payload},
    )

    assert payload == {"wrapped": {"status": "success", "positions": ["COMI"]}}


def test_get_positions_query_returns_only_open_positions_before_now():
    portfolio = Portfolio.create(name="Positions Query Portfolio", type="USER")
    now = datetime.datetime(2026, 3, 17, 12, 0, 0)

    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        stop_loss=47.0,
        target_price=55.0,
        current_price=51.0,
        status="OPEN",
        entry_date=now - datetime.timedelta(days=1),
        currency="EGP",
    )
    Position.create(
        portfolio=portfolio.id,
        ticker="FWRY",
        shares=100,
        entry_price=5.0,
        stop_loss=4.5,
        target_price=6.0,
        current_price=5.2,
        status="CLOSED",
        entry_date=now - datetime.timedelta(days=1),
        currency="EGP",
    )
    Position.create(
        portfolio=portfolio.id,
        ticker="SWDY",
        shares=100,
        entry_price=20.0,
        stop_loss=18.0,
        target_price=24.0,
        current_price=21.0,
        status="OPEN",
        entry_date=now + datetime.timedelta(days=1),
        currency="EGP",
    )

    payload = get_positions_query(
        portfolio_id=portfolio.id,
        now_fn=lambda: now,
        filter_payload_fn=lambda current_payload: current_payload,
    )

    assert [item["ticker"] for item in payload] == ["COMI"]


def test_get_trades_query_orders_by_exit_date_desc_and_honors_limit():
    portfolio = Portfolio.create(name="Trades Query Portfolio", type="USER")
    now = datetime.datetime(2026, 3, 17, 12, 0, 0)

    Trade.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        exit_price=52.0,
        entry_date=now - datetime.timedelta(days=3),
        exit_date=now - datetime.timedelta(days=1),
        pnl=200.0,
        pnl_pct=4.0,
    )
    Trade.create(
        portfolio=portfolio.id,
        ticker="FWRY",
        shares=100,
        entry_price=5.0,
        exit_price=5.5,
        entry_date=now - datetime.timedelta(days=5),
        exit_date=now - datetime.timedelta(days=2),
        pnl=50.0,
        pnl_pct=10.0,
    )
    Trade.create(
        portfolio=portfolio.id,
        ticker="SWDY",
        shares=100,
        entry_price=20.0,
        exit_price=21.0,
        entry_date=now - datetime.timedelta(days=1),
        exit_date=now + datetime.timedelta(days=1),
        pnl=100.0,
        pnl_pct=5.0,
    )

    payload = get_trades_query(
        limit=1,
        portfolio_id=portfolio.id,
        now_fn=lambda: now,
        filter_payload_fn=lambda current_payload: current_payload,
    )

    assert len(payload) == 1
    assert payload[0]["ticker"] == "COMI"


def test_get_portfolio_metrics_query_returns_zero_shape_with_unrealized_pnl():
    portfolio = Portfolio.create(name="Metrics Query Portfolio", type="USER")
    now = datetime.datetime(2026, 3, 17, 12, 0, 0)

    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        stop_loss=47.0,
        target_price=55.0,
        current_price=53.0,
        status="OPEN",
        entry_date=now - datetime.timedelta(days=1),
        currency="EGP",
    )

    payload = get_portfolio_metrics_query(
        portfolio_id=portfolio.id,
        resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
        select_first_portfolio_id_fn=lambda: None,
        update_live_prices_fn=lambda: None,
        now_fn=lambda: now,
    )

    assert payload == {
        "win_rate": 0,
        "total_pnl": 300.0,
        "realized_pnl": 0,
        "unrealized_pnl": 300.0,
        "profit_factor": 0,
        "total_trades": 0,
    }


def test_get_portfolio_metrics_query_uses_existing_portfolio_when_default_id_missing():
    portfolio = Portfolio.create(name="Metrics Existing Portfolio", type="USER")
    now = datetime.datetime(2026, 3, 17, 12, 0, 0)

    Trade.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=10.0,
        exit_price=12.5,
        entry_date=now - datetime.timedelta(days=5),
        exit_date=now - datetime.timedelta(days=1),
        pnl=250.0,
        pnl_pct=25.0,
    )

    payload = get_portfolio_metrics_query(
        portfolio_id=None,
        resolve_portfolio_id_fn=lambda portfolio_id: None,
        select_first_portfolio_id_fn=lambda: portfolio.id,
        update_live_prices_fn=lambda: None,
        now_fn=lambda: now,
    )

    assert payload["total_trades"] == 1
    assert payload["realized_pnl"] == 250.0


def test_get_equity_curve_query_uses_metrics_when_no_trades():
    portfolio = Portfolio.create(name="Curve Query Portfolio", type="USER")
    now = datetime.datetime(2026, 3, 17, 12, 0, 0)

    payload = get_equity_curve_query(
        portfolio_id=portfolio.id,
        resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
        select_first_portfolio_id_fn=lambda: None,
        now_fn=lambda: now,
        get_portfolio_metrics_query_fn=lambda **kwargs: {"unrealized_pnl": 321.5},
    )

    assert payload == [
        {"date": "Baseline", "equity": 1000000},
        {"date": "2026-03-17", "equity": 1000321.5},
    ]


def test_get_portfolio_analysis_query_ignores_price_refresh_failure():
    portfolio = Portfolio.create(name="Analysis Query Portfolio", type="USER")

    payload = get_portfolio_analysis_query(
        portfolio_id=portfolio.id,
        resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
        select_first_portfolio_id_fn=lambda: None,
        update_live_prices_fn=lambda: (_ for _ in ()).throw(RuntimeError("feed down")),
        analyze_portfolio_fn=lambda target_id: {"portfolio_id": target_id, "status": "ok"},
    )

    assert payload == {"portfolio_id": portfolio.id, "status": "ok"}


def test_get_portfolio_report_query_returns_metrics_curve_and_limited_trades():
    portfolio = Portfolio.create(name="Report Query Portfolio", type="USER")
    now = datetime.datetime(2026, 3, 17, 12, 0, 0)

    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        stop_loss=47.0,
        target_price=55.0,
        current_price=53.0,
        status="OPEN",
        entry_date=now - datetime.timedelta(days=3),
        currency="EGP",
    )
    Trade.create(
        portfolio=portfolio.id,
        ticker="FWRY",
        shares=100,
        entry_price=10.0,
        exit_price=12.5,
        entry_date=now - datetime.timedelta(days=4),
        exit_date=now - datetime.timedelta(days=2),
        pnl=250.0,
        pnl_pct=25.0,
    )
    Trade.create(
        portfolio=portfolio.id,
        ticker="SWDY",
        shares=100,
        entry_price=20.0,
        exit_price=21.0,
        entry_date=now - datetime.timedelta(days=3),
        exit_date=now - datetime.timedelta(days=1),
        pnl=100.0,
        pnl_pct=5.0,
    )

    payload = get_portfolio_report_query(
        portfolio_id=portfolio.id,
        trades_limit=1,
        resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
        select_first_portfolio_id_fn=lambda: None,
        update_live_prices_fn=lambda: None,
        now_fn=lambda: now,
    )

    assert payload["metrics"]["total_trades"] == 2
    assert payload["curve"][0] == {"date": "Baseline", "equity": 1000000}
    assert len(payload["trades"]) == 1
    assert payload["trades"][0]["ticker"] == "SWDY"
