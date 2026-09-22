# Horus Analytics II Pine Comment-Aware Hard-Block Scanning Implementation Plan

Date: 2026-04-03
Based on:

- `docs/superpowers/specs/2026-04-03-pine-comment-aware-hard-block-scanning-design.md`
- `core/pine_lab/capabilities.py`
- `core/pine_lab/parser.py`
- `tests/test_pine_profile_promotion.py`

Track: Pine Comment-Aware Hard-Block Scanning
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine comment-aware hard-block scanning design into a safe implementation sequence for Horus Pine preflight.

The implementation must leave six things true:

1. Whole-script hard-block scans ignore full-line `//` comments.
2. Whole-script hard-block scans ignore trailing `//` comment tails.
3. Quoted strings containing `//` remain intact.
4. Active `strategy.short`, `strategy.exit(...)`, and unsafe `request.security(...)` still block exactly as before.
5. Parser/runtime execution behavior remains unchanged.
6. The rollout is protected by focused backend regression coverage.

## 2. In Scope

Primary backend targets:

- `core/pine_lab/capabilities.py`
- targeted backend tests under `tests/`

Primary workflow capability to add:

- string-aware `//` comment stripping before whole-script hard-block scanning

Out of scope for this phase:

- new Pine indicators
- new execution semantics
- `strategy.short` support
- `strategy.exit(...)` support
- repaint normalization
- `request.security(...)` feature expansion
- `/* ... */` block comment parsing
- parser/executor rewrites
- frontend UI changes

## 3. Current Constraints

These existing facts shape the rollout:

1. Whole-script hard blockers are centralized in `core/pine_lab/capabilities.py`.
2. Current hard-block scans operate on raw source text and can treat commented code as active code.
3. Expression-plan parsing and runtime evaluation are not the right seams for this cleanup and should remain unchanged.
4. The change should be localized so it can reduce false positives without altering Pine capability boundaries.
5. `tests/test_pine_profile_promotion.py` already covers Pine preflight behavior and is the right regression seam for this work.

## 4. Execution Rules

These rules apply across all work packages:

1. No active execution-risk code may stop blocking because of this rollout.
2. No quoted string containing `//` may be mangled by the sanitizer.
3. No new Pine capability may be implied by this change.
4. No parser or runtime behavior may change outside whole-script blocker scanning.
5. `/* ... */` handling must remain untouched in this phase.

## 5. Target Module Map

The implementation should converge on this shape.

### Whole-script blocker seam

- `core/pine_lab/capabilities.py`

### Regression seam

- `tests/test_pine_profile_promotion.py`

## 6. Work Package Sequence

Execute this slice in the following order:

1. `PCH-P1` Red-first comment-filter regressions
2. `PCH-P2` String-aware `//` sanitizer
3. `PCH-P3` Hard-block scan integration
4. `PCH-P4` Regression hardening and closeout

This order is intentional:

- tests must define the false-positive boundary first
- the sanitizer should be implemented before integration with blocker scans
- regression hardening should prove we reduced noise without weakening safety

## 7. Work Packages

### PCH-P1. Red-First Comment-Filter Regressions

Purpose:

Define the exact false-positive and safety boundaries before touching the blocker scan.

Target files:

- `tests/test_pine_profile_promotion.py`

Tasks:

1. Add a failing test where a full-line `// strategy.short` does not block.
2. Add a failing test where a trailing `// strategy.short` does not block.
3. Add a failing test where a full-line or trailing `// strategy.exit(...)` does not block.
4. Add a failing test where commented unsafe `request.security(...)` text does not block.
5. Add a failing test where a quoted string like `"http://example.com"` is preserved and does not cause accidental stripping.
6. Preserve guard tests where active:
   - `strategy.short`
   - `strategy.exit(...)`
   - unsafe `request.security(...)`
   still block.

Deliverables:

- explicit regression coverage for comment-aware hard-block scanning

Verification:

- focused Pine preflight tests fail for the right reasons before implementation

Acceptance criteria:

- the tests clearly separate commented-code false positives from active-code blockers

### PCH-P2. String-Aware `//` Sanitizer

Purpose:

Implement a lightweight Pine source sanitizer that strips only `//` comments outside quoted strings.

Target files:

- `core/pine_lab/capabilities.py`

Tasks:

1. Add a helper like `strip_line_comments(source: str) -> str`.
2. Make it preserve line breaks.
3. Make it ignore `//` inside quoted strings.
4. Support:
   - full-line comments
   - trailing comment tails
5. Leave `/* ... */` untouched.

Deliverables:

- reusable string-aware line-comment sanitizer

Verification:

- focused helper behavior covered indirectly through preflight regressions

Acceptance criteria:

- commented hard-block tokens disappear from the scanned source
- quoted strings remain intact

### PCH-P3. Hard-Block Scan Integration

Purpose:

Apply the sanitized source only to whole-script blocker detection while preserving current safety behavior.

Target files:

- `core/pine_lab/capabilities.py`

Tasks:

1. Run `strategy.short` detection on the sanitized source.
2. Run `strategy.exit(...)` detection on the sanitized source.
3. Run whole-script unsafe `request.security(...)` detection on the sanitized source.
4. Run optional whole-script unsupported `ta.*` scanning on the sanitized source when that mode is enabled.
5. Keep all blocker messages unchanged.

Deliverables:

- comment-aware whole-script blocker detection

Verification:

- `PCH-P1` regressions now pass

Acceptance criteria:

- commented execution-risk code no longer blocks
- active execution-risk code still blocks with the same reasons

### PCH-P4. Regression Hardening and Closeout

Purpose:

Prove that comment-aware scanning reduces false positives without regressing current Pine preflight behavior.

Target files:

- `tests/test_pine_profile_promotion.py`
- nearby Pine regression files only if needed

Tasks:

1. Re-run focused comment-filter tests.
2. Re-run a broader Pine preflight regression sweep.
3. Confirm supported Pine strategies still reach the same readiness states.
4. Confirm no frontend work is needed because this is a backend preflight-only cleanup.

Deliverables:

- stable backend regression sweep

Verification:

- focused Pine preflight tests
- broader Pine regression suite

Acceptance criteria:

- false-positive comment blockers are removed
- active blockers remain intact
- no user-facing Pine capability drift is introduced

## 8. Suggested Test Matrix

At minimum, the rollout should cover:

1. `commented_short_line_does_not_block`
2. `trailing_comment_short_does_not_block`
3. `commented_strategy_exit_does_not_block`
4. `commented_unsafe_request_security_does_not_block`
5. `quoted_double_slash_string_is_preserved`
6. `active_strategy_short_still_blocks`
7. `active_strategy_exit_still_blocks`
8. `active_unsafe_request_security_still_blocks`

## 9. Rollout Notes

This slice should be implemented as a whole-script blocker cleanup only.

If block comments remain a source of false positives after this phase, they should be handled in a separate design/plan cycle instead of being folded into this small rollout.

## 10. Recommended First Slice

Start with `PCH-P1` and `PCH-P2`.

That gives the team the most leverage quickly:

- the false-positive boundary is pinned down in tests first
- the sanitizer can be developed in isolation
- blocker integration can then stay minimal and low-risk
