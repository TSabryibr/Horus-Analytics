# Pre-Close Daily Preview Signal Implementation Plan

Date: 2026-06-05
Based on:

- `docs/superpowers/specs/2026-06-05-pre-close-daily-preview-design.md`
- `docs/superpowers/plans/2026-06-03-signal-followups-channel-policy-implementation-plan.md`
- `docs/superpowers/plans/2026-04-22-telegram-lifecycle-follow-up-automation-implementation-plan.md`
- `core/DailyScanner.py`
- `core/scheduling.py`
- `core/replay_engine.py`
- `core/signals/runs.py`
- `core/signals/executor.py`
- `core/signals/publishing.py`
- `core/signals/lifecycle.py`
- `routes/signals.py`
- `routes/replay.py`
- `tests/test_scanner_and_data.py`
- `tests/test_broadcast_reliability.py`
- `tests/test_horus_signal_intake_service.py`
- `tests/test_replay_engine.py`
- `tests/test_signal_executor.py`
- `tests/test_signals_publish_service.py`

Track: Pre-Close Daily Preview Signals
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved pre-close behavior as a daily signal preview:

`daily scanner rules + latest live price as the temporary daily close`

The rollout should:

1. remove strategy drift between pre-close and daily signal qualification
2. keep Type 1 signal-only and independent from portfolio execution checks
3. keep Type 2 and Type 3 eligible for portfolio heat, capacity, pending entries, and auto-entry
4. create confirmation or caution cancellation follow-ups after the final daily scan
5. make replay pre-close behavior match live scheduling behavior

## 2. In Scope

Primary implementation targets:

- scanner preview data preparation for daily rules using live close substitution
- scheduler changes to record pre-close previews and reconcile them at daily close
- lifecycle/follow-up queue support for `PRE_CLOSE_NOT_CONFIRMED`
- service routing separation so Type 1 delivery is not blocked by portfolio checks
- replay parity for pre-close preview and daily confirmation/cancellation
- focused backend tests for scanner, scheduler, publishing, execution, and replay behavior

Out of scope:

- changing the daily signal strategy itself
- weakening final daily signal qualification
- adding new subscriber tiers
- bypassing automated main-channel policy
- changing manual Telegram send behavior
- rebuilding the packaged EXE in this implementation slice

## 3. Execution Rules

1. Treat the approved design as the source of truth.
2. Do not create a second pre-close strategy path.
3. Keep daily rules shared between confirmed daily and pre-close preview scans.
4. The only pre-close scanner input difference should be the temporary close/volume overlay from live data.
5. Keep freshness checks before preview generation.
6. Do not let portfolio heat or auto-entry blocks suppress Type 1 signal-only delivery.
7. Let portfolio-managed tiers use existing daily execution and capacity rules.
8. Make final daily scan the authority for confirming or canceling pre-close previews.
9. Use durable lifecycle/follow-up records; do not send cancellation messages as one-off direct Telegram calls.
10. Preserve existing uncommitted fixes and do not revert unrelated workspace changes.

## 4. Work Package Sequence

Execute in this order:

1. `PCDP-P1` Scanner daily-preview mode
2. `PCDP-P2` Scheduler publish split and preview reconciliation
3. `PCDP-P3` Lifecycle and follow-up cancellation support
4. `PCDP-P4` Portfolio-managed execution boundary
5. `PCDP-P5` Replay parity
6. `PCDP-P6` Verification and regression lock

This order makes the scanner behavior correct first, then wires delivery and lifecycle behavior around it.

## 5. Work Packages

### PCDP-P1. Scanner Daily-Preview Mode

Purpose:

Make pre-close call the daily scanner rules with a live temporary close instead of using separate pre-close-only signal validation.

Target files:

- `core/DailyScanner.py`
- `core/signals/runs.py`
- `routes/signals.py`
- `tests/test_scanner_and_data.py`
- `tests/test_signals_run_service.py`
- `tests/test_signals_p0.py`

Tasks:

1. Add an explicit preview mode helper or parameter that means daily rules with live close substitution.
2. Preserve `is_pre_close=True` as an external scan type marker, but prevent it from enabling separate signal rejection rules.
3. Keep live universe merging and freshness requirements for pre-close.
4. Ensure final signal cards still carry `Confirmation = PRE-CLOSE`.
5. Add scanner tests proving pre-close uses daily rule qualification after live close overlay.
6. Add a regression test where a candidate rejected by old pre-close-only validation can pass when daily rules pass.

