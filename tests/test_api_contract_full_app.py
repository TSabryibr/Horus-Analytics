from fastapi.testclient import TestClient
import pytest

import api


client = TestClient(api.app, raise_server_exceptions=False)


def _ready_pipeline_state(state: str = "FRESH") -> dict:
    return {
        "bootstrap_complete": True,
        "status": "READY",
        "pipeline_state": state,
        "message": f"pipeline={state}",
        "freshness": {},
        "stale_override": False,
    }


def test_openapi_exposes_full_app_route_groups():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    operation_tags = {
        tag
        for path_item in paths.values()
        if isinstance(path_item, dict)
        for operation in path_item.values()
        if isinstance(operation, dict)
        for tag in operation.get("tags", [])
    }

    for path in (
        "/api/v1/system/status",
        "/api/v1/data/ticker/{ticker}",
        "/api/v1/portfolio",
        "/api/v1/news",
        "/api/v1/settings",
        "/api/v1/simulation/status",
        "/api/v1/scanner/status",
        "/api/v1/strategy",
        "/api/v1/live/status",
        "/api/v1/signals/runs",
        "/api/v1/ai/daily-report",
        "/api/v1/reports/analysis",
        "/api/v1/notifications/webhook/status",
        "/api/v1/system/audit",
    ):
        assert path in paths

    assert {
        "system",
        "data",
        "portfolio",
        "analytics",
        "settings",
        "simulation",
        "scanner",
        "strategy",
        "live",
        "signals",
        "ai-report",
        "analysis-reports",
        "notifications",
        "audit",
    }.issubset(operation_tags)


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/api/status",
        "/api/v1/health",
        "/api/v1/system/status",
        "/api/v1/settings",
        "/api/v1/notifications/webhook/status",
    ],
)
def test_api_v1_responses_apply_no_cache_headers(monkeypatch, path):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))
    monkeypatch.setattr("routes.system.refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))

    response = client.get(path)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"


def test_legacy_api_status_alias_returns_system_status(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))
    monkeypatch.setattr("routes.system.refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))

    response = client.get("/api/status")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "READY"
    assert body["pipeline_state"] == "FRESH"


def test_unknown_api_route_returns_json_404_with_no_cache_headers(monkeypatch):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))

    response = client.get("/api/v1/definitely-missing")

    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"


@pytest.mark.parametrize(
    ("method", "path", "json_body"),
    [
        ("POST", "/api/v1/scanner/start", None),
        ("POST", "/api/v1/live/start", None),
        ("POST", "/api/v1/live/stop", None),
        ("POST", "/api/v1/control/scan", None),
        ("POST", "/api/v1/strategy/apply", {"params": {"RISK_PER_TRADE": 1.0}}),
        ("POST", "/api/v1/signals/publish", {"run_id": 1}),
        ("POST", "/api/v1/signals/publish/retry", {"delivery_ids": [1]}),
        ("POST", "/api/v1/signals/publish/retry-latest", None),
        ("POST", "/api/v1/signals/outcomes/rebuild", {"run_id": 1}),
        ("POST", "/api/v1/signals/validation/walkforward/run", {"index": "EGX30"}),
        ("POST", "/api/v1/portfolio/add", {"ticker": "COMI"}),
        ("POST", "/api/v1/trade/add", {"ticker": "COMI"}),
        ("POST", "/api/v1/portfolio/close", {"ticker": "COMI"}),
        ("POST", "/api/v1/trade/close", {"ticker": "COMI"}),
        ("POST", "/api/v1/portfolio/update", {"ticker": "COMI"}),
        ("POST", "/api/v1/portfolio/seed", {}),
        ("POST", "/api/v1/portfolios", {"name": "Contract Test"}),
        ("DELETE", "/api/v1/portfolios/1", None),
    ],
)
def test_stale_mode_blocks_all_critical_app_actions(monkeypatch, method, path, json_body):
    from config import app_factory
    monkeypatch.setattr(app_factory, "_is_non_trading_day", lambda: False)
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("STALE"))

    response = client.request(method, path, json=json_body)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "stale_mode"
    assert body["pipeline_state"] == "STALE"
    assert body["method"] == method
    assert body["path"] == path


def test_stale_mode_does_not_block_portfolio_default_assignment(monkeypatch):
    from config import app_factory
    monkeypatch.setattr(app_factory, "_is_non_trading_day", lambda: False)
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("STALE"))

    response = client.post("/api/v1/portfolios/default", json={"portfolio_id": 1})

    assert response.status_code != 503


def test_daily_signal_runs_are_not_blanket_blocked_by_stale_mode_middleware(monkeypatch):
    from config import app_factory
    monkeypatch.setattr(app_factory, "_is_non_trading_day", lambda: False)
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("STALE"))
    monkeypatch.setattr(
        "routes.signals.run_daily_signals_logic",
        lambda req: {
            "status": "delegated",
            "scan_type": req.scan_type,
            "message": "route-level freshness gate should decide this path",
        },
    )

    response = client.post(
        "/api/v1/signals/runs/daily",
        json={"run_date": "2026-04-16", "scan_type": "DAILY"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "delegated"
    assert body["scan_type"] == "DAILY"
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/portfolio/balance",
        "/api/v1/portfolios",
        "/api/v1/notifications/webhook/status",
        "/api/v1/system/audit",
        "/api/v1/reports/analysis?period=weekly&force_refresh=true",
    ],
)
def test_representative_dependency_protected_routes_are_accessible_without_api_key(monkeypatch, path):
    monkeypatch.setattr(api, "_readiness_gate_disabled", lambda: False)
    monkeypatch.setattr(api, "refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))
    monkeypatch.setattr("routes.system.refresh_pipeline_state", lambda force=False: _ready_pipeline_state("FRESH"))
    monkeypatch.setattr(
        "routes.analysis_reports.evaluate_data_freshness_logic",
        lambda **kwargs: {"overall_ok": True, "issues": []},
    )

    response = client.get(path)

    assert response.status_code == 200
