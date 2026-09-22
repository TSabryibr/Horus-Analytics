# Horus Analytics II Pine Block-Comment Hard-Block Scanning Design

Date: 2026-04-03
Status: Approved design
Authoring mode: Brainstorming-approved design

Based on:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `tests/test_pine_comment_filter.py`

## 1. Purpose

This design extends the Pine preflight comment cleanup already added for `//` comments.

Today, whole-script hard-block scans and parser pre-processing still treat `/* ... */` block-comment text as active code. That can create false-positive blockers in realistic TradingView scripts where alternate logic, experimental filters, or pasted reference sections are wrapped in block comments.

The goal of this phase is to make Pine preflight analysis ignore non-nested `/* ... */` block comments while preserving the existing execution-risk safety boundary.

## 2. Product Outcome

The operator-facing outcome should be:

1. Paste a Pine strategy into Pine Lab.
2. Run preflight.
3. Block-commented `strategy.short`, `strategy.exit(...)`, or unsafe `request.security(...)` text does not block the script.
4. Active code containing those constructs still blocks exactly as before.
5. The Pine runtime does not claim any new execution capability; it simply stops misreading block-commented code as active logic.

## 3. Design Goals

This phase should leave seven things true:

1. Full-line `/* ... */` comments are ignored by analysis.
2. Inline block comments are ignored by analysis.
3. Multiline block comments are ignored by analysis.
4. Quoted strings containing `/*`, `*/`, or `//` are preserved correctly.
5. Active execution-risk code still blocks globally.
6. Parser line structure remains stable because block-comment newlines are preserved.
7. The rollout is protected by focused backend regression tests.

## 4. Non-Goals

This phase does not attempt to:

- support `strategy.short`
- support `strategy.exit(...)`
- support repaint or cross-symbol `request.security(...)`
- add new Pine indicators
- implement nested block comments
- implement full Pine lexical parsing
- rewrite user Pine code
- change backtest execution semantics

## 5. Current State

Comment-aware hard-block scanning currently handles:

- full-line `// ...` comments
- trailing `// ...` comment tails

That cleanup is centralized through a source sanitizer used by:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`

But block comments such as:

```pine
/*
strategy.entry("Short", strategy.short)
strategy.exit("Risk", "Long", stop=close * 0.95)
*/
```

or:

```pine
fast = ta.sma(close, 10) /* strategy.short */
```

can still be misread as active Pine code during preflight analysis.

## 6. Recommended Approach

Three approaches were considered:

### Option 1. Extend the existing sanitizer into a unified Pine comment stripper

Keep the current string-aware `//` handling and add non-nested `/* ... */` removal outside quoted strings. Reuse the same sanitizer for:

- whole-script hard-block scanning
- parser pre-processing

Pros:

- one source of truth
- keeps scanner and parser behavior aligned
- smallest safe extension of the current implementation

Cons:

- still not a full Pine lexer
- still intentionally does not support nested block comments

### Option 2. Add a second block-comment-only pass

Leave the existing `//` stripper unchanged and run a separate `/* ... */` removal step before scanning and parsing.

Pros:

- straightforward to bolt on

Cons:

- easier for the two passes to drift
- duplicates comment-state logic

### Option 3. Build a full Pine lexer/tokenizer

Create a dedicated lexical layer for comments, strings, and tokens.

Pros:

- strongest long-term foundation

Cons:

- much larger scope than needed
- unnecessary risk for a focused false-positive cleanup

### Recommendation

Use Option 1.

This preserves the existing small-surface approach while extending it to the next common real-world comment pattern.

## 7. Block-Comment Filtering Scope

This phase should ignore:

- full-line block comments
- inline block comments
- multiline block comments

Examples:

```pine
/* strategy.entry("Short", strategy.short) */
```

should not block.

```pine
fast = ta.sma(close, 10) /* strategy.short */
```

should also not block.

```pine
/*
htfClose = request.security("EGX:COMI", "1D", close, gaps=barmerge.gaps_off, lookahead=barmerge.lookahead_on)
*/
```

should not block.

This phase should preserve:

- quoted strings containing `//`
- quoted strings containing `/*`
- quoted strings containing `*/`

Example:

```pine
labelText = "literal /* not a comment */ text"
```

must remain intact.

This phase should not process:

- nested `/* ... /* ... */ ... */` comment structures

The first closing `*/` should end the active block comment.

## 8. Implementation Seam

The change should stay localized to:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`

Implementation shape:

1. Replace the line-only sanitizer with a unified Pine comment stripper.
2. Keep it string-aware.
3. Track block-comment state outside strings.
4. Preserve newline characters while stripping block comments.
5. Reuse the sanitized source for both:
   - whole-script hard-block scans
   - parser pre-processing

The sanitizer should be responsible for:

- `strategy.short` scanning
- `strategy.exit(...)` scanning
- whole-script `request.security(...)` blocker detection
- optional whole-script unsupported `ta.*` scans
- parser protection from comment tails and block-comment bodies

The sanitizer should not alter:

- runtime evaluation
- execution behavior
- Pine capability boundaries

## 9. Safety Rules

The following must remain true after rollout:

1. Active `strategy.short` still blocks.
2. Active `strategy.exit(...)` still blocks.
3. Active unsafe `request.security(...)` still blocks.
4. Strings containing comment tokens are preserved.
5. Newlines inside stripped block comments are preserved.
6. No new Pine capability is implied by this cleanup.

## 10. Edge-Case Policy

### 10.1 Unclosed block comments

If the sanitizer sees `/*` without a closing `*/`, it should treat the rest of the file as commented for analysis only.

This is the safest phase-1 behavior because it avoids false-positive execution-risk blockers from code the user clearly intended to comment out.

### 10.2 Nested block comments

Nested block comments are out of scope.

If another `/*` appears while already inside a block comment, it should be treated as plain comment content until the first closing `*/`.

## 11. Testing Strategy

Backend regression coverage should prove:

### 11.1 Block-commented short-side code does not block

- full-line `/* strategy.short */`
- inline `/* strategy.short */`
- multiline block containing `strategy.short`

### 11.2 Block-commented exit code does not block

- inline or multiline `strategy.exit(...)`

### 11.3 Block-commented unsafe `request.security(...)` text does not block

- repaint or cross-symbol examples only inside block comments

### 11.4 Parser stability

- assignment lines with inline block-comment tails still parse correctly
- multiline block comments between definitions do not poison plan extraction

### 11.5 String safety

- strings such as `"http://example.com"` remain intact
- strings containing `/* ... */` markers remain intact

### 11.6 Active execution-risk code still blocks

- live `strategy.short`
- live `strategy.exit(...)`
- live unsafe `request.security(...)`

## 12. Rollout Boundary

This is a preflight-analysis cleanup only.

It should not:

- change Pine runtime capability
- change backtest execution
- weaken active execution-risk blockers
- add nested comment support
- expand `request.security(...)` support

## 13. Recommendation

Extend the current Pine comment sanitizer so it strips non-nested `/* ... */` block comments outside quoted strings and reuse that sanitized source for both hard-block scanning and parser pre-processing.

This is the smallest safe next step for reducing Pine preflight noise in larger TradingView scripts while keeping Horus execution boundaries intact.
