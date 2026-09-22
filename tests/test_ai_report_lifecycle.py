from core.settings import settings
from fastapi.testclient import TestClient

import api
from api import app
from core.ai_report.lifecycle import run_ollama_report_session
from utils.ollama_manager import OllamaManager, _normalize_ollama_host

client = TestClient(app, raise_server_exceptions=False)


def _snapshot_fixture():
    return {
        "as_of": "2026-03-31T10:00:00",
        "news": {"count": 1, "sentiment_score": 55, "sentiment_regime": "NEUTRAL", "headlines": []},
        "sectors": {"count": 2, "leading": [], "lagging": []},
        "whales": {"count": 0, "accumulation_count": 0, "distribution_count": 0, "top_accumulation": [], "top_distribution": []},
        "traps": {"bull_trap_count": 0, "bear_trap_count": 0, "recent_bull_traps": [], "recent_bear_traps": []},
        "arbitrage": {"count": 0, "top_mirrors": []},
        "strategy": {"regime": "NEUTRAL", "regime_score": 0, "volatility": "NORMAL", "reasoning": "Test", "changes": []},
        "oracle": {"macro_signal": "NEUTRAL", "macro_message": "Test", "macro_correlation": 0.1, "squeeze_count": 0, "top_squeezes": []},
        "signals": {
            "latest_run": None,
            "active_recommendations": [],
            "latest_scanner_signals": [],
            "buy_count": 0,
            "sell_count": 0,
            "avg_score": 0,
            "avg_confidence": 0,
            "whale_trap_summary": {},
            "enforcement_summary": {},
            "calibration_summary": {},
        },
        "portfolio": {
            "portfolio_id": 1,
            "portfolio_name": "My Portfolio",
            "open_positions": 0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "total_pnl": 0.0,
            "top_positions": [],
            "warnings": [],
        },
    }


class _FakeOllamaManager:
    def __init__(self, *, start_ok=True, ready_ok=True, stop_ok=True, base_url="http://127.0.0.1:11434"):
        self.start_ok = start_ok
        self.ready_ok = ready_ok
        self.stop_ok = stop_ok
        self.base_url = base_url
        self.calls = []

    def ensure_service_running(self, async_start=True):
        self.calls.append(("ensure_service_running", async_start))
        return self.start_ok

    def wait_until_ready(self, timeout_sec):
        self.calls.append(("wait_until_ready", timeout_sec))
        return self.ready_ok

    def stop_service(self, timeout_sec=10.0):
        self.calls.append(("stop_service", timeout_sec))
        return self.stop_ok

    def uses_local_service(self):
        return _normalize_ollama_host(self.base_url) in {"", "127.0.0.1", "localhost", "::1"}


def test_run_ollama_report_session_skips_local_process_management_for_remote_endpoint():
    fake_manager = _FakeOllamaManager(
        start_ok=True,
        ready_ok=True,
        stop_ok=True,
        base_url="http://ollama.internal:11434",
    )

    report, err, metadata = run_ollama_report_session(
        generate_report=lambda: ({"headline": "remote-ok"}, None),
        manager=fake_manager,
        ready_timeout_sec=5.0,
    )

    assert err is None
    assert report == {"headline": "remote-ok"}
    assert metadata["report_mode"] == "OLLAMA"
    assert metadata["ollama_start_attempted"] is False
    assert metadata["ollama_ready"] is True
    assert metadata["ollama_shutdown_attempted"] is False
    assert metadata["ollama_shutdown_ok"] is False
    assert fake_manager.calls == [("wait_until_ready", 5.0)]


def test_run_ollama_report_session_keeps_local_lifecycle_for_loopback_endpoint():
    fake_manager = _FakeOllamaManager(
        start_ok=True,
        ready_ok=True,
        stop_ok=True,
        base_url="http://127.0.0.1:11434",
    )

    report, err, metadata = run_ollama_report_session(
        generate_report=lambda: ({"headline": "local-ok"}, None),
        manager=fake_manager,
        ready_timeout_sec=5.0,
    )

    assert err is None
    assert report == {"headline": "local-ok"}
    assert metadata["report_mode"] == "OLLAMA"
    assert metadata["ollama_start_attempted"] is True
    assert metadata["ollama_ready"] is True
    assert metadata["ollama_shutdown_attempted"] is True
    assert metadata["ollama_shutdown_ok"] is True
    assert fake_manager.calls == [
        ("ensure_service_running", False),
        ("wait_until_ready", 5.0),
        ("stop_service", 10.0),
    ]


