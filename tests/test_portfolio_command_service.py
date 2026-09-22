import pytest
from fastapi import HTTPException

from core.portfolio.commands import (
    add_trade_command,
    close_trade_command,
    initialize_portfolio_genesis_command,
    seed_demo_portfolio_command,
    update_trade_command,
)


class _TradeRequest:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_add_trade_command_raises_when_no_user_portfolio():
    req = _TradeRequest(portfolio_id=None, ticker="COMI", shares=100, price=50.0, type="EXISTING")

    with pytest.raises(HTTPException) as exc_info:
        add_trade_command(
            req,
            resolve_portfolio_id_fn=lambda portfolio_id: None,
            enforce_manual_entry_gate_fn=lambda ticker: ("COMI", {"allowed": True}),
            add_gold_fn=lambda **kwargs: {"status": "success"},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "No user portfolio found"


def test_add_trade_command_delegates_to_add_gold():
    req = _TradeRequest(portfolio_id=4, ticker="COMI", shares=100, price=50.0, type="EXISTING")
    calls = {}

    def _add_gold(**kwargs):
        calls["payload"] = kwargs
        return {"status": "success"}

    result = add_trade_command(
        req,
        resolve_portfolio_id_fn=lambda portfolio_id: 4,
        enforce_manual_entry_gate_fn=lambda ticker: ("COMI", {"allowed": True, "reason": "ok"}),
        add_gold_fn=_add_gold,
    )

    assert result == {"status": "success"}
    assert calls["payload"] == {
        "ticker": "COMI",
        "shares": 100,
        "price": 50.0,
        "type": "EXISTING",
        "portfolio_id": 4,
    }


def test_close_trade_command_maps_draupnir_error_to_http_400():
    req = _TradeRequest(portfolio_id=2, ticker="FWRY", shares=None, price=5.8)

    with pytest.raises(HTTPException) as exc_info:
        close_trade_command(
            req,
            resolve_portfolio_id_fn=lambda portfolio_id: 2,
            melt_gold_fn=lambda ticker, shares, price, portfolio_id: {
                "status": "error",
                "message": "Close operation failed",
            },
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Close operation failed"


def test_update_trade_command_raises_500_when_position_update_fails():
    req = _TradeRequest(portfolio_id=3, ticker="SWDY", shares=None, price=None, sl=19.0, tp=26.0)

    with pytest.raises(HTTPException) as exc_info:
        update_trade_command(
            req,
            resolve_portfolio_id_fn=lambda portfolio_id: 3,
            update_position_fn=lambda **kwargs: False,
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Failed to update position"


def test_update_trade_command_returns_success_payload():
    req = _TradeRequest(portfolio_id=3, ticker="SWDY", shares=None, price=None, sl=19.0, tp=26.0)
    calls = {}

    def _update_position(**kwargs):
        calls["payload"] = kwargs
        return True

    result = update_trade_command(
        req,
        resolve_portfolio_id_fn=lambda portfolio_id: 3,
        update_position_fn=_update_position,
    )

    assert result == {"status": "success", "message": "Position updated"}
    assert calls["payload"] == {
        "ticker": "SWDY",
        "shares": None,
        "entry_price": None,
        "sl": 19.0,
        "tp": 26.0,
        "portfolio_id": 3,
    }


def test_initialize_portfolio_genesis_command_creates_default_user_portfolio_when_missing():
    req = _TradeRequest(portfolio_id=None, egp_balance=100000, usd_balance=5000, holdings=[])
    created = {}

    class _Portfolio:
        id = 9
        cash_egp = 0
        cash_usd = 0

        def save(self):
            created["saved"] = True

    def _create_portfolio(**kwargs):
        created["payload"] = kwargs
        return _Portfolio()

    result = initialize_portfolio_genesis_command(
        req,
        resolve_portfolio_id_fn=lambda portfolio_id: None,
        get_portfolio_fn=lambda portfolio_id: None,
        create_portfolio_fn=_create_portfolio,
        normalize_ticker_fn=lambda ticker: ticker.strip().upper(),
        is_excluded_ticker_fn=lambda ticker: False,
        add_gold_fn=lambda **kwargs: {"status": "success"},
        write_lock_file_fn=lambda: created.setdefault("lock_written", True),
    )

    assert result == {
        "status": "success",
        "cash_egp": 100000,
        "cash_usd": 5000,
        "holdings_added": 0,
        "errors": [],
    }
    assert created["payload"] == {"name": "My Portfolio", "type": "USER"}
    assert created["saved"] is True
    assert created["lock_written"] is True


def test_initialize_portfolio_genesis_command_collects_holding_errors():
    req = _TradeRequest(
        portfolio_id=4,
        egp_balance=50000,
        usd_balance=0,
        holdings=[
            _TradeRequest(ticker="   ", shares=100, price=50.0),
            _TradeRequest(ticker="COMI", shares=100, price=50.0),
            _TradeRequest(ticker="FWRY", shares=200, price=5.0),
        ],
    )

    class _Portfolio:
        id = 4
        cash_egp = 0
        cash_usd = 0

        def save(self):
            return None

    result = initialize_portfolio_genesis_command(
        req,
        resolve_portfolio_id_fn=lambda portfolio_id: 4,
        get_portfolio_fn=lambda portfolio_id: _Portfolio(),
        create_portfolio_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("create should not be called")),
        normalize_ticker_fn=lambda ticker: ticker.strip().upper(),
        is_excluded_ticker_fn=lambda ticker: ticker == "COMI",
        add_gold_fn=lambda **kwargs: {"status": "error", "message": "provider failed"},
        write_lock_file_fn=lambda: None,
    )

    assert result["holdings_added"] == 0
    assert result["errors"] == [
        "UNKNOWN: Ticker is required",
        "COMI: blacklisted ticker",
        "FWRY: provider failed",
    ]


def test_initialize_portfolio_genesis_command_consolidates_duplicate_holdings():
    req = _TradeRequest(
        portfolio_id=4,
        egp_balance=0,
        usd_balance=0,
        holdings=[
            _TradeRequest(ticker="TYCN", shares=6470, price=15.3),
            _TradeRequest(ticker="tycn", shares=1230, price=14.25),
            _TradeRequest(ticker="GTEX", shares=240000, price=0.0381),
        ],
    )
    calls = []

    class _Portfolio:
        id = 4
        cash_egp = 0
        cash_usd = 0

        def save(self):
            return None

    def _add_gold(**kwargs):
        calls.append(kwargs)
        return {"status": "success"}

    result = initialize_portfolio_genesis_command(
        req,
        resolve_portfolio_id_fn=lambda portfolio_id: 4,
        get_portfolio_fn=lambda portfolio_id: _Portfolio(),
        create_portfolio_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("create should not be called")),
        normalize_ticker_fn=lambda ticker: ticker.strip().upper(),
        is_excluded_ticker_fn=lambda ticker: False,
        add_gold_fn=_add_gold,
        write_lock_file_fn=lambda: None,
    )

    assert result["holdings_added"] == 2
    assert calls == [
        {
            "ticker": "TYCN",
            "shares": 7700.0,
            "price": pytest.approx((6470 * 15.3 + 1230 * 14.25) / 7700),
            "type": "EXISTING",
            "portfolio_id": 4,
        },
        {
            "ticker": "GTEX",
            "shares": 240000.0,
            "price": pytest.approx(0.0381),
            "type": "EXISTING",
            "portfolio_id": 4,
        },
    ]


def test_seed_demo_portfolio_command_preserves_skip_when_positions_exist():
    class _Positions:
        @staticmethod
        def count():
            return 1

    portfolio = _TradeRequest(id=7, positions=_Positions())

    result = seed_demo_portfolio_command(
        portfolio_id=7,
        get_portfolio_fn=lambda portfolio_id: portfolio,
        is_excluded_ticker_fn=lambda ticker: False,
        create_position_fn=lambda **kwargs: (_ for _ in ()).throw(AssertionError("create_position should not be called")),
    )

    assert result == {"status": "skipped"}


def test_seed_demo_portfolio_command_raises_not_found():
    with pytest.raises(HTTPException) as exc_info:
        seed_demo_portfolio_command(
            portfolio_id=999,
            get_portfolio_fn=lambda portfolio_id: None,
            is_excluded_ticker_fn=lambda ticker: False,
            create_position_fn=lambda **kwargs: None,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Not found"
