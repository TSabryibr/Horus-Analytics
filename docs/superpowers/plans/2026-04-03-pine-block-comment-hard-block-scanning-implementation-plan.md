# Horus Analytics II Pine Block-Comment Hard-Block Scanning Implementation Plan

Date: 2026-04-03
Based on:

- `docs/superpowers/specs/2026-04-03-pine-block-comment-hard-block-scanning-design.md`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `tests/test_pine_comment_filter.py`

Track: Pine Block-Comment Hard-Block Scanning
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine block-comment scanning design into a safe implementation sequence for Horus Pine preflight.

The implementation must leave seven things true:

1. Whole-script hard-block scans ignore full-line `/* ... */` comments.
2. Whole-script hard-block scans ignore inline `/* ... */` comments.
3. Whole-script hard-block scans ignore multiline `/* ... */` comments.
4. Quoted strings containing `/*`, `*/`, or `//` remain intact.
5. Active `strategy.short`, `strategy.exit(...)`, and unsafe `request.security(...)` still block exactly as before.
6. Parser line structure remains stable because stripped block comments preserve newlines.
7. The rollout is protected by focused backend regression coverage.

## 2. In Scope

Primary backend targets:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- targeted backend tests under `tests/`

Primary workflow capability to add:

- unified Pine comment stripping that handles both `//` and non-nested `/* ... */` comments outside quoted strings

Out of scope for this phase:

- new Pine indicators
- new execution semantics
- `strategy.short` support
- `strategy.exit(...)` support
- repaint normalization
- `request.security(...)` feature expansion
- nested block comment parsing
- full Pine lexical parsing
- frontend UI changes

## 3. Current Constraints

These existing facts shape the rollout:

1. Whole-script hard blockers are centralized in `core/pine_lab/capabilities.py`.
2. Parser pre-processing already uses the shared comment sanitizer from `core/pine_lab/parser.py`.
3. Current cleanup already handles `//` comments safely, so this rollout must extend that behavior instead of replacing it with a second drifting path.
4. The change should stay localized so it reduces false positives without altering Pine capability boundaries.
5. `tests/test_pine_comment_filter.py` is already the correct focused regression seam for this work.

## 4. Execution Rules

These rules apply across all work packages:

1. No active execution-risk code may stop blocking because of this rollout.
2. No quoted string containing comment markers may be mangled by the sanitizer.
3. Newlines inside stripped block comments must be preserved.
4. No new Pine capability may be implied by this change.
5. Nested block comments remain unsupported in this phase.

## 5. Target Module Map

The implementation should converge on this shape.

### Shared comment sanitizer seam

- `core/pine_lab/capabilities.py`

### Parser pre-processing seam

- `core/pine_lab/parser.py`

### Regression seam

- `tests/test_pine_comment_filter.py`
- nearby Pine regression tests only if needed

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PBC-P1` Red-first block-comment regressions
2. `PBC-P2` Unified Pine comment sanitizer
3. `PBC-P3` Hard-block and parser integration verification
4. `PBC-P4` Regression hardening and closeout

This order is intentional:

- tests must define the false-positive boundary first
- the sanitizer should be extended before any broader validation
- integration verification should prove scanner and parser stay aligned

## 7. Work Packages

### PBC-P1. Red-First Block-Comment Regressions

Purpose:

Define the exact false-positive and safety boundaries before extending the sanitizer.

Target files:

- `tests/test_pine_comment_filter.py`

Tasks:

1. Add a failing test where full-line `/* strategy.short */` does not block.
2. Add a failing test where inline `/* strategy.short */` does not block.
3. Add a failing test where block-commented `strategy.exit(...)` does not block.
4. Add a failing test where multiline block-commented unsafe `request.security(...)` text does not block.
5. Add a failing test where quoted strings containing `/* ... */` remain intact.
6. Add a failing parser-facing test where an assignment line contains an inline block-comment tail and still preflights cleanly.
7. Preserve guard tests where active:
   - `strategy.short`
   - `strategy.exit(...)`
   - unsafe `request.security(...)`
   still block.

Deliverables:

- explicit regression coverage for block-comment-aware preflight analysis

Verification:

- focused Pine comment-filter tests fail for the right reasons before implementation

Acceptance criteria:

- the tests clearly separate block-comment false positives from active-code blockers

### PBC-P2. Unified Pine Comment Sanitizer

Purpose:

Extend the current line-comment sanitizer into a unified Pine comment stripper that handles both `//` and non-nested `/* ... */` comments outside quoted strings.