def test_wait_until_ready_returns_true_when_service_recovers(monkeypatch):
    manager = OllamaManager()
    checks = iter([False, False, True])

    monkeypatch.setattr(manager, "is_service_running", lambda: next(checks))
    monkeypatch.setattr("utils.ollama_manager.time.sleep", lambda *_args, **_kwargs: None)

    assert manager.wait_until_ready(timeout_sec=1.0, poll_interval_sec=0.01) is True


def test_stop_service_returns_true_when_service_already_stopped(monkeypatch):
    manager = OllamaManager()
    monkeypatch.setattr(manager, "is_service_running", lambda: False)

    assert manager.stop_service(timeout_sec=0.01) is True


def test_stop_service_uses_taskkill_for_windows_service_shutdown(monkeypatch):
    manager = OllamaManager()
    calls = []

    monkeypatch.setattr(manager, "is_service_running", lambda: True)
    monkeypatch.setattr(manager, "wait_until_ready", lambda timeout_sec, poll_interval_sec=0.25: False)
    monkeypatch.setattr("utils.ollama_manager.sys.platform", "win32")
    monkeypatch.setattr("utils.ollama_manager.time.sleep", lambda *_args, **_kwargs: None)

    def _fake_run(command, **kwargs):
        calls.append((command, kwargs))

        class _Completed:
            returncode = 0

        return _Completed()

    monkeypatch.setattr("utils.ollama_manager.subprocess.run", _fake_run)

    assert manager.stop_service(timeout_sec=0.5) is True
    assert calls[0][0] == ["taskkill", "/F", "/IM", "ollama.exe", "/T"]


def test_ai_daily_report_local_mode_exposes_idle_lifecycle_metadata(monkeypatch):
    snapshot = _snapshot_fixture()
    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", lambda snapshot, fallback_report: (None, None))

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=false&provider=LOCAL")

    assert response.status_code == 200
    body = response.json()
    assert body["report_mode"] == "LOCAL"
    assert body["ollama_start_attempted"] is False
    assert body["ollama_ready"] is False
    assert body["ollama_shutdown_attempted"] is False
    assert body["ollama_shutdown_ok"] is False
    assert body["ollama_lifecycle_reason"] is None


def test_ai_daily_report_ollama_start_failure_falls_back_with_lifecycle_metadata(monkeypatch):
    snapshot = _snapshot_fixture()
    fake_manager = _FakeOllamaManager(start_ok=False, ready_ok=False, stop_ok=True)

    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._build_ollama_manager", lambda base_url=None: fake_manager, raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_PROVIDER", "OLLAMA", raising=False)
    monkeypatch.setattr(
        "routes.ai_report._maybe_generate_llm_report",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("LLM generation should not run when Ollama start fails")),
    )

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["source"] == "rule_based"
    assert body["source_module"] == "LOCAL"
    assert body["degraded"] is True
    assert body["report_mode"] == "OLLAMA_FALLBACK"
    assert body["ollama_start_attempted"] is True
    assert body["ollama_ready"] is False
    assert body["ollama_shutdown_attempted"] is True
    assert body["ollama_shutdown_ok"] is True
    assert body["ollama_lifecycle_reason"] == "ollama_start_failed"
    assert body["fallback_reason"] == "Ollama service failed to start."


def test_ai_daily_report_ollama_success_reports_shutdown_metadata(monkeypatch):
    snapshot = _snapshot_fixture()
    fake_manager = _FakeOllamaManager(start_ok=True, ready_ok=True, stop_ok=True)

    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._build_ollama_manager", lambda base_url=None: fake_manager, raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_PROVIDER", "OLLAMA", raising=False)

    def _fake_llm(snapshot, fallback_report):
        setattr(__import__("routes.ai_report", fromlist=["x"])._maybe_generate_llm_report, "last_source_module", "OLLAMA")
        setattr(__import__("routes.ai_report", fromlist=["x"])._maybe_generate_llm_report, "last_fallback_reason", None)
        return fallback_report, None

    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", _fake_llm)

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "llm"
    assert body["source_module"] == "OLLAMA"
    assert body["report_mode"] == "OLLAMA"
    assert body["ollama_start_attempted"] is True
    assert body["ollama_ready"] is True
    assert body["ollama_shutdown_attempted"] is True
    assert body["ollama_shutdown_ok"] is True
    assert body["ollama_lifecycle_reason"] is None


