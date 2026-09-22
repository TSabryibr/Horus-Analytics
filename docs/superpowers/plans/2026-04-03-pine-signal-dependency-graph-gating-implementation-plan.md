# Horus Analytics II Pine Signal Dependency-Graph Gating Implementation Plan

Date: 2026-04-03
Based on:

- `docs/superpowers/specs/2026-04-03-pine-signal-dependency-graph-gating-design.md`
- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/expression_eval.py`
- `core/pine_lab/executor.py`
- `tests/test_pine_profile_promotion.py`

Track: Pine Signal Dependency-Graph Gating
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine signal dependency-graph gating design into a safe implementation sequence for Horus Pine preflight.

The implementation must leave six things true:

1. Whole-script hard blockers remain strict and global.
2. Unsupported indicator calls outside the reachable entry/exit dependency graph no longer block Pine preflight.
3. Unsupported indicator calls inside the reachable entry/exit dependency graph still block Pine preflight.
4. Unresolved references only block when they are reachable from entry/exit.
5. Already-supported Pine backtests behave the same way they do today.
6. The rollout is protected by focused backend regression coverage.

## 2. In Scope

Primary backend targets:

- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py`
- targeted backend tests under `tests/`

Primary workflow capability to add:

- dependency-scoped validation for signal-language support

Out of scope for this phase:

- new Pine indicators
- new execution semantics
- repaint normalization
- `strategy.short` support
- `strategy.exit(...)` support
- new `request.security(...)` capability
- frontend UI changes
- full comment-aware Pine lexical parsing

## 3. Current Constraints

These existing facts shape the rollout:

1. Whole-script hard blockers already live in `core/pine_lab/capabilities.py` and should stay there.
2. Expression-plan parsing and capability walking already live in `core/pine_lab/parser.py`, making it the right seam for dependency scoping.
3. The current parser builds `definitions`, `entry_expression`, and `exit_expression`, which is enough to compute a reachable signal graph.
4. The current parser still validates more broadly than needed by walking definitions outside the minimal signal dependency chain.
5. `tests/test_pine_profile_promotion.py` is already the strongest integration seam for Pine preflight behavior.
6. Runtime/executor behavior should not be changed in this phase unless tests prove that a parser-only refactor accidentally regressed an existing supported path.

## 4. Execution Rules

These rules apply across all work packages:

1. No whole-script hard blocker may be softened into dependency-scoped behavior.
2. No unsupported `ta.*` call may be ignored if it is reachable from entry/exit.
3. No unresolved variable may be ignored if it is reachable from entry/exit.
4. No parser change may alter the execution meaning of already-supported Pine strategies.
5. No new Pine feature may be implied by this rollout; this is a false-blocking reduction only.

## 5. Target Module Map

The implementation should converge on this shape.

### Whole-script blocker seam

- `core/pine_lab/capabilities.py`

### Dependency-graph parser seam

- `core/pine_lab/parser.py`

### Regression seam

