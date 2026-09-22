# Horus Matrix Execution Design

Date: 2026-04-08
Based on:

- `core/scheduling.py`
- `core/AutoTrader.py`
- `routes/signals.py`
- `core/signals/workspace.py`
- `core/portfolio/identity.py`
- `database.py`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`

Track: Premium Signal Operations
Status: Draft design for review
Owner model: Single owner

## 1. Why this is the next target

The app already has strong pieces of the premium-signal workflow, but they are split across separate systems:

- signal generation and recommendation persistence
- Telegram publish and retry
- simulation auto-entry
- position monitoring and auto-close
- portfolio-scoped reporting

What is missing is a single portfolio-centered execution lane that turns approved signals into a managed subscriber product.

The requested `Horus` matrix is that missing lane. It should:

- open internal ledger positions from intraday and pre-close signals during market hours
- open daily signals at the next working-session open only
- manage the lifecycle of one position per ticker
- update stops and targets when newer stronger signals arrive
- auto-close on stop, target, or trailing logic
- send Telegram lifecycle notifications for open, update, and close
- record the full lifecycle inside the app's default premium workspace

## 2. Goal

Introduce `Horus` as a dedicated `USER` matrix and internal execution workspace that becomes the default operator portfolio while keeping:

- `Daily Simulation` alive as a separate `SYSTEM` portfolio
- `Intraday Simulation` alive as a separate `SYSTEM` portfolio
- the existing signal generation pipeline intact

The result should be a clean premium execution path that is portfolio-scoped, Telegram-aware, idempotent under retries, and isolated from other matrices in reporting and pre-close behavior.

## 3. Decisions captured

The approved business rules for this design are:

- `Horus` is added as a new `USER` portfolio and becomes the default workspace
- `Daily Simulation` and `Intraday Simulation` remain separate and continue to exist
- all `Horus` trading is inside the app's internal portfolio ledger for now
- new `Horus` trades reuse the app's current simulation sizing rules
- only one open `Horus` position per ticker is allowed
- a later signal for an already-open `Horus` ticker updates the existing trade instead of opening another one
- a stronger later signal may tighten risk and improve exits, and may also loosen the stop or widen the target if the newer setup is stronger
- intraday and pre-close signals execute during market hours when generated
- daily signals execute only at the next working-session open if the trade was not already activated earlier by intraday or pre-close
- if the next session opens within `1.5%` of the daily signal entry, `Horus` may execute at the adjusted open and notify Telegram that entry changed because of the gap
- if the next session opens more than `1.5%` away from the daily signal entry, `Horus` skips the trade and notifies Telegram that the setup was invalidated by the gap

## 4. In scope

- seed and prefer the `Horus` user portfolio
- add `Horus` to the default workspace-selection flow
- create a dedicated `Horus` execution lifecycle tied to signal runs and recommendations
- open, update, monitor, and close `Horus` internal ledger positions
- send Telegram lifecycle messages for `Horus`
- keep `Horus` reporting and workspace analytics portfolio-scoped
- keep matrix behavior isolated so AI report, recommendations, and pre-close execution context can differ by portfolio

## 5. Out of scope

This design does not include:

- live broker execution or Trading 212 order placement
- changing the existing simulation portfolios into the `Horus` portfolio
- redesigning the portfolio UI
- changing how core market signals are generated
- subscriber billing, entitlement packaging, or commercial plan management
- strategy-parameter recalibration beyond reusing the current sizing logic and adjusting stop/target/trailing behavior for `Horus`

## 6. Recommended approach

Recommended approach: build a dedicated `Horus` execution lane on top of the existing signals pipeline.

This keeps the current market-signal and recommendation path as the source of truth for what the market is offering, while adding a separate portfolio-scoped engine for what `Horus` actually did with those signals.

### 6.1 Alternatives considered

### Option A. Extend the existing `AutoTrader` path directly

Pros:

- smaller initial diff
- reuses current scanner-to-trade flow quickly

Cons:

- keeps older simulation behavior coupled to the new premium workflow
- mixes legacy system-portfolio assumptions with matrix-specific business rules
- makes Telegram trade lifecycle harder to isolate cleanly

Reject for this project.

### Option B. Dedicated `Horus` execution lane behind existing signal runs

Pros:

- fits the desired premium-signal lifecycle directly
- preserves `Daily Simulation` and `Intraday Simulation`
- gives `Horus` clear portfolio ownership and reporting isolation
- maps well onto the existing signal run, recommendation, delivery, and outcome seams

Cons:

- requires a new execution state seam
- adds a moderate backend diff across scheduling, execution, and reporting links

Recommendation:

- choose Option B

### Option C. Full matrix execution framework for all matrices

Pros:

- most future-proof
- generalizes execution behavior for later premium products

Cons:

- too large for the first premium execution release
- introduces abstraction pressure before `Horus` proves the model

Reject for this phase.

## 7. Current seam map

The current codebase already has the right anchors for this feature:

- `core/scheduling.py` owns intraday, pre-close, daily signal, and trade-monitor scheduling
- `routes/signals.py` already persists signal runs, recommendations, deliveries, outcomes, and workspace metrics
- `core/AutoTrader.py` already contains internal entry sizing and stop/target/trailing monitoring logic, but it is scoped to current simulation behavior and `SYSTEM` portfolios
- `database.py` already models `Portfolio`, `Position`, `Trade`, `SignalRun`, `SignalRecommendation`, `SignalDelivery`, and `SignalOutcome`
- `core/portfolio/identity.py` and `frontend/src/app/context/PortfolioContext.tsx` already define the app's default portfolio resolution behavior
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx` already shows `active_matrix` from `USER` portfolios
- `routes/ai_report.py`, `routes/analysis_reports.py`, and `core/signals/workspace.py` already support portfolio-scoped reporting and cache partitioning

