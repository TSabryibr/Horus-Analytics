# Horus Analytics II Pine Logic Import Implementation Plan

Date: 2026-04-04
Based on:

- `docs/superpowers/specs/2026-04-04-pine-logic-import-design.md`
- `docs/ExProfit.pine`
- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `core/pine_lab/__init__.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `frontend/src/app/optimization/hooks/usePineBacktest.ts`
- `tests/test_pine_profile_promotion.py`
- `tests/test_pine_comment_filter.py`
- `core/ai_report/generation.py`
- `core/ai_report/boundary.py`

Track: Pine Logic Import
Status: Proposed plan
Owner model: Single owner

## 1. Goal

This plan turns the approved Pine Logic Import design into a staged implementation sequence for Horus.

The implementation must leave eight things true:

1. Horus keeps the existing native Pine runtime path unchanged.
2. Horus gains a separate `Logic Import` path for mixed real-world Pine scripts.
3. Phase 1 import remains signal-only:
   - `long_entry`
   - `short_entry`
   - `long_exit`
   - `short_exit`
4. Every imported result is a structured Horus rule spec plus a human-readable review surface.
5. No imported rule spec reaches backtesting until it passes validation and explicit operator approval.
6. Translator output is traceable back to Pine variables and expressions.
7. The first delivered slice is preview-first and does not depend on full Pine runtime compatibility.
8. The rollout is protected by backend and frontend regression coverage.

## 2. In Scope

This plan covers the staged delivery of:

- Pine signal extraction
- reduced source pack generation
- AI-assisted rule spec translation with deterministic fallback behavior
- rule spec validation
- import preview API
- Pine Lab `Logic Import` UI flow
- approved-spec backtesting in a later slice
- saved imported profiles in a later slice

Primary backend targets:

- `core/pine_lab/parser.py`
- new import-focused helpers under `core/pine_lab/`
- `core/pine_lab/executor.py` or a new import-executor seam in a later slice
- `routes/strategy.py`

Primary frontend targets:

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- new Logic Import hooks under `frontend/src/app/optimization/hooks/`

Primary regression targets:

- new backend tests under `tests/`
- new frontend tests under `frontend/src/app/optimization/`

Out of scope for this track:

- MT4 or MT5 import
- full TradingView parity
- Pine trade management import
- stop loss, take profit, sizing, trailing, or partial exits
- automatic live promotion into scanner runtime
- replacement of existing native Pine runtime endpoints

## 3. Current Constraints

These existing facts shape the rollout:

1. Horus already has Pine runtime endpoints in `routes/strategy.py`:
   - `/api/v1/strategy/pine/preflight`
   - `/api/v1/strategy/pine/backtest`
   - Pine scanner profile routes
2. Current Pine runtime logic lives in:
   - `core/pine_lab/parser.py`
   - `core/pine_lab/executor.py`
3. Current frontend Pine Lab assumes a single Pine path built around:
   - `usePinePreflight.ts`
   - `usePineBacktest.ts`
   - `PineLabPanel.tsx`
4. The approved design requires a separate import lane, so existing runtime behavior must not be overloaded or weakened.
5. Existing Pine tests are already extensive, but they are centered on runtime preflight and runtime backtesting rather than import-preview behavior.
6. The repo already has Ollama and structured-JSON prompting patterns under `core/ai_report/`, so the import translator should reuse those patterns rather than growing an unrelated provider stack.
7. `docs/ExProfit.pine` is already a useful real-world regression fixture because native runtime preflight blocks it while the import lane should still attempt to recover signal logic.

## 4. Execution Rules

These rules apply across all work packages:

1. Existing `/api/v1/strategy/pine/preflight` behavior must remain a native runtime contract.
2. Existing `/api/v1/strategy/pine/backtest` behavior must remain a native runtime contract.
3. Import preview must use separate routes and separate response shapes where the semantics differ.
4. No AI or translator output may be backtested directly without schema validation.
5. Every machine-readable imported rule must preserve traceability to the reduced source pack.
6. Phase 1 and phase 2 must stay signal-only; trade management import remains blocked.
7. When the translator fails or AI is unavailable, Horus must fall back to a deterministic draft scaffold rather than fail silently.
8. Warnings, unresolved references, and low confidence must remain visible all the way to the review surface.

## 5. Target Module Map

The implementation should converge on this shape.

### Existing runtime seam to preserve

- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`

