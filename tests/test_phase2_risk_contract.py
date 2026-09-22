from fastapi.testclient import TestClient

from api import app
from core.pine_lab.profiles import build_promotion_summary

client = TestClient(app, raise_server_exceptions=False)


def test_pine_promotion_summary_blocks_high_risk_of_ruin():
    summary = build_promotion_summary(
        backtest_summary={
            "total_return": 12.0,
            "trade_count": 15,
            "max_drawdown": 8.0,
            "risk_of_ruin_pct": 4.5,
            "monte_carlo_pass": False,
        },
        compatibility_summary={"readiness": "READY", "compatibility_score": 90.0},
        ranking_summary={"combined_score": 80.0},
    )

    assert summary["profile_state"] == "DRAFT"
    assert "risk_of_ruin_pct" in summary["failed_gates"]
    assert "monte_carlo" in summary["failed_gates"]


def test_strategy_backtest_rejects_zero_slippage_assumption():
    response = client.post(
        "/api/v1/strategy/backtest",
        json={
            "index": "EGX30",
            "capital": 100000,
            "params": {"SL_PCT": 2.0},
            "commission_pct": 0.05,
            "slippage_pct": 0.0,
        },
    )

    assert response.status_code == 400
    assert "slippage_pct must be > 0" in response.json()["detail"]


def test_pine_promotion_summary_requires_phase3_evidence_and_validation():
    summary = build_promotion_summary(
        backtest_summary={
            "total_return": 18.0,
            "trade_count": 45,
            "max_drawdown": 9.0,
            "risk_of_ruin_pct": 0.4,
            "monte_carlo_pass": True,
            "walk_forward_pass": True,
            "oos_trade_count": 12,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
            "promotion_artifacts": {"artifact_hash": "abc123"},
        },
        compatibility_summary={"readiness": "READY", "compatibility_score": 92.0},
        ranking_summary={"combined_score": 82.0},
    )

    assert summary["profile_state"] == "READY"
    assert summary["failed_gates"] == []


def test_pine_promotion_summary_blocks_without_walk_forward_or_artifacts():
    summary = build_promotion_summary(
        backtest_summary={
            "total_return": 18.0,
            "trade_count": 45,
            "max_drawdown": 9.0,
            "risk_of_ruin_pct": 0.4,
            "monte_carlo_pass": True,
            "walk_forward_pass": False,
            "oos_trade_count": 0,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
        },
        compatibility_summary={"readiness": "READY", "compatibility_score": 92.0},
        ranking_summary={"combined_score": 82.0},
    )

    assert summary["profile_state"] == "DRAFT"
    assert "walk_forward" in summary["failed_gates"]
    assert "oos_trade_count" in summary["failed_gates"]
    assert "promotion_artifacts" in summary["failed_gates"]