The missing capability is a first-class execution lifecycle that links one user matrix to one signal-driven trade-management model.

## 8. Architecture

### 8.1 Portfolio identity

Seed a new `USER` portfolio named `Horus` in `database.py`.

Default resolution changes:

- backend default portfolio resolution should prefer `Horus`, then `My Portfolio`, then the first `USER` portfolio
- frontend auto-selection should prefer `Horus`, then `My Portfolio`, then the first `USER` portfolio
- `active_matrix` continues to display all `USER` portfolios, including `Horus`

This makes `Horus` the default operator workspace without removing manual switching between matrices.

### 8.2 Dedicated execution state

Add a new execution-state table dedicated to matrix-driven signal lifecycle, for example `HorusExecution` or `MatrixExecution`.

Required responsibilities:

- link `portfolio`, `signal run`, and `signal recommendation`
- track one managed lifecycle per ticker per portfolio
- distinguish `PENDING_OPEN`, `OPEN`, `UPDATED`, `CLOSED`, `SKIPPED`, and `FAILED`
- record trigger source such as `INTRADAY`, `PRE_CLOSE`, `DAILY_NEXT_OPEN`
- store planned entry, actual entry, gap-adjusted entry status, active stop, active target, active trailing state, close reason, and linked `Position` or `Trade` IDs
- store Telegram delivery markers for open, update, close, and skip notifications
- preserve the reason a trade was skipped or updated

This table is the durable workflow ledger for premium execution. `Position` and `Trade` remain the financial ledger.

### 8.3 Execution services

Introduce focused services rather than growing `core/AutoTrader.py` into a second mixed-responsibility engine.

Recommended seams:

- `core/horus/identity.py`
  `Horus` portfolio lookup and default resolution helpers
- `core/horus/executor.py`
  open-or-update decisions for new recommendations
- `core/horus/monitor.py`
  stop, target, and trailing close evaluation for open Horus positions
- `core/horus/telegram.py`
  message builders and idempotent delivery helpers for `OPEN`, `UPDATE`, `CLOSE`, and `SKIP`
- `core/horus/reconciliation.py`
  rebuild links between `Horus` execution state and `Position` or `Trade` rows when needed

Final filenames may vary, but the responsibilities should remain separated this way.

## 9. Execution flow

### 9.1 Intraday and pre-close

When a completed recommendation set is available during market hours:

