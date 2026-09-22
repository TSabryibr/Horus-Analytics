# Horus Analytics II Phase 9 Telegram Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/telegram/page.tsx`
- `frontend/src/app/telegram/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 9 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/telegram/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- Telegram config bootstrap behavior
- config save semantics
- general broadcast semantics
- signal-card generation semantics
- AI daily report, weekly report, and monthly report dispatch behavior
- scan-trigger behavior
- current visible activity-log behavior

The route currently mixes three separate workflow domains in one file:

1. configuration bootstrap and config-modal editing
2. broadcast and report-dispatch command flows
3. shared sending/log/runtime state and large section rendering

Phase 9 should separate those workflows into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/telegram/page.tsx` is the strongest remaining frontend runtime target after the completed portfolio, settings, live, simulation, and optimization decompositions.

It is the right next boundary because:

- it is currently one of the largest untreated frontend routes at about 568 lines
- it owns both config-management and command-dispatch workflows
- it mixes modal state, async command state, and shared activity-log rendering in one component
- it coordinates several backend endpoints from one route
- it already has route-level test anchors that make structural extraction safer

The file currently combines:

- config bootstrap fetch
- config modal open/close and hydration
- config save flow
- general text/image broadcast flow
- signal-card generation flow
- AI daily report dispatch
- weekly/monthly analysis report dispatch
- scan-trigger commands
- shared sending state
- shared activity-log state
- large section rendering blocks

That makes the route harder to change safely because one edit can affect config persistence, broadcast dispatch, logging, and modal behavior at once.

## 3. Scope

Primary source file:

- `frontend/src/app/telegram/page.tsx`

Primary extraction target areas:

- `frontend/src/app/telegram/hooks/`
- `frontend/src/app/telegram/components/`
- `frontend/src/app/telegram/lib/`

In scope:

- config bootstrap and refresh behavior
- config modal state and config-save flow
- general broadcast flow
- signal-card flow
- AI daily report dispatch
- weekly/monthly analysis report dispatch
- scan-trigger actions
- shared activity-log state
- shared route shell and section/modal extraction

Out of scope:

- visual redesign of the Telegram route
- backend endpoint changes
- changing `/api/v1/telegram/config`, `/api/v1/telegram/broadcast`, `/api/v1/telegram/signal-card`, `/api/v1/ai/daily-report/broadcast`, `/api/v1/reports/analysis/broadcast`, or `/api/v1/control/scan`
- changing Telegram business rules or report semantics
- changing the visible wording of success/error/log outcomes unless required for contract preservation

## 4. Target Boundary

After decomposition, `frontend/src/app/telegram/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and presentational sections
- final ownership of modal mounting

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- config bootstrap and config refresh logic
- config form state and save behavior
- broadcast and signal-card submission logic
- report-dispatch and scan-trigger command flows
- shared activity-log append behavior
- large section and modal render blocks

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted panels and modal
- small amounts of glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move runtime, config, and broadcast/report behaviors behind separate hooks and extract major route sections into focused components.

Pros:

- strongest structural result
- matches the successful settings, live, simulation, and optimization decomposition pattern
- avoids leaving config and command-dispatch behavior tangled together

Cons:

- larger initial diff
- requires careful sequencing around shared sending/log state

### Option 2. Broadcast-first only, config later

Extract the broadcaster and report-dispatch side first and leave config bootstrap and config modal in the route.

Pros:

- lower short-term diff
- simpler first extraction

Cons:

- leaves one of the highest-risk async flows in the route
- weakens the value of the checkpoint

### Option 3. Section-components first, hooks later

Move JSX blocks into components first and keep all state/effects route-local.

Pros:

- makes the file look smaller quickly

Cons:

- simply relocates the visual tangle
- weak boundaries
- poor long-term testability

### Recommended option

Option 1.

The Telegram page already contains multiple independent async workflows. The correct boundary is one hook per capability plus a shared shell and focused sections.

## 6. Target Module Map

### `frontend/src/app/telegram/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted sections and modal

### `frontend/src/app/telegram/hooks/useTelegramRuntime.ts`

Owns:

- config bootstrap fetch
- shared sending/message state if it remains route-wide
- activity-log append behavior
- config-modal open state
- shared runtime helpers such as safe header construction if still needed

### `frontend/src/app/telegram/hooks/useTelegramConfig.ts`

Owns:

- config form state
- config-form hydration from loaded config
- config save flow
- config refresh integration

