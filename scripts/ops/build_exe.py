import shutil
import subprocess
import sys
import os
import stat
import time
from pathlib import Path


def _handle_remove_readonly(func, path, exc=None):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _force_remove_dir(path: Path, max_retries: int = 5, delay: float = 1.0) -> None:
    if not path.exists():
        return
    for attempt in range(max_retries):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(path, onexc=_handle_remove_readonly)
            else:
                shutil.rmtree(path, onerror=_handle_remove_readonly)
            if not path.exists():
                return
        except Exception:
            pass
        time.sleep(delay)
    if path.exists():
        print(f"Warning: Directory {path} could not be fully removed.")


def run_command(cmd: list[str], cwd: Path | None = None, env: dict | None = None, allow_failure: bool = False) -> None:
    
    printable = " ".join(f'"{c}"' if ' ' in c else c for c in cmd)
    print(f"Running: {printable}")
    
    try:
        # Try running directly as a list first (safest)
        result = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env, check=False)
    except FileNotFoundError:
        # Fallback to shell=True for things like 'npm' which might be aliases/batch files on Windows
        # We use the printable string which has proper quoting
        result = subprocess.run(printable, cwd=str(cwd) if cwd else None, env=env, shell=True, check=False)
        
    if result.returncode != 0 and not allow_failure:
        raise SystemExit(f"Error: command failed with return code {result.returncode}: {printable}")
    if result.returncode != 0 and allow_failure:
        print(f"Warning: command returned {result.returncode}, continuing: {printable}")


def _find_built_exe(dist_dir: Path) -> Path | None:
    preferred = [
        dist_dir / "HorusApp" / "HorusAnalytics.exe",
        dist_dir / "HorusAnalytics.exe",
    ]
    for candidate in preferred:
        if candidate.exists():
            return candidate

    direct = sorted(dist_dir.glob("*.exe"), key=lambda p: p.stat().st_mtime, reverse=True)
    if direct:
        return direct[0]

    nested = [
        p for p in dist_dir.glob("**/*.exe")
        if "_internal" not in p.parts and p.name.lower() != "node.exe"
    ]
    nested = sorted(nested, key=lambda p: p.stat().st_mtime, reverse=True)
    if nested:
        return nested[0]
    return None


def _copy_runtime_env_to_dist(project_root: Path, built_exe: Path) -> None:
    if os.getenv("HORUS_INCLUDE_RUNTIME_SECRETS_IN_DIST", "").strip().lower() not in {"1", "true", "yes", "on"}:
        print("Skipping runtime env copy. Set HORUS_INCLUDE_RUNTIME_SECRETS_IN_DIST=1 for a private local build.")
        return

    env_src = project_root / ".env"
    if not env_src.exists():
        print("Warning: .env was not found at project root; skipping dist env copy.")
        return

    env_target = built_exe.parent / ".env"
    shutil.copy2(env_src, env_target)
    print(f"Copied runtime env: {env_target}")


def _copy_runtime_settings_to_dist(project_root: Path, built_exe: Path) -> None:
    if os.getenv("HORUS_INCLUDE_RUNTIME_SECRETS_IN_DIST", "").strip().lower() not in {"1", "true", "yes", "on"}:
        print("Skipping runtime settings copy. Set HORUS_INCLUDE_RUNTIME_SECRETS_IN_DIST=1 for a private local build.")
        return

    settings_src = project_root / "settings.json"
    if not settings_src.exists():
        print("Warning: settings.json was not found at project root; skipping dist settings copy.")
        return

    settings_target = built_exe.parent / "settings.json"
    shutil.copy2(settings_src, settings_target)
    print(f"Copied runtime settings: {settings_target}")


def _copy_reset_script_to_dist(project_root: Path, built_exe: Path) -> None:
    reset_src = project_root / "RESET_APP_STATE.bat"
    if not reset_src.exists():
        print("Warning: RESET_APP_STATE.bat not found at project root; skipping dist reset script copy.")
        return

    reset_target = built_exe.parent / "RESET_APP_STATE.bat"
    shutil.copy2(reset_src, reset_target)
    print(f"Copied reset script: {reset_target}")


def _ensure_fresh_dist_runtime(built_exe: Path) -> None:
    """
    Enforce a fresh runtime state inside dist output.
    This guarantees no stale DB/data/log artifacts ship with a new build.
    """
    app_dir = built_exe.parent

    files_to_remove = [
        "horus.db",
        "horus.db-wal",
        "horus.db-shm",
        "signal_archive.json",
        "journal.json",
        "genesis.lock",
        "settings.json",
        "api_errors.log",
        "autotrader.log",
        "scanner.log",
    ]
    dirs_to_remove = [
        "reports",
    ]

    for name in files_to_remove:
        target = app_dir / name
        if target.exists():
            target.unlink()
            print(f"Removed stale runtime file: {target}")

    for name in dirs_to_remove:
        target = app_dir / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
            print(f"Removed stale runtime folder: {target}")


