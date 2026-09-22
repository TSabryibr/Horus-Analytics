# Horus Analytics II Reliability-First Program Design

Date: 2026-03-16
Status: Approved for planning review
Primary objective: Production stability and operational hardening
Planning horizon: 2-3 months
Execution model: Single owner

## 1. Purpose

This spec defines a 2-3 month reliability-first improvement program for Horus Analytics II. The goal is not a broad rewrite. The goal is to make the existing system safer to operate, safer to release, easier to diagnose, and easier to evolve without destabilizing trading, reporting, ingestion, and frontend behavior.

The program is designed around the current repo state:

- A mixed FastAPI backend and Next.js frontend with broad feature coverage.
- Large, high-risk route and service modules.
- A substantial automated test surface, but uneven risk coverage.
- Existing Kubernetes and CI scaffolding.
- Many defensive `except Exception` paths that preserve uptime but reduce failure visibility.

This design intentionally uses relevant installed skills by domain instead of forcing every available skill into the program.

## 2. Codebase Observations

The roadmap is based on the current repository shape and the highest-risk modules:

### Backend/API hotspots

- `api.py` (~745 lines)
- `routes/ai_report.py` (~1981 lines)
- `routes/signals.py` (~1592 lines)
- `routes/portfolio.py` (~1099 lines)
- `routes/analytics.py` (~651 lines)

These files currently mix transport concerns, orchestration, fallback behavior, and domain logic. This increases regression risk and makes error contracts hard to reason about.

### Core/domain hotspots

- `core/ReportGenerator.py` (~749 lines)
- `core/Mimir_WFA.py` (~496 lines)
- `core/DataManager.py` (~408 lines)
- `core/scheduling.py` (~399 lines)
- `core/AutoTrader.py` (~382 lines)
- `core/RiskManager.py` (~372 lines)
- `core/SignalEngine.py` (~371 lines)
- `core/pipeline.py` (~248 lines)

### Data pipeline hotspots

- `data_engine/ingest_intraday.py` (~469 lines)
- `data_engine/local_feed_selector.py` (~465 lines)
- `data_engine/ingest_history.py` (~384 lines)
- `data_engine/metastock_dat_source.py` (~296 lines)
- `data_engine/mubasher_sqlite_source.py` (~295 lines)
- `data_engine/pipeline_worker.py` (~289 lines)
- `data_engine/api.py` (~280 lines)
- `data_engine/sync.py` (~231 lines)

### Frontend hotspots

- `frontend/src/app/context/MarketContext.tsx` (~145 lines but dense in fetch responsibility)
- `frontend/src/app/components/Sidebar.tsx` (~445 lines)
- Broad page surface across analytics, live, portfolio, settings, scanner, strategy, status, telegram, whales, and news routes.

### Quality and stability concerns observed

- Many broad `except Exception` handlers in backend, routes, core, and data-engine modules.
- Route modules are oversized and likely carrying too much orchestration logic.
- Data freshness and degraded-mode behavior exist, but there is still too much implicit fallback behavior.
- Frontend build/export behavior required hardening and recently exposed real issues when strict gates were restored.
- The repository has many tests, but release confidence still depends on targeting the right failure modes.

## 3. Program Strategy

Recommended strategy: `Reliability-First Program`

The sequencing rule is:

1. Stabilize platform boundaries first.
2. Split internals behind those boundaries.
3. Optimize performance and operator workflows after the architecture is safer.

This is preferred over:

- Architecture-first refactor: too much early churn for one owner.
- Surface hardening only: faster initially, but leaves structural instability in place.

## 4. Program Structure

The program will run as five separate tracks:

1. Backend/API Stability
2. Data Pipeline Reliability
3. Frontend Runtime Stability
4. Testing and CI Confidence
5. Operations and Observability

These tracks run in parallel, but not with equal intensity at all times. Backend/API and data pipeline remain the primary risk center throughout the program.

## 5. Track Definitions

### 5.1 Backend/API Stability

Scope:

- Decompose oversized route files by capability.
- Move orchestration and business logic out of transport handlers.
- Normalize success, error, and fallback contracts.
- Reduce catch-all exception behavior in top-risk endpoints.
- Clarify authentication and side-effect boundaries.

Primary target files:

- `api.py`
- `routes/ai_report.py`
- `routes/signals.py`
- `routes/portfolio.py`
- `routes/analytics.py`
- `routes/system.py`
- `routes/settings.py`

Expected outcomes:

- Route handlers become thinner and easier to test.
- Failure modes become explicit at the HTTP boundary.
- Refactors stop requiring edits across unrelated transport and domain logic.

### 5.2 Data Pipeline Reliability

Scope:

- Formalize freshness, stale mode, sync, retry, and worker-state semantics.
- Separate ingestion, provider selection, and persistence responsibilities.
- Tighten data-quality checks and degraded-mode diagnostics.
- Make provider fallback behavior observable and testable.
- Reduce silent recovery logic where it hides broken assumptions.

Primary target files:

- `data_engine/ingest_intraday.py`
- `data_engine/ingest_history.py`
- `data_engine/local_feed_selector.py`
- `data_engine/pipeline_worker.py`
- `data_engine/sync.py`
- `data_engine/freshness.py`
- `data_engine/data_quality.py`
- `core/pipeline.py`

Expected outcomes:

- Pipeline states are measurable rather than inferred.
- Recovery behavior becomes deterministic enough to test and operate.
- Provider health and data freshness become first-class operational concepts.

### 5.3 Frontend Runtime Stability

Scope:

- Standardize page/data boundaries.
- Reduce duplicated fetch and error-handling logic.
- Keep static export compatibility explicit.
- Make loading, stale-data, and partial-failure behavior consistent.
- Reduce state drift across contexts and page-level data access.

Primary target files:

- `frontend/src/app/context/GlobalDataContext.tsx`
- `frontend/src/app/context/MarketContext.tsx`
- `frontend/src/app/context/NewsContext.tsx`
- `frontend/src/lib/api.ts`
- `frontend/src/app/components/Sidebar.tsx`
- high-traffic pages under `frontend/src/app/`

Expected outcomes:

- UI behavior becomes more predictable under backend slowness or partial outage.
- Frontend runtime no longer relies on page-specific ad hoc fetch behavior.
- Export/build/runtime rules remain aligned.

### 5.4 Testing and CI Confidence

Scope:

- Maintain strict build and browser gates.
- Align tests to failure modes, not just file inventory.
- Increase contract and integration coverage around high-risk seams.
- Protect route decomposition and pipeline refactors with targeted regression tests.
- Preserve artifact visibility for browser and CI failures.

Primary target areas:

- `.github/workflows/ci.yml`
- `tests/`
- `frontend/src/**/*.test.tsx`
- `frontend/e2e/`

Expected outcomes:

- Release gates reflect real system risk.
- Refactors become safer because seam-level coverage exists.
- CI becomes a decision tool instead of a best-effort signal.

### 5.5 Operations and Observability

Scope:

- Standardize logging and failure classification.
- Improve health semantics for backend, pipeline, and worker recovery.
- Define operator decision rules: retry, degrade, fail-fast, or stop.
- Add deployment and runtime sanity validation.
- Produce lightweight runbooks and release checks.

Primary target files:

- `api.py`
- `routes/system.py`
- `core/scheduling.py`
- `core/websocket.py`
- `utils/logger.py`
- deployment and environment wiring

Expected outcomes:

- Failures are diagnosable.
- Operational state is legible to one owner.
- Deployment trust is based on validation, not assumption.

## 6. Phased Execution Plan

### Phase 1: Safety Rails and Failure Visibility

Duration: Month 1

Goals:

- Stop silent failure in the highest-risk areas.
- Tighten release gates.
- Make degraded behavior visible.
- Build a baseline for safe refactoring.

Work focus by track:

- Backend/API:
  inventory endpoint failure modes, define error mapping, reduce the most dangerous broad catches in high-risk routes.
- Data pipeline:
  define worker and freshness states, add degraded-mode diagnostics, validate provider failover behavior.
- Frontend:
  keep strict build/export/runtime gates and stabilize page/data boundaries where they are breaking production assumptions.
- Testing/CI:
  maintain strict frontend build and browser checks, add targeted regression coverage for recently hardened boundaries.
- Operations:
  make logging and status output reliable enough to diagnose top-severity failures.

Phase 1 exit criteria:

- Critical failure paths are visible.
- Frontend build and backend tests are trustworthy release gates.
- Degraded mode is explicit in at least the core pipeline and system-status flows.

### Phase 2: Structural Repair in High-Risk Areas

Duration: Month 2

Goals:

- Split oversized modules.
- Separate transport/orchestration/domain responsibilities.
- Clarify interfaces between backend, pipeline, and frontend.

Work focus by track:

- Backend/API:
  split route modules by capability and move business logic into service modules.
- Data pipeline:
  separate ingestion, provider selection, persistence, and state transition concerns.
- Frontend:
  normalize shared data access and remove duplicated fetch/state logic where backend seams are now clearer.
- Testing/CI:
  add contract/integration coverage around the refactored seams.
- Operations:
  improve structured status and log output around the newly clarified subsystem boundaries.

Phase 2 exit criteria:

- High-risk modules have clearer ownership.
- Important boundaries can be understood without reading large internals.
- Refactors in one subsystem no longer require broad incidental edits.

### Phase 3: Throughput, Operational Confidence, and Product Stability

Duration: Month 3

Goals:

- Optimize measured bottlenecks.
- Improve operator workflows.
- Improve UX stability under stress and partial outage.

Work focus by track:

- Backend/API and data pipeline:
  profile and optimize real bottlenecks rather than hypothetical ones.
- Frontend:
  improve behavior around stale data, loading states, and partial service loss.
- Testing/CI:
  ensure critical-path coverage remains aligned with changed architecture.
- Operations:
  add runbooks, deployment checks, and explicit retry/degrade/fail-fast guidance.

Phase 3 exit criteria:

- The app is easier to operate.
- The app is easier to change.
- The app is less surprising under failure and load.

## 7. Operating Model

This program must run as small, reviewable increments. The unit of work should typically be one subsystem seam at a time:

- one route family
- one worker flow
- one context/data boundary
- one deployment check
- one observability gap

Execution rules:

1. Every structural refactor starts with a failing regression test or an equivalent explicit harness.
2. Every high-risk change ships with one diagnostic improvement.
3. No large module split should happen at the same time as unrelated behavior changes in the same area.
4. Broad `except Exception` handling should be reduced only after the target error contract and fallback behavior are explicit.
5. At the end of each month, the repo must remain in a releasable state.

## 8. Anti-Goals

The program will not do the following early:

- No broad rewrite of trading domain logic purely for architecture aesthetics.
- No large UI redesign detached from runtime stability.
- No migration of every module at once.
- No continued reliance on broad catch-all error handling as a long-term safety mechanism.
- No performance optimization before the high-risk system seams are stabilized.

## 9. Success Criteria

By the end of the program:

- The highest-risk oversized modules are reduced or split behind clearer boundaries.
- Critical backend and pipeline failures are classified and visible.
- Frontend production builds, browser checks, and backend tests are reliable release gates.
- The app has explicit degraded-mode behavior for stale data, provider failure, and partial service loss.
- There is a stable operator workflow for understanding system state and validating deployments.

## 10. Deliverables

This program should produce:

1. A prioritized subsystem backlog by track.
2. A month-by-month execution plan with checkpoint criteria.
3. A shortlist of target files and modules for decomposition.
4. A stability KPI set.
5. A lightweight operating pack:
   health definitions, recovery notes, deployment checklist, and regression gates.

## 11. Initial Backlog Shape

### Highest-priority early backlog

- Reduce the most dangerous generic exception paths in top-risk routes.
- Standardize system and pipeline state semantics.
- Add targeted integration and contract tests around high-risk backend seams.
- Continue normalizing frontend export/build/runtime behavior.
- Improve logging and status visibility for background workers and recovery flows.

### Next structural backlog

- Decompose `routes/ai_report.py`
- Decompose `routes/signals.py`
- Decompose `routes/portfolio.py`
- Split ingestion/provider/persistence concerns in the data engine
- Consolidate frontend shared data access behavior

### Later optimization backlog

- Profile reporting and scan performance.
- Optimize measured slow paths only after contracts stabilize.
- Improve operator experience for diagnosing degraded mode and partial outage behavior.

## 12. Relevant Skill Mapping

Only relevant installed skills should be used. The program should not attempt to use every available skill.

### Backend/API

- `fastapi-expert`
- `fastapi-async-patterns`
- `backend-testing`
- `code-review-quality`

### Data pipeline and Python performance

- `python-performance-optimization`
- `performance-optimization`
- `backend-testing`
- `trading-expert` where market logic needs domain validation

### Frontend stability

- `accelint-nextjs-best-practices`
- `frontend-testing`
- `frontend-testing-best-practices`
- `playwright-core`

### CI/CD and release hardening

- `github-actions-templates`
- `playwright-ci`

### Documentation and execution discipline

- `documentation-writer`
- `code-review-quality`

## 13. Measurable KPIs

The roadmap should track a small set of decision-grade metrics:

- Frontend production build pass rate
- Backend critical-path test pass rate
- Browser smoke/E2E pass rate
- Number of top-risk modules still above agreed size/ownership thresholds
- Number of critical flows with explicit degraded-mode behavior
- Number of operator-visible failure classes with actionable diagnostics

## 14. Planning Readiness

This spec is ready to transition into an implementation plan if:

- the user approves the written document
- the roadmap remains scoped to the five tracks above
- the implementation plan preserves the month-by-month releasable-state constraint
- the implementation planning step is allowed to split work into track-specific plans or phase-specific plans so execution stays focused for a single owner