def test_ai_daily_report_ollama_readiness_timeout_falls_back_cleanly(monkeypatch):
    snapshot = _snapshot_fixture()
    fake_manager = _FakeOllamaManager(start_ok=True, ready_ok=False, stop_ok=True)

    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._build_ollama_manager", lambda base_url=None: fake_manager, raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_PROVIDER", "OLLAMA", raising=False)
    monkeypatch.setattr(
        "routes.ai_report._maybe_generate_llm_report",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("LLM generation should not run before readiness succeeds")),
    )

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "rule_based"
    assert body["report_mode"] == "OLLAMA_FALLBACK"
    assert body["ollama_start_attempted"] is True
    assert body["ollama_ready"] is False
    assert body["ollama_shutdown_attempted"] is True
    assert body["ollama_shutdown_ok"] is True
    assert body["ollama_lifecycle_reason"] == "ollama_start_timeout"
    assert "did not become ready" in body["fallback_reason"]


def test_ai_daily_report_shutdown_failure_keeps_successful_report(monkeypatch):
    snapshot = _snapshot_fixture()
    fake_manager = _FakeOllamaManager(start_ok=True, ready_ok=True, stop_ok=False)

    monkeypatch.setattr("routes.ai_report._collect_cross_tab_snapshot", lambda portfolio_id=None: snapshot)
    monkeypatch.setattr("routes.ai_report._build_ollama_manager", lambda base_url=None: fake_manager, raising=False)
    monkeypatch.setattr(settings, "AI_REPORT_PROVIDER", "OLLAMA", raising=False)

    def _fake_llm(snapshot, fallback_report):
        setattr(__import__("routes.ai_report", fromlist=["x"])._maybe_generate_llm_report, "last_source_module", "OLLAMA")
        setattr(__import__("routes.ai_report", fromlist=["x"])._maybe_generate_llm_report, "last_fallback_reason", None)
        return fallback_report, None

    monkeypatch.setattr("routes.ai_report._maybe_generate_llm_report", _fake_llm)

    response = client.get("/api/v1/ai/daily-report?force_refresh=true&use_llm=true")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["source"] == "llm"
    assert body["source_module"] == "OLLAMA"
    assert body["report_mode"] == "OLLAMA"
    assert body["ollama_shutdown_attempted"] is True
    assert body["ollama_shutdown_ok"] is False
    assert body["ollama_lifecycle_reason"] == "ollama_shutdown_failed"


def test_startup_skips_ollama_warmup_for_on_demand_ai_reports(monkeypatch):
    class _FakeOllama:
        def __init__(self):
            self.calls = []

        def ensure_service_running(self, async_start=True):
            self.calls.append(("ensure_service_running", async_start))

        def ensure_model_available(self, model_name):
            self.calls.append(("ensure_model_available", model_name))

    fake_ollama = _FakeOllama()
    monkeypatch.setattr(settings, "AI_REPORT_PROVIDER", "OLLAMA", raising=False)
    from config.app_factory import _initialize_ai_report_ollama_runtime
    result = _initialize_ai_report_ollama_runtime(fake_ollama)

    assert result["warmup_skipped"] is True
    assert result["reason"] == "on_demand_ai_report_lifecycle"
    assert fake_ollama.calls == []


def test_ai_daily_report_broadcast_returns_lifecycle_metadata(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_TOKEN", "token-123", raising=False)
    monkeypatch.setattr(settings, "CHAT_ID", "-100123", raising=False)
    monkeypatch.setattr(
        "routes.ai_report.get_ai_daily_report",
        lambda **_kwargs: {
            "status": "success",
            "source_module": "LOCAL",
            "generated_at": "2026-03-31T12:00:00",
            "degraded": True,
            "degradation_reason": "llm_provider_failed",
            "fallback_reason": "Ollama service failed to start.",
            "provider_fallback_used": False,
            "snapshot_degraded": False,
            "snapshot_degradation": {"degraded": False, "issues": [], "module_status": {}},
            "report_mode": "OLLAMA_FALLBACK",
            "ollama_start_attempted": True,
            "ollama_ready": False,
            "ollama_shutdown_attempted": True,
            "ollama_shutdown_ok": True,
            "ollama_lifecycle_reason": "ollama_start_failed",
        },
    )
    monkeypatch.setattr("routes.ai_report.TelegramBot_Alerts.send_message", lambda _message: {"ok": True})

    response = client.post(
        "/api/v1/ai/daily-report/broadcast",
        json={"force_refresh": True, "use_llm": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report_mode"] == "OLLAMA_FALLBACK"
    assert body["ollama_start_attempted"] is True
    assert body["ollama_ready"] is False
    assert body["ollama_shutdown_attempted"] is True
    assert body["ollama_shutdown_ok"] is True
    assert body["ollama_lifecycle_reason"] == "ollama_start_failed"