Deliverables:

- one shared daily signal qualification path
- pre-close signals marked as previews
- tests locking that pre-close no longer drifts from daily rules

Verification:

- `python -m pytest tests/test_scanner_and_data.py tests/test_signals_run_service.py tests/test_signals_p0.py -q`

Acceptance criteria:

- pre-close and daily use the same route/scoring rules for signal qualification
- pre-close still requires credible live data
- pre-close output remains identifiable as `PRE-CLOSE`

### PCDP-P2. Scheduler Publish Split And Preview Reconciliation

Purpose:

Make scheduled pre-close publishing record preview state and make scheduled daily reconcile that state.

Target files:

- `core/scheduling.py`
- `core/signals/publishing.py`
- `tests/test_horus_signal_intake_service.py`
- `tests/test_broadcast_reliability.py`
- `tests/test_signals_publish_service.py`

Tasks:

1. Record which tickers were published as pre-close previews for each market date and destination scope.
2. On final daily scan, match daily recommendations against prior pre-close previews.
3. Mark matched previews as confirmed.
4. Identify unmatched previews for cancellation follow-up creation.
5. Preserve existing dispatch toggles and automated main-channel policy.
6. Ensure subscriber-only delivery can still happen when the main channel level is `none`.

Deliverables:

- preview-to-daily reconciliation
- confirmed and not-confirmed preview outcomes
- scheduler tests for pre-close followed by daily confirmation and cancellation

Verification:

- `python -m pytest tests/test_horus_signal_intake_service.py tests/test_broadcast_reliability.py tests/test_signals_publish_service.py -q`

Acceptance criteria:

- daily scan confirms prior previews that still qualify
- daily scan cancels prior previews that disappear
- main-channel policy and subscriber delivery remain independent

### PCDP-P3. Lifecycle And Follow-Up Cancellation Support

Purpose:

Create a durable caution follow-up for pre-close previews that the final daily scan does not confirm.

Target files:

- `core/signals/lifecycle.py`
- `core/signals/followups.py`
- `core/TelegramBot_Alerts.py`
- `core/horus/telegram.py`
- `routes/signals.py`
- `tests/test_signal_followup_queue.py`
- `tests/test_telegram_followups.py`
- `tests/test_published_signal_lifecycle.py`

Tasks:

1. Add or reuse a lifecycle/follow-up trigger for `PRE_CLOSE_NOT_CONFIRMED`.
2. Generate client-facing caution copy: `Pre-close signal not confirmed`.
3. Close the preview lifecycle for signal-only destinations that received the original pre-close card.
4. Deduplicate cancellation follow-ups by lifecycle, trigger state, and destination.
5. Keep lifecycle truth independent from Telegram delivery success.

Deliverables:

- durable cancellation follow-up jobs
- Telegram copy for caution cancellation
- duplicate protection around pre-close cancellation

Verification:

- `python -m pytest tests/test_signal_followup_queue.py tests/test_telegram_followups.py tests/test_published_signal_lifecycle.py -q`

Acceptance criteria:

- unmatched pre-close previews create one cancellation follow-up per eligible destination
- the follow-up clearly says the final daily scan did not confirm the preview
- failed delivery does not reopen or mutate lifecycle truth

### PCDP-P4. Portfolio-Managed Execution Boundary

Purpose:

Keep Type 1 signal-only while allowing Type 2 and Type 3 pre-close recommendations to use daily portfolio execution behavior.

Target files:

- `core/signals/executor.py`
- `core/signals/publishing.py`
- `core/scheduling.py`
- `tests/test_signal_executor.py`
- `tests/test_signals_publish_service.py`
- `tests/test_broadcast_reliability.py`

Tasks:

1. Ensure Type 1 publish paths use `include_portfolios=False`.
2. Ensure portfolio-managed pre-close paths can invoke capacity, heat, pending-entry, and auto-entry logic when enabled.
3. Cancel pending managed entries when final daily does not confirm a pre-close preview.
4. Add tests where portfolio heat blocks managed execution but Type 1 still receives the pre-close signal.
5. Add tests where managed pending entries are canceled on daily non-confirmation.

Deliverables:

- service-tier execution separation
- cancellation behavior for managed pending entries
- regression tests for Type 1 independence from portfolio checks

Verification:

- `python -m pytest tests/test_signal_executor.py tests/test_signals_publish_service.py tests/test_broadcast_reliability.py -q`

