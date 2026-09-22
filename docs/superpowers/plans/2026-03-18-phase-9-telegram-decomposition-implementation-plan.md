# Horus Analytics II Phase 9 Telegram Decomposition Implementation Plan

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/specs/2026-03-18-phase-9-telegram-decomposition-design.md`

Track: Frontend Runtime Stability
Phase: Phase 9
Status: Complete on 2026-03-18
Owner model: Single owner

## 1. Goal

This plan turns the approved Phase 9 Telegram decomposition design into an executable extraction sequence. The purpose is to turn `frontend/src/app/telegram/page.tsx` into a thin route shell without changing the route path, backend API contracts, Telegram config semantics, broadcast semantics, report-dispatch behavior, scan-trigger behavior, or current visible activity-log behavior.

Phase 9 Telegram work should leave six things true:

1. The route page is no longer the primary home of config bootstrap and refresh orchestration.
2. The route page is no longer the primary home of config-form editing and config-save behavior.
3. The route page is no longer the primary home of broadcast, signal-card, and report-dispatch workflows.
4. Shared activity-log and modal-open behavior are isolated behind explicit seams.
5. Shared Telegram shell, status, broadcast, signal, config, and log panels are extracted into focused components.
6. The extraction pattern is reusable for the remaining large frontend runtime routes after `telegram`.

## 2. In Scope

Primary source file:

- `frontend/src/app/telegram/page.tsx`

Primary extraction target areas:

- `frontend/src/app/telegram/hooks/`
- `frontend/src/app/telegram/lib/`
- `frontend/src/app/telegram/components/`

Primary route responsibilities to preserve:

- config bootstrap and refresh behavior
- config modal open/save semantics
- general text/image broadcast behavior
- signal-card validation and dispatch semantics
- AI daily report dispatch behavior
- weekly/monthly analysis report dispatch behavior
- scan-trigger behavior
- current visible activity-log behavior

Out of scope for this Phase 9 slice:

- visual redesign of the Telegram page
- backend endpoint changes
- payload-schema changes for `/api/v1/telegram/config`
- payload-schema changes for `/api/v1/telegram/broadcast`
- payload-schema changes for `/api/v1/telegram/signal-card`
- payload-schema changes for `/api/v1/ai/daily-report/broadcast`
- payload-schema changes for `/api/v1/reports/analysis/broadcast`
- payload-schema changes for `/api/v1/control/scan`
- changes to Telegram business interpretation
- decomposing unrelated frontend routes in the same slice

## 3. Existing Test Anchors

Keep these green throughout the extraction:

- `frontend/src/app/telegram/page.test.tsx`
- `frontend/src/app/components/Sidebar.test.tsx`

Add direct seam tests gradually instead of replacing route coverage early:

- `frontend/src/app/telegram/hooks/useTelegramRuntime.test.tsx`
- `frontend/src/app/telegram/hooks/useTelegramConfig.test.tsx`
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.test.tsx`
- selected component tests for shell, config modal, broadcast panel, signal panel, and activity log

## 4. Target Module Map

The decomposition should converge on this internal shape:

### `frontend/src/app/telegram/hooks/useTelegramRuntime.ts`

Owns:

- config bootstrap fetch
- activity-log append behavior
- shared sending/runtime state if it remains cross-workflow
- config-modal open state
- narrow route-wide helpers such as request header construction if still needed

### `frontend/src/app/telegram/hooks/useTelegramConfig.ts`

Owns:

- config form state
- config hydration from current config
- config save flow
- config refresh wiring after save

### `frontend/src/app/telegram/hooks/useTelegramBroadcasts.ts`

Owns:

- general text/image broadcast flow
- signal-card validation and dispatch flow
- AI daily report dispatch
- weekly/monthly analysis report dispatch
- scan-trigger command flows

### `frontend/src/app/telegram/lib/telegramTransforms.ts`

Owns:

- pure log-line formatting helpers
- small status-label helpers
- pure form helpers if they reduce duplication cleanly

