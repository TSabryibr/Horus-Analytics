# Horus Analytics II Phase 5 Settings Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-5-settings-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 5
Status: Completed on 2026-03-18
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 5 settings decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/settings/page.tsx` into a thin route shell without changing the route path, backend API contracts, provider save/test semantics, exclusions behavior, or destructive operations behavior.

Phase 5 settings work should leave six things true:

1. The route page is no longer the primary home of bootstrap and save orchestration.
2. Settings load/runtime behavior is directly testable through a dedicated hook seam.
3. Provider and delivery actions are directly testable through an action hook seam.
4. Exclusions behavior is directly testable through a dedicated exclusions seam.
5. Destructive and operational controls are isolated behind an operations seam.
6. The extraction pattern is reusable for the remaining large frontend routes such as `live` and `simulation`.

## 2. In Scope

Primary source file:

- `frontend/src/app/settings/page.tsx`

Primary extraction target areas:

- `frontend/src/app/settings/hooks/`
- `frontend/src/app/settings/lib/`
- `frontend/src/app/settings/components/`

Primary route responsibilities to preserve:

- initial settings and exclusions load
- save settings and exclusions
- AI provider save/test flows
- Telegram and webhook delivery-related actions that currently live in the page
- exclusions add/remove/autocomplete
- local data-source policy editing
- market-hours editing
- historical backfill start/poll flow
- hard-reset flow

Out of scope for this Phase 5 slice:

- visual redesign of the settings page
- backend endpoint changes
- settings payload schema changes
- semantics changes for backfill or hard reset
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/settings/page.test.tsx`
- `frontend/src/app/context/GlobalDataContext.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/settings/hooks/useSettingsRuntime.test.tsx`
- `frontend/src/app/settings/hooks/useSettingsActions.test.tsx`
- `frontend/src/app/settings/hooks/useSettingsExclusions.test.tsx`
- `frontend/src/app/settings/hooks/useSettingsOperations.test.tsx`
- selected section-component tests for extracted settings sections

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/settings/hooks/useSettingsRuntime.ts`

Owns:

- bootstrap loading of settings, exclusions, and ticker universe
- base URL resolution
- shared message and loading state
- dirty-state calculation against original payloads

### `frontend/src/app/settings/hooks/useSettingsActions.ts`

Owns:

- save settings payload
- save/test AI provider credentials
- Telegram/webhook-related action flows currently tied to the route
- success/error mapping for those actions

### `frontend/src/app/settings/hooks/useSettingsExclusions.ts`

Owns:

- exclusion list state
- add/remove logic
- autocomplete filtering and selection helpers

### `frontend/src/app/settings/hooks/useSettingsOperations.ts`

Owns:

- historical backfill start and polling
- hard-reset token acquisition and execution
- operational status mapping

### `frontend/src/app/settings/lib/settingsForms.ts`

Owns:

- small normalization helpers for settings forms
- coercion utilities shared by hooks and presentational sections

### `frontend/src/app/settings/components/`

Target components:

- `SettingsShell.tsx`
- `SettingsTradingSection.tsx`
- `SettingsDeliverySection.tsx`
- `SettingsDataSourcesSection.tsx`
- `SettingsExclusionsSection.tsx`
- `SettingsMarketHoursSection.tsx`
- `SettingsOperationsSection.tsx`

The route page should remain the route owner and composition point. These extracted units should not import the route file.

## 5. Package Sequence

Execute the settings decomposition in this order:

1. `F5-P1` Runtime hook and shell extraction
2. `F5-P2` Actions hook and delivery/provider section extraction
3. `F5-P3` Exclusions and policy section extraction
4. `F5-P4` Operations seam, route slimdown, and checkpoint closeout

This order is intentional:

- the runtime seam removes the broadest route-local async state first
- provider and delivery actions are the highest-risk non-destructive mutation surface
- exclusions and policy sections can move after the shared runtime and action seams are stable
- destructive operations should move after the route’s shared message/base-URL contracts are already extracted

## 6. Work Packages

### F5-P1. Runtime Hook and Settings Shell Extraction

Purpose:

Establish one reusable seam for settings bootstrap and page-level runtime state before moving save and operations logic.

Target files:

- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/settings/hooks/useSettingsRuntime.ts`
- `frontend/src/app/settings/components/SettingsShell.tsx`

Tasks:

1. Move settings, exclusions, and ticker-universe bootstrap loading into `useSettingsRuntime`.
2. Move base URL resolution, shared message state, and dirty-state calculation into the same hook.
3. Extract the page frame and top-level save bar into `SettingsShell`.
4. Keep the route page as the owner of hook wiring and section composition.
5. Add direct tests for successful load, partial failure, and abort-cleanup behavior.

Deliverables:

- first reusable settings runtime hook
- thinner route shell
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/settings/page.test.tsx src/app/settings/hooks/useSettingsRuntime.test.tsx`

Acceptance criteria:

- bootstrap fetch logic no longer lives inline in the route page
- current route-level settings tests stay green
- runtime seam is directly testable without rendering the full page

### F5-P2. Actions Hook and Delivery/Provider Section Extraction

Purpose:

Move save and provider-action orchestration behind a command-style seam while preserving current provider and delivery behavior.

Target files:

- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/settings/hooks/useSettingsActions.ts`
- `frontend/src/app/settings/components/SettingsDeliverySection.tsx`
- `frontend/src/app/settings/lib/settingsForms.ts`

Tasks:

1. Move save settings/exclusions orchestration into `useSettingsActions`.
2. Move AI provider save/test flows into the same hook.
3. Move Telegram/webhook-related action flows currently tied to the route into the same hook.
4. Extract the delivery/provider section into `SettingsDeliverySection`.
5. Add direct action-hook tests for success, failure, and timeout/error mapping cases.

Deliverables:

- action-oriented settings hook seam
- extracted delivery/provider section
- direct action-hook regression coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/settings/page.test.tsx src/app/settings/hooks/useSettingsActions.test.tsx`

Acceptance criteria:

- settings save and provider-action logic are no longer primarily route-local
- route-level save/provider behavior remains unchanged
- new hook tests cover the main user-facing failure paths

### F5-P3. Exclusions and Policy Section Extraction

Purpose:

Isolate blacklist and policy editing from the broader save and runtime logic so the settings route stops mixing search/autocomplete state with the rest of the page.

Target files:

- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/settings/hooks/useSettingsExclusions.ts`
- `frontend/src/app/settings/components/SettingsExclusionsSection.tsx`
- `frontend/src/app/settings/components/SettingsDataSourcesSection.tsx`
- `frontend/src/app/settings/components/SettingsMarketHoursSection.tsx`
- `frontend/src/app/settings/components/SettingsTradingSection.tsx`

Tasks:

1. Move exclusion list state, add/remove logic, and autocomplete filtering into `useSettingsExclusions`.
2. Extract the exclusions section into `SettingsExclusionsSection`.
3. Extract the data-sources section, market-hours section, and trading/risk controls into focused components.
4. Add direct tests for exclusion add/remove/autocomplete and selected policy-section interactions.

Deliverables:

- dedicated exclusions seam
- extracted policy and exclusions sections
- direct exclusions regression coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/settings/page.test.tsx src/app/settings/hooks/useSettingsExclusions.test.tsx`

Acceptance criteria:

- exclusion behavior is no longer primarily route-local
- market-hours and data-source rendering no longer dominate the route file
- route-level settings behavior remains stable

### F5-P4. Operations Seam, Route Slimdown, and Closeout

Purpose:

Remove the remaining route-local business blocks, isolate destructive controls, and define the frontend checkpoint for this Phase 5 slice.

Target files:

- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`
- all new hook/component test files
- Phase 5 checkpoint docs

Tasks:

1. Move historical backfill start/poll logic into `useSettingsOperations`.
2. Move hard-reset token acquisition and execution into the same hook.
3. Extract the operations section into `SettingsOperationsSection`.
4. Remove dead or duplicated helper bodies from the route once extracted seams are live.
5. Run the full frontend baseline and browser checks.
6. Write the Phase 5 checkpoint summary and update the roadmap status.

Deliverables:

- dedicated operations seam
- materially thinner settings route page
- expanded direct seam coverage
- Phase 5 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/settings/page.tsx` is primarily a route shell and composition layer
- destructive controls are isolated behind an operations seam
- frontend baseline remains green
- the settings page has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted
5. rollback path

Minimum required verification for this Phase 5 slice:

- route-level settings Jest tests
- direct hook tests for runtime, actions, exclusions, and operations
- frontend lint and strict production build
- Playwright browser baseline

## 8. Risks and Controls

### Risk: state fragmentation across too many hooks

Control:

- keep each hook capability-bounded and return one coherent contract object instead of many independent values

### Risk: prop drilling from the route into every section

Control:

- extract UI sections around workflow boundaries rather than arbitrary markup blocks

### Risk: behavior drift in destructive controls

Control:

- preserve existing route-level tests and add direct operations tests before removing route-local logic

## 9. Suggested Execution Cadence

For a single owner, the expected order is:

1. `F5-P1`
2. `F5-P2`
3. `F5-P3`
4. `F5-P4`

Do not start the next package until the current package’s targeted tests are green.

## 10. Exit Checklist for the Phase 5 Settings Slice

This slice is complete when all of the following are true:

- `frontend/src/app/settings/page.tsx` is no longer the primary home for load/save/provider/operations orchestration
- runtime, actions, exclusions, and operations seams exist and are directly tested
- destructive controls remain behavior-compatible with the current backend contract
- the full frontend baseline and browser baseline are green
- a Phase 5 checkpoint summary is written and linked from the top-level roadmap

## 11. Recommended Next Move After This Plan

Phase 5 is complete. The next useful move after this slice is to plan the next frontend decomposition target, starting with `frontend/src/app/live/page.tsx`.
