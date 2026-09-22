# 2026-04-30 Session Log Annotated Report

Source log: [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md)

## Scope

This report focuses on:

- scanner runs
- signal and broadcast behavior
- Telegram activity
- dedup and suppression behavior
- whether alerts were sent versus suppressed

Routine UI requests, static asset loads, and repeated frontend polling noise are grouped unless they affect operator outcomes.

## Executive Summary

- The system started cleanly and registered the scheduled scanner and signal jobs early in the session ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L30), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L32), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L50)).
- Intraday scanning ran **47** times. Only **8** runs produced an actual intraday broadcast completion; **39** runs were fully suppressed after dedup ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L782), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L900), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5420)).
- Auto-entry was disabled, so scanner and scheduler could broadcast alerts without opening portfolio positions ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L742), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L785)).
- Mid-session, the system began generating more intraday candidates, but `SignalExecutor` started throwing repeated recommendation-processing errors: `unsupported operand type(s) for &: 'str' and 'str'`. That strongly reduced how many signals survived to broadcast ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3795), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5199), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5410)).
- Telegram command polling had intermittent timeouts, but outbound scheduler broadcasts still logged as completed. The log shows listener instability, not a clean proof of outbound delivery failure ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1524), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3981), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5299), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5963)).
- Pre-close and daily broadcasts were more operationally active than intraday, but that should not be read as trustworthy pricing. The pre-close/daily side broadcasted `4` signals at 14:10 and `10` signals at 15:00 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5440), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5936)).
- Operator follow-up after the session reported that the pre-close signal set used prior-day ticker prices rather than current-session prices. That means the pre-close path remained capable of broadcasting, but the pricing context was stale and the signals were not reliable for trading decisions.

## Chronological Annotated Timeline

### 1. Startup and scheduler initialization

- The app started normally, initialized the audit log, registered all expected jobs, and started the Telegram command listener ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L30), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L32), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L50)).
- Session mode was `LIVE`, and the sync worker immediately detected stale data and kicked off a full sync ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L42), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L48)).

Operator impact:

- No startup failure is visible.
- The system was in a valid state to scan and broadcast.

### 2. Manual scanner interaction before the first scheduled broadcast

- A manual scanner start for `intraday=false&profile_id=1` returned `200 OK` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L730)).
- Almost immediately, the scanner reported: `Auto-trade disabled; signals not auto-entered` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L742)).

Operator impact:

- This explains why alerts can exist without portfolio entries.
- It does not indicate broadcast failure.

### 3. First scheduled intraday run: real alert emitted

- The first scheduled intraday run started at 10:08, scanned 270 tickers, and found `1` signal ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L776), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L780)).
- The scheduler persisted the run as `completed`, broadcasted `1` signal after dedup, skipped auto-entry because auto-trade was disabled, and then completed broadcast with `cards=1, summary_signals=1` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L783), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L784), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L785), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L786)).

Operator impact:

- This is the cleanest proof that at least one intraday alert path worked end to end on the scheduler side.
- It does not prove position entry, because auto-entry was disabled.

### 4. Long dedup-suppressed intraday phase

- From 10:13 onward, repeated intraday runs kept finding signals, but dedup dropped all of them and broadcast was suppressed:
  - `10:13` run 2: `dedup dropped 1/1` and `nothing to broadcast` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L899), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L900), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L901)).
  - The same pattern repeats at 10:18, 10:23, 10:28, 10:33, 10:38, 10:43, 10:48, 10:53, 10:58, 11:03 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L973), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1045), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1115), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1254), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1287), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1323), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1358), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1394), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1429), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1466)).
- At 11:08, the pattern briefly broke and the system broadcasted `3` intraday signals successfully ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1500), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1502), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1504)).
- Immediately after that, dedup suppression resumed for runs 14 through 24, each finding `3` signals and then filtering all of them away ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1537), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1539), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1895)).

Operator impact:

- The scanner was alive and producing candidates, but the operator would see a lot of "signal exists in scan" behavior without repeated Telegram cards because dedup was doing its job aggressively.
- This is likely why it could feel like the system was "quiet" even while scans were active.

### 5. Data freshness warnings during intraday session

- The system raised repeated `intraday_live_ratio_low` alerts, first with `observed=0.0` very early and then again later in the session ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L752), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1912), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4229), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4687), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4941)).
- Later, a `history_fresh_ratio_low` warning also appeared ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5601)).

Operator impact:

- These warnings weaken confidence in real-time data freshness during parts of the session.
- They also help explain later stale-data handling and manual override behavior.

### 6. Mid-session shift: more candidates, but recommendation-processing errors begin

- At 12:18, intraday runs moved from `3` signals to `4` signals, and the first `SignalExecutor` recommendation errors appeared:
  - `unsupported operand type(s) for &: 'str' and 'str'` for AALR, KWIN, NINH, FNAR ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3792), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3795)).
- That run still broadcasted `2` signals after dedup ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3799), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3801)).
- From 12:23 through 12:53, the same error pattern repeated across the same names, and most runs were fully suppressed after dedup ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3837), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3841), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3971), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3975), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4173), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4177)).

Operator impact:

- This is a real anomaly, not normal dedup behavior.
- The scanner was generating recommendations, but downstream processing was breaking for many of them.
- Because the log only says `dedup dropped`, the operator-facing symptom could easily look like a dedup issue even when recommendation processing was failing underneath.

### 7. Blocked intraday run phase

- From 12:58 through 13:38, intraday runs kept returning `4` signals, but the persisted run status became `blocked` repeatedly: runs 33 through 41 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4211), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4212), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4412), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4496), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4639), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4734), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4804), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4839), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4968), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5063)).
- Every one of those blocked runs ended with dedup filtering all signals and only a dedup status update being broadcasted ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4213), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5065)).

Operator impact:

- This is the most severe suppression phase in the session.
- Even though the scanner kept seeing candidates, the session produced no actionable intraday alert stream for the operator during this block.

### 8. Manual stale override and manual daily scanner attempt

- At 13:39, a manual scanner start for `intraday=false&profile_id=1` first returned `503 Service Unavailable` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5161)).
- The operator then approved stale data bypass, and the same scanner start succeeded ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5164), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5166)).
- Immediately after, `AutoTrader` reported `Processing 0 scanner signals for portfolio: Swing Signals` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5168)).

Operator impact:

- This strongly suggests the manual daily scan did not produce a tradable signal set for the Swing Signals portfolio at that moment.
- It also shows stale-data protections were active enough to block a scan until manually overridden.

### 9. Late intraday recovery: some alerts get out again, but errors continue

- From 13:43 onward, intraday candidate counts rose again:
  - `4` signals at 13:43 and 13:48 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5194), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5235))
  - `5` signals at 13:53 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5277))
  - `8` signals at 13:58 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5318))
  - `6` signals at 14:03 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5364))
  - `9` signals at 14:08 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5405))
- Recommendation-processing errors continued on most names, but some alerts still survived dedup and were broadcast:
  - `1` signal at 13:43 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5204), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5205))
  - `1` signal at 13:53 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5288), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5289))
  - `1` signal at 13:58 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5332), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5333))
  - `1` signal at 14:03 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5376), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5377))
  - `2` signals at 14:08 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5420), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5421))

Operator impact:

- The alerting system was not dead; it was limping.
- Broadcasts resumed, but most of the candidate set was still being lost before operator delivery.

### 10. Pre-close daily run: broadcast path alive, pricing trust degraded

- The scheduled pre-close scan ran at 14:10 with `Intraday=False`, found `4` signals, and persisted as `completed` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5430), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5435)).
- `SignalExecutor` still threw four recommendation-processing errors for HELI, NHPS, NCCW, and CLHO ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5436), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5439)).
- Even so, the scheduler broadcasted all `4` signals and completed with `cards=3, summary_signals=4` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5440), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5443)).
- Operator validation after the session indicates these pre-close signals were built from yesterday's ticker prices rather than current-session prices. That observation is not directly proven by a single log line here, but it is consistent with the broader freshness warnings and stale-override behavior elsewhere in the session.