- the `Horus` executor evaluates the target recommendations for the `Horus` portfolio
- if no open `Horus` trade exists for a ticker, it opens immediately in the internal ledger using the current simulation sizing rules
- if an open `Horus` trade already exists for that ticker, the recommendation becomes a trade-update event instead of a second entry
- the open or update is recorded in the dedicated execution table
- the actual Telegram entry or update message is sent only after the ledger write succeeds

### 9.2 Daily after-hours

Daily signals generated after market hours must not be treated as same-session fills.

Instead:

- daily recommendations create `PENDING_OPEN` execution records when no earlier Horus activation exists for that ticker
- the execution record stores the original signaled entry, stop, target, and the next eligible market session

This prevents look-ahead bias and keeps the premium signal trail faithful to the actual market timing.

### 9.3 Next-session open gap handling

At the next working-session open:

- if the tradable opening price is at or within `1.5%` of the original daily signal entry, the system opens the trade
- if the actual execution price differs from the original signal entry, the execution record is marked as gap-adjusted
- the Telegram open message explicitly notes that the market opened with a gap and the entry changed
- if the opening price is more than `1.5%` away from the original signal entry, the system skips the trade, records the skip reason, and sends a Telegram invalidation notice

### 9.4 Single-position rule

`Horus` manages at most one open position per ticker.

If a later signal arrives for an already-open `Horus` ticker:

- do not create another position
- evaluate whether the new recommendation is stronger
- if stronger, update the active stop, target, and trailing behavior on the existing trade
- persist both prior values and new values in execution history

This keeps premium-signal state coherent and avoids conflicting Telegram instructions for the same ticker.

## 10. Monitoring and close logic

`Horus` should have a dedicated monitoring path, scheduled alongside the existing trade monitor but scoped only to the `Horus` portfolio and the new execution table.

Close evaluation order should be deterministic:

1. stop-loss breach
2. target hit
3. trailing-stop breach after trailing is armed

Rules:

- a stop-loss hit closes the internal position immediately and records a `STOP_LOSS` close reason
- a target hit closes the internal position and records a `TARGET` close reason
- a trailing breach closes the internal position and records a `TRAILING_STOP` close reason
- newer stronger signals may explicitly loosen stop or widen target when they update an already-open trade
- automatic trailing logic itself must still ratchet only in the safer direction once armed

This distinction matters: strategy upgrades may loosen risk, but automatic trailing should not.

## 11. Telegram lifecycle

Telegram is downstream from the ledger and must be idempotent.

Lifecycle message types:

- `OPEN`
  sent after a Horus trade is actually opened, using the actual execution price
- `UPDATE`
  sent when a later stronger signal materially changes stop, target, or trailing behavior on an already-open trade
- `CLOSE`
  sent when the position is auto-closed, including close reason, exit price, and realized P&L
- `SKIP`
  sent when a pending next-open daily trade is invalidated by the opening gap or another fail-closed execution condition

Delivery rules:

- no Telegram lifecycle message may be sent before the corresponding ledger event is persisted
- retries and overlapping scheduler ticks must not duplicate messages
- the execution table should store delivery markers or message IDs so the system can prove whether an `OPEN`, `UPDATE`, `CLOSE`, or `SKIP` notice was already sent

## 12. Matrix isolation

Matrix isolation must be enforced in the data model and execution policy, not only in the UI.

The following state remains portfolio-scoped:

- open positions
- closed trades
- `Horus` execution records
- signal deliveries
- audit events
- workspace signal performance
- AI report and analysis report context

This means two matrices may observe the same raw market recommendation set while still behaving differently because:

- one matrix may already hold the ticker
- one matrix may have skipped a gap-invalidated daily setup
- one matrix may have accepted a stronger later update
- one matrix may have already closed the trade

That separation is the intended product behavior.

## 13. Reporting behavior

Portfolio-scoped reporting already exists in important places and should be reused rather than replaced.

Key behavior:

- `routes/ai_report.py` should use `Horus` as the default workspace context when no portfolio is specified
- `routes/analysis_reports.py` should continue using explicit or resolved `portfolio_id` so `Horus` reports remain separate
- `core/signals/workspace.py` continues computing workspace signal performance per `USER` portfolio
- signal recommendations and outcome views should be able to display the `Horus` context clearly when requested from the workspace

