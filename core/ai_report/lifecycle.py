from __future__ import annotations

import logging
from typing import Any, Callable, Optional


logger = logging.getLogger("horus.ai_report.lifecycle")


def run_ollama_report_session(
    *,
    generate_report: Callable[[], tuple[Optional[dict[str, Any]], Optional[str]]],
    manager: Any,
    ready_timeout_sec: float,
) -> tuple[Optional[dict[str, Any]], Optional[str], dict[str, Any]]:
    metadata = {
        "report_mode": "OLLAMA_FALLBACK",
        "ollama_start_attempted": False,
        "ollama_ready": False,
        "ollama_shutdown_attempted": False,
        "ollama_shutdown_ok": False,
        "ollama_lifecycle_reason": None,
    }
    manage_local_service = bool(getattr(manager, "uses_local_service", lambda: True)())

    try:
        if manage_local_service:
            metadata["ollama_start_attempted"] = True
            started = bool(manager.ensure_service_running(async_start=False))
            if not started:
                metadata["ollama_lifecycle_reason"] = "ollama_start_failed"
                return None, "Ollama service failed to start.", metadata

        ready = bool(manager.wait_until_ready(timeout_sec=ready_timeout_sec))
        metadata["ollama_ready"] = ready
        if not ready:
            metadata["ollama_lifecycle_reason"] = "ollama_start_timeout" if manage_local_service else "ollama_remote_unreachable"
            failure_label = "Ollama service did not become ready" if manage_local_service else "Ollama endpoint did not become ready"
            return None, f"{failure_label} within {ready_timeout_sec:.1f}s.", metadata

        report, err = generate_report()
        if report is not None:
            metadata["report_mode"] = "OLLAMA"
            return report, None, metadata

        metadata["ollama_lifecycle_reason"] = "ollama_generation_failed"
        return None, err or "Ollama report generation failed.", metadata
    finally:
        if manage_local_service:
            metadata["ollama_shutdown_attempted"] = True
            shutdown_ok = bool(manager.stop_service())
            metadata["ollama_shutdown_ok"] = shutdown_ok
            if not shutdown_ok and metadata["ollama_lifecycle_reason"] is None:
                metadata["ollama_lifecycle_reason"] = "ollama_shutdown_failed"
                logger.warning("Ollama shutdown failed after AI report session.")