Acceptance criteria:

- Type 1 pre-close cards are not blocked by portfolio heat or auto-entry
- Type 2 and Type 3 can still be governed by portfolio risk controls
- non-confirmed previews do not leave stale pending managed entries

### PCDP-P5. Replay Parity

Purpose:

Make Market Replay run the same pre-close preview and daily confirmation/cancellation flow as the live scheduler.

Target files:

- `core/replay_engine.py`
- `routes/replay.py`
- `frontend/src/app/simulation/hooks/useReplay.ts`
- `frontend/src/app/simulation/components/ReplayPanel.tsx`
- `tests/test_replay_engine.py`
- `frontend/src/app/simulation/hooks/useReplay.test.tsx`
- `frontend/src/app/simulation/components/ReplayPanel.test.tsx`

Tasks:

1. Ensure replay pre-close builds the same temporary daily candle as live pre-close.
2. Ensure replay final daily scan reconciles pre-close previews.
3. Support the existing option to treat replay as a real market session without bypassing Telegram safety controls.
4. Update replay tests to compare live and replay pre-close behavior.
5. Update frontend labels only if existing replay controls need clearer wording.

Deliverables:

- replay/live parity for pre-close previews
- replay confirmation and cancellation behavior
- tests for replay session behavior

Verification:

- `python -m pytest tests/test_replay_engine.py -q`
- `npm test --prefix frontend -- ReplayPanel useReplay`

Acceptance criteria:

- replay pre-close can produce the same preview result as live mode for the same simulated data
- replay daily can confirm or cancel prior replay pre-close previews
- real-session replay publishing remains explicitly controlled

### PCDP-P6. Verification And Regression Lock

Purpose:

Run focused backend and frontend checks that cover the full pre-close preview rollout and nearby previously fixed areas.

Target files:

- tests touched by `PCDP-P1` through `PCDP-P5`
- changed frontend replay tests if needed

Tasks:

1. Run scanner and signal-run tests.
2. Run scheduler and broadcast reliability tests.
3. Run publishing, lifecycle, follow-up, and executor tests.
4. Run replay tests.
5. Run frontend replay tests if frontend files changed.
6. Run `git diff --check` against touched files.

Deliverables:

- passing focused regression suite
- clean whitespace diff check
- clear final implementation summary

Verification:

- `python -m pytest tests/test_scanner_and_data.py tests/test_signals_run_service.py tests/test_signals_p0.py -q`
- `python -m pytest tests/test_horus_signal_intake_service.py tests/test_broadcast_reliability.py tests/test_signals_publish_service.py -q`
- `python -m pytest tests/test_signal_executor.py tests/test_signal_followup_queue.py tests/test_telegram_followups.py tests/test_published_signal_lifecycle.py -q`
- `python -m pytest tests/test_replay_engine.py -q`
- `npm test --prefix frontend -- ReplayPanel useReplay`
- `git diff --check`

Acceptance criteria:

- all focused tests pass or any remaining failures are unrelated and documented
- no pre-close-only strategy filter can reject a signal that daily rules would accept
- Type 1, Type 2, Type 3, main-channel, and replay behavior match the approved spec

## 6. Risks And Controls

Risk: Scanner drift remains hidden behind `is_pre_close`.

Control: Add tests around route selection and candidate validation that compare pre-close preview with daily qualification.

Risk: Type 1 delivery is accidentally coupled to portfolio execution.

Control: Keep publish destination flags explicit and add heat-block regression tests.

Risk: Duplicate cancellation follow-ups are sent after repeated daily jobs or retries.

Control: Deduplicate by lifecycle, trigger state, and destination.

Risk: Replay publishes live Telegram messages unexpectedly.

Control: Preserve explicit replay-as-real-session and Telegram safety settings.

Risk: Existing uncommitted fixes are overwritten.

Control: Read each touched file before editing and apply narrow patches only.

## 7. Recommended Execution Notes

Start with `PCDP-P1`. The scanner path is the root behavior. If it remains wrong, scheduler, follow-up, and replay changes can still produce the wrong product outcome.

Use narrow tests first, then broaden to the focused suite after the scheduler and lifecycle packages are wired.

## 8. Recommended Next Move After This Plan

Begin implementation with `PCDP-P1` by changing `core/DailyScanner.py` so pre-close preview keeps live data substitution but shares final daily signal qualification rules.
