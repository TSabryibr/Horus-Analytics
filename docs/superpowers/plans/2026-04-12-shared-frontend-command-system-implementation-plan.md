# Horus Analytics II Shared Frontend Command System Implementation Plan

Date: 2026-04-12
Based on:

- `docs/superpowers/specs/2026-04-12-shared-frontend-command-system-design.md`
- `frontend/package.json`
- `frontend/playwright.config.ts`
- `frontend/playwright.audit.config.ts`
- `frontend/src/app/globals.css`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/IndustrialCard.tsx`
- `frontend/src/app/components/custom/IndustrialButton.tsx`
- `frontend/src/app/components/custom/IndustrialInput.tsx`
- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `frontend/src/app/live/components/LiveShell.tsx`
- `frontend/src/app/status/components/StatusShell.tsx`
- `frontend/e2e/e2e_crawl.spec.ts`
- `frontend/e2e/_phase3_audit.spec.ts`

Track: Frontend Shared Chrome Refresh
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved shared command-system refresh as an ordered frontend rollout that:

1. centralizes the page-frame and surface contract
2. standardizes navbar, header, toolbar, and card primitives
3. uses Oracle as the reference implementation
4. aligns Scanner, Live, and Status to the same shell language
5. keeps the broader app visually compatible with the new shared chrome
6. verifies the refresh with browser-first route crawl and layout audit coverage

## 2. In Scope

Primary implementation targets:

- global frontend chrome and token definitions
- shared navbar, header, toolbar, and card primitives
- Oracle, Scanner, Live, and Status shell alignment
- Home and remaining shell compatibility with the new page-frame contract
- Playwright crawl and layout-audit verification for the refreshed shared system
- narrow component-test coverage for shared primitives and shell contracts touched in this slice

Primary files expected to move:

- `frontend/src/app/globals.css`
- `frontend/src/app/components/MainLayoutWrapper.tsx`
- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/components/custom/`
- `frontend/src/app/oracle/components/`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/scanner/components/`
- `frontend/src/app/live/components/`
- `frontend/src/app/status/components/`
- `frontend/e2e/_phase3_audit.spec.ts`
- `frontend/e2e/e2e_crawl.spec.ts`

Out of scope for this slice:

- backend logic changes
- route-path or navigation-IA changes
- a full redesign of every analytical panel in the app
- cleanup of unrelated stale Jest suites that are not directly touched by the shared chrome rollout
- broad feature work outside the approved shared command-system spec

## 3. Execution Rules

These rules apply across the rollout:

1. Build the shared page-frame and primitive contract first; do not restyle route shells on top of undefined or duplicated global classes.
2. Treat Oracle as the reference page for the visual system, then align Scanner, Live, and Status against that reference.
3. Keep the refresh scanability-first; cinematic treatment must come from hierarchy, depth, and atmosphere rather than denser ornament.
4. Prefer additive extraction inside `frontend/src/app/components/custom/` instead of route-local chrome duplication.
5. Preserve `main` landmark visibility, sticky offsets, and overflow safety on every route touched.
6. Use browser-first verification at every major checkpoint; do not rely on stale page-specific unit suites as the primary signal.
7. Keep route data behavior stable unless a shell integration change requires a minimal presentational seam update.
8. Treat missing centralized definitions for `page-shell`, `page-shell-wide`, `page-shell-compact`, `section-surface`, `section-surface-muted`, and related classes as a first-class foundation task.

## 4. Work Package Sequence

Execute in this order:

1. `SFCS-P1` Global page-frame and token foundation
2. `SFCS-P2` Shared chrome primitive extraction
3. `SFCS-P3` Oracle reference rollout
4. `SFCS-P4` Scanner, Live, and Status shell alignment
5. `SFCS-P5` Home and remaining shell compatibility sweep
6. `SFCS-P6` Browser-first regression lock and release checkpoint

This order is intentional:

- the current shell classes are used broadly but are not centrally defined, so the page-frame contract must land first
- shared navbar, header, toolbar, and card primitives should stabilize before route adoption begins
- Oracle should define the reference implementation before the other high-value analytical routes inherit the system
- secondary shell compatibility should be resolved only after the core routes establish the final chrome language
- full-app browser verification should lock the integrated result, not partial intermediate assumptions

## 5. Work Packages

### SFCS-P1. Global Page-Frame and Token Foundation

Purpose:

Create the centralized layout and surface contract that the rest of the rollout depends on.

Target files:

- `frontend/src/app/globals.css`
- `frontend/src/app/layout.tsx`
- `frontend/src/app/components/MainLayoutWrapper.tsx`

Tasks:

1. Centralize the currently implicit shared shell classes in `globals.css`, including:
   - `page-shell`
   - `page-shell-wide`
   - `page-shell-compact`
   - `section-surface`
   - `section-surface-muted`
   - `stagger-in`
2. Add command-system token groups for:
   - page atmosphere
   - shell spacing
   - surface elevation tiers
   - chrome border intensity
   - sticky offsets below navbar and banner chrome
3. Align `MainLayoutWrapper` with the new page-frame contract so navbar, simulation banner, main content, scan overlays, and footer share one depth model.
4. Preserve the existing boot and layout composition semantics in `layout.tsx` while making the global chrome contract explicit.
5. Add or refine any minimal utility classes needed for safe overflow control and sticky-panel spacing across desktop and mobile.

Deliverables:

- centralized page-frame and surface utility contract
- shared global chrome tokens
- consistent navbar-to-main-to-footer frame behavior

Verification:

- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e:audit`

