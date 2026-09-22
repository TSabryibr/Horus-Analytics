# Horus Analytics II Pine Signal Expression Runtime Design

Date: 2026-04-01
Status: Proposed
Authoring mode: Brainstorming-approved design

Based on:

- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `docs/superpowers/specs/2026-03-30-pine-egx-strategy-lab-design.md`

## 1. Purpose

This design defines the next Pine runtime expansion for Horus Strategy Lab.

The current runtime supports only a narrow subset of Pine strategies based on:

- `ta.crossover(...)`
- `ta.crossunder(...)`
- `ta.sma(close, N)`
- `ta.ema(close, N)`

The next phase broadens Pine support to cover:

- `RSI`
- `MACD`
- custom boolean conditions
- general long-only signal expressions composed from supported nodes

The goal is to support much more realistic Pine signal logic without pretending to support full TradingView execution semantics.

## 2. Product Outcome

The operator-facing outcome should be:

1. Paste a Pine strategy into Pine Lab.
2. Run preflight.
3. If the script uses supported long-only signal expressions, Horus returns `READY`.
4. If the script contains unsupported functions, short-side execution, or ambiguous expressions, Horus returns `BLOCKED` with a specific reason.
5. Supported scripts can run EGX backtests under Horus execution assumptions.
6. The UI clearly distinguishes between:
   - supported signal logic
   - unsupported execution semantics

## 3. Design Goals

This package should leave six things true:

1. Preflight and execution use the same capability model.
2. Horus supports broader Pine signal logic beyond moving-average-only crossover patterns.
3. Unsupported expressions are blocked explicitly before backtest.
4. Short-side execution remains blocked clearly in this phase.
5. The runtime remains deterministic and EGX-focused.
6. Pine Lab diagnostics become more specific and more trustworthy.

## 4. Non-Goals

This phase does not attempt to:

- support full TradingView Pine semantics
- support `strategy.short` execution
- support stop/limit order modeling
- support pyramiding
- support partial exits
- support every Pine built-in function
- silently approximate unsupported nodes

## 5. Current State

The current Pine runtime is implemented in:

- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`

Today, the supported execution contract is effectively limited to:

- `ta.crossover` / `ta.crossunder`
- SMA/EMA-based price and MA crossover logic
- long entry / flat exit

This is intentionally conservative, but too narrow for many practical Pine strategies.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Expression-tree Pine runtime

Parse Pine entry/exit conditions into a small internal expression tree and evaluate those nodes bar-by-bar.

Pros:

- clear support boundaries
- aligned preflight and runtime behavior
- easy to extend incrementally
- deterministic and testable

Cons:

- more upfront structure than regex-only matching

### Option 2. Regex expansion

Keep adding regex patterns for more indicators and condition shapes.

Pros:

- fastest short-term implementation

Cons:

- brittle as soon as conditions become nested or reused
- hard to trust

### Option 3. Broad mini-interpreter

Build a more complete Pine-like evaluator now.

Pros:

- ambitious long-term story

Cons:

- too risky for this phase
- easy to create subtle mismatches

### Recommendation

Use Option 1.

This gives Horus a trustworthy middle layer:

- much broader signal parsing
- hard-blocked unsupported behavior
- no false promise of full Pine parity

## 7. Accepted Syntax for This Phase

This phase should support Pine scripts that express long-only trading logic using:

### 7.1 Supported indicators and values

- `ta.rsi(close, N)`
- `ta.macd(close, fast, slow, signal)`
- `ta.sma(close, N)`
- `ta.ema(close, N)`
- `close`
- numeric literals

### 7.2 Supported operators

- `>`
- `>=`
- `<`
- `<=`
- `==`
- `!=`
- `and`
- `or`
- `not`

### 7.3 Supported Pine helper functions

- `ta.crossover(...)`
- `ta.crossunder(...)`

### 7.4 Supported condition shapes

Named-condition blocks such as:

```pine
r = ta.rsi(close, 14)
emaFast = ta.ema(close, 20)
longCondition = r < 30 and close > emaFast
exitCondition = r > 60 or ta.crossunder(close, emaFast)

if longCondition
    strategy.entry("Long", strategy.long)
if exitCondition
    strategy.close("Long")
```

Inline conditions such as:

```pine
if ta.rsi(close, 14) < 30 and close > ta.ema(close, 20)
    strategy.entry("Long", strategy.long)
