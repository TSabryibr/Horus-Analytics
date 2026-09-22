# Horus Analytics II Phase 11 Audit Decomposition Design

Date: 2026-03-18
Based on:

- `docs/superpowers/plans/2026-03-16-reliability-first-program-implementation-plan.md`
- `frontend/src/app/audit/page.tsx`
- `frontend/src/app/audit/page.test.tsx`

Track: Frontend Runtime Stability
Phase: Phase 11 candidate
Status: Draft design for review
Owner model: Single owner

## 1. Goal

This design defines the next frontend runtime decomposition wave for `frontend/src/app/audit/page.tsx`.

The objective is to turn the route into a thin composition shell while preserving:

- the current route path
- audit bootstrap fetch behavior
- day-range and strategy-filter behavior
- CSV export behavior
- current visible chart and summary rendering semantics
- real-time WebSocket audit-stream behavior
- duplicate-suppression behavior for incoming audit logs
- current loading and ledger interaction behavior

The route currently mixes four separate concerns in one file:

1. audit fetch/runtime state
2. real-time WebSocket stream lifecycle
3. chart and summary derivation
4. ledger rendering and interaction state

Phase 11 should separate those concerns into explicit seams without changing what the page does.

## 2. Why This Route Is Next

`frontend/src/app/audit/page.tsx` is the strongest remaining untreated frontend runtime target after the completed portfolio, settings, live, simulation, optimization, Telegram, and Oracle decompositions.

It is the right next boundary because:

- it is currently the largest untreated frontend route at about 447 lines
- it owns both bootstrap fetch and real-time WebSocket behavior
- it mixes export logic with chart shaping and expandable ledger behavior
- it coordinates multiple independent UI regions from one component
- it already has route-level test anchors that make structural extraction safer

The file currently combines:

- initial audit fetch
- day-range query switching
- strategy filtering
- expanded-row state
- CSV export generation
- chart-series shaping
- WebSocket setup and cleanup
- duplicate suppression for streamed logs
- large chart, summary, and ledger render blocks

That makes the route harder to change safely because one edit can affect fetch behavior, stream merges, export semantics, and dashboard rendering at once.

## 3. Scope

Primary source file:

- `frontend/src/app/audit/page.tsx`

Primary extraction target areas:

- `frontend/src/app/audit/hooks/`
- `frontend/src/app/audit/components/`
- `frontend/src/app/audit/lib/`

In scope:

- bootstrap fetch and loading behavior
- day-range and strategy-filter behavior
- expanded-row state
- CSV export behavior
- chart and comparison-data shaping
- WebSocket audit-stream lifecycle
- duplicate-suppression and bounded log insertion behavior
- route shell extraction
- charts/summary/ledger panel extraction

Out of scope:

- visual redesign of the audit route
- backend endpoint changes
- WebSocket payload contract changes
- changes to audit business rules or metric definitions
- changing visible wording except where required for structural extraction

## 4. Target Boundary

After decomposition, `frontend/src/app/audit/page.tsx` should keep only:

- top-level composition
- lightweight wiring between extracted hooks and panels

Everything else should move behind explicit seams.

### Route responsibilities that should leave the page

- bootstrap fetch logic
- day-range and filter orchestration
- CSV export generation
- comparison-data shaping
- WebSocket setup and cleanup
- duplicate suppression for incoming audit logs
- large chart render block
- large summary/sidebar block
- large ledger render block

### Route responsibilities that may remain

- top-level section ordering
- composition of extracted panels
- small glue code if needed for composition

## 5. Recommended Approach

Three approaches were considered:

### Option 1. Full capability split in one phase

Move runtime fetch/export behavior and WebSocket stream behavior behind separate hooks and extract the three major UI regions into focused panels.

Pros:

- strongest structural result
- addresses both fetch-side and stream-side complexity together
- matches the successful Phase 4 through Phase 10 frontend decomposition pattern

Cons:

- larger first diff than a fetch-only extraction

### Option 2. Fetch/filter/export first, stream later

Extract the bootstrap/runtime side first and leave the WebSocket stream route-local.

Pros:

- lower first diff

Cons:

- leaves the highest-risk async behavior in the route
- weakens the checkpoint value

### Option 3. Panel-components first

Move JSX into components but leave runtime and stream logic in the route.

Pros:

- makes the file look smaller quickly

Cons:

- weak boundary
- poor long-term testability
- leaves the route responsible for the real complexity

### Recommended option

Option 1.

The audit page is not large because of one giant visual tree alone. It is large because it combines a dashboard, an export path, and a real-time log stream. The correct boundary has to pull both runtime and stream behavior out of the route in the same wave.

## 6. Target Module Map

### `frontend/src/app/audit/page.tsx`

Owns:

- top-level composition
- wiring extracted hooks to extracted panels

### `frontend/src/app/audit/hooks/useAuditRuntime.ts`

Owns:

- bootstrap fetch
- loading state
- day-range state
- strategy-filter state
- expanded-row state
- CSV export behavior
- comparison/chart data shaping

### `frontend/src/app/audit/hooks/useAuditStream.ts`

Owns:

- WebSocket setup
- payload parsing
- duplicate suppression
- bounded live-log insertion
- cleanup on unmount

### `frontend/src/app/audit/lib/auditTransforms.ts`

Owns:

- pure comparison-data shaping helpers
- CSV row shaping helpers
- badge/status helpers
- pure log-merge helpers if they reduce hook complexity cleanly

### `frontend/src/app/audit/components/AuditShell.tsx`

Owns:

- page frame
- title and header chrome
- day-range controls
- refresh and export buttons
- loading-state shell

### `frontend/src/app/audit/components/AuditChartsPanel.tsx`

Owns:

- performance comparison chart
- strategy-health radar surface

### `frontend/src/app/audit/components/AuditSummaryPanel.tsx`

Owns:

- KPI/sidebar summary surface
- strategy-card area

### `frontend/src/app/audit/components/AuditLedgerPanel.tsx`

Owns:

- filter controls
- audit log table
- expandable row rendering
- ledger badges and outcome display

## 7. Data Flow

The intended runtime flow is:

1. `page.tsx` reads fetch/export state through `useAuditRuntime`
2. `useAuditRuntime` exposes current audit data plus derived comparison/ledger state
3. `page.tsx` wires `setAudit` or equivalent update hooks into `useAuditStream`
4. `useAuditStream` merges streamed audit rows without changing route ownership
5. `page.tsx` passes display-ready props into `AuditShell`, `AuditChartsPanel`, `AuditSummaryPanel`, and `AuditLedgerPanel`
6. panels render without owning async orchestration

This keeps behavior in hooks, pure shaping in `auditTransforms`, and rendering in components.

## 8. Error Handling And Contract Preservation

The decomposition must preserve the current visible behavior for:

- initial loading state
- fetch failures that currently log without crashing the route
- day-range re-fetches
- strategy filtering
- CSV export initiation
- real-time WebSocket updates
- duplicate streamed logs
- no-data or partial-data cases in chart and ledger surfaces

Key rule:

- no backend API contract changes
- no WebSocket payload contract changes
- no semantic changes to export behavior
- no changes to visible route outcomes beyond structural extraction

## 9. Testing Strategy

Existing route protection to keep green:

- `frontend/src/app/audit/page.test.tsx`

New direct seam tests:

- `frontend/src/app/audit/hooks/useAuditRuntime.test.tsx`
  - fetch success/failure
  - day-range re-fetch
  - export behavior
  - derived comparison data
- `frontend/src/app/audit/hooks/useAuditStream.test.tsx`
  - socket message parsing
  - duplicate suppression
  - bounded insertion
  - cleanup behavior
- `frontend/src/app/audit/components/AuditShell.test.tsx`
- `frontend/src/app/audit/components/AuditChartsPanel.test.tsx`
- `frontend/src/app/audit/components/AuditSummaryPanel.test.tsx`
- `frontend/src/app/audit/components/AuditLedgerPanel.test.tsx`

Release gate for the Phase 11 checkpoint:

- `npm --prefix frontend run lint`
- `npm --prefix frontend run test -- --runInBand`
- `npm --prefix frontend run build`
- `npm --prefix frontend run test:e2e`

## 10. Execution Sequencing

Recommended implementation order:

1. extract `auditTransforms.ts`
2. extract `useAuditRuntime.ts`
3. extract `useAuditStream.ts`
4. extract `AuditShell.tsx`
5. extract `AuditChartsPanel.tsx`
6. extract `AuditSummaryPanel.tsx`
7. extract `AuditLedgerPanel.tsx`
8. slim `page.tsx` to composition only
9. run broader frontend verification and write checkpoint docs

This ordering stabilizes pure helpers and runtime/stream contracts before moving the large UI blocks.

## 11. Exit Criteria

Phase 11 should be considered complete when:

- `frontend/src/app/audit/page.tsx` is primarily composition and lightweight wiring
- bootstrap runtime behavior lives in `useAuditRuntime`
- WebSocket lifecycle lives in `useAuditStream`
- chart, summary, and ledger rendering live in extracted panels
- existing route tests remain green
- direct seam tests cover the extracted hooks and core panels
- the frontend verification gate passes

## 12. Risks And Mitigations

### Risk: stream-merge behavior drifts during extraction

Mitigation:

- isolate duplicate suppression and merge rules early
- lock the stream seam with direct tests

### Risk: export or filter semantics drift

Mitigation:

- keep route tests green while adding direct runtime coverage
- move export shaping into pure helpers first if needed

### Risk: over-engineering a medium-sized page

Mitigation:

- keep only the minimum seam set
- avoid adding extra abstraction beyond runtime, stream, transforms, shell, and the three main panels