def _seed_runtime_data(project_root: Path, built_exe: Path) -> None:
    """Seed data lake history and intraday store from project root if missing or empty."""
    src_data = project_root / "data"
    if not src_data.exists():
        return
    dist_data = built_exe.parent / "data"
    dist_data.mkdir(parents=True, exist_ok=True)

    src_egx = src_data / "EGX"
    if src_egx.exists():
        dist_egx = dist_data / "EGX"
        dist_egx.mkdir(parents=True, exist_ok=True)

        src_intraday_db = src_egx / "intraday_store.sqlite"
        dist_intraday_db = dist_egx / "intraday_store.sqlite"
        if src_intraday_db.exists():
            if not dist_intraday_db.exists() or dist_intraday_db.stat().st_size < 100000:
                shutil.copy2(src_intraday_db, dist_intraday_db)
                print(f"Seeded intraday store: {dist_intraday_db} ({src_intraday_db.stat().st_size} bytes)")

        src_history = src_egx / "history"
        dist_history = dist_egx / "history"
        if src_history.exists():
            dist_history.mkdir(parents=True, exist_ok=True)
            for p in src_history.glob("*.parquet"):
                dist_p = dist_history / p.name
                if not dist_p.exists():
                    shutil.copy2(p, dist_p)


def _backup_runtime_data(dist_dir: Path, backup_dir: Path) -> None:
    app_dir = dist_dir / "HorusAnalytics"
    if not app_dir.exists():
        return
    backup_dir.mkdir(parents=True, exist_ok=True)
    for path in app_dir.iterdir():
        if path.name == "HorusAnalytics.exe" or path.name == "_internal":
            continue
        try:
            if path.is_file():
                shutil.copy2(path, backup_dir / path.name)
            elif path.is_dir():
                shutil.copytree(path, backup_dir / path.name, dirs_exist_ok=True)
            print(f"Backed up runtime asset: {path.name}")
        except Exception as e:
            print(f"Warning: Failed to back up {path.name}: {e}")


def _restore_runtime_data(backup_dir: Path, dist_dir: Path) -> None:
    app_dir = dist_dir / "HorusAnalytics"
    if not backup_dir.exists() or not app_dir.exists():
        return
    for path in backup_dir.iterdir():
        try:
            if path.is_file():
                shutil.copy2(path, app_dir / path.name)
            elif path.is_dir():
                shutil.copytree(path, app_dir / path.name, dirs_exist_ok=True)
            print(f"Restored runtime asset: {path.name}")
        except Exception as e:
            print(f"Warning: Failed to restore {path.name}: {e}")
    shutil.rmtree(backup_dir, ignore_errors=True)


def build_exe() -> None:
    project_root = Path(__file__).resolve().parent.parent.parent
    frontend_dir = project_root / "frontend"
    spec_file = project_root / "horus.spec"
    dist_dir = project_root / "dist"
    backup_dir = project_root / "build_runtime_backup"

    if shutil.which("npm") is None:
        raise SystemExit("Error: npm is not available in PATH. Install Node.js and retry.")
    if not frontend_dir.exists():
        raise SystemExit(f"Error: frontend directory not found: {frontend_dir}")
    if not spec_file.exists():
        raise SystemExit(f"Error: PyInstaller spec not found: {spec_file}")

    # KILL LINGERING PROCESSES
    print("Stopping any running HorusAnalytics instances...")
    if os.name == 'nt':
        subprocess.run(["taskkill", "/F", "/IM", "HorusAnalytics.exe", "/T"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["taskkill", "/F", "/IM", "horus.exe", "/T"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2) # Wait for file locks to release

    # BACKUP ACTIVE RUNTIME DATA
    print("Backing up active session data...")
    _backup_runtime_data(dist_dir, backup_dir)

    # CLEAN BUILD AND DIST
    for folder in ["build", "dist"]:
        path = project_root / folder
        if path.exists():
            print(f"Cleaning {folder}...")
            _force_remove_dir(path)

    print("--- Building Frontend (Next.js Static Export) ---")
    run_command(["npm", "install"], cwd=frontend_dir)
    run_command(["npm", "audit", "fix"], cwd=frontend_dir, allow_failure=True)
    env = os.environ.copy()
    api_key = os.getenv("API_KEY", "horus_default_key")
    env["NEXT_PUBLIC_API_KEY"] = api_key
    print(f"Building frontend with NEXT_PUBLIC_API_KEY={api_key[:4]}****")
    
    run_command(["npm", "run", "build"], cwd=frontend_dir, env=env)

    out_dir = frontend_dir / "out"
    index_file = out_dir / "index.html"
    if not out_dir.exists() or not index_file.exists():
        raise SystemExit("Error: frontend build did not produce frontend/out/index.html.")

    print("\n--- Bundling EXE with PyInstaller ---")
    _force_remove_dir(dist_dir / "HorusAnalytics")
    run_command([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "pyinstaller"])
    
    # Use the spec file for the final build
    run_command([sys.executable, "-m", "PyInstaller", "--clean", "--noconfirm", str(spec_file)], cwd=project_root)

    dist_dir = project_root / "dist"
    built_exe = _find_built_exe(dist_dir) if dist_dir.exists() else None
    if built_exe is None:
        raise SystemExit("Error: build finished but no .exe was found under dist/.")

    _ensure_fresh_dist_runtime(built_exe)
    _restore_runtime_data(backup_dir, dist_dir)
    _seed_runtime_data(project_root, built_exe)
    _copy_runtime_env_to_dist(project_root, built_exe)
    _copy_runtime_settings_to_dist(project_root, built_exe)
    _copy_reset_script_to_dist(project_root, built_exe)

    print("\nBuild complete.")
    print("Note: keep your runtime .env and data folders next to the executable when needed.")


if __name__ == "__main__":
    build_exe()
