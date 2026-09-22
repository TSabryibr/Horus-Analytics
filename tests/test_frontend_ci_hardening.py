from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"
LEGACY_WORKFLOW = ROOT / ".github" / "workflows" / "main.yml"
NEXT_CONFIG = ROOT / "frontend" / "next.config.ts"
PLAYWRIGHT_CONFIG = ROOT / "frontend" / "playwright.config.ts"
PLAYWRIGHT_AUDIT_CONFIG = ROOT / "frontend" / "playwright.audit.config.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_ci_workflow_consolidates_frontend_quality_gates() -> None:
    workflow = _read(CI_WORKFLOW)

    assert "concurrency:" in workflow
    assert "branches: [main, master, develop, Usung-Hermes]" in workflow
    assert "frontend-check:" in workflow
    assert "npm --prefix frontend run typecheck" in workflow
    assert "frontend-e2e:" in workflow
    assert "Set up Python for Backend API" in workflow
    assert "pip install -r requirements.txt" in workflow
    assert "cache-dependency-path: package-lock.json" in workflow
    assert "npm ci" in workflow
    assert "npm --prefix frontend run lint" in workflow
    assert "npm --prefix frontend run test -- --runInBand" in workflow
    assert "npm --prefix frontend run build" in workflow
    assert "npm --prefix frontend exec playwright install --with-deps" in workflow
    assert "npm --prefix frontend run test:e2e" in workflow
    assert "actions/cache@v4" in workflow
    assert "~/.cache/ms-playwright" in workflow
    assert "playwright-report" in workflow
    assert "test-results/" in workflow


def test_duplicate_main_workflow_is_removed() -> None:
    assert not LEGACY_WORKFLOW.exists()


def test_next_build_no_longer_ignores_typescript_or_eslint_failures() -> None:
    next_config = _read(NEXT_CONFIG)

    assert "ignoreDuringBuilds" not in next_config
    assert "ignoreBuildErrors" not in next_config


def test_playwright_config_uses_ci_friendly_reporting() -> None:
    playwright_config = _read(PLAYWRIGHT_CONFIG)

    assert "process.env.CI" in playwright_config
    assert "github" in playwright_config
    assert "open: 'never'" in playwright_config
    assert "testIgnore: ['**/_phase3_audit.spec.ts']" in playwright_config


def test_manual_audit_playwright_config_exists() -> None:
    audit_config = _read(PLAYWRIGHT_AUDIT_CONFIG)

    assert "testMatch: '**/_phase3_audit.spec.ts'" in audit_config
    assert "workers: 1" in audit_config