Target files:

- `core/pine_lab/capabilities.py`

Tasks:

1. Replace the line-only helper with a shared Pine comment stripper.
2. Preserve line breaks while stripping block comments.
3. Ignore `//`, `/*`, and `*/` markers inside quoted strings.
4. Support:
   - full-line comments
   - trailing line-comment tails
   - full-line block comments
   - inline block comments
   - multiline block comments
5. Treat unclosed block comments as continuing to end-of-file for analysis only.
6. Keep nested block comments unsupported and end comments at the first closing `*/`.

Deliverables:

- reusable string-aware unified Pine comment sanitizer

Verification:

- focused helper behavior covered indirectly through preflight regressions

Acceptance criteria:

- block-commented hard-block tokens disappear from analyzed source
- quoted strings and newline structure remain intact

### PBC-P3. Hard-Block and Parser Integration Verification

Purpose:

Apply the sanitized source consistently to both whole-script blocker detection and parser pre-processing while preserving current safety behavior.

Target files:

- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`

Tasks:

1. Keep whole-script blocker detection on sanitized source.
2. Confirm parser pre-processing also uses the same sanitized source path.
3. Verify no duplicate sanitizer logic is introduced.
4. Keep blocker messages unchanged.
5. Confirm line-comment behavior remains green after block-comment support is added.

Deliverables:

- aligned scanner and parser comment handling

Verification:

- `PBC-P1` regressions now pass

Acceptance criteria:

- block-commented execution-risk code no longer blocks
- active execution-risk code still blocks with the same reasons
- parser line extraction remains stable around removed block comments

### PBC-P4. Regression Hardening and Closeout

Purpose:

Prove that block-comment-aware scanning reduces false positives without regressing current Pine preflight behavior.

Target files:

- `tests/test_pine_comment_filter.py`
- nearby Pine regression files only if needed

Tasks:

1. Re-run focused comment-filter tests.
2. Re-run a broader Pine preflight regression sweep.
3. Confirm supported Pine strategies still reach the same readiness states.
4. Confirm this remains a backend preflight-analysis cleanup with no frontend work required.

Deliverables:

- stable backend regression sweep

Verification:

- focused Pine comment-filter tests
- broader Pine regression suite

Acceptance criteria:

- false-positive block-comment blockers are removed
- active blockers remain intact
- no user-facing Pine capability drift is introduced

## 8. Suggested Test Matrix

At minimum, the rollout should cover:

1. `block_commented_short_line_does_not_block`
2. `inline_block_comment_short_does_not_block`
3. `block_commented_strategy_exit_does_not_block`
4. `block_commented_unsafe_request_security_does_not_block`
5. `inline_block_comment_assignment_still_parses`
6. `quoted_block_comment_markers_are_preserved`
7. `active_strategy_short_still_blocks`
8. `active_strategy_exit_still_blocks`
9. `active_unsafe_request_security_still_blocks`

## 9. Rollout Notes

This slice should be implemented as an analysis cleanup only.

If nested block comments or deeper Pine lexical edge cases become important later, they should be handled in a separate design/plan cycle instead of being folded into this focused rollout.

## 10. Recommended First Slice

Start with `PBC-P1` and `PBC-P2`.

That gives the team the most leverage quickly:

- the block-comment false-positive boundary is pinned down in tests first
- the sanitizer can be extended in one place
- parser and blocker verification can then stay minimal and low-risk
