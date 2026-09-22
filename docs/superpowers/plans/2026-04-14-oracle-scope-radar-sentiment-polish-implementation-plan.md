# Oracle Scope Radar And Sentiment Polish Implementation Plan

Date: 2026-04-14
Based on:

- `docs/superpowers/specs/2026-04-14-oracle-scope-radar-sentiment-polish-design.md`
- `core/ai_report/asset.py`
- `routes/ai_report.py`
- `tests/test_ai_asset_report.py`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/page.test.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SupportResistanceRadar.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SentimentTimeline.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`

Track: Oracle Scope Hybrid Tactical Panels
Status: Planned
Owner model: Single owner

## 1. Planning Goal

Implement the approved Oracle scope-polish pass so Horus:

1. renders meaningful lower Oracle panels for `EGX30`, `EGX70`, `EGX100`, and `UNIVERSE`
2. keeps a concrete lead ticker anchor in broad-scope Oracle views
3. stops showing broken-looking scope placeholders like `0.00` radar anchors and low-signal empty narrative panels
4. preserves existing single-ticker deep-scan behavior
5. verifies the hybrid scope contract with focused backend and frontend tests

## 2. In Scope

Primary implementation targets:

- scope-aware asset-report payload enrichment
- lead-ticker resolution for broad Oracle scopes
- clustered support/resistance payload generation for basket scopes
- split basket-plus-lead-ticker sentiment payload generation
- hybrid radar rendering in Oracle
- split sentiment rendering in Oracle
- focused regression coverage for backend and Oracle frontend behavior

Primary files expected to move:

- `core/ai_report/asset.py`
- `routes/ai_report.py`
- `tests/test_ai_asset_report.py`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/page.test.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SupportResistanceRadar.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SentimentTimeline.tsx`
- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`

Out of scope for this slice:

- redesigning the overall Oracle page layout
- replacing the Oracle asset selector or broadening its option set
- changing the main AI report LLM contract beyond additive scope fields
- introducing charting dependencies or a new visualization framework
- redesigning archive browsing or Oracle rail telemetry

## 3. Execution Rules

These rules apply across the slice:

1. Treat the backend asset snapshot as the source of truth; the frontend should render explicit scope payloads rather than infer broad-scope meaning from sparse ticker fields.
2. Preserve direct single-ticker Oracle behavior unless the approved scope-hybrid design explicitly changes it.
3. Keep new scope payload fields additive and backward compatible with existing stored asset reports.
4. Prefer truthful reduced-data states over decorative filler when scope clustering or lead-ticker data is insufficient.
5. Write or update focused tests before landing production changes that alter the scope data contract or Oracle sub-panel rendering.

## 4. Work Package Sequence

Execute in this order:

1. `OSRP-P1` Backend scope snapshot enrichment
2. `OSRP-P2` Hybrid radar rendering
3. `OSRP-P3` Split sentiment rendering
4. `OSRP-P4` Oracle page integration and regression lock

This order is intentional:

- the frontend hybrid panels need an explicit backend payload before they can render deterministically
- the radar and sentiment panels should be implemented independently against the new payload contract
- page integration should happen after both panels can render their intended states

## 5. Work Packages

### OSRP-P1. Backend Scope Snapshot Enrichment

Purpose:

Extend the Oracle asset-report snapshot so broad-scope views expose basket zones, a lead ticker, and split narrative data without breaking single-ticker payloads.

Target files:

- `core/ai_report/asset.py`
- `routes/ai_report.py`
- `tests/test_ai_asset_report.py`

Tasks:

1. Add scope-aware helpers for:
   - lead ticker selection
   - support cluster derivation
   - resistance cluster derivation
   - basket vs lead-ticker news partitioning
2. Extend broad-scope snapshots to return additive fields:
   - `scope`
   - `lead_ticker`
   - `scope_levels`
   - `lead_ticker_levels`
   - `scope_news_mentions`
   - `lead_ticker_news_mentions`
3. Keep single-ticker snapshots valid by:
   - preserving current top-level fields
   - returning new scope fields only when appropriate
4. Normalize `UNIVERSE` to `ALL` at the backend seam while keeping stored payloads consistent.
5. Keep legacy report-refresh behavior intact for old placeholder scope payloads if the existing refresh guard needs to consider the new fields.

Deliverables:

- enriched asset-report payload for broad Oracle scopes
- deterministic lead-ticker selection contract
- clustered support/resistance payloads for scope views
- split narrative payloads for scope and lead ticker

Verification:

- `.\.venv313\Scripts\python.exe -m pytest tests/test_ai_asset_report.py -q`

Acceptance criteria:

- `EGX30`, `EGX70`, `EGX100`, and `ALL` snapshots expose lead-ticker metadata and scope-level tactical data
- single-ticker snapshots still behave as direct deep scans
- asset-report tests cover both scope and single-name payload paths

### OSRP-P2. Hybrid Radar Rendering

Purpose:

Upgrade the Oracle S/R radar so broad scopes render basket-level zones plus one concrete lead ticker anchor instead of collapsing into `0.00` or empty states.

Target files:

- `frontend/src/app/oracle/components/tac-briefing/SupportResistanceRadar.tsx`
- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/page.test.tsx`

Tasks:

1. Extend the radar component to support two rendering modes:
   - single-ticker mode
   - scope-hybrid mode
