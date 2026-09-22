# Horus Analytics II Pine Signal Expression Runtime Implementation Plan

Date: 2026-04-01
Based on:

- `docs/superpowers/specs/2026-04-01-pine-signal-expression-runtime-design.md`
- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `frontend/src/app/optimization/page.test.tsx`
- `tests/test_pine_profile_promotion.py`

Track: Pine Signal Expression Runtime
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine signal-expression runtime design into an implementation sequence that fits the current Horus Pine Lab architecture.

The implementation must leave six things true:

1. Preflight and backtest share the same capability model and normalized execution plan.
2. Horus supports long-only Pine scripts built from RSI, MACD, SMA, EMA, boolean operators, comparisons, and crossover/crossunder.
3. Unsupported expressions, short-side execution, and unsupported order semantics are blocked explicitly before backtest.
4. The executor runs normalized expression trees rather than hardcoded moving-average pattern types.
5. Pine Lab diagnostics explain exactly why a script is `READY` or `BLOCKED`.
6. The rollout is protected by focused backend and frontend tests without depending on live Pine execution outside Horus.

## 2. In Scope

Primary backend targets:

- `core/pine_lab/parser.py`
- new `core/pine_lab/expression_nodes.py`
- new `core/pine_lab/expression_eval.py`
- new `core/pine_lab/capabilities.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- targeted tests under `tests/`

Primary frontend targets:

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `frontend/src/app/optimization/page.test.tsx`

Primary workflow capabilities to add:

- normalized Pine expression plans
- long-only RSI/MACD/custom boolean condition support
- blocked-node diagnostics for unsupported Pine expressions
- parser/runtime alignment across preflight and backtest
- Pine Lab UI messaging for long-only phase and runtime limits

Out of scope for this phase:

- `strategy.short` execution
- `strategy.exit` stop/limit semantics
- pyramiding
- partial exits
- best-effort execution of unsupported expressions
- TradingView parity for complex order behavior

## 3. Current Constraints

These existing facts shape the rollout:

1. `core/pine_lab/parser.py` currently uses direct pattern matching and returns readiness largely from entry/exit detection plus a small runtime capability check.
2. `core/pine_lab/executor.py` still assumes simple strategy kinds and evaluates only a narrow subset of signal logic.
3. `routes/strategy.py` exposes Pine preflight and backtest through one stable API contract that the frontend already consumes.
4. `frontend/src/app/optimization/components/PineLabPanel.tsx` already surfaces blocked-preflight diagnostics and disables backtest when preflight is blocked.
5. `tests/test_pine_profile_promotion.py` already covers Pine preflight/backtest profile contracts and is the best initial backend seam for new parser/runtime coverage.
6. `frontend/src/app/optimization/page.test.tsx` already exercises Pine Lab flows and should remain the main frontend integration seam.

The plan must address each of those constraints directly.

## 4. Execution Rules

These rules apply across all work packages:

1. No new Pine capability may be executable at runtime unless preflight can detect and approve it first.
2. No unsupported expression may be approximated silently.
3. No short-side behavior may slip through as partially supported in this phase.
4. No change may broaden Pine order semantics beyond the current simple long entry / flat exit model.
5. No frontend message should imply full Pine compatibility.
6. No test may depend on a live TradingView environment or external Pine runner.
7. No unrelated Pine Lab profile promotion behavior should regress while expanding the parser/runtime.

## 5. Target Module Map

The implementation should converge on this shape.

### Backend parsing seams

- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/expression_nodes.py`

### Backend runtime seams

- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`

### API seams

- `routes/strategy.py`

### Frontend seams

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`

### Test seams

- `tests/test_pine_profile_promotion.py`
- optional new parser-focused backend test file if coverage becomes too crowded
- `frontend/src/app/optimization/page.test.tsx`

The route layer should remain the API contract owner. Parsing and execution should move toward a normalized plan owned by the Pine runtime.

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PSR-P1` Expression plan scaffolding and support matrix
2. `PSR-P2` Variable resolution and boolean expression parsing
3. `PSR-P3` Indicator node support for RSI, SMA, EMA, and comparisons
4. `PSR-P4` MACD tuple parsing and crossover support
5. `PSR-P5` Executor migration to normalized expression evaluation
6. `PSR-P6` API diagnostics and Pine Lab messaging
7. `PSR-P7` Hardening, regression coverage, and closeout

This order is intentional:

- the support matrix and expression plan must exist before broader parsing can be trusted
- variable resolution must stabilize before indicators and tuple assignment can be layered in
- MACD support should land only after the generic expression model is already working
- executor migration should consume the normalized plan rather than add another parallel runtime path
- UI work should reflect already-stable readiness diagnostics, not guess at backend semantics

## 7. Work Packages

### PSR-P1. Expression Plan Scaffolding and Support Matrix

Purpose:

Define the normalized runtime model for Pine expressions and centralize capability rules.

Target files:

- new `core/pine_lab/expression_nodes.py`
- new `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- targeted backend tests

