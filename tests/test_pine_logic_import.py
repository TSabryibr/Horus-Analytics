from fastapi.testclient import TestClient
import pandas as pd

from api import app


client = TestClient(app, raise_server_exceptions=False)


def _make_import_history() -> pd.DataFrame:
    closes = [10, 10, 10, 10, 10, 11, 12, 13, 14, 13, 12, 11, 10, 9, 8]
    dates = pd.date_range("2025-01-01", periods=len(closes), freq="D")
    return pd.DataFrame(
        {
            "Date": dates,
            "Open": closes,
            "High": [value + 0.5 for value in closes],
            "Low": [value - 0.5 for value in closes],
            "Close": closes,
            "Volume": [1_000_000] * len(closes),
        }
    )


def test_pine_import_preview_returns_reviewable_draft_for_supported_strategy():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Importable Breakout", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["import_mode"] == "LOGIC_IMPORT"
    assert body["review_status"] in {"READY_FOR_REVIEW", "NEEDS_MANUAL_REVIEW"}
    assert body["reduced_source_pack"]["candidate_signals"]
    assert body["rule_spec"]["signals"]["long_entry"]["source_name"] in {"longCondition", "longE"}
    assert body["rule_spec"]["signals"]["long_exit"]["source_name"] in {"exitCondition", "longX"}
    assert body["rule_spec"]["human_summary"]["long_entry"]
    assert body["rule_spec"]["traceability"]


