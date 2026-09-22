import datetime
from pathlib import Path

import pytest
from fastapi import HTTPException

from database import Portfolio, Position
from core.portfolio.management import (
    build_portfolio_management_report,
    get_portfolio_rebalancing_command,
    parse_holding_input,
    send_portfolio_management_report_command,
    split_telegram_message,
    tp2_from_tp1,
    trigger_portfolio_snapshot_command,
)


class _Holding:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_tp2_from_tp1_returns_zero_for_non_positive():
    assert tp2_from_tp1(0.0, env_get_fn=lambda key, default: "4") == 0.0


def test_parse_holding_input_derives_shares_from_total_cost():
    holding = _Holding(
        ticker="COMI",
        shares=None,
        entry_price=50.0,
        total_cost=5000.0,
        stop_loss=None,
        target_price=None,
        currency="egp",
        sector="Banking",
        notes="VIP",
    )

    parsed = parse_holding_input(
        holding,
        normalize_ticker_fn=lambda ticker: ticker.strip().upper(),
        is_excluded_ticker_fn=lambda ticker: False,
        sl_pct=5.0,
        tp1_pct=10.0,
    )

    assert parsed["shares"] == 100
    assert parsed["currency"] == "EGP"


def test_build_portfolio_management_report_returns_action_items():
    portfolio = Portfolio.create(name="Management Report Seam", type="USER", cash_egp=1000.0, cash_usd=0.0)
    Position.create(
        portfolio=portfolio.id,
        ticker="COMI",
        shares=100,
        entry_price=50.0,
        stop_loss=47.0,
        target_price=55.0,
        current_price=55.0,
        status="OPEN",
        entry_date=datetime.datetime(2026, 3, 16, 12, 0, 0),
        currency="EGP",
    )

    report = build_portfolio_management_report(
        portfolio_id=portfolio.id,
        refresh_prices=False,
        resolve_portfolio_id_fn=lambda portfolio_id: portfolio.id,
        get_portfolio_fn=lambda target_id: portfolio,
        update_live_prices_fn=lambda: None,
        is_excluded_ticker_fn=lambda ticker: False,
        analyze_portfolio_fn=lambda target_id: {"status": "HEALTHY", "health_score": 85, "heat": 10, "recommendations": []},
        now_fn=lambda: datetime.datetime(2026, 3, 17, 12, 0, 0),
        tp2_from_tp1_fn=lambda tp1: tp1 * 1.04,
    )

    assert report["summary"]["open_positions"] == 1
    assert report["action_items"][0]["action"] == "TAKE_PROFIT_REVIEW"


def test_send_portfolio_management_report_command_counts_failures():
    report = {
        "portfolio": {"id": 1, "name": "Demo"},
        "summary": {"open_positions": 1},
    }

    result = send_portfolio_management_report_command(
        report=report,
        include_positions=5,
        chat_id="-1001",
        format_report_fn=lambda current_report, include_positions: "x" * 20,
        split_message_fn=lambda text, max_len=3500: ["chunk1", "chunk2"],
        send_message_fn=lambda chunk, chat_id=None: {"ok": chunk == "chunk1"},
    )

    assert result["status"] == "partial"
    assert result["chunks_sent"] == 1
    assert result["chunks_failed"] == 1


def test_get_portfolio_rebalancing_command_raises_when_missing_portfolio():
    with pytest.raises(HTTPException) as exc_info:
        get_portfolio_rebalancing_command(
            portfolio_id=None,
            model="EQUAL_WEIGHT",
            resolve_portfolio_id_fn=lambda portfolio_id: None,
            get_rebalancing_fn=lambda **kwargs: {},
        )

    assert exc_info.value.status_code == 404


def test_trigger_portfolio_snapshot_command_maps_error_result():
    with pytest.raises(HTTPException) as exc_info:
        trigger_portfolio_snapshot_command(
            portfolio_id=1,
            resolve_portfolio_id_fn=lambda portfolio_id: 1,
            take_snapshot_fn=lambda **kwargs: {"status": "error", "message": "snapshot failed"},
        )

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "snapshot failed"


def test_split_telegram_message_splits_long_text():
    chunks = split_telegram_message("\n".join([f"Line {i}" for i in range(30)]), max_len=40)
    assert len(chunks) > 1


def test_portfolio_route_keeps_single_management_helper_definition():
    route_source = Path("routes/portfolio.py").read_text(encoding="utf-8")

    assert route_source.count("def _format_portfolio_management_report(") == 1
    assert route_source.count("def _split_telegram_message(") == 1
