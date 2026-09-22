from core.simulation import PortfolioSimulator

from core.execution_model import (
    MICROSTRUCTURE_METADATA_FIELDS,
    build_shadow_diagnostics,
)


def test_microstructure_shadow_diagnostics_contract_defaults():
    diagnostics = build_shadow_diagnostics()

    assert MICROSTRUCTURE_METADATA_FIELDS == (
        "route_profile",
        "liquidity_tier",
        "adv_10_shares",
        "adv_10_notional",
        "volume_mult_20",
        "sector_rs_14",
        "vsa_valid",
        "trap_risk",
        "expected_slippage_pct",
        "execution_cap_shares",
    )
    assert diagnostics["rollout_mode"] == "shadow"
    assert diagnostics["liquidity_cap_hits"] == 0
    assert diagnostics["rejected_notional"] == 0.0
    assert diagnostics["unliquidated_shares"] == 0
    assert diagnostics["unliquidated_notional"] == 0.0
    assert diagnostics["vsa_veto_count"] == 0
    assert diagnostics["sector_rs_veto_count"] == 0
    assert diagnostics["slippage_bucket_usage"] == {
        "light": 0,
        "heavy": 0,
        "capped": 0,
    }
    assert diagnostics["route_counts"] == {
        "EGX30_TREND_PROFILE": 0,
        "EGX70_TACTICAL_PROFILE": 0,
        "ILLIQUID_NO_TRADE_PROFILE": 0,
        "UNROUTED": 0,
    }


def test_run_simulation_returns_shadow_microstructure_contract_when_no_stocks(monkeypatch):
    monkeypatch.setattr(PortfolioSimulator, "load_all_stocks", lambda allowed_tickers=None, params=None: {})

    result = PortfolioSimulator.run_simulation(
        cap=200000,
        start_date="2025-01-01",
        end_date="2025-01-31",
        index_choice="EGX30",
        max_positions=5,
    )

    assert result["final_value"] == 200000
    assert result["microstructure"]["metadata_fields"] == list(MICROSTRUCTURE_METADATA_FIELDS)
    assert result["microstructure"]["diagnostics"] == build_shadow_diagnostics()