2. In scope-hybrid mode, render:
   - basket support cluster lines
   - basket resistance cluster lines
   - a highlighted lead ticker anchor
   - legend labels that distinguish basket vs lead-ticker semantics
3. Add a truthful calibration state for broad scopes when level density is insufficient.
4. Update Oracle page wiring to pass explicit scope-level radar props from the report snapshot instead of relying only on `entry`, `stop`, and `target`.

Deliverables:

- hybrid scope radar renderer
- explicit Oracle page wiring for scope-level tactical levels
- non-broken reduced-data state for insufficient scope levels

Verification:

- `npm --prefix frontend test -- --runInBand src/app/oracle/page.test.tsx`

Acceptance criteria:

- broad-scope Oracle views no longer show `0.00`-style radar anchors when valid scope data exists
- single-name Oracle views still render direct ticker levels
- reduced-data states read as intentional calibration messages, not broken charts

### OSRP-P3. Split Sentiment Rendering

Purpose:

Render basket-level narrative hits first and lead-ticker narrative highlights second so Oracle scope sentiment is both market-aware and executable.

Target files:

- `frontend/src/app/oracle/components/tac-briefing/SentimentTimeline.tsx`
- `frontend/src/app/oracle/components/tac-briefing/SentimentTimeline.test.tsx`
- `frontend/src/app/oracle/page.tsx`

Tasks:

1. Extend `SentimentTimeline` to accept split input groups:
   - basket narrative hits
   - lead ticker focus hits
2. Keep the aggregate score and regime basket-level in scope mode.
3. Render clear section labels for:
   - `Scope Narrative`
   - `Lead Ticker Focus`
4. Collapse the lead-ticker section cleanly when no lead-ticker hits exist.
5. Preserve current single-name rendering when Oracle is focused on a direct ticker.

Deliverables:

- split sentiment panel for broad Oracle scopes
- single-name-compatible sentiment renderer
- regression coverage for split and single-name modes

Verification:

- `npm --prefix frontend test -- --runInBand src/app/oracle/components/tac-briefing/SentimentTimeline.test.tsx src/app/oracle/page.test.tsx`

Acceptance criteria:

- basket-level sentiment stays primary in broad-scope mode
- lead-ticker narrative renders as a secondary tactical section when available
- single-ticker Oracle sentiment behavior remains intact

### OSRP-P4. Oracle Page Integration And Regression Lock

Purpose:

Lock the new Oracle scope contract in page-level integration tests and ensure the header, AI briefing, radar, and sentiment panels read the same scope truth.

Target files:

- `frontend/src/app/oracle/page.tsx`
- `frontend/src/app/oracle/page.test.tsx`
- `frontend/src/app/oracle/components/OracleShell.tsx`
- `frontend/src/app/oracle/components/OracleAiReportPanel.tsx`

Tasks:

1. Align page copy and panel titles with scope-aware payload fields so broad scopes read as broad scopes and lead tickers read as lead tickers.
2. Ensure Oracle page integration uses the additive payload fields from `asset.py` instead of ad hoc frontend-only fallback assumptions.
3. Add or update tests for:
   - broad-scope Oracle render path
   - lead-ticker-enhanced radar render path
   - split sentiment render path
   - preserved single-ticker deep scan path

Deliverables:

- Oracle page integration that consumes the new scope payload contract consistently
- focused regression suite covering scope vs single-name Oracle behavior

Verification:

- `npm --prefix frontend test -- --runInBand src/app/oracle/page.test.tsx src/app/oracle/components/OracleShell.test.tsx src/app/oracle/components/OracleAiReportPanel.test.tsx`

Acceptance criteria:

- Oracle scope views render coherent hybrid tactical panels
- header and sub-panels stay consistent about scope and lead ticker
- direct ticker views continue to behave like single-name analysis

## 6. Risks and Controls

Risk: scope clustering creates false precision from thin recommendation data.
Control: require a minimum level count for cluster rendering and fall back to an explicit calibration state when density is too low.

Risk: lead ticker changes too often between refreshes and makes scope views feel unstable.
Control: choose the lead ticker using a stable priority order and keep the selection logic centralized in `asset.py`.

Risk: frontend rendering starts inferring missing scope structure again.
Control: keep the new payload fields explicit and make page wiring consume those fields directly.

Risk: split sentiment sections add clutter when the scope has little news.
Control: collapse empty subsections and keep reduced-data copy concise and intentional.

## 7. Recommended Execution Notes

- Keep scope-level tactical heuristics in `core/ai_report/asset.py` rather than scattering cluster-building across route and frontend seams.
- Reuse the existing Oracle scope normalization path so `UNIVERSE` and `ALL` do not drift.
- Prefer additive snapshot changes over changing existing field semantics; this minimizes migration risk for stored reports.

## 8. Recommended Next Move After This Plan

Start with `OSRP-P1`: extend `core/ai_report/asset.py` so broad Oracle scopes emit explicit `lead_ticker`, `scope_levels`, `lead_ticker_levels`, `scope_news_mentions`, and `lead_ticker_news_mentions` fields, then lock that payload with `tests/test_ai_asset_report.py`. After that, implement `OSRP-P2` and `OSRP-P3` against the stabilized payload contract and finish with `OSRP-P4` page-level regression coverage.
