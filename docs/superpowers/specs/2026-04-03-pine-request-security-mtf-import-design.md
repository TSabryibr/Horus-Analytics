# Horus Analytics II Pine `request.security` MTF Import Design

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

This design defines the next Pine runtime expansion for Horus Strategy Lab after the recent indicator-language support improvements.

The current Pine runtime already supports:

- `ta.sma`
- `ta.ema`
- `ta.rsi`
- `ta.macd`
- `ta.atr`
- `ta.highest`
- `ta.lowest`
- `ta.wma`
- `ta.vwma`
- `ta.linreg`
- `ta.alma`
- boolean conditions
- comparisons
- `ta.crossover`
- `ta.crossunder`

The next phase broadens Pine signal support to cover a safe first slice of `request.security(...)` usage as deterministic higher-timeframe series import.

The goal is to unblock realistic multi-timeframe Pine signal conditions while keeping execution semantics conservative and trustworthy.

## 2. Product Outcome

The operator-facing outcome should be:

1. Paste a Pine strategy into Pine Lab.
2. Run preflight.
3. Scripts using safe, same-symbol higher-timeframe `request.security(...)` imports inside supported long-only signal conditions can reach `READY`.
4. Scripts that still depend on repaint behavior, cross-symbol imports, or unsupported execution features remain `BLOCKED`.
5. Diagnostics become more precise by distinguishing:
   - supported deterministic MTF imports
   - still-unsupported repaint/lookahead semantics
   - still-unsupported alternate symbol imports
   - still-unsupported order semantics

## 3. Design Goals

This phase should leave seven things true:

1. Preflight and runtime stay aligned through the shared expression-plan path.
2. `request.security(...)` becomes valid only in safe, deterministic same-symbol higher-timeframe forms.
3. Imported higher-timeframe series can participate in supported long-only signal expressions.
4. Unsupported repaint/lookahead behavior remains blocked explicitly.
5. Unsupported cross-symbol imports remain blocked explicitly.
6. Pine Lab diagnostics become more informative without falsely claiming TradingView parity.
7. The rollout is protected by backend and frontend regression coverage.

## 4. Non-Goals

This phase does not attempt to:

- support cross-symbol `request.security(...)`
- support repaint semantics
- support `lookahead_on`
- support arbitrary `barmerge` emulation
- support custom wrapper functions that obscure security semantics
- support `strategy.short`
- support `strategy.exit(...)` stop/limit execution semantics
- provide full TradingView `request.security` compatibility

## 5. Current State

Current Pine capability detection is centralized in:

- `core/pine_lab/capabilities.py`

Current preflight parsing is centered in:

- `core/pine_lab/parser.py`

Current execution is driven by:

- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`

Today, the Pine runtime blocks all `request.security(...)` usage, even when the script is simply importing same-symbol higher-timeframe data into a signal condition. That keeps execution safe, but it blocks many practical MTF Pine strategies.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Deterministic same-symbol MTF import

Treat `request.security(...)` as a validated expression node that imports higher-timeframe values for the current symbol only.

Pros:

- keeps preflight and runtime aligned
- unblocks the most practical MTF strategy shape
- preserves deterministic behavior

Cons:

- requires real parser and evaluator work
- intentionally narrower than TradingView

### Option 2. Best-effort `request.security` emulation

Try to support a broad range of `request.security` shapes and parameters.

Pros:

- broader coverage on paper

Cons:

- high mismatch risk
- hard to trust
- likely to create subtle repaint errors

### Option 3. Keep blanket block until full MTF semantics exist

Continue blocking all `request.security(...)` usage.

Pros:

- safest short-term

Cons:

- stops many practical Pine strategies
- prevents honest incremental progress

### Recommendation

Use Option 1.

This keeps the Pine runtime honest:

- broader signal support
- unchanged execution limits
- no fake TradingView parity

## 7. Supported Syntax for This Phase

This phase should support these forms:

- `request.security(syminfo.tickerid, "60", close)`
- `request.security(syminfo.tickerid, "1D", ta.ema(close, 20))`
- direct assignment into a variable used later in a signal condition

Accepted constraints:

- same symbol only
- higher timeframe only
- literal/string timeframe only
- imported expression built from already-supported Pine nodes
- use inside supported long-only signal conditions

Example accepted shapes:

```pine
htfClose = request.security(syminfo.tickerid, "1D", close)
htfTrend = request.security(syminfo.tickerid, "1D", ta.ema(close, 20))
longCondition = close > htfTrend and close > htfClose
exitCondition = close < htfTrend

if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
```

## 8. Explicitly Blocked Usage in This Phase

Even after this expansion, the following remain blocked:

- `request.security("EGX:COMI", "1D", close)` when it is not the current symbol context
- `request.security(..., ..., ..., barmerge.gaps_off, barmerge.lookahead_on)`
- wrappers that imply repaint behavior
- unsupported inner expressions
- lower-timeframe import semantics
- non-literal timeframe expressions we cannot map deterministically
- unsupported execution features outside the MTF import itself

This means mixed scripts should become partially unblocked, not fully executable.

## 9. Runtime Behavior

The runtime should treat supported `request.security(...)` calls as deterministic higher-timeframe series imports.

### 9.1 Validation

Parser validation should confirm:

- symbol resolves to current symbol only
- timeframe is literal and higher than the base series timeframe
- imported expression is composed only of already-supported nodes
- repaint/lookahead semantics are not requested

### 9.2 Evaluation

Runtime evaluation should:

1. evaluate the inner supported expression on resampled higher-timeframe bars
2. align the higher-timeframe result to the lower-timeframe bar index
3. forward-fill the higher-timeframe value onto the base index for signal evaluation

### 9.3 Output Contract

Imported series must align to the bar index so they can be used in:

- comparisons
- boolean composition
- supported long-only signal plans

## 10. Preflight Contract

Preflight should:

1. stop showing blanket `request.security` blocking for safe phase-1 forms
2. continue blocking unsafe uses precisely
3. include request-security-derived support in `supported_nodes` or diagnostics in a consistent way

Example block outcomes after this phase:

- `Blocked: request.security only supports same-symbol imports in this phase.`
- `Blocked: request.security lookahead/repaint behavior is not supported in this phase.`
- `Blocked: request.security inner expression depends on unsupported Pine nodes.`

## 11. Pine Lab UX Impact

Pine Lab diagnostics should become more precise.

The `Runtime Limits` section should shrink when a script only depends on supported same-symbol higher-timeframe imports.

The supported-feature messaging should expand to include a label such as:

- `Same-symbol higher-timeframe security imports`

The UI should still avoid implying support for:

- repaint behavior
- cross-symbol import semantics
- short-side execution
- stop/limit order semantics

## 12. Testing Strategy

Backend tests should cover:

- preflight acceptance for supported same-symbol literal-timeframe imports
- continued blocking for alternate symbol imports
- continued blocking for unsupported repaint/lookahead variants
- runtime evaluation of imported higher-timeframe `close`
- runtime evaluation of imported higher-timeframe EMA or other already-supported inner expressions

Frontend tests should cover:

- updated supported runtime features in Pine diagnostics
- blocked mixed scripts showing precise `request.security` reasons

## 13. Rollout Notes

This should land as a conservative MTF signal-input expansion only.

Execution semantics remain unchanged:

- long-only
- simple entry/flat-exit model
- no stop/limit simulation

That keeps the new support useful without overstating `request.security` compatibility.
