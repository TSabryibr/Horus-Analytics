# Quality Assurance & Test Coverage Gap Matrix
**Swarm Specialist:** `qa-engineer`  
**Target:** Test Suites, Edge Cases, Mock Isolation, and Regression Safety Gates  
**Evaluation Scope:** Untested failure paths, boundary conditions, mock leaks, and regression gates.

---

## 1. Test Suite State & Health Overview

| Metric | Measured Status | Standard / Target | Assessment |
| :--- | :--- | :--- | :--- |
| **Total Test Files** | 109 active, 31 quarantined in `legacy_root` | Clean separation | High Coverage |
| **Regression Suite Pass Rate** | 100% (all verified suites passing) | 100% | Stable Baseline |
| **Direct Pytest Execution** | Fails without `-m` (`ModuleNotFoundError`) | Clean execution via `pytest` | **Defect (QA-DX-1)** |
| **Failure Path Mocking** | Partial (only happy path + "chat not found") | All unrecoverable codes | **Gap (QA-GAP-1)** |
| **Simulated Time Coverage** | Unenforced in `core/` (wall clock leaks) | Strict `TimeUtils` isolation | **Gap (QA-GAP-2)** |

---

## 2. Critical Coverage Gaps & Untested Failure Paths

### GAP-01: Telegram Permanent Error & Subscriber Invalidation
- **Location:** [`core/signals/publishing.py:587-632`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/signals/publishing.py#L587-L632)
- **Current Test:** [`tests/test_horus_signal_intake_service.py:470-534`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/tests/test_horus_signal_intake_service.py#L470-L534)
- **The Blind Spot:**
  1. The existing test only injects `{"ok": False, "description": "Bad Request: chat not found"}`.
  2. The test sets `max_retries=0`, masking the fact that production runs (`max_retries=2` or `3`) sleep with exponential backoff on permanent errors.
  3. No test covers `"Forbidden: bot was blocked by the user"`, `"Forbidden: user is deactivated"`, or `"Bad Request: chat was deleted"`.
- **Regression Risk:** A code change to error handling could silently re-introduce retry storms or fail to pause blocked clients without triggering any test failure.
- **Required Test:**
  Create a parameterized test suite verifying that for all unrecoverable Telegram error codes (400, 403) and messages:
  - Exactly 1 attempt is made (retries are immediately aborted without sleep).
  - `client.delivery_fail_count` is incremented.
  - After 3 failures, `client.delivery_paused` becomes `True`.

### GAP-02: Simulated Time Invariance under `TimeUtils`
- **Location:** [`core/TimeUtils.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/TimeUtils.py), [`core/confluence.py:71`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/confluence.py#L71), [`core/AutoTrader.py:533`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/AutoTrader.py#L533)
- **Current State:** No automated test asserts that `core/` modules do not invoke raw `datetime.datetime.now()`.
- **The Blind Spot:** When tests or replays freeze or shift time using `TimeUtils.set_simulated_time()`, modules that call `datetime.now()` continue reading the host operating system clock.
- **Required Test:**
  Add a dedicated unit test setting `TimeUtils.set_simulated_time(datetime(2025, 5, 1, 12, 0))` and asserting that `confluence.py` evaluates May seasonal probabilities, not the current real calendar month.

### GAP-03: Dual `ConfluenceEngine` Import Coexistence
- **Location:** [`core/confluence.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/confluence.py) vs [`core/ConfluenceEngine.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/core/ConfluenceEngine.py)
- **Current State:** Each test suite tests only one engine in isolation (`test_confluence_engine.py` imports only `core.confluence`).
- **The Blind Spot:** No test verifies that an application thread importing `core.confluence` and another thread importing `core.ConfluenceEngine` do not collide or mutate shared state in `sys.modules`.
- **Required Test:**
  Import both classes in the same test module, instantiate both, and execute methods simultaneously to ensure separation.

### GAP-04: Watchdog Scheduler Pause / Resume Lifecycle
- **Location:** [`config/scheduler_setup.py:34-76`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/config/scheduler_setup.py#L34-L76)
- **Current Test:** [`tests/test_signal_sla_and_watchdog.py`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/tests/test_signal_sla_and_watchdog.py) tests `MarketFeedWatchdog.check_and_heal()` in isolation.
- **The Blind Spot:** No test verifies the APScheduler integration itself—specifically, that when `is_market_open()` toggles between `True` and `False`, `market_watchdog` is properly paused and resumed without leaking running tasks.
- **Required Test:**
  Mock `scheduler.pause_job` and `scheduler.resume_job` to assert state transition handling.

---

## 3. Quarantined Legacy Test Suite Assessment

The directory `tests/legacy_root/` contains 31 test files from prior architectural iterations:
```text
tests/legacy_root/
├── test_api.py
├── test_autotrader.py
├── test_execution_watchdog.py
├── test_hang[1-7].py
├── test_niflheim.py
├── test_scanner.py
└── ... (25 additional files)
```
- **Finding:** These tests are properly quarantined via `norecursedirs = tests/legacy_root` in [`pytest.ini`](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/pytest.ini).
- **Recommendation:** Keep them in `tests/legacy_root` for reference, but add a docstring in each file noting its archived status, preventing confusion for new maintainers.

---

SOURCES (LAYER 2 NAVIGATION)
docs/audit/phase2-gap-analysis/00-index.md
 -> Root index and navigation hub
docs/audit/phase2-gap-analysis/01-summary/executive-summary.md
 -> High-level synthesis of gap analysis findings
docs/audit/phase2-gap-analysis/02-analysis/code-review.md
 -> Code review, naming collisions, and time semantics analysis
docs/audit/phase2-gap-analysis/02-analysis/reliability-failure-modes.md
 -> SRE review of runtime failure modes and Telegram retry loops
docs/audit/phase2-gap-analysis/03-dossiers/action-matrix.md
 -> Prioritized P0/P1/P2 actionable remediation tasks with code diffs
