# Horus Analytics II Pine Core Indicator Signal Support Design

Date: 2026-04-03
Status: Approved design
Authoring mode: Brainstorming-approved design

Based on:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/page.test.tsx`

## 1. Purpose

This design defines the next Pine runtime expansion for Horus Strategy Lab.

The current Pine runtime already supports:

- `ta.sma`
- `ta.ema`
- `ta.rsi`
- `ta.macd`
- boolean conditions
- comparisons
- `ta.crossover`
- `ta.crossunder`

The next phase broadens Pine signal support to cover a first core-indicator slice:

- `ta.atr`
- `ta.highest`
- `ta.lowest`
- `ta.wma`
- `ta.vwma`

The goal is to unblock more realistic Pine signal conditions while keeping execution semantics conservative and trustworthy.

## 2. Product Outcome

The operator-facing outcome should be:

1. Paste a Pine strategy into Pine Lab.
2. Run preflight.
3. Scripts using these core indicators inside supported long-only signal conditions can reach `READY`.
4. Scripts that still depend on unsupported execution or data features remain `BLOCKED`.
5. Diagnostics become more precise by distinguishing:
   - supported signal-layer indicators
   - still-unsupported order semantics
   - still-unsupported multi-timeframe/data features

## 3. Design Goals

This phase should leave six things true:

1. Preflight and runtime stay aligned through the shared expression-plan path.
2. `ATR`, `highest`, `lowest`, `WMA`, and `VWMA` become valid signal-expression nodes.
3. These indicators are supported only for signal conditions in this phase.
4. Unsupported execution semantics remain blocked explicitly.
5. Pine Lab diagnostics become more informative without falsely claiming Pine parity.
6. The rollout is protected by backend and frontend regression coverage.

## 4. Non-Goals

This phase does not attempt to:

- support `strategy.short`
- support `strategy.exit(...)` stop/limit execution semantics
- support `request.security`
- support `ta.pivothigh`, `ta.pivotlow`, `ta.valuewhen`
- support `ta.kc`, `ta.linreg`, `ta.alma`
- silently approximate unsupported nodes
- provide full TradingView Pine compatibility

## 5. Current State

Current Pine capability detection is centralized in:

- `core/pine_lab/capabilities.py`

Current preflight parsing is centered in:

- `core/pine_lab/parser.py`

Current execution is driven by:

- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`

Today, the Pine runtime blocks all of the requested core-indicator functions even when the script only uses them inside signal conditions. That keeps execution safe, but it stops many practical Pine strategies at preflight.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Expand the expression engine with core indicator nodes

Add these indicators as first-class supported expression nodes in both parser capability checks and runtime evaluation.

Pros:

- keeps preflight and runtime aligned
- builds on the normalized expression engine already in progress
- safest long-term extension path

Cons:

- requires real evaluator work, not just preflight whitelisting

### Option 2. Regex-based whitelist expansion

Only broaden preflight acceptance through capability patterns.

Pros:

- fastest short-term

Cons:

- risks reintroducing preflight/runtime mismatch
- not trustworthy

### Option 3. Support indicators only in narrow hardcoded shapes

Allow a few canned condition forms but avoid generalized expression support.

Pros:

- safer than regex-only

Cons:

- too limited for real scripts
- creates another special-case runtime path

### Recommendation

Use Option 1.

This keeps the Pine runtime honest:

- broader signal support
- unchanged execution limits
- no fake `READY` states

## 7. Supported Syntax for This Phase

This phase should support these functions as expression nodes:

- `ta.atr(length)`
- `ta.highest(series, length)`
- `ta.lowest(series, length)`
- `ta.wma(series, length)`
- `ta.vwma(series, length)`

These should be usable inside:

- comparisons
- boolean expressions
- named conditions
- inline `if` conditions
- long-only entry/exit signal plans

Example accepted condition shapes:

```pine
atrOk = ta.atr(14) < 3
trendOk = close > ta.vwma(close, 20)
breakout = close > ta.highest(high, 20)

if atrOk and trendOk
    strategy.entry("Long", strategy.long)
```

```pine
if close < ta.lowest(low, 10)
    strategy.close("Long")
```

## 8. Supported Series Inputs

This phase should support these series inputs where relevant:

- `close`
- `open`
- `high`
- `low`
- `volume`

That enables realistic uses such as:

- `ta.highest(high, 20)`
- `ta.lowest(low, 20)`
- `ta.vwma(close, 20)`

## 9. Explicitly Blocked Usage in This Phase

Even after this expansion, the following remain blocked:

- `strategy.short`
- `strategy.exit(...)`
- `request.security(...)`
- unsupported indicator calls outside this phase

This means mixed scripts should become partially unblocked, not fully executable.

Example:

- no longer blocked by `ta.atr`
- still blocked by `strategy.exit`
- still blocked by `request.security`

## 10. Runtime Behavior

The runtime should treat these indicators as standard expression-evaluator nodes.

### 10.1 `ta.atr`

Evaluate using standard true range and rolling average over the requested length.

### 10.2 `ta.highest`

Evaluate the rolling maximum over the requested series and length.

### 10.3 `ta.lowest`

Evaluate the rolling minimum over the requested series and length.

### 10.4 `ta.wma`

Evaluate weighted moving average over the requested series and length.

### 10.5 `ta.vwma`

Evaluate volume-weighted moving average using price series and `volume`.

Each result must align to the bar index so it can be used in:

- comparisons
- boolean composition
- crossover/crossunder, where relevant

## 11. Preflight Contract

Preflight should:

1. include the new indicator names in `supported_nodes`
2. stop blocking scripts solely because they use these indicators in supported signal conditions
3. continue blocking unsupported features precisely

Example block outcomes after this phase:

- `Blocked: strategy.short is not supported in this phase.`
- `Blocked: strategy.exit stop/limit execution is not available in this phase.`
- `Blocked: request.security is not supported by the Horus Pine runtime.`
- `Blocked: ta.kc() is not supported by the Horus Pine runtime.`

## 12. Pine Lab UX Impact

Pine Lab diagnostics should become more precise.

The `Runtime Limits` section should shrink when a script only depends on newly supported indicators.

The supported-feature messaging should expand to include labels such as:

- `ATR threshold conditions`
- `Highest/lowest breakout conditions`
- `WMA/VWMA trend conditions`

The UI should still avoid implying support for:

- short-side execution
- stop/limit order semantics
- multi-timeframe data requests

## 13. Testing Strategy

Backend tests should cover:

- preflight acceptance for each new indicator
- mixed boolean expressions using the new indicators
- deterministic runtime evaluation for each indicator
- continued blocking for `strategy.short`, `strategy.exit`, and `request.security`

Frontend tests should cover:

- updated supported runtime features in Pine diagnostics
- blocked mixed scripts showing only the remaining unsupported features

## 14. Rollout Notes

This should land as a conservative signal-language expansion only.

Execution semantics remain unchanged:

- long-only
- simple entry/flat-exit model
- no stop/limit simulation

That keeps the new support useful without overstating Pine compatibility.