### New import domain seam

- `core/pine_lab/importer.py`
  Signal extraction orchestration and reduced source pack building.

- `core/pine_lab/import_spec.py`
  Rule spec schema helpers, normalization, and response shape helpers.

- `core/pine_lab/import_validator.py`
  Validation rules for translated rule specs and approval readiness.

- `core/pine_lab/import_translation.py`
  Translator prompt builder, structured JSON parsing, provider fallback handling, and deterministic draft fallback.

- `core/pine_lab/import_executor.py`
  Later-stage executor for approved imported rule specs.

- `core/pine_lab/__init__.py`
  Export the import-preview and later import-backtest entry points.

### API seam

- `routes/strategy.py`

### Frontend seam

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePineLogicImport.ts`
- `frontend/src/app/optimization/hooks/usePineImportBacktest.ts`

### Regression seam

- `tests/test_pine_logic_import.py`
- targeted Pine runtime guard coverage in `tests/test_pine_profile_promotion.py`
- `frontend/src/app/optimization/components/PineLabPanel.test.tsx`
- `frontend/src/app/optimization/hooks/usePineLogicImport.test.tsx`

## 6. Work Package Sequence

Execute this track in the following order:

1. `PLI-P1` Red-first import contract and schema regressions
2. `PLI-P2` Signal extractor and reduced source pack
3. `PLI-P3` Translator boundary and rule-spec validator
4. `PLI-P4` Import preview API integration
5. `PLI-P5` Pine Lab `Logic Import` preview UI
6. `PLI-P6` Approved-spec backtesting and comparison
7. `PLI-P7` Saved imported profiles and scanner boundary

This order is intentional:

- contract tests must define what import preview means before implementation
- extraction must exist before translation can be trusted
- validation must exist before any route or UI can expose the feature safely
- preview must ship before approved-spec backtesting
- saved profiles should come only after the import-preview and backtest paths are stable

## 7. Work Packages

### PLI-P1. Red-First Import Contract And Schema Regressions

Purpose:

Define the import-preview contract before any new import code is written.

Target files:

- new `tests/test_pine_logic_import.py`
- optional small guard additions in `tests/test_pine_profile_promotion.py`

Tasks:

1. Add a failing test for `import-preview` on a simple Pine strategy that should produce:
   - `status = success`
   - a reduced source pack
   - a draft rule spec
   - readable signal summaries
2. Add a failing test where a mixed indicator script with extra plots and alerts still produces an import preview rather than a native-runtime-style hard block.
3. Add a failing test for validation that rejects:
   - invented variables
   - missing signal fields
   - unsupported operators
4. Add a failing test for translator fallback behavior when no AI translation succeeds.
5. Preserve a guard test proving native runtime routes still behave the same way they do today.

Deliverables:

- explicit backend contract for import-preview
- explicit contract for validator rejection behavior

Verification:

- focused import tests fail for the right reasons before implementation

Acceptance criteria:

- the import-preview response contract is pinned down in tests before code changes begin

### PLI-P2. Signal Extractor And Reduced Source Pack

Purpose:

Build the import-facing extraction layer without changing native runtime semantics.

Target files:

- `core/pine_lab/parser.py`
- new `core/pine_lab/importer.py`

Tasks:

1. Reuse existing parser knowledge where helpful, but keep import extraction separate from native runtime readiness decisions.
2. Add candidate-signal detection for likely booleans such as:
   - `longE`
   - `shortE`
   - `longX`
   - `shortX`
   - `buySignal`
   - `sellSignal`
3. Trace the dependency chain for candidate signals.
4. Capture Pine inputs and indicator calls that materially affect the candidate signals.
5. Build a reduced source pack with:
   - candidate signals
   - dependent definitions
   - source snippets
   - warnings
   - unresolved references
   - ignored sections
6. Explicitly classify non-signal sections such as:
   - plots
   - labels
   - fills
   - alerts
   - styling
   - visual helper code
7. Ensure a mixed script like `docs/ExProfit.pine` can surface a useful candidate-signal pack even if native runtime preflight remains blocked.

Deliverables:

- import-focused signal extractor
- reduced source pack builder

Verification:

- `PLI-P1` extraction tests pass

Acceptance criteria:

- import preview can recover a signal-focused representation from real mixed Pine scripts without changing native runtime rules

### PLI-P3. Translator Boundary And Rule-Spec Validator

Purpose:

Convert the reduced source pack into a structured Horus rule spec safely.

Target files:

- `core/pine_lab/import_translation.py`
- `core/pine_lab/import_spec.py`
- `core/pine_lab/import_validator.py`
- `core/ai_report/generation.py` only if a small shared helper extraction is truly needed

Tasks:

1. Define the machine-readable rule spec schema from the approved design:
   - `source`
   - `parameters`
   - `indicators`
   - `signals`
   - `human_summary`
   - `traceability`
   - `ignored_sections`
   - `warnings`
   - `confidence`
2. Build a structured translator prompt that:
   - only sees the reduced source pack
   - requires valid JSON output
   - forbids invented variables
   - requires warnings and low-confidence markers when needed
3. Reuse existing provider patterns from the AI report stack for:
   - JSON response parsing
   - code-fence stripping
   - Ollama fallback behavior where appropriate
4. Add a deterministic fallback translator that returns a draft scaffold using the extracted candidate signals and source snippets when the AI step fails or is unavailable.
5. Implement validator rules for:
   - schema integrity
   - source-pack traceability
   - supported operator set
   - required signal coverage
   - confidence and unresolved-reference coherence

Deliverables:

- structured translator boundary
- deterministic fallback scaffold
- rule-spec validator

Verification:

- `PLI-P1` validator and fallback tests pass

Acceptance criteria:

- Horus can always return either:
   - a validated translated rule spec
   - or a clearly marked deterministic draft scaffold
- Horus never returns unvalidated free-form AI text as an executable artifact

### PLI-P4. Import Preview API Integration

Purpose:

Expose the new import-preview workflow through dedicated backend endpoints.

Target files:

- `routes/strategy.py`
- `core/pine_lab/__init__.py`
- import-focused backend modules from earlier packages

Tasks:

1. Add `POST /api/v1/strategy/pine/import-preview`.
2. Validate payload fields similarly to current Pine routes:
   - `script_source`
   - `market`
   - `timeframe`
   - `date_from`
   - `date_to`
3. Return an import-preview response containing at minimum:
   - reduced source pack summary
   - generated rule spec
   - warnings
   - confidence
   - ignored sections
   - review readiness
4. Keep native runtime route outputs unchanged.
5. Ensure route errors are structured and operator-readable.

Deliverables:

- import-preview endpoint
- import-preview route coverage

Verification:

- backend import-preview tests pass
- native runtime route tests remain green

Acceptance criteria:

- operators can request a reviewable import preview without invoking native Pine runtime semantics

### PLI-P5. Pine Lab `Logic Import` Preview UI

Purpose:

Expose the new import-preview workflow inside the existing Pine Lab.

Target files:

- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- new `frontend/src/app/optimization/hooks/usePineLogicImport.ts`
- new frontend tests

Tasks:

1. Add a Pine Lab submode switch:
   - `Native Pine Runtime`
   - `Logic Import`
2. Keep current `usePinePreflight` and `usePineBacktest` flows intact for native runtime.
3. Add a new hook for `Logic Import` preview requests.
4. Add a review surface showing:
   - signal summaries
   - machine-readable signals
   - warnings
   - confidence
   - ignored sections
   - traceability
   - `Needs Manual Review` versus `Ready For Approval`
5. Add operator controls for:
   - `Extract Rule Spec`
   - optional review edits in a later increment if needed
   - approval state storage for the later backtest step

Deliverables:

- Pine Lab `Logic Import` preview UI
- frontend regression coverage

Verification:

- new PineLabPanel and hook tests pass

Acceptance criteria:

- the operator can generate and review an import preview in the UI without disrupting native Pine runtime usage

### PLI-P6. Approved-Spec Backtesting And Comparison

Purpose:

Enable phase 2 backtesting for validated and operator-approved rule specs.

Target files:

- new `core/pine_lab/import_executor.py`
- `routes/strategy.py`
- new `frontend/src/app/optimization/hooks/usePineImportBacktest.ts`
- Pine Lab result surface components or existing result views

Tasks:

1. Add an executor that consumes the structured rule spec rather than raw Pine.
2. Enforce an approval gate:
   - only validated
   - explicitly approved specs
   may be backtested
3. Add `POST /api/v1/strategy/pine/import-backtest`.
4. Return:
   - backtest summary
   - trade log
   - equity curve
   - imported-rule metadata
   - comparison values against Horus core over the same market window
5. Exclude any unsupported trade-management fields from execution and surface them as ignored metadata only.

Deliverables:

- approved-spec backtest executor
- import-backtest route
- comparison-capable frontend flow

Verification:

- import-backtest tests pass
- existing native Pine backtest tests remain green

Acceptance criteria:

- approved imported logic can be tested fairly inside Horus without using raw Pine execution

### PLI-P7. Saved Imported Profiles And Scanner Boundary

Purpose:

Persist strong imported rule specs for repeatable research while keeping live-scanner boundaries explicit.

Target files:

- `routes/strategy.py`
- profile persistence seam under `core/pine_lab/`
- relevant database/profile serialization tests

Tasks:

1. Add `POST /api/v1/strategy/pine/import-profile`.
2. Persist:
   - approved rule spec
   - source metadata
   - summary metrics
   - warnings and confidence
3. Keep imported profiles distinct from native runtime Pine profiles if their metadata or execution semantics differ.
4. Keep live activation explicit and operator-controlled.

Deliverables:

- saved imported profile capability

Verification:

- import-profile tests pass
- scanner profile behavior remains stable

Acceptance criteria:

- reusable imported logic can be saved without blurring the boundary between native Pine runtime profiles and imported signal-spec profiles

## 8. Suggested Test Matrix

At minimum, this track should cover:

1. `import_preview_returns_draft_spec_for_supported_strategy`
2. `import_preview_recovers_signal_pack_from_mixed_indicator_script`
3. `import_preview_surfaces_ignored_visual_sections`
4. `import_preview_marks_low_confidence_when_dependencies_are_unresolved`
5. `import_validator_rejects_invented_variables`
6. `import_validator_rejects_missing_signal_fields`
7. `import_validator_rejects_unsupported_operators`
8. `import_translation_falls_back_to_deterministic_draft_when_ai_unavailable`
9. `native_pine_preflight_route_remains_unchanged`
10. `logic_import_ui_switches_without_breaking_native_runtime_controls`
11. `import_backtest_requires_explicit_approval`
12. `import_backtest_uses_structured_rule_spec_not_raw_pine`

## 9. Rollout Notes

This track should be treated as a staged research-enablement rollout, not a one-shot Pine compatibility project.

The most important boundary is:

- preview first
- backtest second
- reusable profiles third

If the translator boundary proves too unstable early on, the track should still ship stage 1 using:

- signal extraction
- reduced source pack
- deterministic draft scaffold
- human review surface

That fallback still creates operator value and keeps the design honest.

## 10. Recommended First Slice

Start with `PLI-P1` through `PLI-P5`.

That gives the team the highest-value first release:

- import-preview exists
- real mixed Pine scripts can be analyzed
- the operator can review a Horus rule spec before any test runs
- native Pine runtime stays untouched

Do not start with import-backtest.

The review boundary is the safety line for this whole feature, so it should be proven in production-shaped flows before the first executable slice is added.
