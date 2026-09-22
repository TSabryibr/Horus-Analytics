# 2026-04-30 Market Session Log Analysis

Source: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md)

## Scope

This report focuses on execution and portfolio behavior only:

- scanner starts and run statuses
- signal persistence and dedup
- SignalExecutor behavior
- AutoTrader behavior
- blocked states and stale-data gates
- reasons portfolio entries did not open

Repetitive UI polling, static asset requests, and routine scheduler heartbeat lines are grouped and omitted unless they affect execution.

## Chronological Summary

### 1. Startup and live-session mode were normal

- Session jobs were registered for `LIVE` and `ANALYSIS` at startup ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:26)).
- Effective session mode started as `LIVE` because the market was open ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:44)).
- Telegram listener also started normally ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:50)).

Interpretation: the app booted into the expected live operating mode. No startup failure explains the empty portfolios.

### 2. First scanner runs produced signals, but auto-entry was explicitly disabled

- Manual scanner start succeeded at 10:03 for profile `1` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:730)).
- Immediately after, the scanner logged: `Auto-trade disabled; signals not auto-entered` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:742)).
- The scheduled intraday run at 10:08 found `1` signal and persisted it as `completed` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:778), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:780), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:783)).
- That same run then logged: `Auto-trade disabled; skipping auto-entry` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:785)).
- Another intraday run at 11:08 broadcast `3` signals, but again skipped auto-entry for the same reason ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1502), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1503)).

Interpretation: early in the session, alerts could be broadcast, but portfolio entry was intentionally shut off.

### 3. Many scheduled intraday runs never reached broadcast because dedup removed everything

Repeated pattern across the morning:

- Signals were found and persisted as `completed` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:899), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:972), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1044), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1114)).
- Dedup then dropped `1/1`, `3/3`, or `4/4` signals, leaving nothing to broadcast ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:900), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:901), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1539), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1540), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4213), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4214)).

Interpretation: even before the later execution bug, the effective tradable/broadcastable signal flow was being heavily reduced by deduplication.

### 4. Around midday, execution behavior changed: auto-entry disable messages stopped, and SignalExecutor errors started

- Settings were edited around 12:07 via `POST /api/v1/settings` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1959), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1963)).
- After that point, the earlier `Auto-trade disabled; skipping auto-entry` message no longer appears in the scheduled signal path.
- The first clear execution failure appears at 12:18, when a completed intraday run (`run_id=25`) is followed by `SignalExecutor` errors on every recommendation ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3793), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3795), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3796), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3797), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3798)).

Interpretation: the session appears to move from "entry intentionally disabled" into "entry attempted but broken in execution logic."

### 5. The main runtime failure repeated for the rest of the live session

The same exception repeats across intraday and pre-close runs:

- `unsupported operand type(s) for &: 'str' and 'str'`

Examples:

- Intraday run 42 at 13:43 ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5197), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5199), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5200), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5201), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5202))
- Intraday run 43 at 13:48 ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5238), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5240), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5241), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5242), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5243))
- Intraday run 45 at 13:58 ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5321), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5323), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5330))
- Intraday run 47 at 14:08 ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5408), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5410), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5418))
- Pre-close run 48 at 14:10 ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5435), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5436), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5439))

Interpretation: once this bug appears, recommendations are still persisted and some survive dedup and get broadcast, but execution is not reliable enough to open positions.

### 6. Stale-data protection also blocked manual scanner starts later in the session

- Intraday feed quality alerts were raised multiple times: `intraday_live_ratio_low` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:752), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1912), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4229), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4687), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4941)).
- Sync worker repeatedly reported `state=STALE` with `intraday_ratio=0.0` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4264), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4307), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4341), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4461), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4532), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4768), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4948)).
- Manual scanner starts then failed with `503 Service Unavailable` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4996), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5161)).
- After the user approved a stale-data override, scanner start succeeded ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5164), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5165), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5166)).

Interpretation: stale-data gating explains some rejected manual starts, but it does not explain the empty portfolios after override. The later execution bug still does.