Acceptance criteria:

- the shared shell and surface classes are defined centrally instead of being only implicit usage contracts
- main content remains visible and free of critical overflow regressions in the audit
- navbar, banner, main feed, and footer share stable vertical framing

### SFCS-P2. Shared Chrome Primitive Extraction

Purpose:

Turn the approved command-system chrome into reusable shared primitives rather than one-off route markup.

Target files:

- `frontend/src/app/components/custom/IndustrialNavbar.tsx`
- `frontend/src/app/components/custom/IndustrialCard.tsx`
- `frontend/src/app/components/custom/IndustrialButton.tsx`
- `frontend/src/app/components/custom/IndustrialInput.tsx`
- `frontend/src/app/components/custom/CommandHeader.tsx`
- `frontend/src/app/components/custom/CommandToolbar.tsx`
- `frontend/src/app/components/custom/IndustrialNavbar.test.tsx`
- `frontend/src/app/components/custom/IndustrialCard.test.tsx`
- `frontend/src/app/components/custom/CommandHeader.test.tsx`
- `frontend/src/app/components/custom/CommandToolbar.test.tsx`

Tasks:

1. Refresh `IndustrialNavbar` into the approved grouped command ribbon:
   - stronger left brand block
   - cleaner horizontally scrollable route strip
   - clearer ops cluster for runtime, sync, and language
   - one shared active-route frame treatment
2. Expand `IndustrialCard` into the shared surface-card contract with explicit tone variants for `primary`, `secondary`, and `rail`.
3. Normalize button and input sizing so toolbars and command rails can share one height and interaction language.
4. Introduce `CommandHeader` as the reusable page-hero contract:
   - eyebrow label
   - title
   - mission text
   - status chip row
   - action rail slot
5. Introduce `CommandToolbar` as the shared filter/action strip contract for dense controls.
6. Add focused component tests for primitive rendering, tone/state variants, and landmark expectations.

Deliverables:

- reusable shared command-header primitive
- reusable shared command-toolbar primitive
- upgraded navbar and surface-card primitives
- focused shared-primitive tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/custom/IndustrialNavbar.test.tsx src/app/components/custom/IndustrialCard.test.tsx src/app/components/custom/CommandHeader.test.tsx src/app/components/custom/CommandToolbar.test.tsx`
- `npm --prefix frontend run build`

Acceptance criteria:

- shared chrome primitives exist outside any one route
- navbar grouping, active state, and mobile horizontal scroll behavior are standardized
- card tone hierarchy is available without route-local duplication

### SFCS-P3. Oracle Reference Rollout

Purpose:

Apply the shared system to Oracle first and use it as the visual reference implementation for the refresh.

Target files:

- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`
- `frontend/src/app/oracle/components/tac-briefing/ReportHistoryBrowser.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SupportResistanceRadar.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SentimentTimeline.tsx`
- `frontend/src/app/oracle/components/OracleShell.test.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.test.tsx`

Tasks:

1. Replace the current Oracle header treatment with the shared `CommandHeader` contract.
2. Convert Oracle search and action controls to the shared `CommandToolbar` language.
3. Reframe the main intelligence briefing as the `primary` surface-card tier.
4. Reframe radar and sentiment modules as `secondary` surface-card tier panels.
5. Reframe archives and tactical status as `rail` panels with consistent sticky spacing and height behavior.
6. Preserve Oracle data-fetch, ticker-search, refresh, and history-selection behavior while updating only the chrome contract.

Deliverables:

- Oracle as the first complete command-system page
- shared Oracle shell aligned with the approved card hierarchy

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/oracle/components/OracleShell.test.tsx src/app/oracle/components/OracleAiReportPanel.test.tsx`
- `npm --prefix frontend run build`

Acceptance criteria:

- Oracle reads as the reference page for the shared command system
- search, refresh, and archives remain intact
- primary, secondary, and rail surface tiers are visibly distinct

### SFCS-P4. Scanner, Live, and Status Shell Alignment

Purpose:

Move the other key acceptance routes onto the same shared shell language established by Oracle.

Target files:

- `frontend/src/app/scanner/components/ScannerShell.tsx`
- `frontend/src/app/scanner/components/ScannerControls.tsx`
- `frontend/src/app/scanner/components/ScannerPulsePanel.tsx`
- `frontend/src/app/scanner/components/ScannerResultsTable.tsx`
- `frontend/src/app/live/components/LiveShell.tsx`
- `frontend/src/app/status/components/StatusShell.tsx`
- `frontend/src/app/status/components/StatusFreshnessPanel.tsx`
- `frontend/src/app/status/components/StatusDiagnosticsPanel.tsx`
- `frontend/src/app/scanner/components/ScannerShell.test.tsx`
- `frontend/src/app/scanner/components/ScannerControls.test.tsx`
- `frontend/src/app/scanner/components/ScannerPulsePanel.test.tsx`
- `frontend/src/app/scanner/components/ScannerResultsTable.test.tsx`
- `frontend/src/app/live/components/LiveShell.test.tsx`
- `frontend/src/app/status/components/StatusShell.test.tsx`
- `frontend/src/app/status/components/StatusFreshnessPanel.test.tsx`
- `frontend/src/app/status/components/StatusDiagnosticsPanel.test.tsx`

Tasks:

1. Align Scanner to the shared command-header and command-toolbar contracts without changing scanner data semantics.
2. Normalize Scanner alert, stale-mode, and result-surface styling to the shared surface and alert language.
3. Align Live shell controls, header, and alert surfaces to the shared command-system primitives while keeping live-feed behavior intact.
4. Align Status shell header, runtime chips, and freshness/diagnostics support surfaces to the same chrome contract.
5. Keep page-specific density where needed, but remove route-local chrome shapes that conflict with the new system.
6. Update targeted shell and panel tests only where the shared contract is intentionally changed.

Deliverables:

- Scanner aligned to the shared command system
- Live aligned to the shared command system
- Status aligned to the shared command system

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/scanner/components/ScannerShell.test.tsx src/app/scanner/components/ScannerControls.test.tsx src/app/scanner/components/ScannerPulsePanel.test.tsx src/app/scanner/components/ScannerResultsTable.test.tsx src/app/live/components/LiveShell.test.tsx src/app/status/components/StatusShell.test.tsx src/app/status/components/StatusFreshnessPanel.test.tsx src/app/status/components/StatusDiagnosticsPanel.test.tsx`
- `npm --prefix frontend run build`

Acceptance criteria:

- Scanner, Live, and Status share the new shell language without losing route-specific readability
- alert, state, and support surfaces no longer feel like unrelated one-off systems
- no route-local chrome contract remains necessary for the aligned shells

### SFCS-P5. Home and Remaining Shell Compatibility Sweep

Purpose:

Ensure the new global page-frame and surface contract does not leave the rest of the app visually or structurally inconsistent.

Target files:

- `frontend/src/app/components/HomeShell.tsx`
- `frontend/src/app/analytics/components/AnalyticsShell.tsx`
- `frontend/src/app/arbitrage/components/ArbitrageShell.tsx`
- `frontend/src/app/audit/components/AuditShell.tsx`
- `frontend/src/app/news/components/NewsShell.tsx`
- `frontend/src/app/optimization/components/OptimizationShell.tsx`
- `frontend/src/app/portfolio/components/PortfolioShell.tsx`
- `frontend/src/app/reports/weekly/components/WeeklyReportShell.tsx`
- `frontend/src/app/seasonality/components/SeasonalityShell.tsx`
- `frontend/src/app/sectors/components/SectorShell.tsx`
- `frontend/src/app/settings/components/SettingsShell.tsx`
- `frontend/src/app/simulation/components/SimulationShell.tsx`
- `frontend/src/app/strategy/components/StrategyShell.tsx`
- `frontend/src/app/telegram/components/TelegramShell.tsx`
- `frontend/src/app/traps/components/TrapsShell.tsx`
- `frontend/src/app/whales/components/WhalesShell.tsx`

Tasks:

1. Align `HomeShell` with the updated page-frame contract so the top-level dashboard still reads as part of the same product family.
2. Sweep the remaining shell files for:
   - broken spacing against the new `page-shell` contract
   - mismatched section-surface usage
   - inconsistent sticky offsets
   - layout regressions introduced by the new chrome primitives
