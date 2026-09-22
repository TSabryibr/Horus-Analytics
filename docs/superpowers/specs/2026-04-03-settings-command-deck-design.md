# Settings Command Deck Design

Date: 2026-04-03
Status: Draft for review

## Summary

Redesign the Settings tab into an operator-first command deck that keeps all existing functionality intact while making system status, active risks, and high-impact actions immediately visible.

The page should feel like a cold, high-control operations console for EGX operators:

- operations and runtime status first
- configuration second
- destructive actions isolated
- dense but readable
- no decorative noise

## Goals

1. Make the first screenful immediately useful for an operator.
2. Surface system readiness before users scroll into forms.
3. Reorganize settings into a workflow-driven structure instead of an implementation-history structure.
4. Preserve all current actions and API behavior unless change is required for correctness.
5. Improve clarity, hierarchy, and validation feedback without breaking the current settings flows.

## Non-Goals

1. Do not redesign backend contracts unless required for correctness.
2. Do not remove existing settings functionality.
3. Do not introduce a new global settings backend surface for phase one.
4. Do not turn the page into a playful or consumer-style dashboard.

## Users And Tone

Primary users are high-intensity quantitative operators working in a volatile EGX environment.

The interface should feel:

- cold
- precise
- institutional
- tactical
- mechanically calm

It must avoid:

- purple-heavy accents
- celebratory UI
- Web3 styling
- glowing gimmicks
- generic SaaS admin-card repetition

## Information Architecture

The page should be reorganized into a command-deck structure:

1. Mission header
2. Status matrix
3. Main operator workspace
4. Danger zone

### 1. Mission Header

The top header should contain:

- page identity
- operator guidance
- unsaved-change state
- primary save action

This area should make save state obvious without forcing the user to hunt for feedback.

### 2. Status Matrix

A compact status matrix appears directly under the header and summarizes the current operational posture:

- Ollama
- Telegram
- Webhook
- Data Mounts
- Scheduler
- Backfill
- Save State

These are derived from existing frontend/runtime state wherever possible.

### 3. Main Operator Workspace

Desktop layout:

- sticky left rail
- dense right content panel

Mobile layout:

- sticky jump bar replacing the left rail
- stacked modules preserving the same order

Section order in the right content panel:

1. Operations and Runtime
2. Strategy and Risk
3. Delivery and AI
4. Data Source Policy
5. Exclusions and Market Hours

### 4. Danger Zone

Hard reset remains visually and spatially isolated at the bottom of the page.

## Layout Model

## Left Rail

The left rail is not a second content area. It is a control and attention surface only.

It contains:

- section navigation
- current active section highlight
- attention queue

The attention queue should summarize issues such as:

- missing Telegram configuration
- Ollama not tested or not reachable
- missing data mounts
- failed save/test actions
- active backfill errors

## Right Panel Modules

Each module should use the same structure:

- short mission label
- short operator-facing description
- core fields
- local action row
- local success/error surface

This keeps actions attached to the fields they affect.

## Functional Mapping

## Operations and Runtime

This section moves to the top of the main content area.

It contains:

- historical backfill controls
- live backfill progress state
- runtime guidance
- scheduler-related visibility if already available in current state

The backfill panel should read as an active console block, not as a passive form.

## Strategy and Risk

Current strategy and risk fields remain, but are grouped more tightly and visually structured to support faster scanning.

This includes:

- signal logic controls
- risk controls
- ATR controls when enabled
- auto-trading state

## Delivery and AI

Telegram, Webhook, and Ollama are grouped together because they are delivery/runtime-adjacent operations.

Rules:

- Telegram save/test stays local to Telegram
- Webhook test stays local to Webhook
- Ollama save/test stays local to Ollama
- each sub-block shows its own status/result

## Data Source Policy

Local data provider configuration remains its own module, but should expose mount readiness more clearly.

The UI should make these states easy to read:

- provider selected
- mount available
- mount missing
- path configured or missing

