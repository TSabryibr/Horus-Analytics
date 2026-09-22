# Pre-Close Daily Preview Signal Design

Date: 2026-06-05
Status: Approved design for user review
Authoring mode: Brainstorming-approved design

Based on:

- `core/DailyScanner.py`
- `core/scheduling.py`
- `core/replay_engine.py`
- `core/signals/runs.py`
- `core/signals/executor.py`
- `core/signals/publishing.py`
- `core/signals/routing.py`
- `core/signals/lifecycle.py`
- `routes/signals.py`
- `routes/replay.py`
- `tests/test_broadcast_reliability.py`
- `tests/test_horus_signal_intake_service.py`
- `tests/test_replay_engine.py`
- `tests/test_signal_executor.py`
- `tests/test_signals_publish_service.py`

## 1. Purpose

Pre-close signals should simulate the future daily signal before the EGX market closes.

The business goal is to give subscribers a short buying window near the end of the trading session. In the EGX market, this is especially useful because a valid daily setup may only be practically actionable during the final minutes before the official daily signal is confirmed.

Pre-close is therefore not a separate strategy. It is a daily signal preview:

`daily rules + latest live market price as today's temporary close`

## 2. Problem Summary

The current pre-close path can behave like a stricter live strategy. It uses live/pre-close-specific validation and can reject names that later appear in the real daily scan.

This creates a product mismatch:

- The user expects pre-close to predict the daily signal.
- The scanner currently can reject pre-close candidates using rules that are not part of the final daily scan.
- A stock can be blocked at pre-close and then become a valid daily signal at close.
- Subscribers lose the final buying window the pre-close feature is meant to provide.

The June 4, 2026 packaged session showed this mismatch. The pre-close run scanned successfully but rejected every candidate, while the later daily scan produced valid signals.

## 3. Goals

This design is successful when:

1. pre-close uses the same signal rules as the daily scanner
2. the only signal-input difference is that pre-close uses the latest live price as the temporary close
3. pre-close no longer applies extra pre-close-only rejection rules that daily would not apply
4. Type 1 stays signal-only with no portfolio heat or auto-entry blocking
5. Type 2 and Type 3 can use portfolio heat, capacity checks, pending entries, and auto-entry like daily
6. the final daily scan confirms or cancels prior pre-close previews
7. replay pre-close behavior matches real market pre-close behavior
8. Telegram delivery honors the existing subscriber and main-channel policies

## 4. Non-Goals

This phase does not:

- change the core daily signal strategy
- weaken the daily scanner rules
- force Type 1 into portfolio management
- make main-channel delivery ignore admin policy
- make pre-close an independent intraday strategy
- guarantee that every pre-close signal remains valid at the final daily close

## 5. Recommended Approach

Use one shared daily rule engine with two market-data modes.

`DAILY_CONFIRMED` uses the official end-of-day candle.

`PRE_CLOSE_PREVIEW` uses the same daily rule engine, but overlays today's daily candle with live near-close market data. The live price becomes the temporary daily close. Live volume can be used as the temporary daily volume when available, but the rule logic remains the daily logic.

This keeps the scanner behavior explainable:

- If the market closed now, would this become a daily signal?
- If yes, publish it as a pre-close preview.
- At the official close, confirm it or cancel it.

## 6. Scanner Behavior

Pre-close should call the daily scanner through a preview mode, not through a separate strategy route.

Required behavior:

1. Load the normal daily universe.
2. Merge latest live EGX data for the current session.
3. Replace today's candidate close with the latest live price.
4. Replace or update today's candidate volume with live session volume when available.
5. Run the same daily signal scoring and route logic.
6. Mark resulting signals with `Confirmation = PRE-CLOSE`.
7. Preserve enough metadata to compare the preview against the final daily scan.

Extra live-only rejection rules should not block pre-close unless the same rule is also part of daily signal qualification.

Freshness checks still apply. If live data is too stale for a credible preview, pre-close should not pretend the temporary close is valid.

## 7. Service Behavior

Type 1 remains signal-only.

Type 1 receives:

- pre-close signal cards
- daily confirmation follow-up cards
- caution cancellation follow-up cards when the final daily scan does not confirm the preview
- normal TP1, TP2, stop-loss, and expiry follow-ups after a published signal lifecycle starts

Type 1 does not receive:

- portfolio heat blocks
- auto-entry cards
- portfolio allocation decisions
- portfolio management instructions beyond signal lifecycle guidance

Type 2 and Type 3 are portfolio-managed services.

Type 2 and Type 3 may use:

- portfolio heat checks
- cash and capacity checks
- pending open entries
- auto-entry if enabled
- managed portfolio lifecycle behavior

Portfolio checks should not suppress Type 1 signal-only delivery. A signal can be blocked for portfolio-managed execution while still being valid for Type 1 signal delivery.

## 8. Daily Confirmation And Cancellation

The final daily scan is the confirmation authority.

When daily runs after pre-close:

1. Match final daily signals against the earlier pre-close preview by ticker, scan date, and strategy identity where available.
2. If the ticker remains valid, the daily card or follow-up confirms the pre-close preview.
3. If the ticker no longer qualifies, create a caution follow-up card:

`Pre-close signal not confirmed`

The cancellation card should make clear that:

- the pre-close idea was a preview
- the final daily scan did not confirm it
- no further action should be taken from that pre-close signal

Cancellation should close the pre-close preview lifecycle for Type 1 subscribers and any eligible main-channel destination that received the original pre-close card.

For Type 2 and Type 3, cancellation should also cancel any pending portfolio-managed entry that has not opened yet.

## 9. Publishing And Main Channel Policy

Pre-close signal publishing must use the same destination policy as other automated signals.

Subscriber delivery is based on service entitlement.

Main-channel delivery is based on the admin automated channel policy:

- `none`: no automated pre-close cards to the main channel
- `type_1`: Type 1 pre-close service content can go to the main channel
- `type_2`: Type 1 and Type 2 service content can go to the main channel
- `type_3`: Type 1, Type 2, and Type 3 service content can go to the main channel

Manual admin posts remain independent from this automated policy.

## 10. Replay Behavior

Market Replay should support the same pre-close preview behavior.

Replay pre-close should:

1. set simulated time to the configured pre-close timestamp
2. build the same temporary daily candle from replay data available at that time
3. run the same daily preview mode used by the live scheduler
4. run the final daily scan later in the replay session
5. confirm or cancel pre-close previews the same way the live app does

If replay is configured to treat a replay as a real market session, it may publish the same signal and follow-up cards as live mode, subject to explicit replay settings and Telegram safety controls.

## 11. Reliability And Audit

The system should record why each pre-close preview was published, confirmed, canceled, or blocked.

Important audit details:

- scan type: `PRE_CLOSE`
- preview source: live temporary daily close
- live price used as temporary close
- live volume used, if available
- final daily confirmation status
- service tier affected
- whether portfolio checks applied
- whether Type 1 signal-only delivery was unaffected by portfolio checks
- destination policy decision for subscribers and main channel

Duplicate protection should prevent repeated cancellation or confirmation follow-ups for the same pre-close preview and destination.

## 12. Testing Requirements

Tests should cover:

- pre-close uses the same daily rule path with live close substitution
- pre-close does not apply separate pre-close-only rejection rules
- a ticker rejected by old pre-close-only validation can pass when daily rules pass
- Type 1 pre-close delivery is not blocked by portfolio heat or auto-entry checks
- Type 2 and Type 3 pre-close delivery can use portfolio heat and auto-entry checks
- final daily scan confirms matching pre-close previews
- final daily scan sends a caution cancellation follow-up when a preview disappears
- cancellation follow-up closes the Type 1 pre-close preview lifecycle
- Type 2 and Type 3 cancellation removes pending managed entries that never opened
- main-channel pre-close delivery obeys the automated channel level
- replay pre-close produces the same preview and confirmation behavior as live scheduling

## 13. Implementation Boundary

The implementation should prefer a small shared abstraction around daily preview input preparation rather than duplicating scanner logic.

The scanner should expose one clear concept:

`daily scan rules with confirmed close` versus `daily scan rules with temporary live close`

This reduces drift between pre-close and daily behavior and keeps future strategy changes consistent across both modes.