Operator impact:

- The pre-close scheduler and broadcast path stayed alive better than the intraday path.
- That does not make the pre-close output trustworthy. If the signals used prior-day prices, then this was a stale-pricing broadcast, not a healthy trading path.
- The recommendation error is broader than intraday, but it was less damaging to daily broadcast completion than to intraday completion in this session.

### 11. Daily pipeline block and end-of-day daily broadcast

- At 14:45, the daily signal pipeline logged `Daily run status=blocked run_id=49` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5588)).
- At 15:00, the daily signal scan still ran, found `10` signals, and persisted with `status=existing scan_type=DAILY run_id=49` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5931), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5935)).
- The system then broadcasted all `10` daily signals successfully and completed with `cards=3, summary_signals=10` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5936), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5939)).
- Operator validation says the pre-close signal pricing was stale. That raises concern that at least part of this late daily/pre-close output may have been operationally complete but analytically stale.

Operator impact:

- The blocked daily pipeline did not prevent the later daily signal broadcast.
- The end-of-day daily broadcast path remained operational, but operational is not the same as trustworthy if the underlying prices were stale.

### 12. Telegram activity and network health

- Telegram command listener startup is confirmed early in the session ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L50)).
- Telegram polling errors occurred at least four times with increasing retry windows:
  - 11:12 retry in `10s` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1524))
  - 12:33 retry in `20s` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3981))
  - 13:55 retry in `80s` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5299))
  - 15:14 retry in `160s` ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5963))
- Despite those polling issues, the scheduler still logged completed broadcasts and later dispatched the AI daily report to Telegram at 15:01 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5951)).

Operator impact:

- Telegram listener connectivity was unstable.
- However, the log does not show a hard outbound broadcast failure. Outbound send completion is inferred from scheduler `broadcast completed` lines, not from per-message Telegram API confirmations.

## Sent Versus Suppressed

### Clearly sent or at least broadcast-attempt completed

- Intraday:
  - 10:08 `1` signal ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L786))
  - 11:08 `3` signals ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1504))
  - 12:18 `2` signals ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3801))
  - 13:43 `1` signal ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5205))
  - 13:53 `1` signal ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5289))
  - 13:58 `1` signal ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5333))
  - 14:03 `1` signal ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5377))
  - 14:08 `2` signals ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5421))
- Pre-close / daily:
  - 14:10 `4` signals ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5443))
  - 15:00 `10` signals ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5939))
- Other Telegram dispatch:
  - AI daily report at 15:01 ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5951))

### Clearly suppressed

- Intraday runs 2 through 12 were almost entirely dedup-suppressed after the first alert burst ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L900), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1466)).
- Intraday runs 14 through 24 were fully dedup-suppressed ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1539), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1895)).
- Intraday blocked runs 33 through 41 were suppressed completely ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L4212), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5065)).
- Several later runs were partially suppressed because recommendation-processing errors likely removed candidates before the dedup stage ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5199), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5419)).

## Key Anomalies

### 1. Auto-trade disabled while alerts still broadcast

- Confirmed by both scanner and scheduler logs ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L742), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L785)).

Operator impact:

- You can receive Telegram alerts and still see no portfolio entries. That is expected in this session.

### 2. Recommendation-processing exception

- Repeated error: `unsupported operand type(s) for &: 'str' and 'str'` across dozens of recommendations ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3795), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5199), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5436)).

Operator impact:

- This is likely the biggest technical reason candidate counts and delivered alerts diverged.
- It also makes dedup logs harder to interpret, because some drops may actually be downstream recommendation failures first.

### 3. Stale-data protections and manual override

- Manual daily scan was blocked with `503`, then allowed after stale override approval ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5161), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5164)).
- The user's live-session observation that pre-close signals used yesterday's prices strengthens the interpretation that stale-data risk was not just theoretical in this session.

