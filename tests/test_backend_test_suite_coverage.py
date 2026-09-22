import subprocess
import sys
from pathlib import Path
from scripts.run_backend_tests import BATCHES, get_discoverable_test_files


ROOT = Path(__file__).resolve().parents[1]


def test_all_discoverable_test_files_are_batched():
    discoverable = get_discoverable_test_files()
    batched = {f.replace("\\", "/") for b in BATCHES.values() for f in b}

    missing = sorted(discoverable - batched)
    unknown = sorted(batched - discoverable)

    assert not missing, f"Active test files missing from BATCHES: {missing}"
    assert not unknown, f"Dead files present in BATCHES: {unknown}"


def test_run_backend_tests_check_coverage_cli_exits_cleanly():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "run_backend_tests.py"), "--check-coverage"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0
    assert "Coverage check passed" in result.stdout
