procced # Horus Analytics II Phase 5 Settings Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `docs/superpowers/reference/2026-03-18-phase-4-frontend-portfolio-checkpoint-summary.md`

Track: Frontend Runtime Stability
Phase: Phase 5 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Why this is the next Phase 5 target

After the Phase 4 frontend portfolio split, the clearest remaining oversized frontend route is `frontend/src/app/settings/page.tsx`.

Current shape:

- `frontend/src/app/settings/page.tsx` is about 1,200 lines
- it owns bootstrap loading, dirty-state logic, provider save/test flows, webhook and Telegram actions, exclusions management, market-hours editing, local data-source policy, historical backfill, and hard-reset controls
- the current route test file `frontend/src/app/settings/page.test.tsx` protects meaningful behavior, but the implementation still concentrates too many capability domains in one component

This is the next high-value structural target because it mixes normal configuration flows and destructive operational controls in one route-local implementation.

## 2. Phase 5 goal

Turn the settings page into a thin route shell that composes smaller hooks and section components, without changing:

- route path
- backend settings API contracts
- provider save/test semantics
- webhook or Telegram delivery behavior
- exclusions behavior
- market-hours behavior
- hard-reset or backfill behavior

At the end of this slice, the settings surface should have the same capability-oriented structure already introduced in the Phase 4 portfolio frontend split.

## 3. In scope

Primary source:

- `frontend/src/app/settings/page.tsx`

Primary supporting files:

- `frontend/src/app/settings/page.test.tsx`
- frontend settings-related helpers/tests touched by current route behavior

In-scope workflows:

- initial settings and exclusions load
- save settings and exclusions
- AI provider save/test flows
- Telegram/webhook action flows that currently live in the page
- exclusions add/remove/autocomplete
- market-hours and local data-source policy editing
- historical backfill start/poll flow
- hard-reset flow

## 4. Out of scope

This design does not include:

- redesigning the settings UI
- backend endpoint changes
- changing settings payload schema
- changing hard-reset or backfill semantics
- decomposing other frontend routes in the same implementation slice

## 5. Current responsibility map

The current settings page mixes six responsibility classes:

1. Runtime bootstrap, base URL resolution, and shared message/loading state
2. Save orchestration for the main settings payload and exclusions payload
3. Provider-specific save/test flows for AI settings
4. Exclusions search, add/remove, and autocomplete state
5. Destructive and operational controls such as backfill and hard reset
6. Large route-local render blocks for settings sections

This makes the file expensive to change safely because a single edit can affect config state, async workflow logic, and section rendering at once.

## 6. Recommended decomposition approach

Recommended approach: capability split in one slice.

This means extracting the settings route by workflow boundary instead of doing a helper-only or component-only split.

### 6.1 Route shell

Keep `frontend/src/app/settings/page.tsx` as the route owner, but reduce it to:

- route-level composition
- wiring of extracted hooks
- lightweight section-open and message presentation state only if still needed after extraction

### 6.2 Runtime hook

Create a focused runtime hook, for example:

- `frontend/src/app/settings/hooks/useSettingsRuntime.ts`

Responsibilities:

- bootstrap loading of settings, exclusions, and ticker universe
- base URL resolution
- shared loading and message state
- dirty-state calculation against original payloads

This hook should not own provider-test actions or destructive operations.

### 6.3 Action hook

Create a command-style action hook, for example:

- `frontend/src/app/settings/hooks/useSettingsActions.ts`

Responsibilities:

- save settings payload
- save/test AI provider credentials
- Telegram/webhook-related action flows currently tied to the route

This hook should centralize request orchestration and error/success mapping while leaving section rendering to components.

### 6.4 Exclusions hook

Create a dedicated exclusions seam, for example:

- `frontend/src/app/settings/hooks/useSettingsExclusions.ts`

Responsibilities:

- exclusion list state
- add/remove behavior
- autocomplete filtering and selection

This keeps blacklist editing separate from broader configuration save logic.

### 6.5 Operations hook

Create a dedicated operations seam, for example:

- `frontend/src/app/settings/hooks/useSettingsOperations.ts`

Responsibilities:

- historical backfill start and polling
- hard-reset token acquisition and execution
- operational status mapping

