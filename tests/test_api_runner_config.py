from core.settings import settings
import api


def test_resolve_api_port_defaults_to_local_app_contract(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)

    assert api._resolve_api_port() == 8200


def test_resolve_api_port_honors_port_env(monkeypatch):
    monkeypatch.setenv("PORT", "8123")

    assert api._resolve_api_port() == 8123


def test_build_uvicorn_run_kwargs_omits_reload_options_when_reload_disabled(tmp_path):
    kwargs = api._build_uvicorn_run_kwargs(
        host="0.0.0.0",
        port=8200,
        is_debug=False,
        is_frozen=True,
        project_root=str(tmp_path),
    )

    assert kwargs["reload"] is False
    assert "reload_dirs" not in kwargs
    assert "reload_includes" not in kwargs
    assert "reload_excludes" not in kwargs


def test_build_uvicorn_run_kwargs_includes_reload_options_when_reload_enabled(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "data_engine").mkdir()

    kwargs = api._build_uvicorn_run_kwargs(
        host="127.0.0.1",
        port=8123,
        is_debug=True,
        is_frozen=False,
        project_root=str(tmp_path),
    )

    assert kwargs["reload"] is True
    assert kwargs["reload_dirs"] == [
        str(tmp_path / "routes"),
        str(tmp_path / "data_engine"),
    ]
    assert kwargs["reload_includes"] == ["*.py"]
    assert "__pycache__" in kwargs["reload_excludes"]


def test_resolve_startup_session_mode_uses_packaged_auto_detection(monkeypatch):
    monkeypatch.setattr(api.sys, "frozen", True, raising=False)
    monkeypatch.delenv("SESSION_MODE_FORCE", raising=False)
    monkeypatch.setattr(api.TimeUtils, "now", lambda: api.datetime.datetime(2026, 3, 22, 15, 0))
    monkeypatch.setattr(api.settings, "SESSION_MODE", "LIVE", raising=False)
    monkeypatch.setattr(api.settings, "MARKET_WEEKEND", [4, 5], raising=False)
    monkeypatch.setattr(api.settings, "_active_market_start", lambda: "1000", raising=False)
    monkeypatch.setattr(api.settings, "_active_market_end", lambda: "1430", raising=False)

    result = api._resolve_startup_session_mode()

    assert result["configured_session_mode"] == "LIVE"
    assert result["effective_session_mode"] == "ANALYSIS"
    assert result["forced_mode"] is False
    assert api.settings.SESSION_MODE == "ANALYSIS"