Tasks:

1. Define normalized node types for:
   - numeric literals
   - `close`
   - comparisons
   - boolean `and/or/not`
   - indicator calls
   - crossover/crossunder calls
   - named variable references
2. Define a support matrix that can answer:
   - supported now
   - blocked in this phase
   - unsupported node/function name
3. Add a normalized execution-plan shape that includes:
   - indicator definitions
   - variable definitions
   - entry expression tree
   - exit expression tree
   - execution mode
   - block reasons
4. Keep the capability model long-only by construction.

Deliverables:

- reusable expression node model
- centralized Pine capability registry
- normalized plan contract

Verification:

- focused parser/capability tests

Acceptance criteria:

- parser can return a structured plan or precise block reasons
- support boundaries live in one place, not across scattered regex checks

### PSR-P2. Variable Resolution and Boolean Expression Parsing

Purpose:

Teach the parser to resolve named and inline boolean expressions into normalized trees.

Target files:

- `core/pine_lab/parser.py`
- `core/pine_lab/expression_nodes.py`
- targeted backend tests

Tasks:

1. Parse named scalar assignments such as `r = ta.rsi(close, 14)`.
2. Parse named boolean assignments such as `longCondition = r < 30 and close > emaFast`.
3. Parse inline `if` conditions for `strategy.entry` and `strategy.close`.
4. Resolve variable references recursively into supported node types.
5. Hard-block:
   - unresolved names
   - self-referential cycles
   - unsupported function references
   - short-side entry calls

Deliverables:

- named-variable resolution
- inline-condition parsing
- blocked unresolved/ambiguous expression handling

Verification:

- tests for named conditions, inline conditions, nested booleans, and blocked unresolved references

Acceptance criteria:

- parser can reliably map supported long-only custom boolean conditions into an entry/exit plan
- unsupported or ambiguous expressions block with exact reasons

### PSR-P3. Indicator Node Support for RSI, SMA, EMA, and Comparisons

Purpose:

Expand the expression engine to evaluate core long-only signal primitives.

Target files:

- `core/pine_lab/expression_eval.py`
- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- targeted backend tests

Tasks:

1. Add evaluation support for:
   - `close`
   - `ta.rsi(close, N)`
   - `ta.sma(close, N)`
   - `ta.ema(close, N)`
2. Add comparison operator evaluation:
   - `>`, `>=`, `<`, `<=`, `==`, `!=`
3. Add boolean composition evaluation:
   - `and`, `or`, `not`
4. Preserve current SMA/EMA crossover behavior by re-expressing it through the same expression path.

Deliverables:

- evaluator support for RSI and moving-average comparison logic
- removal of direct dependence on hardcoded MA-only strategy kinds for these cases

Verification:

- deterministic runtime tests for RSI threshold logic and mixed boolean expressions

Acceptance criteria:

- scripts like `rsi < 30 and close > ema` can pass preflight and execute correctly
- existing SMA/EMA scenarios still pass

### PSR-P4. MACD Tuple Parsing and Crossover Support

Purpose:

Add support for Pine MACD tuple assignment and MACD-driven entry/exit expressions.

Target files:

- `core/pine_lab/parser.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/expression_nodes.py`
- targeted backend tests

Tasks:

1. Parse tuple assignments such as:
   - `[macdLine, signalLine, hist] = ta.macd(close, 12, 26, 9)`
2. Store tuple outputs in the normalized plan so later conditions can reference them by name.
3. Support `ta.crossover(macdLine, signalLine)` and `ta.crossunder(macdLine, signalLine)`.
4. Hard-block unsupported tuple usage patterns or unresolved tuple members.

Deliverables:

- MACD tuple parsing
- MACD crossover expression support

Verification:

- parser and runtime tests for MACD entry/exit strategies

Acceptance criteria:

- MACD long-only Pine scripts can return `READY` and backtest successfully
- malformed or partially supported tuple expressions block clearly

### PSR-P5. Executor Migration to Normalized Expression Evaluation

Purpose:

Move the Pine executor from strategy-kind branching to plan-driven expression evaluation.

Target files:

- `core/pine_lab/executor.py`
- `core/pine_lab/parser.py`
- targeted backend tests

Tasks:

1. Replace direct strategy-kind branching with execution-plan consumption.
2. Evaluate entry and exit trees bar-by-bar for each ticker.
3. Preserve the current long-only execution model:
   - enter when flat and entry becomes true
   - exit when long and exit becomes true
   - close any remaining position at the end of the test window
4. Preserve existing assumptions for commission, slippage, and final equity reporting.
5. Keep current promotion/ranking outputs compatible with the UI.

Deliverables:

- normalized-plan executor
- backward-compatible Pine backtest response payloads

Verification:

- backend contract tests for Pine backtest
- deterministic runtime tests across SMA, EMA, RSI, and MACD strategies

Acceptance criteria:

- supported scripts execute through one common runtime path
- existing result payload shape remains stable for the frontend

### PSR-P6. API Diagnostics and Pine Lab Messaging

Purpose:

Improve API and frontend messaging so the operator understands broader support boundaries without overconfidence.

Target files:

- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- frontend tests

Tasks:

1. Extend preflight responses with more precise blocked-node diagnostics where needed.
2. Surface long-only phase messaging consistently in Pine Lab.
3. Keep backtest disabled whenever preflight is `BLOCKED`.
4. Show blocked reasons such as:
   - unsupported function
   - unresolved variable
   - short-side execution attempt
   - unsupported order semantics
5. Preserve the current runtime-limits panel pattern while enriching its content.

Deliverables:

- clearer preflight payload diagnostics
- Pine Lab messaging aligned with the broader runtime

Verification:

- frontend tests for blocked diagnostics and successful `READY` flows

Acceptance criteria:

- users can tell whether failure came from unsupported signals or unsupported execution semantics
- Pine Lab no longer feels ambiguous when a script is blocked

### PSR-P7. Hardening, Regression Coverage, and Closeout

Purpose:

Stabilize the expanded Pine runtime and protect the rest of the Pine Lab workflow.

Target files:

- `tests/test_pine_profile_promotion.py`
- optional parser-focused backend test file
- `frontend/src/app/optimization/page.test.tsx`
- any touched runtime files

Tasks:

1. Add regression coverage for:
   - supported RSI strategies
   - supported MACD strategies
   - supported mixed boolean conditions
   - blocked short strategies
   - blocked unsupported functions
   - blocked unresolved variables
2. Re-run Pine profile promotion and optimization frontend suites.
3. Confirm Pine profile creation/activation still works with broader script support.
4. Confirm no frontend flicker or regression was reintroduced in Pine Lab.

Deliverables:

- green Pine backend and frontend suites
- stable broader Pine support without promotion regressions

Verification:

- `tests/test_pine_profile_promotion.py`
- affected optimization frontend tests

Acceptance criteria:

- Pine Lab flows remain green end-to-end after runtime expansion
- new Pine capability does not regress existing profile and UI behavior

## 8. Testing Strategy by Layer

### Backend parser and capability layer

Add focused coverage for:

- named and inline conditions
- nested boolean combinations
- blocked unresolved references
- blocked unsupported functions
- blocked short-side entry
- supported RSI and MACD expression plans

### Backend execution layer

Add deterministic coverage for:

- RSI threshold entry/exit
- MACD crossover entry / crossunder exit
- mixed conditions like `rsi < 30 and close > ema`
- end-of-window forced exit behavior under the existing model

### API layer

Keep route tests ensuring:

- supported scripts return `READY`
- blocked scripts return `BLOCKED` with reasons
- blocked scripts cannot backtest

### Frontend layer

Keep Pine Lab tests covering:

- blocked diagnostics
- disabled backtest state
- successful `READY` transitions for broader supported scripts

## 9. Rollout Notes

This plan should be implemented incrementally and kept releasable after each work package.

Recommended slicing for actual coding sessions:

1. ship the parser/capability scaffolding first
2. add RSI and boolean parsing/evaluation
3. add MACD tuple support
4. migrate executor and enrich UI diagnostics
5. harden with regression coverage

This sequencing reduces risk and makes it easier to spot parser/runtime drift early.

## 10. Success Criteria

This plan is successful when:

- Pine scripts using supported long-only RSI/MACD/custom boolean conditions can pass preflight and backtest correctly
- unsupported Pine expressions block explicitly and consistently before runtime
- the executor uses one normalized expression path rather than another layer of hardcoded strategy kinds
- Pine Lab communicates support boundaries clearly
- broader Pine signal support does not create misleading backtests or regress profile promotion workflows
