# Horus Analytics II Reliability-First Program Implementation Plan

Date: 2026-03-16
Based on: `docs/superpowers/specs/2026-03-16-reliability-first-program-design.md`
Execution model: Single owner
Planning horizon: 2-3 months
Primary objective: Production stability and operational hardening

## 1. Planning Goal

This implementation plan translates the approved reliability-first program design into an execution-ready backlog for one owner. It is designed for a live codebase with existing release pressure, a broad feature surface, and a clear need to reduce operational risk before pursuing wider feature growth.

The plan preserves three constraints:

1. The repository remains releasable at the end of each month.
2. High-risk structural changes are protected by targeted tests and diagnostics.
3. Backend/API and data pipeline stability remain the primary risk center, without neglecting frontend, CI, and operations.

## 1A. Current Execution Status

Status as of 2026-03-17: Phase 1 is complete in code and verification.

Closeout artifacts:

- Operator note/checklist: `docs/superpowers/reference/2026-03-17-phase-1-operator-checklist.md`
- Final checkpoint summary: `docs/superpowers/reference/2026-03-17-phase-1-final-checkpoint-summary.md`

Final checkpoint result:

- backend baseline passed
- frontend baseline passed
- browser baseline passed
- manual visual audit passed

## 2. Execution Rules

These rules apply to every work package in the program:

1. No structural refactor without a regression harness first.
2. No large module split combined with unrelated behavior changes in the same package.
3. Every high-risk package must include one observability or diagnostics improvement.
4. Every month ends with a release-quality checkpoint:
   backend tests green, frontend production build green, browser checks green.
5. Performance work starts only after the target boundary is stabilized and measurable.
6. Decomposition work must produce smaller units with explicit responsibility and testable seams.
7. If a package crosses backend, pipeline, and frontend concerns at once, split it before implementation.

## 3. Release Checkpoint Commands

These commands define the minimum release-quality checkpoint for this repository. Run them from the repo root. During active package work, narrower suites are acceptable for rapid iteration, but monthly checkpoints should return to this full baseline.

### Backend baseline

PowerShell:

```powershell
$env:HORUS_DB_FILE=':memory:'
$env:HORUS_DISABLE_READINESS_GATE='true'
$env:DEBUG='false'
python -m pytest tests/ --doctest-modules
```

### Frontend baseline

```powershell
npm --prefix frontend run lint
npm --prefix frontend run test -- --runInBand
npm --prefix frontend run build
```

### Browser baseline

Install browsers when needed:

```powershell
npm --prefix frontend exec playwright install
```

Run browser checks:

```powershell
npm --prefix frontend run test:e2e
```

### Checkpoint policy

1. Every Phase 1 package should pass the backend baseline or a justified package subset plus the full frontend baseline when frontend behavior is affected.
2. Every Phase 2 package that changes route, context, or runtime behavior should pass the relevant baseline plus browser checks.
3. Every end-of-month checkpoint should pass all three baselines.

## 4. Track Overview

The plan is divided into five tracks:

1. Backend/API Stability
2. Data Pipeline Reliability
3. Frontend Runtime Stability
4. Testing and CI Confidence
5. Operations and Observability

The tracks run in parallel, but the active focus shifts by phase:

- Phase 1: Backend/API, data pipeline, CI, and observability heavy
- Phase 2: Backend/API and data pipeline decomposition heavy, frontend normalization secondary
- Phase 3: Performance, operator confidence, and runtime polish

## 5. Phase Plan

### Phase 1: Safety Rails and Failure Visibility

Target duration: Weeks 1-4

#### Phase goal

Make failures visible, make releases trustworthy, and make degraded behavior explicit in the highest-risk parts of the app.

#### Phase 1 exit criteria

- [x] Backend failure paths are explicit in top-risk routes.
- [x] Pipeline freshness and degraded states are observable.
- [x] Frontend build, export, and runtime gates are strict and stable.
- [x] Browser-level CI remains active and trustworthy.
- [x] At least one operator-facing system path is easier to diagnose than it is today.

#### Phase 1 work packages