Operator impact:

- The system was protecting against stale conditions, but the operator had to intervene.
- That intervention may have allowed broadcasts to proceed under conditions that were still not pricing-clean enough for trustworthy pre-close output.

### 4. Telegram polling instability

- Four polling timeouts with increasing retry windows are visible ([Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L1524), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L3981), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5299), [Log.md](c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md#L5963)).

Operator impact:

- Telegram command responsiveness was unreliable.
- Outbound alert delivery may still have worked, but the log does not give clean per-message send receipts.

## Summary Metrics

- Intraday scanner runs: `47`
- Intraday runs with broadcast completion: `8`
- Intraday runs fully suppressed after dedup: `39`
- Intraday runs persisted as `blocked`: `9`
- Recommendation-processing errors logged: `72`
- Daily/pre-close scanner runs: `2`
- Daily/pre-close broadcast completions: `2`
- Telegram polling errors: `4`

## Bottom Line

- The scanner was active all session and did produce real alerts.
- The operator likely saw a mismatch between "signals found" and "alerts delivered" mainly because of:
  1. dedup suppression on repeated intraday patterns,
  2. recommendation-processing errors mid-session,
  3. a blocked/stale-data phase,
  4. auto-trade being disabled, which prevented portfolio entries even when alerts were broadcast.
- The daily/pre-close path looked more operationally alive than the intraday path, but it should not be called healthy if it was using prior-day prices.
- Revised trust read for this session:
  1. intraday was degraded by dedup, blocked periods, and a real executor bug,
  2. pre-close/daily was capable of broadcasting but may have been analytically stale,
  3. portfolio non-entry early in the day was still expected while auto-trade was disabled.

## Follow-Up Code Trace

### Pre-close stale pricing path

The most likely root cause of the stale pre-close pricing is now clear in code:

- `core/scheduling.py` runs pre-close via `scheduled_pre_close_scan()`, which calls `scheduled_scan_logic(is_intraday=False, scan_label="PRE-CLOSE")`.
- Inside `scheduled_scan_logic()`, the scanner call sets `scan_kwargs["is_pre_close"] = True` for pre-close runs, but it still leaves `is_intraday=False`.
- `core/signals/runs.py` does the same thing for persisted signal runs: for `scan_type == "PRE_CLOSE"` it adds `is_pre_close=True`, but `is_intraday` is still only `scan_type == "INTRADAY"`.
- `core/DailyScanner.py` then calls `DataManager.get_universe_data(tickers, include_live=is_intraday)`.
- Because `is_intraday=False` for pre-close, `include_live=False`, so the universe is loaded from history only.
- In `core/DataManager.py`, the live session merge of intraday bars into a running daily bar only happens when `include_live=True`.

Practical consequence:

- A pre-close run is labeled as a live pre-close event, but its price inputs still come from the history dataset unless some other path has already written a current-session daily bar into history.
- During market hours, that history bar is typically yesterday's close, which matches the observed behavior from the live session.

### Why freshness did not stop it

The freshness gate is not currently strong enough for pre-close price trust:

- `core/signals/runs.py` blocks runs only when `evaluate_data_freshness(...).overall_ok` is false.
- In `data_engine/freshness.py`, `overall_ok` is computed as:
  - `history_ok and intraday_ok` for `INTRADAY`
  - `history_ok` for everything else
- That means `PRE_CLOSE` is treated like `DAILY`, not like a live intraday-dependent scan.

Practical consequence:

- A pre-close run can pass freshness as long as history is fresh enough for the last completed market day, even if current-session intraday data is missing, stale, or never merged into the signal input prices.

### Root-cause summary

This was not just a UI misunderstanding or a Telegram issue.

- The pre-close scheduler path was operationally alive.
- The pre-close price source was structurally wired to history-only data.
- The freshness gate for `PRE_CLOSE` validated the wrong thing for a live-session pre-close decision.

In plain terms: pre-close was behaving like a daily-history scan with pre-close labeling, not like a true live-session pricing scan.