### `frontend/src/app/telegram/components/`

Target components:

- `TelegramShell.tsx`
- `TelegramStatusCard.tsx`
- `TelegramBroadcastPanel.tsx`
- `TelegramSignalPanel.tsx`
- `TelegramConfigModal.tsx`
- `TelegramActivityLog.tsx`

The route page should remain the route owner and composition point. Extracted units should not import the route file.

## 5. Package Sequence

Execute the Telegram decomposition in this order:

1. `F9-P1` Shared shell and runtime/config bootstrap extraction
2. `F9-P2` Broadcast and signal/report command extraction
3. `F9-P3` Config modal extraction and log/status extraction
4. `F9-P4` Route slimdown and checkpoint closeout

This order is intentional:

- runtime/config moves first because it establishes the shared shell and log pattern
- broadcast/report commands move second because they are the broadest async workflow surface
- config modal and status/log extraction move third because they depend on the runtime/config seam
- final slimdown happens only after all major workflows are extracted and directly tested

## 6. Work Packages

### F9-P1. Shared Shell and Runtime/Config Bootstrap Extraction

Status: Completed on 2026-03-18

Purpose:

Establish the shared route shell and isolate the config bootstrap/runtime behavior before moving the command flows.

Target files:

- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/hooks/useTelegramRuntime.ts`
- `frontend/src/app/telegram/components/TelegramShell.tsx`
- `frontend/src/app/telegram/components/TelegramStatusCard.tsx`

Tasks:

1. Extract the page frame, header, and top-level status chrome into `TelegramShell`.
2. Move config bootstrap, shared log state, and modal-open state into `useTelegramRuntime`.
3. Extract the current configured/online summary surface into `TelegramStatusCard`.
4. Add direct tests for bootstrap success/failure, log insertion, and shell/status rendering.

Deliverables:

- shared Telegram shell
- runtime/bootstrap seam
- extracted status card
- direct runtime seam tests

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/telegram/page.test.tsx src/app/telegram/hooks/useTelegramRuntime.test.tsx src/app/telegram/components/TelegramShell.test.tsx`

Acceptance criteria:

- config bootstrap is no longer primarily route-local
- shared shell is no longer defined inline in the route
- current route-level Telegram tests stay green

### F9-P2. Broadcast and Signal/Report Command Extraction

Status: Completed on 2026-03-18

Purpose:

Move the command-heavy broadcaster and signal/report workflows into a dedicated seam once the runtime shell is stable.

Target files:

- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.ts`
- `frontend/src/app/telegram/components/TelegramBroadcastPanel.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`
- `frontend/src/app/telegram/lib/telegramTransforms.ts`

Tasks:

1. Move general broadcast flow into `useTelegramBroadcasts`.
2. Move signal-card validation and submit flow into `useTelegramBroadcasts`.
3. Move AI daily report, weekly/monthly report, and scan-trigger flows into `useTelegramBroadcasts`.
4. Extract the general broadcast composer into `TelegramBroadcastPanel`.
5. Extract the signal/report action surface into `TelegramSignalPanel`.
6. Move pure log/status helpers into `telegramTransforms.ts`.
7. Add direct tests for command payload mapping, validation, success mapping, and selected panel rendering.

Deliverables:

- dedicated broadcast seam
- extracted broadcast panel
- extracted signal/report panel
- shared Telegram transforms
- direct broadcast seam coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/telegram/page.test.tsx src/app/telegram/hooks/useTelegramBroadcasts.test.tsx`

Acceptance criteria:

- broadcast and report workflows are no longer primarily route-local
- validation behavior remains unchanged
- route-level Telegram behavior remains stable

### F9-P3. Config Modal, Status, and Activity-Log Extraction

Status: Completed on 2026-03-18

Purpose:

Separate the config-form/edit flow and finish the major shared UI extraction around modal and log behavior.

Target files:

- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/hooks/useTelegramConfig.ts`
- `frontend/src/app/telegram/components/TelegramConfigModal.tsx`
- `frontend/src/app/telegram/components/TelegramActivityLog.tsx`

Tasks:

1. Move config form state, hydration, and config-save flow into `useTelegramConfig`.
2. Extract the config modal UI into `TelegramConfigModal`.
3. Extract the activity-log surface into `TelegramActivityLog`.
4. Keep current modal open/save/refresh behavior intact from the user perspective.
5. Add direct tests for config hydration/save mapping and activity-log rendering.

Deliverables:

- dedicated config seam
- extracted config modal
- extracted activity-log surface
- direct config seam coverage

Verification:

- `npm --prefix frontend run test -- --runInBand --testPathPatterns src/app/telegram/page.test.tsx src/app/telegram/hooks/useTelegramConfig.test.tsx`

Acceptance criteria:

- config edit/save behavior is no longer primarily route-local
- modal and activity-log behavior remain unchanged from the user perspective
- route-level Telegram behavior remains stable

### F9-P4. Route Slimdown and Closeout

Status: Completed on 2026-03-18

Purpose:

Remove the remaining route-local helper residue, finish seam coverage, and define the frontend checkpoint for this Phase 9 slice.

Target files:

- `frontend/src/app/telegram/page.tsx`
- all new hook/component test files
- Phase 9 checkpoint docs

Tasks:

1. Remove dead or duplicated helper bodies from the route once extracted seams are live.
2. Keep `page.tsx` focused on composition and minimal modal/status wiring only.
3. Run the full frontend baseline and browser checks.
4. Write the Phase 9 checkpoint summary and update the roadmap status.

Deliverables:

- materially thinner Telegram route page
- expanded direct seam coverage
- Phase 9 checkpoint artifacts

Verification:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

Acceptance criteria:

- `frontend/src/app/telegram/page.tsx` is primarily a route shell and composition layer
- runtime, config, and broadcast/report workflows are isolated behind explicit seams
- frontend baseline remains green
- the Telegram page has direct hook/component seam tests alongside route anchors

## 7. Verification Matrix

Each package must declare:

1. protected behavior
2. direct seam tests added or updated
3. route-level tests kept green
4. release gates impacted
5. rollback path

Minimum required verification for this Phase 9 slice:

- route-level Telegram Jest tests
- direct hook tests for runtime, config, and broadcast seams
- focused component tests for shell, modal, status, broadcast, signal, and log panels
- frontend lint and strict production build
- Playwright browser baseline

## 8. Risks and Controls

### Risk: shared sending/log state becomes coupled across every seam

Control:

- keep the runtime seam narrow and pass only minimal state/actions to each workflow seam

### Risk: config save behavior drifts from current modal semantics

Control:

- preserve the current open/hydrate/save/refresh sequence and cover it with route tests plus config seam tests

### Risk: log formatting becomes inconsistent across workflows

Control:

- centralize log-line formatting behind `useTelegramRuntime` or `telegramTransforms.ts` rather than rebuilding strings in each panel

### Risk: extracted panels become prop-heavy

Control:

- keep async orchestration in hooks and keep panel components display-oriented

## 9. Suggested Execution Cadence

For a single owner, the expected order is:

1. `F9-P1`
2. `F9-P2`
3. `F9-P3`
4. `F9-P4`

Do not start the next package until the current package's targeted tests are green.

## 10. Exit Checklist for the Phase 9 Telegram Slice

This slice is complete when all of the following are true:

- `frontend/src/app/telegram/page.tsx` is no longer the primary home for config, broadcast, and report-dispatch workflows
- runtime, config, and broadcast seams exist and are directly tested
- shared Telegram shell and major panels are extracted
- the full frontend baseline and browser baseline are green
- a Phase 9 checkpoint summary is written and linked from the top-level roadmap

Checkpoint artifact:

- `docs/superpowers/reference/2026-03-18-phase-9-telegram-checkpoint-summary.md`

## 11. Recommended Next Move After This Plan

Phase 9 is complete. Choose the next frontend decomposition target from the roadmap and begin with a design/spec pass before implementation.