##### B1. Backend failure contract inventory

Status: Completed on 2026-03-17

Scope:

- `api.py`
- `routes/ai_report.py`
- `routes/signals.py`
- `routes/portfolio.py`
- `routes/analytics.py`

Tasks:

1. Inventory existing `except Exception` usage and categorize it as startup/runtime, domain fallback, user error, infrastructure error, or hidden failure.
2. Identify which handlers are preserving uptime correctly versus hiding invalid state.
3. Define target HTTP and error-contract patterns for the highest-risk endpoints.
4. Create focused tests for the highest-severity error paths before code changes.

Deliverables:

- Failure-mode matrix by route family
- Prioritized list of catch-all handlers to replace
- Regression tests for the first targeted endpoint family

Verification:

- Tests prove current and intended behavior for critical failure cases.

Closeout note:

- Completed through the Phase 1 backend packages `BA1` through `BA5`, with full backend baseline passing at checkpoint.

##### D1. Pipeline state model hardening

Status: Completed on 2026-03-17

Scope:

- `data_engine/freshness.py`
- `data_engine/pipeline_worker.py`
- `data_engine/sync.py`
- `core/pipeline.py`
- `routes/system.py`

Tasks:

1. Define canonical pipeline states and transition rules.
2. Make stale, syncing, fresh, degraded, and retry states visible through one clear contract.
3. Reduce ambiguity between worker state and API/system state.
4. Add targeted tests for state transitions and degraded-mode reporting.

Deliverables:

- Canonical state mapping
- Updated status reporting contract
- Transition-focused regression coverage

Verification:

- System status reflects worker and freshness state consistently under tests.

Closeout note:

- Completed through the Phase 1 data packages `DP1` through `DP4`, including sync-run diagnostics and provider-fallback visibility.

##### F1. Frontend boundary hardening

Status: Completed for Phase 1 scope on 2026-03-17

Scope:

- `frontend/src/lib/api.ts`
- `frontend/src/app/context/GlobalDataContext.tsx`
- `frontend/src/app/context/MarketContext.tsx`
- export-sensitive routes under `frontend/src/app/`

Tasks:

1. Identify remaining server/client data-boundary inconsistencies.
2. Remove export-breaking or environment-fragile fetch behavior.
3. Standardize critical fetch helpers and fallback handling for the highest-traffic pages.
4. Add route-level regression coverage where export or runtime behavior is fragile.

Deliverables:

- Reduced page-level ad hoc fetch patterns
- Stable export and runtime behavior for critical routes
- New route or context regression tests

Verification:

- Clean production build in a clean workspace
- Existing critical frontend tests still pass

Closeout note:

- Strict build enforcement, runtime/export stabilization, Playwright gating, and manual visual audit all passed. Deeper shared-data normalization remains Phase 2 work.

##### T1. Risk-based CI baseline

Status: Completed on 2026-03-17

Scope:

- `.github/workflows/ci.yml`
- targeted backend and frontend suites

Tasks:

1. Keep strict frontend build and Playwright gates active.
2. Add targeted tests around the first backend and pipeline stability packages.
3. Ensure CI feedback remains actionable and artifact-backed.

Deliverables:

- Stable CI workflow baseline
- Risk-tagged first-wave regression coverage

Verification:

- Build, backend tests, and Playwright artifacts remain available in CI.

Closeout note:

- CI now matches the working frontend command path and the Phase 1 checkpoint commands are documented and passing.

##### O1. Operator diagnostics baseline

Status: Completed on 2026-03-17

Scope:

- `api.py`
- `routes/system.py`
- `utils/logger.py`
- scheduler and worker touchpoints

Tasks:

1. Standardize logging fields for the top-risk failure paths.
2. Improve status messaging for startup, degraded mode, and retry loops.
3. Produce a first-pass operator diagnostic checklist for "system unhealthy" scenarios.

Deliverables:

- More actionable logs and status messages
- First operator diagnostic note

Verification:

- A failure in a top-risk path can be classified from status or log output without code inspection.

Closeout note:

- Completed via improved status/error contracts plus the new Phase 1 operator note/checklist.

### Phase 2: Structural Repair in High-Risk Areas

Target duration: Weeks 5-8

#### Phase goal

Split oversized modules and clarify interfaces so future changes stop requiring broad incidental edits.

#### Phase 2 exit criteria

- At least the first wave of oversized route modules is decomposed or extracted behind stable seams.
- Pipeline responsibilities are clearer and less entangled.
- Frontend shared-data behavior is more standardized.
- New seams are protected by integration or contract tests.

#### Phase 2 work packages

##### B2. Route decomposition wave 1

Status: Completed on 2026-03-17

Priority order:

1. `routes/portfolio.py`
2. `routes/signals.py`
3. `routes/ai_report.py`

Reasoning:

- `routes/portfolio.py` and `routes/signals.py` are central and broad but easier to segment by domain capability.
- `routes/ai_report.py` is the largest file and should be split after an extraction pattern is proven.

Tasks:

1. Create service-layer modules for extracted business logic.
2. Move route handlers toward transport-only responsibilities.
3. Group route responsibilities by capability, not by historical growth.
4. Add contract and integration tests for the new seams.

Deliverables:

- First reusable decomposition pattern
- Smaller route modules with clearer ownership
- Service modules with explicit interfaces

Verification:

- Existing API behavior is preserved.
- New seams are directly testable without full route execution.

Closeout note:

- The `routes/portfolio.py` and `routes/signals.py` Phase 2 decomposition slices are complete and checkpointed in `docs/superpowers/reference/2026-03-17-phase-2-portfolio-checkpoint-summary.md` and `docs/superpowers/reference/2026-03-17-phase-2-signals-checkpoint-summary.md`. The extraction pattern proved out cleanly enough that `routes/ai_report.py` is moved to the next backend decomposition wave rather than being forced into Phase 2 closeout.

##### D2. Pipeline decomposition wave 1

Status: Completed on 2026-03-17

Priority order:

1. `data_engine/ingest_intraday.py`
2. `data_engine/local_feed_selector.py`
3. `data_engine/sync.py`

Tasks:

1. Separate provider selection from ingest orchestration.
2. Separate persistence concerns from retrieval and normalization concerns.
3. Reduce hidden fallback logic that changes runtime behavior without surfacing state.
4. Add tests around provider failure, fallback, and state propagation.

Deliverables:

- Clearer boundaries between provider selection, ingestion, and storage
- Reduced hidden control flow
- Better fallback diagnostics

Verification:

- Provider failover and degraded mode are testable independently of full pipeline runs.

Closeout note:

- Provider normalization, timeframe resolution, context shaping, and reporting now live behind `data_engine/provider_selection.py`, with `data_engine/ingest_history.py`, `data_engine/ingest_intraday.py`, `data_engine/sync.py`, and `routes/data.py` consuming the extracted seam directly and `data_engine/local_feed_selector.py` reduced to source-quality discovery plus provider-decision helpers.

##### F2. Frontend shared-data normalization

Status: Completed on 2026-03-17

Priority areas:

- `frontend/src/app/context/GlobalDataContext.tsx`
- `frontend/src/app/context/MarketContext.tsx`
- selected high-traffic pages

Tasks:

1. Reduce duplicate data-fetch orchestration.
2. Clarify which data should be page-owned versus shared-context-owned.
3. Standardize loading, error, and stale-state patterns across the most used views.

Deliverables:

- Simplified shared-data access
- Reduced fetch duplication
- More consistent runtime behavior under partial outage

Verification:

- Critical pages show consistent state transitions under mock failure scenarios.

Closeout note:

- Shared-data domains now publish explicit `lastUpdated` timestamps through `frontend/src/app/context/NewsContext.tsx`, `frontend/src/app/context/DashboardContext.tsx`, and `frontend/src/app/context/MarketContext.tsx`, with `frontend/src/app/context/GlobalDataContext.tsx` aggregating a real sync-status surface for shared UI consumers. `frontend/src/app/context/MarketContext.tsx` also stopped re-fetching news and market feeds during Oracle hydration, so the shared contexts own those fetches once instead of duplicating them.

