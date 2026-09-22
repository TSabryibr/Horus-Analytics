# Horus Analytics II Pine Comment-Aware Hard-Block Scanning Design

Date: 2026-04-03
Status: Approved design
Authoring mode: Brainstorming-approved design

Based on:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `tests/test_pine_profile_promotion.py`

## 1. Purpose

This design defines a small Pine preflight cleanup for Horus Strategy Lab.

Today, whole-script hard-block scans can still treat commented Pine code as active code when looking for:

- `strategy.short`
- `strategy.exit(...)`
- unsupported or unsafe `request.security(...)`

That creates false-positive blockers for realistic TradingView scripts where alternate logic is left in comments during iteration.

The goal of this phase is to make whole-script hard-block scans comment-aware for `//` comments while preserving the current real safety boundary.

## 2. Product Outcome

The operator-facing outcome should be:

1. Paste a Pine strategy into Pine Lab.
2. Run preflight.
3. Commented `strategy.short`, `strategy.exit(...)`, or unsafe `request.security(...)` text does not block the script.
4. Active code containing those constructs still blocks exactly as before.
5. The Pine runtime does not claim any new execution capability; it simply stops misreading commented code as active logic.

## 3. Design Goals

This phase should leave six things true:

1. Full-line `// ...` comments are ignored by whole-script hard-block scanning.
2. Trailing `// ...` comment tails are ignored by whole-script hard-block scanning.
3. Quoted strings containing `//` are preserved correctly.
4. Active execution-risk code still blocks globally.
5. Parser/runtime execution behavior stays unchanged.
6. The rollout is protected by focused backend regression tests.

## 4. Non-Goals

This phase does not attempt to:

- support `strategy.short`
- support `strategy.exit(...)`
- support repaint or cross-symbol `request.security(...)`
- add new Pine indicators
- implement full Pine lexical parsing
- process `/* ... */` block comments
- rewrite user Pine code
- change backtest execution semantics

## 5. Current State

Whole-script hard-block scanning is centered in:

- `core/pine_lab/capabilities.py`

Those scans currently operate on raw source text for execution-risk blockers such as:

- `strategy.short`
- `strategy.exit(...)`
- unsafe `request.security(...)`

That means a script like:

```pine
// strategy.entry("Short", strategy.short)
```

or:

```pine
strategy.entry("Long", strategy.long) // strategy.short
```

can still create a false blocker during preflight, even though the short-side text is commented out.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Strip `//` comments before whole-script hard-block scanning

Add a lightweight source sanitizer that removes full-line and trailing `//` comments outside quoted strings, then run the existing whole-script blocker scans on the sanitized source.

Pros:

- low risk
- directly addresses the common Pine false-positive pattern
- preserves the current blocker model

Cons:

- does not yet handle `/* ... */`

### Option 2. Ignore only full-line `//` comments

Handle lines that start with `//` but leave trailing comment tails untouched.

Pros:

- simpler

Cons:

- misses a very common TradingView editing pattern
- leaves too much noise in practice

### Option 3. Add full Pine lexical comment parsing

Handle line comments, block comments, and more complex Pine lexical cases up front.

Pros:

- most complete

Cons:

- too much complexity for this cleanup slice
- unnecessary risk compared with the immediate value

### Recommendation

Use Option 1.

This fixes the practical ALGOX-style false positive without turning a comment cleanup into a full parser project.

## 7. Comment Filtering Scope

This phase should ignore:

- full-line `// ...` comments
- trailing `// ...` comment tails on active lines

Examples:

```pine
// strategy.entry("Short", strategy.short)
```

should not block.

```pine
strategy.entry("Long", strategy.long) // strategy.short
```

should also not block on the comment tail.

This phase should preserve:

- quoted strings containing `//`

Example:

```pine
labelText = "http://example.com"
```

must not be chopped at `//`.

This phase should not process:

- `/* ... */` block comments

## 8. Implementation Seam

The change should stay localized to:

- `core/pine_lab/capabilities.py`

Implementation shape:

1. Add a helper such as `strip_line_comments(source: str) -> str`.
2. Make it line-aware and string-aware.
3. Preserve line breaks in the sanitized output.
4. Run whole-script hard-block scans against the sanitized source.

The sanitizer should be used for:

- `strategy.short`
- `strategy.exit(...)`
- whole-script `request.security(...)` blocker detection
- optional unsupported `ta.*` scans when they are enabled at the whole-script level

The sanitizer should not alter:

- expression-plan parsing
- runtime evaluation
- execution behavior

## 9. Safety Rules

The following must remain true after rollout:

1. Active `strategy.short` still blocks.
2. Active `strategy.exit(...)` still blocks.
3. Active unsafe `request.security(...)` still blocks.
4. Strings containing `//` are preserved.
5. This phase adds no new Pine capability.

## 10. Testing Strategy

Backend regression coverage should prove:

### 10.1 Commented short-side code does not block

- full-line `// strategy.short`
- trailing `// strategy.short`

### 10.2 Commented exit code does not block

- full-line `// strategy.exit(...)`
- trailing `// strategy.exit(...)`

### 10.3 Commented unsafe `request.security(...)` text does not block

- cross-symbol or repaint examples only in `//` comments

### 10.4 Active execution-risk code still blocks

- live `strategy.short`
- live `strategy.exit(...)`
- live unsafe `request.security(...)`

### 10.5 Quoted string safety

- strings such as `"http://example.com"` remain intact and do not trigger incorrect comment stripping

## 11. Rollout Boundary

This is a preflight false-positive cleanup only.

It should not:

- change Pine runtime capability
- change backtest execution
- weaken execution-risk blockers
- solve block-comment parsing yet

If block comments remain a problem later, they should be handled in a separate design slice.

## 12. Recommendation

Implement string-aware `//` line-comment stripping in `core/pine_lab/capabilities.py` and use the sanitized source for whole-script hard-block scanning.

This is the smallest safe next step for reducing Pine preflight noise in ALGOX-style scripts while keeping Horus execution boundaries intact.
