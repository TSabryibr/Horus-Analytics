from pathlib import Path

from scripts.ops import build_exe


def test_dist_build_skips_runtime_secret_files_by_default(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    app_dir = tmp_path / "dist" / "HorusApp"
    project_root.mkdir()
    app_dir.mkdir(parents=True)
    built_exe = app_dir / "HorusAnalytics.exe"
    built_exe.write_text("", encoding="utf-8")
    (project_root / ".env").write_text("TELEGRAM_TOKEN=secret\n", encoding="utf-8")
    (project_root / "settings.json").write_text('{"TELEGRAM_TOKEN":"secret"}\n', encoding="utf-8")
    monkeypatch.delenv("HORUS_INCLUDE_RUNTIME_SECRETS_IN_DIST", raising=False)

    build_exe._copy_runtime_env_to_dist(project_root, built_exe)
    build_exe._copy_runtime_settings_to_dist(project_root, built_exe)

    assert not (app_dir / ".env").exists()
    assert not (app_dir / "settings.json").exists()


def test_dist_build_can_opt_in_to_copy_runtime_secret_files(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    app_dir = tmp_path / "dist" / "HorusApp"
    project_root.mkdir()
    app_dir.mkdir(parents=True)
    built_exe = app_dir / "HorusAnalytics.exe"
    built_exe.write_text("", encoding="utf-8")
    (project_root / ".env").write_text("TELEGRAM_TOKEN=secret\n", encoding="utf-8")
    (project_root / "settings.json").write_text('{"TELEGRAM_TOKEN":"secret"}\n', encoding="utf-8")
    monkeypatch.setenv("HORUS_INCLUDE_RUNTIME_SECRETS_IN_DIST", "1")

    build_exe._copy_runtime_env_to_dist(project_root, built_exe)
    build_exe._copy_runtime_settings_to_dist(project_root, built_exe)

    assert (app_dir / ".env").read_text(encoding="utf-8") == "TELEGRAM_TOKEN=secret\n"
    assert (app_dir / "settings.json").read_text(encoding="utf-8") == '{"TELEGRAM_TOKEN":"secret"}\n'


def test_pyinstaller_spec_does_not_bundle_env_file():
    spec_text = Path("horus.spec").read_text(encoding="utf-8")

    assert "('.env', '.')" not in spec_text
    assert '(".env", ".")' not in spec_text