No second reporting framework is needed. The main change is ensuring Horus execution events feed the existing portfolio-scoped reporting surfaces consistently.

## 14. Failure handling

`Horus` should fail closed whenever execution confidence is not high enough.

Fail-closed scenarios include:

- stale or missing intraday market data
- missing or invalid next-open price
- invalid stop or target math
- blocked signal guard state
- duplicate execution attempts for an already-resolved lifecycle event
- any ledger-write failure before Telegram delivery

In those cases:

- do not open or mutate the internal ledger position
- mark the execution lifecycle as `FAILED` or `SKIPPED`
- write an audit event
- emit a Telegram `SKIP` or operator-visible error only when appropriate and idempotent

This is especially important for after-hours daily signals, where pretending to fill on unavailable prices would produce false premium performance.

## 15. Data and migration plan

### 15.1 Seed and default behavior

Update startup initialization to:

- create `Horus` as a `USER` portfolio if it does not exist
- keep `My Portfolio` as a valid `USER` portfolio
- keep `Daily Simulation` and `Intraday Simulation` as separate `SYSTEM` portfolios

### 15.2 New schema

Add the dedicated execution table and any supporting indexes needed for:

- `portfolio + ticker + open-status` lookup
- `portfolio + run + recommendation` lookup
- idempotent Telegram lifecycle lookup
- pending-next-open scheduling lookup

### 15.3 Compatibility

No destructive migration is required for existing portfolios, positions, trades, runs, deliveries, or outcomes.

Existing simulation behavior should continue to function while `Horus` is introduced as an additive path.

## 16. Target file map

Expected primary touch points:

- `database.py`
- `core/portfolio/identity.py`
- `frontend/src/app/context/PortfolioContext.tsx`
- `frontend/src/app/components/sidebar/SidebarPortfolioSwitcher.tsx`
- `core/scheduling.py`
- `routes/signals.py`
- `core/signals/workspace.py`
- `core/AutoTrader.py`

Expected new backend seams:

- `core/horus/identity.py`
- `core/horus/executor.py`
- `core/horus/monitor.py`
- `core/horus/telegram.py`
- `core/horus/reconciliation.py`

Expected tests:

- backend execution and scheduler tests under `tests/`
- portfolio identity and reporting tests under `tests/`
- frontend portfolio-selection tests under `frontend/src/app/context/` and `frontend/src/app/components/`

## 17. Testing strategy

Minimum validation coverage:

- `Horus` is seeded automatically and becomes the default resolved `USER` portfolio
- frontend workspace auto-selection prefers `Horus`
- intraday recommendations open immediately for `Horus`
- pre-close recommendations open immediately for `Horus`
- daily recommendations create `PENDING_OPEN` lifecycles instead of same-session trades
- next-open execution adjusts entry when the gap is within `1.5%`
- next-open execution skips when the gap is greater than `1.5%`
- repeated recommendations for the same open ticker update the existing `Horus` trade rather than opening another one
- stronger later signals can both tighten and loosen stop/target values when explicitly accepted as a trade update
- stop-loss, target, and trailing-stop closes produce the correct `Trade` rows and exactly one `CLOSE` Telegram lifecycle message
- Telegram retries or scheduler overlaps do not duplicate `OPEN`, `UPDATE`, `CLOSE`, or `SKIP` messages
- AI report and workspace metrics remain portfolio-scoped and distinguish `Horus` from other matrices

## 18. Risks to manage during implementation

- mixing older scanner auto-entry code with the new Horus lifecycle could create double execution unless boundaries are explicit
- inferring Horus state only from `Position` and `Trade` would make retries and Telegram idempotency fragile
- treating after-hours daily recommendations as immediate fills would introduce look-ahead bias
- allowing automatic trailing logic to loosen stops would create inconsistent risk behavior
- failing to scope reporting and recommendations by portfolio would make matrices look separate in the UI while sharing execution state underneath

## 19. Recommendation

Implement `Horus` as an additive, portfolio-scoped premium execution lane built on the existing signal pipeline, with a dedicated execution lifecycle table and scheduler-aware trade monitor.

This delivers the requested subscriber workflow without breaking current simulations, and it keeps the premium matrix model clear enough to extend later if additional matrices need their own execution policies.
