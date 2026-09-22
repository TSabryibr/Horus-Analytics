# Horus Analytics II Pine Signal Dependency-Graph Gating Design

Date: 2026-04-03
Status: Approved design
Authoring mode: Brainstorming-approved design

Based on:

- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- `tests/test_pine_profile_promotion.py`

## 1. Purpose

This design defines a parser/preflight improvement for Horus Pine runtime compatibility.

Today, Horus can block a Pine strategy because unsupported `ta.*` calls or unresolved references appear elsewhere in the script, even when they are only used by:

- dashboards
- tables
- plots
- alerts
- visual helper functions
- unused utility definitions

The goal of this phase is to reduce false `BLOCKED` outcomes by validating Pine signal support against the actual entry/exit dependency graph, while preserving strict whole-script blocking for true runtime-risk execution features.

## 2. Product Outcome

The operator-facing outcome should be:

1. Paste a Pine strategy into Pine Lab.
2. Run preflight.
3. Unsupported indicator calls that are outside the entry/exit dependency graph do not block the strategy.
4. Unsupported indicator calls that feed the actual signal path still block the strategy.
5. True execution-risk features still block globally.
6. Mixed real-world TradingView scripts with charts, dashboards, and strategy logic become more likely to reach an honest `READY` state.

## 3. Design Goals

This phase should leave six things true:

1. Pine execution-risk blockers remain strict and global.
2. Signal-language capability validation becomes scoped to the entry/exit dependency graph.
3. Unused definitions and visual-only logic stop poisoning Pine preflight.
4. Unresolved references only block when they are reachable from the signal path.
5. Runtime behavior stays unchanged for already-supported strategies.
6. The rollout is protected by backend regression tests.

## 4. Non-Goals

This phase does not attempt to:

- support new Pine indicators
- support new execution semantics
- support repaint behavior
- support `strategy.short`
- support `strategy.exit(...)`
- support new `request.security(...)` semantics
- fully parse comments to suppress all regex-style false positives
- rewrite or simplify user Pine code automatically

## 5. Current State

Current Pine preflight behavior is centered in:

- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`

Current execution-capability checks include two different categories:

### 5.1 Whole-script checks

These are global scans over the Pine source and are appropriate for true runtime-risk features, such as:

- `strategy.short`
- `strategy.exit(...)`
- unsupported or unsafe `request.security(...)` forms

### 5.2 Expression-plan checks

When Horus builds an expression plan, it currently validates more broadly than needed by iterating over parsed definitions beyond the minimal signal dependency chain.

That means a script can be blocked by unsupported or unresolved constructs in helper definitions that never affect:

- `entry_expression`
- `exit_expression`

This is the false-blocking behavior this design addresses.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Dependency-graph gating for indicators, whole-script gating for execution blockers

Keep whole-script blocking for true runtime-risk features, but scope indicator and unresolved-reference validation to the reachable signal dependency graph.

Pros:

- reduces false blocks safely
- preserves execution honesty
- fits the current expression-plan architecture

Cons:

- requires parser dependency traversal work
- comments/regex false positives for global blockers may still exist until a later cleanup

### Option 2. Dependency-graph gating for everything

Only validate whatever feeds entry/exit and ignore all other script content.

Pros:

- most permissive

Cons:

- too risky
- could hide real execution features that should still block globally

### Option 3. Keep whole-script gating but special-case visual/table sections

Try to ignore certain known Pine patterns heuristically.

Pros:

- smaller initial change

Cons:

- brittle
- misses many real script shapes
- harder to maintain than graph-based scoping

### Recommendation

Use Option 1.

This preserves the current safety line:

- execution-risk semantics remain global blockers
- signal-language support becomes dependency-scoped

## 7. Gating Model

Horus Pine preflight should be split into two validation layers.

### 7.1 Whole-script hard blockers

These remain global and should continue to block no matter where they appear:

- active `strategy.short`
- active `strategy.exit(...)`
- repaint/lookahead `request.security(...)`
- cross-symbol `request.security(...)`
- other true execution-risk semantics already treated as whole-script blockers

### 7.2 Signal dependency-graph blockers

These should be scoped only to the signal path:

- unsupported `ta.*` functions
- unresolved references
- capability errors in definitions reachable from entry/exit

If these appear only in:

- plots
- tables
- labels
- dashboard helpers
- unused utilities
- unused tuple expansions

then they should not block the strategy.

## 8. Dependency Tracing Contract

Dependency tracing should begin from:

- `entry_expression`
- `exit_expression`

and recursively walk through reachable nodes in `definitions`.

The traversal should support the current expression node types:

- `VARIABLE_REF`
- `CALL`
- `BOOL_OP`
- `COMPARE`
- `UNARY_OP`
- `TUPLE_ITEM`
- direct series/literal leaves

Outputs of tracing should include at least:

- reachable definition names
- reachable expressions
- reachable call nodes

The important contract is:

- only reachable definitions participate in scoped capability checks
- unreachable definitions are ignored for scoped indicator validation

## 9. Parser Behavior Changes

The parser should continue to:

- parse assignments into `definitions`
- extract inline and named `entry_expression`
- extract inline and named `exit_expression`

The parser should then:

1. run whole-script hard-block checks as today
2. build the expression plan
3. compute the reachable dependency graph from entry/exit
4. run scoped capability validation only on that reachable subgraph
5. run scoped unresolved-reference validation only on that reachable subgraph

The parser should stop validating all definitions indiscriminately for signal-language support.

## 10. Safety Rules

The following must remain true after rollout:

1. If an unsupported indicator appears inside `longCondition`, `exitCondition`, or anything they depend on, the script still blocks.
2. If an unresolved variable appears inside the signal dependency graph, the script still blocks.
3. If `strategy.short`, repaint `request.security`, or `strategy.exit(...)` appears as active code, the script still blocks globally.
4. Already-supported Pine strategies should continue to behave the same way.
5. This phase reduces false blocks; it does not add fake support.

## 11. Expected ALGOX Impact

For ALGOX-style scripts, this change should improve compatibility by ignoring unrelated appended code such as:

- backtest dashboards
- table renderers
- visual overlays
- alert decorations
- helper blocks unused by the final entry/exit conditions

However, ALGOX should still remain blocked when its actual signal path still depends on unsupported or unsafe constructs such as:

- repaint `request.security` wrappers
- unsupported filters that still feed `leTrigger` or `seTrigger`

This is intentional.

## 12. Testing Strategy

Backend regression coverage should prove four classes of behavior:

### 12.1 Accept mixed scripts with unused unsupported helpers

A strategy should reach `READY` when:

- entry/exit depend only on supported nodes
- unsupported `ta.*` calls exist elsewhere but are unreachable from the signal graph

### 12.2 Keep blocking reachable unsupported indicators

A strategy should remain `BLOCKED` when:

- unsupported `ta.*` calls appear in definitions used by entry/exit

### 12.3 Keep blocking reachable unresolved references

A strategy should remain `BLOCKED` when:

- unresolved variables appear in the reachable signal graph

### 12.4 Preserve whole-script hard blockers

A strategy should remain `BLOCKED` when active code contains:

- `strategy.short`
- `strategy.exit(...)`
- repaint/cross-symbol unsupported `request.security(...)`

## 13. Rollout Boundary

This phase is intentionally parser/preflight scoped.

It should not:

- alter the backtest execution model
- alter trade simulation semantics
- add support for any new Pine node types

If future Pine compatibility work is needed, it should stack on top of this narrower false-blocking surface.

## 14. Recommendation

Implement dependency-graph gating for indicator and unresolved-reference validation while preserving whole-script blocking for true execution-risk features.

This is the safest next step for improving real-world Pine compatibility, especially for large TradingView scripts that mix strategy logic with extensive visual or reporting code.
