# Oracle Scope Radar And Sentiment Polish Design

## Summary

This design upgrades Oracle's broad-scope experience for `EGX30`, `EGX70`, `EGX100`, and `UNIVERSE` so the lower tactical panels stay meaningful when the selected asset is a basket rather than a single ticker.

Today, Oracle can switch the selected asset scope, but the downstream radar and sentiment panels still behave like single-name widgets. That causes empty or low-signal states such as `0.00` radar anchors, missing tactical levels, and generic narrative fallbacks. The goal of this pass is to make scope-level Oracle views feel intentional and decision-ready.

## Problem

For basket scopes:

- The S/R radar expects one concrete asset with a single `entry`, `stop`, and `target`.
- The sentiment panel expects a narrow list of direct ticker hits.
- The result is a degraded UI even when the selected market scope contains valid recommendations, whale flow, traps, and news.

This creates a misleading experience:

- The Oracle header says the selected scope is valid.
- The AI report can produce a scope-level verdict.
- The sub-panels below imply that no tactical detail exists.

## Goals

- Make `EGX30`, `EGX70`, `EGX100`, and `UNIVERSE` render rich Oracle tactical panels.
- Keep a concrete trading anchor visible even in broad-scope mode.
- Preserve direct single-ticker deep scans without diluting them.
- Avoid fake precision or decorative filler.

## Non-Goals

- Rebuild the Oracle page layout.
- Introduce a charting library or complex live plotting.
- Change the main AI briefing contract beyond the fields needed for richer sub-panels.
- Replace single-name Oracle behavior.

## Recommended Approach

Use a hybrid scope model:

- Basket-level tactical zones provide the market-wide map.
- One lead ticker provides the concrete execution anchor.
- Basket headlines remain primary in sentiment.
- Lead-ticker headlines are highlighted as a secondary tactical layer.

This keeps the scope view truthful and actionable at the same time.

## UX Design

### 1. Scope-Aware Radar

For broad scopes, the radar will no longer render only one price point and two lines.

Instead it will show:

- basket support clusters derived from the strongest active recommendations in the selected scope
- basket resistance clusters derived from the strongest active recommendations in the selected scope
- a highlighted lead ticker anchor chosen from the highest-confidence active recommendation in the scope
- clear labeling for the lead ticker so the user knows which name the execution anchor comes from

The visual model:

- outer lines and labels represent cluster zones
- the center anchor represents the lead ticker's current tactical reference
- the legend distinguishes `BASKET SUPPORT`, `BASKET RESISTANCE`, and `LEAD TICKER`

If the scope lacks enough tactical inputs, the radar should show a truthful calibration state such as:

`Insufficient level density for scope radar. Waiting for stronger tactical clustering.`

### 2. Scope-Aware Sentiment Narrative

For broad scopes, the sentiment panel will render in two layers:

- primary layer: basket narrative hits ranked by score and relevance to the selected scope
- secondary layer: highlighted lead-ticker hits for the chosen execution anchor

The sentiment header remains basket-level:

- aggregate score
- regime
- narrative sweep

Below that, the panel should visually separate:

- `Scope Narrative`
- `Lead Ticker Focus`

If only basket news exists, the lead-ticker section collapses.
If only lead-ticker news exists, the basket section still shows the aggregate regime with a reduced-hit note.

### 3. Single-Ticker Preservation

When Oracle is focused on a real ticker such as `COMI`:

- radar remains single-name
- sentiment remains single-name
- no basket cluster framing appears

This avoids making direct deep scans feel less precise.

## Data Design

### Scope Snapshot Additions

The asset-report snapshot should expose enough structure for Oracle's sub-panels to render without guessing:

- `scope`
- `lead_ticker`
- `scope_levels`
- `lead_ticker_levels`
- `scope_news_mentions`
- `lead_ticker_news_mentions`

Suggested shape:

```json
{
  "scope": "EGX70",
  "lead_ticker": "COMI",
  "scope_levels": {
    "supports": [
      { "price": 79.0, "strength": 0.82, "label": "cluster_1", "members": 3 }
    ],
    "resistances": [
      { "price": 89.0, "strength": 0.86, "label": "cluster_1", "members": 4 }
    ]
  },
  "lead_ticker_levels": {
    "ticker": "COMI",
    "entry": 82.5,
    "stop": 79.0,
    "target": 89.0
  },
  "scope_news_mentions": [],
  "lead_ticker_news_mentions": []
}
```

### Lead Ticker Selection

For broad scopes, select the lead ticker using:

1. highest active recommendation confidence
2. highest active recommendation score
3. most complete tactical level set

This gives Oracle one stable focal point for execution context.

### Scope Level Clustering

Broad-scope levels should be derived from active recommendations in the chosen basket:

- collect valid `entry`, `stop`, `target` values
- group near prices into support and resistance clusters
- rank clusters by count and average confidence
- return only the top few clusters to avoid visual noise

This is intentionally heuristic, not a full market-profile engine.

## Component Changes

### Backend

- Extend `core/ai_report/asset.py` to compute scope-level cluster zones and lead ticker metadata.
- Normalize `UNIVERSE` to `ALL` at the snapshot boundary while preserving user-facing labels in the frontend.
- Keep stored asset reports backward compatible by treating the new fields as additive.

### Frontend

- Update `SupportResistanceRadar.tsx` to support two rendering modes:
  - single-ticker mode
  - scope-hybrid mode
- Update `SentimentTimeline.tsx` to accept basket hits and lead-ticker hits separately.
- Update `frontend/src/app/oracle/page.tsx` to pass scope-aware props from the report payload rather than inferring from sparse recommendation data.

## Error Handling

- If scope-level clustering is unavailable, show a scoped calibration message rather than `0.00`.
- If basket narrative hits are empty, keep the aggregate regime but show a reduced-hit notice.
- If lead ticker resolution fails, render basket view only and suppress the lead-ticker section.

## Testing

Add focused coverage for:

- scope-level asset-report generation returns `lead_ticker` and clustered scope levels
- `EGX30`, `EGX70`, `EGX100`, and `ALL` normalize correctly
- Oracle page renders the scope selector and hybrid radar path
- sentiment panel renders basket hits first and lead-ticker highlights second
- single-name Oracle behavior remains unchanged

## Acceptance Criteria

- Oracle no longer shows `0.00` or empty-looking radar states for valid basket scopes.
- Scope-level sentiment no longer collapses into generic placeholder messaging when relevant basket news exists.
- `EGX30`, `EGX70`, `EGX100`, and `UNIVERSE` produce meaningful Oracle tactical context.
- Direct ticker deep scans still behave like single-name analysis.

## Risks

- Over-clustering can create false precision if the input recommendations are thin.
- Basket-level news relevance may be uneven if stories mention constituents inconsistently.
- Lead ticker instability may feel noisy if the selection changes too often between refreshes.

## Recommendation

Implement this as a focused Oracle sub-panel enhancement, not a page redesign.

The highest-value slice is:

1. backend scope payload enrichment
2. hybrid radar rendering
3. split sentiment rendering

That sequence fixes the broken perception first, then improves tactical readability.
