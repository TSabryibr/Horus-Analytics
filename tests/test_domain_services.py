"""
Tests for Domain Service Layer in core/services.
"""

import pytest
from fastapi import HTTPException
from core.services import portfolio_service, signal_service, system_service


def test_portfolio_service_queries():
    default_id = portfolio_service.resolve_id(None)
    assert default_id is None or isinstance(default_id, int)

    if default_id is not None:
        portfolio_data = portfolio_service.get_portfolio(default_id)
        assert isinstance(portfolio_data, dict)
    else:
        # Service correctly propagates HTTPException when no portfolio exists
        with pytest.raises(HTTPException) as exc_info:
            portfolio_service.get_portfolio(default_id)
        assert exc_info.value.status_code == 404

    positions = portfolio_service.get_positions(default_id)
    assert isinstance(positions, list)


def test_signal_service_desk():
    status = signal_service.get_desk_payload()
    assert isinstance(status, dict)

    runs = signal_service.get_run_history(limit=5)
    assert isinstance(runs, list)


def test_system_service_diagnostics():
    health = system_service.get_health_status()
    assert isinstance(health, dict)
    assert "status" in health
    assert "pipeline_state" in health

    logs = system_service.get_audit_trail(limit=10)
    assert isinstance(logs, list)