##### T2. Seam-focused regression expansion

Status: Completed on 2026-03-17

Tasks:

1. Add backend integration coverage for decomposed route families.
2. Add pipeline transition and degraded-mode tests.
3. Add targeted frontend tests around shared-data boundaries.

Deliverables:

- Better alignment between architecture and tests

Verification:

- Refactored seams are covered directly, not only indirectly.

Closeout note:

- Direct seam coverage now exists for portfolio identity/commands/queries/import-export/management, signals boundary/run/publish/outcomes services, and the extracted provider-selection pipeline seam.

##### O2. Structured operating surface

Status: Completed on 2026-03-17

Tasks:

1. Improve health semantics for backend and worker reporting.
2. Standardize operational log messages around retry, degrade, and fail-fast decisions.
3. Draft deployment and health-validation steps for routine releases.

Deliverables:

- Clearer runtime operating surface
- Initial deployment checklist

Verification:

- Release validation can be executed from the checklist without relying on memory.

Closeout note:

- The Phase 2 operating checklist and closeout summary are captured in `docs/superpowers/reference/2026-03-17-phase-2-operating-surface-checklist.md` and `docs/superpowers/reference/2026-03-17-phase-2-final-checkpoint-summary.md`.

### Phase 3: Throughput, Operational Confidence, and Runtime Polish

Target duration: Weeks 9-12

#### Phase goal

Optimize measured bottlenecks, improve operator confidence, and make the app behave consistently under stress.

#### Phase 3 exit criteria

- The most important bottlenecks have been measured and addressed.
- Operator workflows are documented and actionable.
- The app behaves more consistently during stale data, partial service loss, and background-worker issues.

#### Phase 3 work packages

##### P1. Measured performance profiling

Scope:

- reporting flows
- scanning flows
- pipeline-heavy paths
- highest-cost frontend pages

Tasks:

1. Profile backend hot spots before changing them.
2. Profile pipeline throughput and expensive retry loops.
3. Identify the most expensive frontend pages or data-access paths.
4. Prioritize only the top bottlenecks with measurable impact.

Deliverables:

- Bottleneck shortlist with evidence
- Optimization decisions based on measurement

Verification:

- Before and after metrics are captured for each optimization package.

##### O3. Operator runbook pack

Tasks:

1. Write recovery steps for common failure classes:
   pipeline stale, provider unavailable, startup degraded, backend route failure, and frontend runtime or build breakage.
2. Define retry versus degrade versus stop decision rules.
3. Add final deployment validation steps.

Deliverables:

- Lightweight operator runbook pack
- Final release checklist

Verification:

- You can follow the runbook to respond to a representative failure without code spelunking.

##### F3. Runtime UX consistency

Tasks:

1. Standardize stale-data UI semantics where feasible.
2. Improve failure and partial-outage messaging in operator-critical views.
3. Remove remaining inconsistent loading and error behavior in the most important pages.

Deliverables:

- More predictable runtime UX

Verification:

- Critical views behave consistently under simulated partial failure.

Closeout note:

- The frontend runtime decomposition wave now includes completed structural slices for `frontend/src/app/portfolio/page.tsx`, `frontend/src/app/settings/page.tsx`, and `frontend/src/app/live/page.tsx`, with the live slice checkpointed in `docs/superpowers/reference/2026-03-18-phase-6-live-checkpoint-summary.md`.

## 6. Package Dependencies

The following dependencies should guide execution order:

1. `B1` must precede `B2`.
2. `D1` must precede `D2`.
3. `F1` should begin in Phase 1 and continue before `F2`.
4. `T1` must start immediately and continue throughout all phases.
5. `O1` starts in Phase 1. `O2` and `O3` build on that baseline.
6. Phase 3 optimization work must not start before the structural-repair package in the same subsystem is complete.

## 7. First 14-Day Detailed Sprint

This is the immediate execution slice.

### Week 1

1. Build route-failure inventory for:
   - `routes/portfolio.py`
   - `routes/signals.py`
   - `routes/ai_report.py`