def test_pine_import_preview_recovers_signal_pack_from_mixed_indicator_script():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=6
indicator("Mixed Import", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
longE = ta.crossover(fast, slow)
longX = ta.crossunder(fast, slow)
plot(fast)
plot(slow)
alertcondition(longE, title="Long")
label.new(bar_index, close, "demo")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["reduced_source_pack"]["candidate_signals"]
    assert any(section["kind"] == "plot" for section in body["ignored_sections"])
    assert any(section["kind"] == "alert" for section in body["ignored_sections"])
    assert any(section["kind"] == "label" for section in body["ignored_sections"])
    assert body["rule_spec"]["signals"]["long_entry"]["source_name"] == "longE"
    assert body["rule_spec"]["signals"]["long_exit"]["source_name"] == "longX"


def test_pine_import_preview_surfaces_unresolved_references_from_candidate_signals():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
indicator("Unresolved Import", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
longE = ta.crossover(fast, slow) and externalFilter
longX = ta.crossunder(fast, slow)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    unresolved = body["reduced_source_pack"]["unresolved_references"]
    assert unresolved
    assert body["review_status"] == "NEEDS_MANUAL_REVIEW"
    assert unresolved[0]["name"] == "longE"
    assert "externalFilter" in unresolved[0]["references"]
    assert any("unresolved" in warning.lower() for warning in body["warnings"])


def test_pine_import_preview_does_not_flag_ta_crossover_as_unresolved_reference():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
indicator("No False Unresolved", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
leTrigger = ta.crossover(fast, slow)
longE = leTrigger
longX = ta.crossunder(fast, slow)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    unresolved = body["reduced_source_pack"]["unresolved_references"]
    assert unresolved == []
    assert not any("crossover" in warning.lower() and "unresolved" in warning.lower() for warning in body["warnings"])


def test_pine_import_preview_supports_history_references_in_import_signal_logic():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
indicator("History Support", overlay=true)
leTrigger = ta.crossover(close, ta.sma(close, 5))
lxTrigger = false
condition = 0.0
condition := leTrigger and condition[1] <= 0.0 ? 1.0 : lxTrigger and condition[1] >= 1.0 ? 0.0 : nz(condition[1])
longE = leTrigger and condition[1] <= 0.0 and condition == 1.0
longX = lxTrigger and condition[1] >= 1.0 and condition == 0.0
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["review_status"] == "READY_FOR_REVIEW"
    assert body["rule_spec"]["execution_plan"] is not None
    assert body["rule_spec"]["signals"]["long_entry"]["source_name"] == "longE"
    assert body["rule_spec"]["signals"]["long_exit"]["source_name"] == "longX"
    assert not any("unsupported pine expression node" in warning.lower() for warning in body["warnings"])


def test_pine_import_preview_builds_execution_plan_from_direct_triggers_when_state_machine_signals_are_not_importable():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
indicator("Wrapper Trigger Import", overlay=true)
useRes = input(true, "Use Alternate Signals")
basisType = input.string('ALMA', 'MA Type')
basisLen = input.int(2, 'MA Period')
offsetSigma = input.int(5, 'Sigma')
offsetALMA = input.float(0.85, 'ALMA Offset')
delayOffset = input.int(0, 'Delay')
variant(type, src, len, offSig, offALMA) => type == 'ALMA' ? ta.alma(src, len, offALMA, offSig) : ta.ema(src, len)
reso(exp, use, res) => use ? request.security(syminfo.tickerid, res, exp) : exp
closeSeries = variant(basisType, close[delayOffset], basisLen, offsetSigma, offsetALMA)
openSeries = variant(basisType, open[delayOffset], basisLen, offsetSigma, offsetALMA)
closeSeriesAlt = reso(closeSeries, useRes, '1W')
openSeriesAlt = reso(openSeries, useRes, '1W')
lxTrigger = false
sxTrigger = false
leTrigger = ta.crossover(closeSeriesAlt, openSeriesAlt)
seTrigger = ta.crossunder(closeSeriesAlt, openSeriesAlt)
condition = 0.0
longE = leTrigger and condition[1] <= 0.0 and condition == 1.0
shortE = seTrigger and condition[1] >= 0.0 and condition == -1.0
longX = lxTrigger and condition[1] >= 1.0 and condition == 0.0
shortX = sxTrigger and condition[1] <= -1.0 and condition == 0.0
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    execution_plan = body["rule_spec"]["execution_plan"]
    assert execution_plan is not None
    assert execution_plan["entry_expression"]["node_type"] == "VARIABLE_REF"
    assert execution_plan["entry_expression"]["name"] == "leTrigger"
    assert execution_plan["exit_expression"]["node_type"] == "VARIABLE_REF"
    assert execution_plan["exit_expression"]["name"] == "seTrigger"
    assert any("fallback" in warning.lower() and "letrigger" in warning.lower() for warning in body["rule_spec"]["warnings"])


def test_pine_import_preview_uses_deterministic_draft_fallback_when_translation_provider_is_unavailable():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Fallback Import", overlay=true)
basis = ta.sma(close, 20)
longCondition = close > basis
exitCondition = close < basis
if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["translation"]["mode"] == "DETERMINISTIC_DRAFT"
    assert body["translation"]["provider"] == "LOCAL"
    assert body["translation"]["fallback_used"] is True
    assert body["rule_spec"]["warnings"]
    assert any("deterministic draft" in warning.lower() for warning in body["rule_spec"]["warnings"])


def test_pine_import_preview_uses_provider_translation_when_available(monkeypatch):
    monkeypatch.setattr(
        "core.pine_lab.import_translation._attempt_provider_translation",
        lambda **_kwargs: (
            {
                "provider": "OLLAMA",
                "mode": "AI_TRANSLATED",
                "fallback_used": False,
                "model": "qwen-test",
            },
            {
                "signals": {
                    "long_entry": {"status": "mapped", "source_name": "entryA", "confidence": 0.88},
                    "short_entry": {"status": "missing", "source_name": None, "confidence": 0.0},
                    "long_exit": {"status": "mapped", "source_name": "exitB", "confidence": 0.86},
                    "short_exit": {"status": "missing", "source_name": None, "confidence": 0.0},
                },
                "warnings": ["Provider translation succeeded using reduced source pack context."],
            },
            None,
        ),
    )

    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
indicator("Provider Import", overlay=true)
fast = ta.sma(close, 10)
slow = ta.sma(close, 20)
entryA = ta.crossover(fast, slow)
exitB = ta.crossunder(fast, slow)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["translation"]["provider"] == "OLLAMA"
    assert body["translation"]["mode"] == "AI_TRANSLATED"
    assert body["translation"]["fallback_used"] is False
    assert body["rule_spec"]["signals"]["long_entry"]["source_name"] == "entryA"
    assert body["rule_spec"]["signals"]["long_exit"]["source_name"] == "exitB"
    assert body["review_status"] == "READY_FOR_REVIEW"


def test_pine_import_preview_falls_back_when_provider_translation_is_invalid(monkeypatch):
    monkeypatch.setattr(
        "core.pine_lab.import_translation._attempt_provider_translation",
        lambda **_kwargs: (
            {
                "provider": "OLLAMA",
                "mode": "AI_TRANSLATED",
                "fallback_used": False,
                "model": "qwen-test",
            },
            {
                "signals": {
                    "long_entry": {"status": "mapped", "source_name": "inventedSignal", "confidence": 0.91},
                    "short_entry": {"status": "missing", "source_name": None, "confidence": 0.0},
                    "long_exit": {"status": "mapped", "source_name": "exitCondition", "confidence": 0.87},
                    "short_exit": {"status": "missing", "source_name": None, "confidence": 0.0},
                },
                "warnings": [],
            },
            None,
        ),
    )

    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Invalid Provider Import", overlay=true)
basis = ta.sma(close, 20)
longCondition = close > basis
exitCondition = close < basis
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["translation"]["provider"] == "LOCAL"
    assert body["translation"]["mode"] == "DETERMINISTIC_DRAFT"
    assert body["translation"]["fallback_used"] is True
    assert body["rule_spec"]["signals"]["long_entry"]["source_name"] == "longCondition"
    assert any("provider" in warning.lower() and "fallback" in warning.lower() for warning in body["rule_spec"]["warnings"])


def test_pine_import_preview_embeds_execution_plan_for_approved_backtest_path():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Executable Import", overlay=true)
fast = ta.sma(close, 3)
slow = ta.sma(close, 5)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    execution_plan = body["rule_spec"].get("execution_plan")
    assert execution_plan
    assert execution_plan["execution_mode"] == "LONG_ONLY"
    assert execution_plan["entry_expression"]["node_type"] == "VARIABLE_REF"
    assert execution_plan["entry_expression"]["name"] == "longCondition"
    assert execution_plan["exit_expression"]["node_type"] == "VARIABLE_REF"
    assert execution_plan["exit_expression"]["name"] == "exitCondition"


def test_pine_import_backtest_requires_explicit_approval():
    preview = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Approval Gate", overlay=true)
fast = ta.sma(close, 3)
slow = ta.sma(close, 5)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert preview.status_code == 200
    rule_spec = preview.json()["rule_spec"]

    response = client.post(
        "/api/v1/strategy/pine/import-backtest",
        json={
            "rule_spec": rule_spec,
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
            "capital": 100000,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
        },
    )

    assert response.status_code == 400
    assert "approval" in response.json()["detail"].lower()


def test_pine_import_backtest_runs_approved_rule_spec_and_returns_comparison_metrics(monkeypatch):
    preview = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Approved Import", overlay=true)
fast = ta.sma(close, 3)
slow = ta.sma(close, 5)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
plot(fast)
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert preview.status_code == 200
    rule_spec = preview.json()["rule_spec"]

    monkeypatch.setattr("core.pine_lab.import_executor.MarketLists.get_market_list", lambda _market: {"COMI"})
    monkeypatch.setattr("core.pine_lab.import_executor.DataManager.get_stock_data", lambda *_args, **_kwargs: _make_import_history().copy())
    monkeypatch.setattr(
        "core.pine_lab.import_executor.PortfolioSimulator.run_simulation",
        lambda **_kwargs: {
            "starting_capital": 100000,
            "final_value": 103500,
            "total_return": 3.5,
            "trades": [{"ticker": "COMI", "pnl": 3500, "pnl_pct": 3.5}],
            "daily_values": [
                {"date": "2025-01-01", "value": 100000},
                {"date": "2025-01-15", "value": 103500},
            ],
        },
    )

    response = client.post(
        "/api/v1/strategy/pine/import-backtest",
        json={
            "rule_spec": rule_spec,
            "operator_approved": True,
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
            "capital": 100000,
            "commission_pct": 0.05,
            "slippage_pct": 0.1,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["import_mode"] == "LOGIC_IMPORT"
    assert body["backtest_source"] == "IMPORTED_RULE_SPEC"
    assert body["metrics"]["trade_count"] > 0
    assert body["import_metadata"]["operator_approved"] is True
    assert body["comparison"]["horus_core"]["metrics"]["total_return"] == 3.5
    assert body["comparison"]["winner_by_metric"]["trade_count"] in {"IMPORTED", "HORUS_CORE", "TIE"}


def test_pine_import_preview_applies_signal_overrides_for_review_edits():
    response = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
indicator("Override Import", overlay=true)
fast = ta.ema(close, 9)
slow = ta.ema(close, 21)
longE = ta.crossover(fast, slow)
manualEntry = close > slow
longX = ta.crossunder(fast, slow)
""",
            "signal_overrides": {
                "long_entry": "manualEntry",
            },
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["rule_spec"]["signals"]["long_entry"]["source_name"] == "manualEntry"
    assert body["rule_spec"]["execution_plan"]["entry_expression"]["name"] == "manualEntry"
    assert any("override" in warning.lower() for warning in body["rule_spec"]["warnings"])


def test_pine_import_profile_persists_saved_imported_rule_profile():
    preview = client.post(
        "/api/v1/strategy/pine/import-preview",
        json={
            "script_source": """
//@version=5
strategy("Saved Import Fixture", overlay=true)
fast = ta.sma(close, 3)
slow = ta.sma(close, 5)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
// unique-save-profile-fixture-001
""",
            "market": "EGX30",
            "timeframe": "1D",
            "date_from": "2025-01-01",
            "date_to": "2025-12-31",
        },
    )

    assert preview.status_code == 200
    rule_spec = preview.json()["rule_spec"]

    save_response = client.post(
        "/api/v1/strategy/pine/import-profile",
        json={
            "profile_name": "Saved Imported Logic Fixture 001",
            "script_source": """
//@version=5
strategy("Saved Import Fixture", overlay=true)
fast = ta.sma(close, 3)
slow = ta.sma(close, 5)
longCondition = ta.crossover(fast, slow)
exitCondition = ta.crossunder(fast, slow)
// unique-save-profile-fixture-001
""",
            "rule_spec": rule_spec,
            "operator_approved": True,
            "market": "EGX30",
            "timeframe": "1D",
            "backtest_summary": {
                "total_return": 6.2,
                "final_value": 106200,
                "trade_count": 5,
                "win_rate": 60.0,
                "max_drawdown": 2.5,
                "quality_score": 1.4,
            },
            "ranking_summary": {
                "performance_score": 72.0,
                "alignment_score": 31.0,
                "combined_score": 61.0,
            },
        },
    )

    assert save_response.status_code == 200
    saved_body = save_response.json()
    assert saved_body["status"] == "success"
    assert saved_body["source_type"] == "PINE_LOGIC_IMPORT"
    assert saved_body["profile_name"] == "Saved Imported Logic Fixture 001"

    list_response = client.get("/api/v1/strategy/pine/scanner-profiles")
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert any(
        profile["profile_name"] == "Saved Imported Logic Fixture 001"
        and profile["source_type"] == "PINE_LOGIC_IMPORT"
        for profile in list_body["profiles"]
    )

    detail_response = client.get(f"/api/v1/strategy/pine/scanner-profile/{saved_body['profile_id']}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["profile"]["source_type"] == "PINE_LOGIC_IMPORT"
    assert detail_body["import_rule_spec"]["source"]["import_mode"] == "LOGIC_IMPORT"
