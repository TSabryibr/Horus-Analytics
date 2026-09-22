import api
import config.startup as startup


def test_browser_prompt_skipped_by_env(monkeypatch):
    opened = []
    info_logs = []

    monkeypatch.setenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", "1")
    monkeypatch.setattr(startup.webbrowser, "open", opened.append)
    monkeypatch.setattr(startup.logger, "info", info_logs.append)

    did_open = startup._maybe_prompt_to_open_browser(8123)

    assert did_open is False
    assert opened == []
    assert info_logs == ["[Startup] Browser auto-open skipped (HORUS_DISABLE_BROWSER_AUTO_OPEN)."]


def test_browser_prompt_opens_when_user_confirms(monkeypatch):
    opened = []
    prompts = []

    monkeypatch.delenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", raising=False)
    monkeypatch.setattr(startup, "_has_interactive_console", lambda: True)
    monkeypatch.setattr(startup.webbrowser, "open", opened.append)
    monkeypatch.setattr(startup, "_startup_prompt", lambda message: prompts.append(message) or "yes")

    did_open = startup._maybe_prompt_to_open_browser(8123)

    assert did_open is True
    assert opened == ["http://localhost:8123"]
    assert prompts == ["Horus is ready at http://localhost:8123\nOpen frontend in your browser now? [y/N] "]


def test_browser_prompt_defaults_to_no(monkeypatch):
    opened = []
    info_logs = []

    monkeypatch.delenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", raising=False)
    monkeypatch.setattr(startup, "_has_interactive_console", lambda: True)
    monkeypatch.setattr(startup.webbrowser, "open", opened.append)
    monkeypatch.setattr(startup, "_startup_prompt", lambda message: "")
    monkeypatch.setattr(startup.logger, "info", info_logs.append)

    did_open = startup._maybe_prompt_to_open_browser(8123)

    assert did_open is False
    assert opened == []
    assert info_logs == ["[Startup] Browser launch declined by user."]


def test_browser_prompt_skipped_without_interactive_console(monkeypatch):
    opened = []
    info_logs = []

    monkeypatch.delenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", raising=False)
    monkeypatch.setattr(startup, "_has_interactive_console", lambda: False)
    monkeypatch.setattr(startup.webbrowser, "open", opened.append)
    monkeypatch.setattr(startup.logger, "info", info_logs.append)

    did_open = startup._maybe_prompt_to_open_browser(8123)

    assert did_open is False
    assert opened == []
    assert info_logs == ["[Startup] Browser launch prompt skipped (no interactive console). Frontend is ready at http://localhost:8123"]


def test_packaged_app_auto_opens_browser_without_interactive_console(monkeypatch):
    opened = []
    info_logs = []

    monkeypatch.delenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", raising=False)
    monkeypatch.setattr(startup, "_has_interactive_console", lambda: False)
    monkeypatch.setattr(startup.webbrowser, "open", opened.append)
    monkeypatch.setattr(startup.logger, "info", info_logs.append)
    monkeypatch.setattr(startup.sys, "frozen", True, raising=False)

    did_open = startup._maybe_prompt_to_open_browser(8123)

    assert did_open is True
    assert opened == ["http://localhost:8123"]
    assert info_logs == ["[Startup] Browser auto-opened for packaged app at http://localhost:8123"]


def test_prompt_completes_before_post_ready_services_start(monkeypatch):
    events = []

    monkeypatch.delenv("HORUS_DISABLE_BROWSER_AUTO_OPEN", raising=False)
    monkeypatch.setattr(startup, "_has_interactive_console", lambda: True)
    monkeypatch.setattr(startup, "_startup_prompt", lambda message: events.append(("prompt", message)) or "")
    monkeypatch.setattr(startup.logger, "info", lambda message: events.append(("log", message)))

    def start_services():
        events.append(("services", "started"))

    did_open = startup._complete_startup_interaction(8123, start_services)

    assert did_open is False
    assert events[0] == ("prompt", "Horus is ready at http://localhost:8123\nOpen frontend in your browser now? [y/N] ")
    assert events[1] == ("log", "[Startup] Browser launch declined by user.")
    assert events[2] == ("services", "started")