2. Build pipeline-state inventory for:
   - `core/pipeline.py`
   - `data_engine/pipeline_worker.py`
   - `data_engine/freshness.py`
   - `routes/system.py`
3. Identify remaining fragile export and runtime boundaries in frontend routes and contexts.
4. Confirm the release checkpoint commands and run them in the current workspace state.

### Week 2

1. Add first-wave regression tests around the highest-risk backend failure paths.
2. Add first-wave tests for pipeline-state visibility and degraded mode.
3. Improve logging and diagnostics in one top-risk backend flow and one top-risk pipeline flow.
4. Select the first route decomposition target and define its extraction boundaries before code changes begin.

## 8. Monthly Checkpoints

Use these checkpoints to decide whether the program is on track, not just whether tasks were completed.

### End of Month 1

- Failure inventory exists for the main route families and the core pipeline or system-state path.
- At least one top-risk backend error path is covered by regression tests and improved diagnostics.
- Pipeline stale and degraded behavior is visible through status output and tests.
- Frontend build, lint, unit tests, and browser checks are green from a clean checkout.

### End of Month 2

- `routes/portfolio.py` is either decomposed or has a merged extraction pattern ready to reuse.
- One pipeline hotspot has been split into clearer provider, orchestration, and persistence boundaries.
- Shared frontend data flow is more centralized in at least one context boundary.
- Integration tests protect the first extracted backend and pipeline seams.

### End of Month 3

- The top measured bottlenecks have before and after evidence.
- Runbooks exist for the common degraded and recovery scenarios.
- Critical operator-facing views behave consistently under stale data and partial outage.
- The repo can pass the full release checkpoint without ad hoc local fixes.

## 9. Decomposition Targets

Recommended first-wave structural targets:

### Backend/API

- `routes/portfolio.py`
- `routes/signals.py`
- `routes/ai_report.py`

### Data pipeline

- `data_engine/ingest_intraday.py`
- `data_engine/local_feed_selector.py`
- `data_engine/sync.py`

### Frontend

- `frontend/src/app/context/MarketContext.tsx`
- `frontend/src/app/components/Sidebar.tsx` if responsibility cleanup is still needed after data-boundary work

## 10. Verification Matrix

Each major package must declare:

1. Protected behavior
2. Test coverage added or updated
3. Diagnostics improved
4. Release gate impacted
5. Rollback or recovery path

Minimum required verification by track:

### Backend/API

- route-level regression tests
- contract tests for refactored seams
- explicit error-contract checks

### Data pipeline

- transition and degraded-mode tests
- provider-failure and fallback tests
- status and freshness verification

### Frontend

- strict production build
- page or context regression tests where boundaries change
- browser-check coverage for critical views

### Operations

- log and status review for failure classification
- repeatable deployment-validation steps

## 11. KPI Tracking Plan

Track these weekly:

1. Frontend production-build pass rate
2. Backend critical-path test pass rate
3. Browser smoke or E2E pass rate
4. Number of top-risk oversized modules still untreated
5. Number of critical flows with explicit degraded behavior
6. Number of operator-visible failure classes with actionable diagnostics

Recommended review cadence:

- Weekly checkpoint on active package status
- End-of-phase checkpoint against exit criteria

## 12. Skill Usage Plan

The missing `writing-plans` skill was replaced by this plan directly. Implementation work should use the relevant installed skills by package instead of forcing unrelated skills into the program.

### Backend/API packages

- `fastapi-expert`
- `fastapi-async-patterns`
- `backend-testing`
- `code-review-quality`

### Data and pipeline packages

- `python-performance-optimization`
- `performance-optimization`
- `backend-testing`
- `trading-expert` when validating domain-logic changes

### Frontend packages

- `accelint-nextjs-best-practices`
- `frontend-testing`
- `frontend-testing-best-practices`
- `playwright-core`

### CI/CD packages

- `github-actions-templates`
- `playwright-ci`

### Documentation packages

- `documentation-writer`
- `code-review-quality`

## 13. Immediate Next Step