These controls should be included in Phase 5, but isolated from ordinary form-save flows because they are destructive or long-running.

### 6.6 Section components

Extract the largest render blocks into focused section components under:

- `frontend/src/app/settings/components/`

Target groups:

- page shell / save bar
- trading and risk controls
- delivery and provider controls
- local data-source policy
- exclusions section
- market-hours section
- operations section for backfill and hard reset

The section components should be mostly presentational, with handlers and state passed in from the hooks and route shell.

## 7. Alternatives considered

### Option A. Helper extraction only

Pros:

- smallest initial diff
- low wiring risk

Cons:

- leaves the route as the main orchestration hub
- does not materially reduce cognitive load

Reject for this phase.

### Option B. Capability split in one slice

Pros:

- matches the route’s actual responsibility boundaries
- isolates destructive operations from normal settings save logic
- produces real seams that are easy to test directly
- follows the successful Phase 4 portfolio pattern

Cons:

- moderate multi-file diff
- requires careful interface design between hooks and section components

Recommendation:

- choose Option B

### Option C. Component-first split with state left local

Pros:

- makes the route look smaller quickly

Cons:

- keeps async and mutation tangles alive
- likely creates prop-drilling without real structural repair

Reject for this phase.

## 8. Target file map

Proposed target shape:

- `frontend/src/app/settings/page.tsx`
- `frontend/src/app/settings/hooks/useSettingsRuntime.ts`
- `frontend/src/app/settings/hooks/useSettingsActions.ts`
- `frontend/src/app/settings/hooks/useSettingsExclusions.ts`
- `frontend/src/app/settings/hooks/useSettingsOperations.ts`
- `frontend/src/app/settings/lib/settingsForms.ts`
- `frontend/src/app/settings/components/SettingsShell.tsx`
- `frontend/src/app/settings/components/SettingsTradingSection.tsx`
- `frontend/src/app/settings/components/SettingsDeliverySection.tsx`
- `frontend/src/app/settings/components/SettingsDataSourcesSection.tsx`
- `frontend/src/app/settings/components/SettingsExclusionsSection.tsx`
- `frontend/src/app/settings/components/SettingsMarketHoursSection.tsx`
- `frontend/src/app/settings/components/SettingsOperationsSection.tsx`

The final filenames may adjust during implementation, but the boundary split should remain capability-based.

## 9. Testing strategy

Keep the current route coverage in `frontend/src/app/settings/page.test.tsx` and add direct seam tests instead of replacing route tests early.

Minimum new test anchors:

- `useSettingsRuntime.test.tsx`
  load success, partial failure, abort cleanup, dirty-state behavior
- `useSettingsActions.test.tsx`
  save success/failure, AI provider save/test, Telegram/webhook action mapping
- `useSettingsExclusions.test.tsx`
  add/remove, duplicate ignore, autocomplete filtering
- `useSettingsOperations.test.tsx`
  backfill start/poll completion/error, hard-reset token + execute flow
- selected section-component tests for the highest-risk blocks:
  delivery/provider section, exclusions section, operations section

Verification gate for the checkpoint should be:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Risks and controls

### Risk: too many hook return values and prop drilling

Control:

- keep each hook capability-bounded and return coherent contract objects instead of many loosely related primitives

### Risk: behavior drift in provider save/test or destructive controls

Control:

- preserve current route tests and add direct action/operations tests before removing route-local logic

### Risk: over-coupling exclusions to the broader settings form

Control:

- keep exclusions behavior in its own hook and section seam even if it still participates in the overall dirty-state/save story

## 11. Success criteria

This Phase 5 slice is successful if:

- `frontend/src/app/settings/page.tsx` is no longer the primary home of load/save/provider/operations orchestration
- destructive controls are isolated behind an operations seam
- provider and exclusions behavior remain compatible with the current backend contract
- direct hook/component seam tests exist alongside the current route tests
- the full frontend baseline and browser baseline remain green

## 12. Recommended next artifact

If this design looks right, the next artifact should be:

- `docs/superpowers/plans/2026-03-18-phase-5-settings-decomposition-implementation-plan.md`

That plan should turn this design into execution packages, verification gates, and a checkpoint definition for the first Phase 5 settings slice.