```

MACD-style named tuples such as:

```pine
[macdLine, signalLine, hist] = ta.macd(close, 12, 26, 9)
entrySignal = ta.crossover(macdLine, signalLine)
exitSignal = ta.crossunder(macdLine, signalLine)
```

### 7.5 Explicitly blocked syntax in this phase

- `strategy.entry(..., strategy.short)`
- `strategy.exit(...)` stop/limit semantics
- pyramiding controls
- partial close semantics
- unsupported functions such as `request.security`, `ta.stoch`, or any unmodeled Pine built-in
- expressions that reference unresolved or ambiguous variables

## 8. Preflight Contract

Preflight should no longer answer only:

- “did I see entry/exit calls?”

It should now answer:

- what supported nodes were detected
- what named conditions were resolved
- whether the entry and exit trees are fully mappable
- what unsupported nodes blocked execution
- whether the script attempts short-side behavior

### 8.1 Readiness states

- `READY`
  - all required entry/exit expressions are supported
- `BLOCKED`
  - any required expression node is unsupported or ambiguous

This phase does not introduce a soft partial-execution mode.

### 8.2 Example block reasons

Preflight should produce specific messages such as:

- `Blocked: strategy.short is not supported in this phase`
- `Blocked: ta.stoch() is not supported by the Horus Pine runtime`
- `Blocked: condition "entrySignal" depends on unsupported node "request.security"`
- `Blocked: strategy.exit stop/limit execution is not available in this phase`

## 9. Runtime Architecture

The Pine runtime should evolve from pattern matching into a normalized signal-expression engine.

Suggested internal seams:

- `core/pine_lab/parser.py`
  - Pine source to normalized execution plan
- `core/pine_lab/expression_nodes.py`
  - internal expression node models
- `core/pine_lab/expression_eval.py`
  - bar-by-bar evaluation of supported nodes
- `core/pine_lab/capabilities.py`
  - support matrix and block reasons

### 9.1 Normalized execution plan

The parser output should normalize Pine into a plan shaped like:

- indicator definitions
- variable definitions
- resolved entry expression tree
- resolved exit expression tree
- execution mode: `LONG_ONLY`
- blocked features, if any

### 9.2 Execution model

The executor should consume the normalized plan and evaluate it against EGX bar history.

For this phase:

- enter long on the first bar where the entry expression becomes true while flat
- exit long on the first bar where the exit expression becomes true while long
- close any open position at the final bar using the existing terminal exit logic
- keep current commission/slippage assumptions

This phase broadens the signal language, not the order model.

## 10. UI Fit in Pine Lab

The Pine Lab UI should remain structurally the same, but diagnostics should become more explicit.

The panel should surface:

- `Runtime Limits`
- `Unsupported Nodes`
- `Blocked Because`
- `Long-only phase`

The UI should make two things obvious:

1. broader signal logic is now supported
2. complex order semantics are still intentionally blocked

The `Run Pine Backtest` button should remain disabled whenever preflight is `BLOCKED`.

## 11. Testing Strategy

### 11.1 Parser tests

Add coverage for:

- RSI threshold entry/exit parsing
- MACD tuple parsing
- nested boolean expressions
- inline conditions
- named condition reuse
- blocked short-side parsing
- blocked unsupported functions
- blocked unresolved references

### 11.2 Runtime tests

Add deterministic tests for:

- RSI long entry / long exit
- MACD crossover entry / crossunder exit
- mixed boolean logic such as `rsi < 30 and close > ema`
- bar-by-bar evaluation of named and inline conditions

### 11.3 API tests

Add contract tests ensuring:

- supported long-only scripts return `READY`
- unsupported scripts return `BLOCKED` with exact reasons
- blocked scripts cannot be backtested

### 11.4 Frontend tests

Add UI coverage for:

- new unsupported-node diagnostics
- blocked short-side messaging
- successful `READY` flow for RSI and MACD scripts
- disabled backtest button for blocked expressions

## 12. Rollout Strategy

This phase should be delivered incrementally:

### Phase A

- expression tree scaffolding
- named-variable resolution
- long-only boolean expression support

### Phase B

- RSI support
- SMA/EMA support moved fully into expression engine
- parser/runtime alignment tests

### Phase C

- MACD tuple support
- richer blocked-node diagnostics
- Pine Lab UI wording improvements

This sequencing keeps the runtime honest and testable while expanding capability step by step.

## 13. Success Criteria

This design is successful when:

- Pine scripts using supported RSI/MACD/custom long-only conditions pass preflight and backtest correctly
- Pine scripts using unsupported or ambiguous logic block clearly before execution
- Pine Lab no longer gives misleading `READY` results for unsupported signal logic
- operators understand exactly why a script is accepted or blocked
- broader signal support does not imply unsupported execution semantics