Phase 19 is complete for the frontend Whales structural slice. The next active execution target is Phase 20 planning on `frontend/src/app/seasonality/page.tsx`.

Recommended next execution move:

1. Start Phase 20 planning for `frontend/src/app/seasonality/page.tsx`.
2. Follow the same capability-split pattern used in Phases 4 through 19: thin route shell, extracted runtime/action seams, and focused section-level components.

Derived Phase 1 plan artifacts:

- `docs/superpowers/plans/2026-03-16-phase-1-backend-api-plan.md`
- `docs/superpowers/plans/2026-03-16-phase-1-data-pipeline-plan.md`

Derived Phase 2 plan artifacts:

- `docs/superpowers/specs/2026-03-17-phase-2-portfolio-decomposition-design.md`
- `docs/superpowers/plans/2026-03-17-phase-2-portfolio-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-17-phase-2-portfolio-checkpoint-summary.md`
- `docs/superpowers/specs/2026-03-17-phase-2-signals-decomposition-design.md`
- `docs/superpowers/plans/2026-03-17-phase-2-signals-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-17-phase-2-signals-checkpoint-summary.md`
- `docs/superpowers/reference/2026-03-17-phase-2-operating-surface-checklist.md`
- `docs/superpowers/reference/2026-03-17-phase-2-final-checkpoint-summary.md`

Derived Phase 3 plan artifacts:

- `docs/superpowers/specs/2026-03-17-phase-3-ai-report-decomposition-design.md`
- `docs/superpowers/plans/2026-03-17-phase-3-ai-report-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-17-phase-3-ai-report-checkpoint-summary.md`
- `docs/superpowers/reference/2026-03-17-phase-3-operating-surface-checklist.md`
- `docs/superpowers/reference/2026-03-17-phase-3-final-checkpoint-summary.md`

Derived Phase 4 plan artifacts:

- `docs/superpowers/specs/2026-03-17-phase-4-frontend-portfolio-decomposition-design.md`
- `docs/superpowers/plans/2026-03-17-phase-4-frontend-portfolio-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-4-frontend-portfolio-checkpoint-summary.md`

Derived Phase 5 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-5-settings-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-5-settings-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-5-settings-checkpoint-summary.md`

Derived Phase 6 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-6-live-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-6-live-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-6-live-checkpoint-summary.md`

Derived Phase 7 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-7-simulation-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-7-simulation-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-7-simulation-checkpoint-summary.md`

Derived Phase 8 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-8-optimization-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-8-optimization-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-8-optimization-checkpoint-summary.md`

Derived Phase 9 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-9-telegram-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-9-telegram-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-9-telegram-checkpoint-summary.md`

Derived Phase 10 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-10-oracle-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-10-oracle-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-10-oracle-checkpoint-summary.md`

Derived Phase 11 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-11-audit-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-11-audit-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-11-audit-checkpoint-summary.md`

Derived Phase 12 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-12-status-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-12-status-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-12-status-checkpoint-summary.md`

Derived Phase 13 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-13-analytics-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-13-analytics-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-13-analytics-checkpoint-summary.md`

Derived Phase 14 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-14-sectors-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-14-sectors-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-14-sectors-checkpoint-summary.md`

Derived Phase 15 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-15-home-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-15-home-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-15-home-checkpoint-summary.md`

Derived Phase 16 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-16-scanner-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-16-scanner-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-16-scanner-checkpoint-summary.md`

Derived Phase 17 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-17-strategy-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-17-strategy-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-17-strategy-checkpoint-summary.md`

Derived Phase 18 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-18-weekly-report-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-18-weekly-report-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-18-weekly-report-checkpoint-summary.md`

Derived Phase 19 plan artifacts:

- `docs/superpowers/specs/2026-03-18-phase-19-whales-decomposition-design.md`
- `docs/superpowers/plans/2026-03-18-phase-19-whales-decomposition-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-19-whales-checkpoint-summary.md`

That keeps execution focused and matches the approved design rule that implementation planning may be split into track-specific or phase-specific plans for a single owner.