## Exclusions and Market Hours

These stay lower in the page because they are less urgent than runtime and delivery operations, but they should still benefit from better grouping and clearer copy.

## Status Derivation Model

Phase one should derive command-deck statuses from existing state instead of introducing a new backend endpoint.

### Derived Cards

`Save State`

- sourced from `hasChanges`, `saving`, and the global message state

`Ollama`

- sourced from presence of base URL/model plus the latest Ollama save/test result

`Telegram`

- sourced from token/chat completeness and Telegram action results

`Webhook`

- sourced from `WEBHOOK_ENABLED`, URL presence, and test result

`Data Mounts`

- sourced from mount/path availability fields already returned in settings payload

`Backfill`

- sourced from existing `useSettingsOperations` backfill state

`Scheduler`

- sourced from existing market-hours settings and any currently available runtime hints on the page

## Component Plan

Add page-level orchestration and presentation components while preserving existing domain modules.

### New Components

- `SettingsCommandDeckHeader`
- `SettingsStatusMatrix`
- `SettingsSectionRail`
- `SettingsOperatorModule`

### Existing Components To Keep And Reposition

- `SettingsSignalLogicSection`
- `SettingsRiskControlsSection`
- `SettingsDeliveryChannelsSection`
- `SettingsAiProvidersSection`
- `SettingsDataSourcesSection`
- `SettingsExclusionsSection`
- `SettingsMarketHoursSection`
- `SettingsOperationsSection`
- `SettingsShell`

### New Page-Level Derived State

Create a page-level derived status mapper that converts existing frontend/runtime state into command-deck cards and attention items.

This mapper should remain pure and testable.

## Visual Direction

The redesign should follow the project’s existing design context:

- industrial institutional terminal feel
- slate-heavy neutrals
- crisp cyan/teal for ready/supportive states
- amber/coral for warnings and blocked/destructive states
- high-contrast tags instead of relying on color alone

Visual guidance:

- strong typography hierarchy
- less generic card repetition
- tighter grouping for high-priority controls
- restrained motion only where state changes need feedback

## Interaction Rules

1. Keep primary save visible and clearly state when no changes exist.
2. Keep local module actions adjacent to the module they affect.
3. Show validation and action feedback at the module level when possible.
4. Preserve disabled/loading states for all asynchronous actions.
5. Maintain clear separation between normal operations and destructive actions.

## Testing Plan

## Frontend

Extend the current test surface to cover:

1. command-deck layout rendering
2. status matrix derived-state rendering
3. correct section order
4. sticky save/action behavior
5. section rail rendering and mobile-safe fallback
6. existing action flows still wired correctly:
   - settings save
   - Telegram save/test
   - Ollama save/test
   - webhook test
   - exclusions save
   - backfill
   - hard reset trigger wiring

Add focused tests for the new derived status mapper.

## Backend

Keep backend testing focused on preserving existing settings and action behavior:

1. settings payload remains compatible with the redesigned UI
2. current action endpoints continue to behave correctly
3. no accidental regressions in Ollama-only configuration handling

## Rollout Plan

1. Refactor shell and page layout into command-deck structure.
2. Add derived status matrix and attention queue.
3. Reposition existing domain modules into the new workflow order.
4. Improve copy, labels, and local validation surfaces.
5. Run targeted frontend and backend tests.
6. Fix regressions before any further visual polish.

## Risks

1. Reorganization may break test assumptions tied to old layout text/order.
2. Desktop density may become too heavy without disciplined spacing.
3. Mobile behavior may regress if left rail logic is not adapted carefully.
4. Module-local action feedback may become inconsistent if derived state is duplicated instead of centralized.

## Acceptance Criteria

The redesign is complete when:

1. the first screenful prioritizes operations and status
2. all current settings actions still work correctly
3. status cards reflect real frontend/runtime state
4. destructive actions remain isolated
5. targeted frontend and backend tests pass
6. the page feels more like an operator console than a generic settings form