3. Prefer compatibility edits over full redesigns for these secondary routes.
4. Fix only the shell-level mismatches needed to keep the shared command system coherent across the broader app.

Deliverables:

- Home visually compatible with the shared command system
- remaining shell files normalized enough to avoid obvious chrome drift

Verification:

- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- Home still feels intentional within the new shared system
- remaining shell routes do not exhibit obvious page-frame drift or overflow regressions
- the full route crawl remains navigable after the compatibility sweep

### SFCS-P6. Browser-First Regression Lock and Release Checkpoint

Purpose:

Lock the rollout with browser-first verification and the smallest necessary targeted test coverage.

Target files:

- `frontend/e2e/e2e_crawl.spec.ts`
- `frontend/e2e/_phase3_audit.spec.ts`
- touched shell and primitive test files from `SFCS-P2` through `SFCS-P5`
- `frontend/.qa/phase3/report.json`

Tasks:

1. Update the Playwright crawl and audit only where the shared command-system rollout introduces a new stable contract worth checking.
2. Re-run the full route crawl and desktop/mobile layout audit against the refreshed app.
3. Regenerate the `.qa/phase3` report artifacts if the audit contract is still the active source of record.
4. Keep Jest coverage focused on shared primitives and touched shell contracts instead of broadening stale suite drift.
5. Record any remaining known test drift that is outside this shared-chrome slice.

Deliverables:

- refreshed browser-first verification evidence
- updated shared-shell and primitive test coverage
- explicit release checkpoint for the command-system rollout

Verification:

- `npm --prefix frontend run test:e2e`
- `npm --prefix frontend run test:e2e:audit`
- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/components/custom/IndustrialNavbar.test.tsx src/app/components/custom/IndustrialCard.test.tsx src/app/components/custom/CommandHeader.test.tsx src/app/components/custom/CommandToolbar.test.tsx src/app/oracle/components/OracleShell.test.tsx src/app/oracle/components/OracleAiReportPanel.test.tsx src/app/scanner/components/ScannerShell.test.tsx src/app/scanner/components/ScannerControls.test.tsx src/app/scanner/components/ScannerPulsePanel.test.tsx src/app/scanner/components/ScannerResultsTable.test.tsx src/app/live/components/LiveShell.test.tsx src/app/status/components/StatusShell.test.tsx src/app/status/components/StatusFreshnessPanel.test.tsx src/app/status/components/StatusDiagnosticsPanel.test.tsx`

Acceptance criteria:

- full-route crawl passes
- desktop and mobile audit passes without critical layout errors
- shared primitive and shell tests cover the new command-system contract
- any remaining unrelated Jest drift is explicitly isolated from this rollout

## 6. Risks and Controls

### Risk 1. Shared foundation changes break untouched shell routes

Control:

- centralize the missing shell contract first
- reserve a dedicated compatibility sweep for remaining shell files
- use the full route crawl before calling the rollout stable

### Risk 2. Oracle becomes polished while the rest of the app still drifts

Control:

- treat Oracle only as the reference implementation, not the end state
- align Scanner, Live, and Status in the same rollout track before closeout

### Risk 3. Browser-first confidence is diluted by stale unit-test drift

Control:

- keep Playwright crawl and layout audit as release gates
- add narrow shared-primitive tests only where the contract truly changes
- do not expand cleanup scope into unrelated legacy suite failures

### Risk 4. Cinematic treatment reduces readability on dense analytical pages

Control:

- preserve the scanability-first rule in every package
- limit motion and glow to chrome layers
- validate Scanner, Live, and Status with both desktop and mobile browser passes

### Risk 5. Sticky rails and toolbars regress on smaller screens

Control:

- centralize sticky offsets in the token layer
- test rail collapse and toolbar wrapping on mobile during audit
- keep right rails secondary to main-column readability

## 7. Recommended Execution Notes

- Start with `SFCS-P1` and `SFCS-P2` together if implementation batching is needed, because the route work depends on both the global frame contract and the shared chrome primitives.
- Keep route logic changes minimal and intentional; this rollout should primarily reshape presentation seams, not rework data hooks.
- Use Oracle screenshots and audit results as the visual checkpoint for the reference system before applying the same language to Scanner, Live, and Status.
- Treat the current implicit `page-shell` and `section-surface` contract as technical debt that should be eliminated early, not worked around route by route.

## 8. Recommended Next Move After This Plan

Execute `SFCS-P1` and `SFCS-P2` as the first active implementation slice. They establish the global page-frame contract and shared chrome primitives that every route-level package depends on.