### `frontend/src/app/telegram/hooks/useTelegramBroadcasts.ts`

Owns:

- general text/image broadcast flow
- signal-card validation and submit flow
- AI daily report dispatch
- weekly/monthly report dispatch
- scan-trigger commands

### `frontend/src/app/telegram/lib/telegramTransforms.ts`

Owns:

- pure formatting helpers for log lines
- small status-label helpers
- form helpers if they reduce duplication cleanly

### `frontend/src/app/telegram/components/TelegramShell.tsx`

Owns:

- page frame
- header
- status banner
- top-level layout chrome

### `frontend/src/app/telegram/components/TelegramStatusCard.tsx`

Owns:

- current online/offline/configured summary surface

### `frontend/src/app/telegram/components/TelegramBroadcastPanel.tsx`

Owns:

- general broadcast composer
- image-attachment surface
- broadcast action trigger

### `frontend/src/app/telegram/components/TelegramSignalPanel.tsx`

Owns:

- signal-card form
- AI daily report trigger
- weekly/monthly report triggers
- scan-trigger actions

### `frontend/src/app/telegram/components/TelegramConfigModal.tsx`

Owns:

- config modal presentation
- config form rendering
- config-save trigger

### `frontend/src/app/telegram/components/TelegramActivityLog.tsx`

Owns:

- activity-log rendering
- empty-state display
- scroll-anchor placement

## 7. Data Flow

The intended post-decomposition flow is:

1. `page.tsx` mounts and composes `TelegramShell`.
2. `useTelegramRuntime` loads current config and owns shared log/runtime state.
3. `useTelegramConfig` consumes the loaded config, hydrates the config form, and handles config save/refresh.
4. `useTelegramBroadcasts` receives shared log/message hooks and executes broadcast/report/scan actions.
5. extracted components render current state and dispatch user actions back into the relevant hook seam.

The route should not remain the place where fetch orchestration and UI layout are interleaved.

## 8. Error Handling and Behavioral Preservation

The decomposition must preserve current user-visible behavior:

- config bootstrap failure should still avoid crashing the route
- failed config saves should still produce visible error feedback via the activity log or current message surface
- missing required signal-card fields should still block submission and log the warning
- failed report/scan dispatches should still surface readable log entries
- shared sending state should still prevent conflicting submissions where the current route already does so

Do not change backend contracts in this phase. Any normalization should happen only in extracted UI seams.

## 9. Testing and Verification Strategy

Keep existing route protection green:

- `frontend/src/app/telegram/page.test.tsx`

Add direct seam coverage:

- `frontend/src/app/telegram/hooks/useTelegramRuntime.test.tsx`
- `frontend/src/app/telegram/hooks/useTelegramConfig.test.tsx`
- `frontend/src/app/telegram/hooks/useTelegramBroadcasts.test.tsx`
- `frontend/src/app/telegram/components/TelegramShell.test.tsx`
- `frontend/src/app/telegram/components/TelegramConfigModal.test.tsx`
- `frontend/src/app/telegram/components/TelegramBroadcastPanel.test.tsx`
- `frontend/src/app/telegram/components/TelegramSignalPanel.test.tsx`
- `frontend/src/app/telegram/components/TelegramActivityLog.test.tsx`

Release gate for the Phase 9 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Risks and Controls

### Risk: shared sending state becomes coupled to every hook

Control:

- keep the shared runtime seam narrow and pass only the minimal state/actions each workflow needs

### Risk: config save behavior drifts from current modal behavior

Control:

- preserve the current modal open/save/refresh sequence and lock it with route tests plus a config seam test

### Risk: activity-log behavior becomes inconsistent across workflows

Control:

- centralize log append formatting behind the runtime seam or a pure transform helper instead of rebuilding strings in each component

### Risk: extracted sections become prop-heavy

Control:

- keep async behavior in hooks and keep section components display-oriented

## 11. Exit Criteria

Phase 9 should be considered complete when all of the following are true:

- `frontend/src/app/telegram/page.tsx` is no longer the primary home for config, broadcast, and report-dispatch workflows
- runtime, config, and broadcast seams exist and are directly tested
- major route sections and config modal are extracted into focused components
- the full frontend baseline and browser baseline are green
- a Phase 9 checkpoint summary is written and linked from the top-level roadmap

## 12. Recommended Next Move

Write the Phase 9 implementation plan next, then start with the shared runtime/config seam before moving the broadcast and report-dispatch surfaces.
