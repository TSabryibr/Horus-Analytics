# Phase 21 Design Spec: News Decomposition

Date: 2026-03-19
Status: Amended
Scope: `frontend/src/app/news/NewsClient.tsx`
Objective: Decompose the monolithic `NewsClient` into a thin shell, a runtime hook, pure transforms, and focused presentational components.

## 1. Current State

### Route structure (already split)

`page.tsx` (11 lines) is already a **Server Component shell** that wraps `<GlobalDataProvider><NewsClient /></GlobalDataProvider>`. It has its own route-level regression test (`page.route.test.tsx`, 1 test). This file is **not touched** by this phase.

### `NewsClient.tsx` (155 lines) — decomposition target

The file mixes five concerns:

| Concern | Lines | Notes |
|---|---|---|
| Context consumption | L3-9 | `useNewsData()` from `GlobalDataContext` |
| Pure class helpers | L11-15, L28-32 | `getSentimentColor`, `getBifrostRegimeClass` |
| JSX icon helper | L17-21 | `getSentimentIcon` — returns React elements |
| Bifrost score normalization | L23-26 | `Number(newsSentiment?.score ?? 50)` etc. |
| Progress-bar color logic | L76-77 | Ternary selecting `bg-amber-400 / bg-rose-400 / bg-slate-400` |
| Header rendering | L37-54 | Title, subtitle, and refresh button |
| Sentiment panel rendering | L57-94 | Score bar, regime badge, Greed/Fear hits |
| News card grid rendering | L97-151 | Loading state, card grid with source/score/tickers/link |

### Existing test surface

| File | Tests | Mock target |
|---|---|---|
| `page.test.tsx` | 7 tests | Mocks `useNewsData` from `GlobalDataContext` |
| `page.route.test.tsx` | 1 test | Mocks `GlobalDataProvider` and `NewsClient` |

> [!IMPORTANT]
> The 7 tests in `page.test.tsx` import and render `NewsClient` directly, mocking `useNewsData()`. If we introduce a `useNewsRuntime` hook that wraps `useNewsData`, the existing tests continue to work **only if `useNewsRuntime` internally calls `useNewsData`** — the test mock path stays the same. No mock-path migration is required.

## 2. Target Architecture

```
news/
├── page.tsx                  ← UNCHANGED (Server Component shell)
├── page.test.tsx             ← UNCHANGED (regression)
├── page.route.test.tsx       ← UNCHANGED (regression)
├── NewsClient.tsx            ← SLIMMED to ~30 lines (composition only)
├── hooks/
│   └── useNewsRuntime.ts     ← NEW: context proxy + Bifrost normalization
├── lib/
│   └── newsTransforms.ts     ← NEW: pure class/string helpers
└── components/
    ├── NewsShell.tsx          ← NEW: header + refresh + page-shell wrapper
    ├── NewsSentimentPanel.tsx ← NEW: Bifrost score/regime/hits visualization
    └── NewsCard.tsx           ← NEW: individual news item card
```

### Dropped from original plan: `NewsGrid.tsx`

The grid is a single `<div className="grid ...">` wrapper with a loading ternary. This has near-zero standalone value — keeping the grid layout and loading branch inline in `NewsClient.tsx` composition is simpler and avoids a low-value file.

## 3. Component Responsibilities

### 3.1 `lib/newsTransforms.ts` (Pure helpers)

| Function | Input → Output | Notes |
|---|---|---|
| `getSentimentColor(score: number)` | → Tailwind class string | Pure, no JSX |
| `getBifrostRegimeClass(regime: string)` | → Tailwind class string | Pure, no JSX |
| `getBifrostBarColor(score: number)` | → Tailwind class string | Extracted from L76-77 |
| `formatSentimentScore(score: number)` | → formatted string like `"+3"` or `"-2"` | Extracted from L112 inline logic |

> [!NOTE]
> `getSentimentIcon` returns React elements (JSX), so it **stays as a component-level helper** inside `NewsCard.tsx`, not in the pure transforms file.

### 3.2 `hooks/useNewsRuntime.ts`

- Calls `useNewsData()` from `GlobalDataContext` (preserving the mock path for existing tests).
- Normalizes raw sentiment into typed computed values:
  - `bifrostScore: number` (from `Number(newsSentiment?.score ?? 50)`)
  - `bifrostRegime: string` (from `newsSentiment?.regime ?? "BORING MORTALS"`)
  - `bifrostBull: number` (from `Number(newsSentiment?.bull_count ?? 0)`)
  - `bifrostBear: number` (from `Number(newsSentiment?.bear_count ?? 0)`)
- Exposes: `{ news, isLoading, onRefresh, bifrostScore, bifrostRegime, bifrostBull, bifrostBear }`

### 3.3 `components/NewsShell.tsx`

- Props: `loading, onRefresh, children`
- Renders: `<div className="page-shell">`, the header (`Scroll` icon, title, subtitle), and the refresh `<button>`.
- Wraps `{children}` for content composition.

### 3.4 `components/NewsSentimentPanel.tsx`

- Props: `score, regime, regimeClass, barColorClass, bullHits, bearHits`
- Renders: The full "News Sentiment Analyzer / Greed vs Fear" card with score bar and hit counters.
- Uses pure transform outputs via props (no internal logic).

### 3.5 `components/NewsCard.tsx`

- Props: `source, title, summary, link, tickers, gossipScore`
- Contains `getSentimentIcon` as a local helper (returns JSX).
- Uses `getSentimentColor` from transforms for the score badge.
- Renders: Source badge, score badge, title, summary, ticker pills, and external link.

## 4. Verification Strategy

### Regression safety
- All 7 tests in `page.test.tsx` pass unchanged against the refactored `NewsClient`.
- The 1 test in `page.route.test.tsx` passes unchanged (it mocks `NewsClient` entirely).
- Mock path is preserved: tests mock `useNewsData` from `GlobalDataContext`, and `useNewsRuntime` wraps that hook internally.

### New unit tests
- `hooks/useNewsRuntime.test.tsx`: Verify Bifrost normalization (null sentiment → defaults, valid data → computed values).
- `lib/newsTransforms.test.ts`: Verify all pure helpers return correct class strings for boundary inputs.
- `components/NewsShell.test.tsx`: Verify header rendering, refresh callback, and loading state.
- `components/NewsSentimentPanel.test.tsx`: Verify score display, regime badge, and hit counters.
- `components/NewsCard.test.tsx`: Verify source, title, tickers, external link, and sentiment icon/color.

### Full suite gate
- `npm --prefix frontend run test -- --runInBand` must remain green (target: 424+ tests).
