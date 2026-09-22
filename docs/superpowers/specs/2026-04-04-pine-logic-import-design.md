# Horus Analytics II Pine Logic Import Design

Date: 2026-04-04
Status: Approved design
Authoring mode: Brainstorming-approved design

Based on:

- `docs/ExProfit.pine`
- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`
- `frontend/src/app/optimization/hooks/usePinePreflight.ts`
- `docs/superpowers/specs/2026-03-30-pine-egx-strategy-lab-design.md`

## 1. Purpose

This design defines a Pine-first import workflow for Horus that focuses on extracting strategy logic from outside scripts instead of trying to execute full TradingView behavior.

The operator goal is:

- search for outside Pine indicators or strategies
- extract the entry and exit logic they use
- review that logic as a human-readable Horus rule spec
- backtest the imported logic inside Horus
- compare it fairly against Horus core logic

This phase is intentionally narrower than Pine execution.

The phase 1 goal is specifically:

- Pine import first, not MT4 or MT5
- signal logic only
- human review before any backtest
- Horus-native testing after approval

## 2. Product Outcome

The operator-facing outcome should be:

1. Open Pine Lab.
2. Choose a new `Logic Import` path instead of the existing native Pine runtime path.
3. Paste a Pine indicator or strategy, even if it contains mixed visual code, alerts, or unsupported execution features.
4. Let Horus isolate the likely signal logic and produce a draft Horus rule spec.
5. Review the generated long entry, short entry, long exit, and short exit logic in readable form.
6. See confidence, warnings, ignored Pine sections, and traceability back to the original script.
7. Approve the spec.
8. Backtest the approved spec inside Horus using Horus data and Horus execution assumptions.
9. Compare the imported logic against Horus core and decide whether it is worth promoting later.

## 3. Design Goals

This phase should leave seven things true:

1. Horus can learn from outside Pine scripts without pretending to support full Pine execution.
2. Mixed real-world scripts can still be useful even when they are blocked by the native Pine runtime.
3. Imported logic is reviewed as a human-readable Horus rule spec before any test runs.
4. The backtester consumes structured Horus rules, not raw Pine and not raw AI prose.
5. Signal extraction, translation, validation, and backtesting stay separate so failures are explainable.
6. Uncertainty is surfaced honestly through warnings, unresolved references, and confidence markers.
7. The design leaves room for future MT4 and MT5 import work without coupling them into this first release.

## 4. Non-Goals

Phase 1 does not attempt to:

- support MT4 or MT5 import
- guarantee full TradingView parity
- execute full Pine order-management behavior
- import Pine sizing, risk management, partial exits, stop loss, or take profit logic
- auto-run imported logic without human review
- auto-promote imported logic into the live scanner
- replace the existing native Pine runtime path

## 5. Current State

Horus already has a Pine Lab foundation in:

- `core/pine_lab/parser.py`
- `core/pine_lab/executor.py`
- `routes/strategy.py`
- `frontend/src/app/optimization/components/PineLabPanel.tsx`

The current system is designed around a narrow Pine execution contract:

- preflight Pine scripts
- extract supported signal expressions when possible
- backtest compatible Pine logic on Horus market data
- create Pine-backed scanner profiles

That path is useful for supported scripts but is not the right seam for mixed real-world scripts that contain:

- visual overlays
- labels and tables
- alert blocks
- wrapper helpers
- unsupported Pine runtime semantics

As of 2026-04-04, running current preflight against `docs/ExProfit.pine` reports:

- `script_type = INDICATOR`
- no detected executable entries or exits
- `readiness = BLOCKED`
- blocked reasons tied to wrapped `request.security(...)` helper patterns and lookahead or repaint behavior

That result is honest for native Pine runtime support, but it still leaves potentially valuable signal logic trapped inside the script. This design addresses that gap.

## 6. Recommended Approach

Three approaches were considered.

### Option 1. Manual-assisted import

Horus scans the script, finds candidate variables such as `longE`, `shortE`, `longX`, and `shortX`, then asks the operator to map them into Horus fields before building a rule spec.

Pros:

- smallest implementation
- safest from a hallucination perspective
- works on messy scripts

Cons:

- too much operator effort for repeated strategy discovery
- slower when exploring many outside scripts

### Option 2. Hybrid extractor plus AI translator

Horus extracts likely signal logic and supporting definitions, builds a reduced source pack, sends only that pack to a constrained converter or AI, and receives a structured Horus rule spec for review.

Pros:

- best fit for the operator goal
- much less engineering than full Pine support
- scales better for repeated outside-strategy discovery
- still keeps the human review gate

Cons:

- requires strong validation and traceability
- needs confidence scoring and failure handling to stay trustworthy

### Option 3. Full Pine-to-Horus compiler

Expand Horus until it can translate most Pine scripts deterministically without any AI-assisted conversion.

Pros:

- deterministic once mature
- easier to audit at steady state

Cons:

- highest engineering cost
- slowest route to value
- still fragile against real-world mixed Pine scripts

### Recommendation

Use Option 2 with Option 1 as the fallback when confidence is low.

This keeps the workflow practical:

- outside Pine script
- logic extraction
- Horus rule spec generation
- operator review
- Horus-native backtest
- comparison against Horus core

## 7. Workflow And Boundaries

Phase 1 should introduce a new Pine Lab submode:

- `Native Pine Runtime`
- `Logic Import`

The existing runtime path remains unchanged.

The new `Logic Import` path should be recommended for:

- indicator scripts that embed signal booleans
- large mixed Pine files
- scripts blocked by unsupported runtime semantics but still readable at the signal level

The `Logic Import` workflow should be:

1. Paste Pine source.
2. Horus runs a lightweight structural scan to find candidate signal variables and supporting definitions.
3. Horus reduces the script into a signal-focused source pack.
4. Horus sends that reduced pack to a constrained translator.
5. Horus validates the returned rule spec.
6. Horus shows a human-readable review surface.
7. The operator approves or rejects the spec.
8. Only approved specs can run through Horus backtesting.

Phase 1 imports only signal logic:

- `long_entry`
- `short_entry`
- `long_exit`
- `short_exit`

Phase 1 explicitly ignores:

- order sizing
- stop loss
- take profit
- partial exits
- trailing logic
- plot and drawing behavior
- alert decoration
- style code

Horus applies its own testing environment after approval rather than pretending to import full platform behavior.

## 8. Core Components

The system should be split into five focused pieces.

### 8.1 Pine Signal Extractor

This component lives beside the current Pine tooling and is responsible for:

- identifying candidate signal outputs
- tracing dependencies needed to explain those outputs
- isolating only the definitions that matter for signal extraction

Typical candidate outputs include names such as:

- `longE`
- `shortE`
- `longX`
- `shortX`
- `buySignal`
- `sellSignal`
- similarly shaped boolean signal variables

The extractor should not try to prove Pine runtime compatibility. Its job is to find likely signal logic.

### 8.2 Reduced Source Pack Builder

This component converts the raw script into a compact translation package containing:

- candidate signal names
- dependent expressions
- referenced Pine inputs
- referenced indicator calls
- warnings about unresolved pieces
- ignored sections that were intentionally excluded

The reduced pack should remove noise such as:

- plots
- labels
- fills
- tables
- alerts
- styling blocks
- purely visual helper code

### 8.3 Horus Rule Spec Translator

This component calls a converter or AI with a strict schema and strict instructions.

Its job is to return:

- structured Horus signal rules
- human-readable explanations
- traceability back to the Pine source pack
- warnings when any mapping is approximate or incomplete

The translator should never return free-form prose as the primary artifact. The primary artifact is the rule spec.

### 8.4 Rule Spec Validator

This component validates the translator output before it becomes testable.

It should reject output that:

- invents variables or indicators not present in the reduced source pack
- omits required signal fields without explicitly marking them unresolved
- uses unsupported Horus operators
- breaks the rule spec schema
- claims high confidence despite unresolved dependencies

### 8.5 Review And Approval Surface

This component presents the spec for operator review in a format that is both readable and auditable.

It should show:

- long entry explanation
- short entry explanation
- long exit explanation
- short exit explanation
- parameters carried from Pine inputs
- ignored sections
- unresolved references
- warnings
- confidence
- ready or not-ready status for Horus backtesting

No spec should move into backtesting without explicit operator approval.

## 9. UI Design

The UI should extend the existing Pine Lab rather than creating an unrelated import page.

### 9.1 Pine Lab submode switch

Add a submode switch inside the Pine area:

- `Native Pine Runtime`
- `Logic Import`

This preserves the current runtime workflow while making the new import workflow discoverable.

### 9.2 Logic Import actions

The import flow should use a simple staged interface:

1. `Extract Rule Spec`
2. `Review / Edit`
3. `Approve And Backtest`
4. `Save As Horus Profile` in a later increment

### 9.3 Review layout

The review surface should clearly separate:

- imported rule summary
- machine-readable rule structure
- original Pine traceability
- ignored Pine sections
- confidence and warnings
- backtest readiness

The operator should be able to understand what Horus believes the script means without reading raw JSON.

## 10. Backend API Contract

This workflow should use dedicated import endpoints instead of overloading the current native Pine preflight route.

### 10.1 Import preview

- `POST /api/v1/strategy/pine/import-preview`

Input:

- Pine source
- market
- timeframe
- date range

Output:

- reduced source pack summary
- generated Horus rule spec
- confidence and warnings
- ignored sections
- traceability back to Pine variables and lines
- readiness for manual review

### 10.2 Import backtest

- `POST /api/v1/strategy/pine/import-backtest`

Input:

- approved Horus rule spec
- market
- timeframe
- date range
- capital
- commission
- slippage

Output:

- Horus-native backtest summary
- trade log
- equity curve
- comparison metrics versus Horus core
- import metadata and warnings carried forward

### 10.3 Import profile later

- `POST /api/v1/strategy/pine/import-profile`

This later endpoint should persist an approved imported rule spec as a reusable Horus profile.

## 11. Rule Spec Contract

The generated rule spec should be both readable and executable.

Suggested top-level structure:

```json
{
  "source": {},
  "parameters": [],
  "indicators": [],
  "signals": {
    "long_entry": {},
    "short_entry": {},
    "long_exit": {},
    "short_exit": {}
  },
  "human_summary": {},
  "traceability": [],
  "ignored_sections": [],
  "warnings": [],
  "confidence": {}
}
```

The fields should mean:

- `source`
  Original script hash, source type, import timestamp, and import mode.

- `parameters`
  Pine inputs that materially affect the extracted signals.

- `indicators`
  Normalized indicator formulas Horus will use for evaluation.

- `signals`
  The machine-readable Horus expressions for entries and exits.

- `human_summary`
  Plain-English explanation of what each imported signal means.

- `traceability`
  Mapping back to Pine variable names, expressions, and line references.

- `ignored_sections`
  Things intentionally excluded from phase 1 import.

- `warnings`
  Unresolved references, approximations, unsupported fragments, and low-confidence mappings.

- `confidence`
  Overall confidence and per-signal confidence.

The backtester must consume the structured spec rather than:

- the original Pine source
- raw AI output
- human summary text

This creates a stable approval boundary between translation and testing.

## 12. Comparison With Horus Core

The imported logic should be testable using the same Horus market context and cost assumptions used elsewhere in Pine Lab or related strategy workflows.

The comparison surface should show at least:

- imported strategy total return
- imported strategy max drawdown
- imported strategy win rate
- imported strategy trade count
- imported strategy quality metric
- Horus core comparison metrics over the same market and time window
- operator-visible statement of which logic won on which dimensions

The comparison goal is not to prove the imported logic is universally better.

The comparison goal is to make outside-strategy research visible and fair inside Horus.

## 13. Safeguards And Error Handling

The import workflow should be strict about uncertainty.

### 13.1 Safeguards

If extraction confidence is low, Horus may still show a draft spec, but it should:

- mark the result as `Needs Manual Review`
- block backtest approval until the operator explicitly confirms it

If the translator cannot map a condition cleanly, Horus should:

- preserve the original Pine expression in the review output
- avoid inventing a clean-looking Horus equivalent

If a script contains unsupported runtime features that are irrelevant to the extracted signals, Horus should:

- list them under `ignored_sections`
- continue when signal extraction is still possible

If no usable entry or exit signals can be isolated, Horus should fail explicitly with:

- `No executable signal logic extracted`

### 13.2 Error handling

Extractor errors should show:

- candidate variables found
- where dependency tracing stopped
- what references remain unresolved

Translator errors should show:

- the reduced source pack that was sent
- the missing or invalid output field

Validation errors should show:

- schema violations
- invented references
- unsupported Horus operators
- broken traceability

Backtest gate errors should show:

- the exact rule or indicator that prevented execution

## 14. Testing Strategy

This phase should be covered by four layers of tests.

### 14.1 Extractor tests

Given Pine snippets, verify:

- candidate signal detection
- dependency tracing
- ignored visual-only sections

### 14.2 Reduced source pack tests

Verify:

- plots, labels, fills, and alerts are excluded
- signal dependencies remain intact
- relevant inputs and indicator calls are preserved

### 14.3 Spec validation tests

Verify invalid translator output is rejected for:

- invented variables
- missing signal fields
- unsupported operators
- invalid schema
- broken traceability

### 14.4 End-to-end import tests

Use real scripts, including `docs/ExProfit.pine`, and verify Horus can:

- generate a reviewable rule spec
- surface warnings honestly
- require approval before backtesting
- run approved specs through Horus-native testing
- compare imported logic against Horus core

## 15. Rollout Plan

This work should ship in three stages.

### Stage 1. Import preview only

Deliver:

- extractor
- reduced source pack
- translator
- validator
- review surface

Do not enable backtesting yet.

### Stage 2. Approved-spec backtesting

Allow reviewed and approved specs to run through Horus-native backtests and comparison views.

### Stage 3. Saved imported profiles

Allow strong imported specs to be persisted as reusable Horus profiles.

Promotion into live scanner behavior should remain explicit and operator-controlled.

## 16. Risks And Trade-Offs

The main trade-off in this design is choosing an honest import workflow over fake Pine compatibility.

This means:

- some scripts will still fail import
- some mappings will remain low confidence
- some results will require manual correction

That is acceptable in phase 1 because the real value is:

- extracting useful outside logic faster
- testing it fairly in Horus
- keeping the review boundary explicit

The design should optimize for truthfulness and operator trust over automation theater.
