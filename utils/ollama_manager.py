import subprocess
import time
import requests
import logging
import os
import sys
import threading
from urllib.parse import urlparse

logger = logging.getLogger("horus.ollama_manager")

_LOCAL_OLLAMA_HOSTS = {"", "127.0.0.1", "localhost", "::1"}


def _normalize_ollama_host(base_url: str) -> str:
    raw_base_url = str(base_url or "").strip()
    if not raw_base_url:
        return ""

    parsed = urlparse(raw_base_url if "://" in raw_base_url else f"http://{raw_base_url}")
    return (parsed.hostname or "").strip().lower()

class OllamaManager:
    """
    Manages the lifecycle of the Ollama service to ensure it's available for the application.
    """
    def __init__(self, base_url="http://127.0.0.1:11434"):
        self.base_url = base_url.rstrip("/")
        self._service_thread = None

    def uses_local_service(self) -> bool:
        return _normalize_ollama_host(self.base_url) in _LOCAL_OLLAMA_HOSTS

    def is_service_running(self):
        """Checks if the Ollama service is responsive."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def wait_until_ready(self, timeout_sec=10.0, poll_interval_sec=0.5):
        """Polls until the Ollama HTTP endpoint responds or timeout expires."""
        deadline = time.monotonic() + max(0.0, float(timeout_sec))
        while time.monotonic() <= deadline:
            if self.is_service_running():
                return True
            time.sleep(max(0.01, float(poll_interval_sec)))
        return self.is_service_running()

    def start_service(self):
        """Attempts to start the Ollama service."""
        if self.is_service_running():
            logger.info("Ollama service is already running.")
            return True

        logger.info("Starting Ollama service (ollama serve)...")
        try:
            # Launch ollama serve as a background process
            # On Windows, we use CREATE_NO_WINDOW if available to prevent a console popup
            creationflags = 0
            if sys.platform == "win32":
                # DETACHED_PROCESS or CREATE_NO_WINDOW
                creationflags = 0x00000008 | 0x08000000

            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags,
                shell=False
            )

            if self.wait_until_ready(timeout_sec=10.0, poll_interval_sec=1.0):
                logger.info("Ollama service started successfully.")
                return True

            logger.error("Ollama service failed to start within 10 seconds.")
            return False
        except Exception as e:
            logger.error(f"Failed to start Ollama service: {e}")
            return False

    def ensure_service_running(self, async_start=True):
        """
        Ensures the Ollama service is running. 
        If async_start is True, it starts it in a background thread to avoid blocking startup.
        """
        if self.is_service_running():
            return True

        if async_start:
            self._service_thread = threading.Thread(target=self.start_service, daemon=True)
            self._service_thread.start()
            return True
        else:
            return self.start_service()

    def stop_service(self, timeout_sec=10.0):
        """Stops the Ollama service process without touching the desktop app wrapper."""
        if not self.is_service_running():
            logger.info("Ollama service is already stopped.")
            return True

        try:
            if sys.platform == "win32":
                completed = subprocess.run(
                    ["taskkill", "/F", "/IM", "ollama.exe", "/T"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    shell=False,
                    timeout=max(1.0, float(timeout_sec)),
                )
                if completed.returncode not in (0, 128):
                    logger.warning("taskkill returned non-zero while stopping Ollama: %s", completed.returncode)
            else:
                completed = subprocess.run(
                    ["pkill", "-f", "ollama serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                    shell=False,
                    timeout=max(1.0, float(timeout_sec)),
                )
                if completed.returncode not in (0, 1):
                    logger.warning("pkill returned non-zero while stopping Ollama: %s", completed.returncode)
        except Exception as e:
            logger.error(f"Failed to stop Ollama service: {e}")
            return False

        stopped = not self.wait_until_ready(timeout_sec=max(0.5, float(timeout_sec)), poll_interval_sec=0.25)
        if stopped:
            logger.info("Ollama service stopped successfully.")
        else:
            logger.warning("Ollama service did not stop within %.1f seconds.", float(timeout_sec))
        return stopped

    def ensure_model_available(self, model_name):
        """Checks if the specified model is available, and pulls it if not."""
        if not self.is_service_running():
            logger.warning("Ollama service not running; cannot check model availability.")
            return False

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5.0)
            if response.status_code != 200:
                return False
            
            models = response.json().get("models", [])
            model_names = [m.get("name") for m in models]
            
            if model_name in model_names or f"{model_name}:latest" in model_names:
                logger.info(f"Ollama model '{model_name}' is available.")
                return True
            
            logger.info(f"Ollama model '{model_name}' not found. Attempting to pull...")
            # We don't block startup for a pull, but we trigger it
            def pull_model():
                try:
                    requests.post(f"{self.base_url}/api/pull", json={"name": model_name}, timeout=(5.0, 300.0))
                    logger.info(f"Finished pulling Ollama model '{model_name}'.")
                except Exception as e:
                    logger.error(f"Failed to pull Ollama model '{model_name}': {e}")

            threading.Thread(target=pull_model, daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return False