- `tests/test_pine_profile_promotion.py`

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PDG-P1` Red-first dependency-gating regressions
2. `PDG-P2` Reachable signal-graph collector
3. `PDG-P3` Scoped capability and unresolved-reference validation
4. `PDG-P4` Regression hardening and closeout

This order is intentional:

- the regression tests must define the new contract first
- graph collection must exist before scoped validation can be trusted
- broader regression hardening should happen only after the new gating path is stable

## 7. Work Packages

### PDG-P1. Red-First Dependency-Gating Regressions

Purpose:

Define the new preflight contract in tests before changing parser behavior.

Target files:

- `tests/test_pine_profile_promotion.py`

Tasks:

1. Add a failing test where:
   - entry/exit use only supported nodes
   - an unsupported `ta.*` helper exists elsewhere but is unreachable
   - expected result is `READY`
2. Add a failing test where:
   - unsupported `ta.*` appears inside a reachable definition
   - expected result is `BLOCKED`
3. Add a failing test where:
   - an unresolved variable exists only in an unreachable helper
   - expected result is `READY`
4. Keep or extend a guard test where:
   - `strategy.short`, `strategy.exit(...)`, or unsafe `request.security(...)` still blocks globally

Deliverables:

- explicit regression coverage for dependency-scoped validation

Verification:

- focused Pine preflight tests fail for the right reasons before implementation

Acceptance criteria:

- the new tests capture the false-blocking problem and the preserved safety boundary clearly

### PDG-P2. Reachable Signal-Graph Collector

Purpose:

Compute the minimal reachable expression subgraph from `entry_expression` and `exit_expression`.

Target files:

- `core/pine_lab/parser.py`

Tasks:

1. Add a recursive collector that walks from:
   - `entry_expression`
   - `exit_expression`
2. Support the current node types:
   - `VARIABLE_REF`
   - `CALL`
   - `BOOL_OP`
   - `COMPARE`
   - `UNARY_OP`
   - `TUPLE_ITEM`
3. Record at least:
   - reachable definition names
   - reachable expressions or nodes needed for later validation
4. Keep traversal cycle-safe using the same defensive pattern already used elsewhere for variable resolution

Deliverables:

- reusable signal dependency-graph collector

Verification:

- focused parser tests or integration assertions through preflight

Acceptance criteria:

- the parser can distinguish reachable definitions from unused definitions reliably

### PDG-P3. Scoped Capability and Unresolved-Reference Validation

Purpose:

Apply scoped validation only to the reachable signal graph while preserving whole-script hard blockers.

Target files:

- `core/pine_lab/parser.py`
- `core/pine_lab/capabilities.py` if any boundary cleanup is needed, but only minimally

Tasks:

1. Leave whole-script hard-block checks unchanged.
2. Change unresolved-reference validation so it only walks reachable expressions.
3. Change capability validation so it only walks reachable expressions/definitions.
4. Stop validating all parsed definitions indiscriminately for signal-language support.
5. Preserve existing plan-building behavior for already-supported strategies.

Deliverables:

- dependency-scoped signal validation
- preserved whole-script hard blockers

Verification:

- `PDG-P1` regressions now pass

Acceptance criteria:

- unreachable unsupported helpers no longer block
- reachable unsupported helpers still block
- whole-script hard blockers still block globally

### PDG-P4. Regression Hardening and Closeout

Purpose:

Prove that the new parser gating reduces false blocks without regressing current Pine support.

Target files:

- `tests/test_pine_profile_promotion.py`
- any nearby Pine regression files if needed

Tasks:

1. Re-run the focused dependency-gating tests.
2. Re-run broader Pine preflight/backtest regressions.
3. Confirm request-security slices and supported indicator slices remain green.
4. Confirm no frontend work is needed for this phase because the operator-facing surface is still standard Pine preflight output.

Deliverables:

- stable backend regression sweep

Verification:

- focused Pine preflight tests
- broader Pine regression suite

Acceptance criteria:

- the new gating behavior is covered and stable
- current supported Pine slices remain green

## 8. Suggested Test Matrix

At minimum, the rollout should cover:

1. `unreachable_unsupported_helper_does_not_block`
2. `reachable_unsupported_helper_blocks`
3. `unreachable_unresolved_reference_does_not_block`
4. `reachable_unresolved_reference_blocks`
5. `global_strategy_short_still_blocks`
6. `global_strategy_exit_still_blocks`
7. `unsafe_request_security_still_blocks`
8. `existing_supported_expression_plan_still_ready`

## 9. Rollout Notes

This slice should be implemented as a parser/preflight refinement, not as a runtime feature expansion.

If ALGOX-style scripts remain blocked after this work, that outcome is still useful because it will mean the remaining blockers are real signal-path issues, not unrelated dashboard or helper noise.

## 10. Recommended First Slice

Start with `PDG-P1` and `PDG-P2`.

That gives the team the most leverage quickly:

- tests define the contract first
- the graph collector becomes the foundation for the scoped validation pass
- the most important false-blocking behavior becomes measurable before broader refactoring
