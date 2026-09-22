from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "dock" + "er"
TOKEN_TITLE = "Dock" + "er"
COMPOSE_TOKEN = TOKEN + "-compose"


def _tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def test_container_runtime_files_are_not_present():
    banned = [
        "." + TOKEN + "ignore",
        ".env." + TOKEN,
        COMPOSE_TOKEN + ".yml",
        TOKEN_TITLE + "file.backend",
        TOKEN_TITLE + "file.frontend",
    ]

    present = [name for name in banned if (ROOT / name).exists()]

    assert present == []


def test_tracked_files_do_not_reference_container_runtime():
    banned_terms = [
        TOKEN,
        TOKEN_TITLE,
        COMPOSE_TOKEN,
        TOKEN_TITLE + "file",
        ".env." + TOKEN,
        "host." + TOKEN + ".internal",
    ]
    allowed_files = {Path("tests/test_no_container_runtime.py")}
    hits: list[str] = []

    for path in _tracked_files():
        rel_path = path.relative_to(ROOT)
        rel_str = str(rel_path).replace("\\", "/")
        if (
            rel_path in allowed_files
            or not path.exists()
            or path.is_dir()
            or rel_str.startswith(".claude/")
            or rel_str.startswith(".agents/")
            or rel_str.startswith("docs/")
            or rel_str.startswith("council-")
        ):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            lowered = line.lower()
            for term in banned_terms:
                if term.lower() in lowered:
                    hits.append(f"{rel_path}:{line_no}: {line.strip()}")

    assert hits == []