### 7. AutoTrader did run once for a manual scanner path, but there were zero signals to process

- After the stale override and successful manual scanner start, `AutoTrader` logged: `Processing 0 scanner signals for portfolio: Swing Signals` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5168)).

Interpretation: at least one manual daily scanner request reached AutoTrader, but there were no scanner signals available for portfolio entry on that path.

### 8. No successful position-open evidence appears anywhere in the session

Across the log:

- there are no `Auto-Entered` lines
- there are no successful `position opened` or similar execution confirmations
- trade monitor jobs keep running successfully, but without any indication of newly opened live signal positions ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:760), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:792), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5178))

Interpretation: the empty portfolios match the log. This was not just a UI refresh problem.

### 9. The session ended by transitioning out of LIVE mode

- At 14:30, session mode transitioned from `LIVE` to `ANALYSIS` and stopped the live feed manager ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5552), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5555), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5556)).
- The 14:45 daily signal pipeline then logged `run status=blocked` for run `49` ([docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5588)).

Interpretation: after 14:30, the system was no longer in the normal live-entry regime anyway.

## Root Causes

### Root cause 1: auto-entry was disabled for part of the session

Evidence:

- [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:742)
- [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:785)
- [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1503)

Effect:

- signals could be persisted and broadcast
- portfolios remained empty by design

### Root cause 2: once auto-entry appears to have been enabled, SignalExecutor crashed on recommendations

Evidence:

- first clear onset: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3795)
- repeated through intraday and pre-close runs: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5199), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5240), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5323), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5436)

Effect:

- recommendations were not cleanly executable
- no successful entry confirmations appear afterward

Likely technical bug:

- a boolean/filter expression is using `&` on string operands instead of boolean series or booleans
- this is almost certainly inside the recommendation-processing path used by `SignalExecutor`

### Root cause 3: dedup removed most candidate signals even when scans completed

Evidence:

- all candidates removed: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:901), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:1540), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3842)
- partial drop examples: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:3800), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5203), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5420)

Effect:

- many runs never had anything left to broadcast or potentially route
- this reduced usable signal flow before entry logic even got a chance

### Root cause 4: stale-data safeguards blocked some manual scanner starts

Evidence:

- stale feed warnings: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4264), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4948)
- blocked starts: [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:4996), [docs/Log.md](/abs/path/c:/Users/TSabr/Horus/Horus-Analytics-II/docs/Log.md:5161)

Effect:

- manual scanner attempts were sometimes rejected before execution

## Likely Fixes

1. Fix the `SignalExecutor` recommendation-processing bug first.
   - Search the execution/recommendation path for a boolean condition using `&` on string fields.
   - This is the main production blocker once auto-entry is turned on.

2. Verify the exact `AUTO_TRADE_ENABLED` transition in settings logs or code instrumentation.
   - The log shows behavior changed midday, but not the value payload itself.
   - Add explicit setting-change audit logs for future sessions.

3. Instrument entry success/failure at the portfolio-write boundary.
   - Add logs for:
     - recommendation accepted
     - entry blocked by gate
     - position created with portfolio id
   - Right now the log proves failure, but not the exact last successful handoff boundary after `SignalExecutor`.

4. Review dedup rules.
   - Dedup is dropping entire runs too often to be operationally transparent.
   - At minimum, log dedup reason categories per dropped signal.

5. Improve stale-data diagnostics on scanner start.
   - The stale override worked, but the operator had to infer why `503` was happening.
   - Return/log the exact freshness gate reason in the scanner-start response path.

## Bottom Line

The portfolios stayed empty for two different reasons during the same session:

1. early session: auto-trade was disabled, so broadcast happened without entry
2. later session: execution reached `SignalExecutor`, but recommendation processing repeatedly crashed with `unsupported operand type(s) for &: 'str' and 'str'`

Secondary contributors:

- aggressive dedup removed many candidate runs
- stale-data protection blocked some manual starts until override

The highest-value next action is to debug and fix the `SignalExecutor` string-`&` failure before relying on live portfolio entry again.
