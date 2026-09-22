import datetime

from core.portfolio.queries import get_trades_query
from database import Portfolio, Trade


def test_get_trades_query_displays_profitable_stop_loss_as_trailing_stop():
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    trade = Trade.create(
        portfolio=portfolio,
        ticker="ASCM",
        shares=10,
        entry_price=61.49,
        exit_price=62.72,
        entry_date=datetime.datetime(2026, 6, 15, 10, 0),
        exit_date=datetime.datetime(2026, 6, 15, 10, 53),
        pnl=12.3,
        pnl_pct=2.0003,
        reason="STOP_LOSS",
    )

    rows = get_trades_query(
        limit=10,
        portfolio_id=portfolio.id,
        now_fn=lambda: datetime.datetime(2026, 6, 16, 0, 0),
        filter_payload_fn=lambda payload: payload,
    )

    assert rows[0]["reason"] == "TRAILING_STOP"
    assert Trade.get_by_id(trade.id).reason == "STOP_LOSS"


def test_get_trades_query_keeps_losing_stop_loss_as_stop_loss():
    portfolio = Portfolio.get(Portfolio.name == "Intraday Signals")
    Trade.create(
        portfolio=portfolio,
        ticker="GPIM",
        shares=10,
        entry_price=1.15,
        exit_price=1.1466,
        entry_date=datetime.datetime(2026, 6, 15, 10, 0),
        exit_date=datetime.datetime(2026, 6, 15, 11, 20),
        pnl=-0.034,
        pnl_pct=-0.2957,
        reason="STOP_LOSS",
    )

    rows = get_trades_query(
        limit=10,
        portfolio_id=portfolio.id,
        now_fn=lambda: datetime.datetime(2026, 6, 16, 0, 0),
        filter_payload_fn=lambda payload: payload,
    )

    assert rows[0]["reason"] == "STOP_LOSS"
