# Phase 21 Implementation Plan: News Decomposition

Date: 2026-03-19
Based on: `docs/superpowers/specs/2026-03-19-phase-21-news-decomposition-design.md`

## Objective

Decompose `NewsClient.tsx` (155 lines) into a thin composition shell backed by `useNewsRuntime`, `newsTransforms`, and three focused presentational components (`NewsShell`, `NewsSentimentPanel`, `NewsCard`).

> [!IMPORTANT]
> `page.tsx` is already a Server Component shell — it is **not touched**. The decomposition target is `NewsClient.tsx` only.

## Proposed Changes

### Transforms & Runtime

#### [NEW] [newsTransforms.ts](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/news/lib/newsTransforms.ts)
- `getSentimentColor(score)` — returns Tailwind class string for score badges
- `getBifrostRegimeClass(regime)` — returns Tailwind class string for regime badges
- `getBifrostBarColor(score)` — returns progress-bar background class
- `formatSentimentScore(score)` — returns formatted score string with sign prefix

#### [NEW] [useNewsRuntime.ts](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/news/hooks/useNewsRuntime.ts)
- Wraps `useNewsData()` from `GlobalDataContext` (preserving existing test mock path)
- Normalizes raw sentiment into typed fields: `bifrostScore`, `bifrostRegime`, `bifrostBull`, `bifrostBear`
- Exposes `{ news, isLoading, onRefresh, bifrostScore, bifrostRegime, bifrostBull, bifrostBear }`

---

### Presentational Components

#### [NEW] [NewsShell.tsx](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/news/components/NewsShell.tsx)
- Props: `loading`, `onRefresh`, `children`
- Renders: `page-shell` wrapper, header with `Scroll` icon, title, subtitle, refresh button

#### [NEW] [NewsSentimentPanel.tsx](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/news/components/NewsSentimentPanel.tsx)
- Props: `score`, `regime`, `regimeClass`, `barColorClass`, `bullHits`, `bearHits`
- Renders: Score bar, regime badge, Greed/Fear hit counters

#### [NEW] [NewsCard.tsx](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/news/components/NewsCard.tsx)
- Props: `source`, `title`, `summary`, `link`, `tickers`, `gossipScore`
- Contains `getSentimentIcon` locally (returns JSX — can't live in pure transforms)
- Uses `getSentimentColor` from transforms for score badge styling

---

### Composition Shell

#### [MODIFY] [NewsClient.tsx](file:///c:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/news/NewsClient.tsx)
- Slimmed to ~30 lines: calls `useNewsRuntime`, wires transforms, composes `NewsShell` > `NewsSentimentPanel` + card grid

## Verification Plan

### Regression (existing — must stay green)
- `page.test.tsx` (7 tests) — imports `NewsClient` directly, mocks `useNewsData`
- `page.route.test.tsx` (1 test) — mocks `GlobalDataProvider` and `NewsClient`

### New unit tests
- `useNewsRuntime.test.tsx` — Bifrost normalization, null-sentiment defaults
- `newsTransforms.test.ts` — boundary-value checks for all pure helpers
- `NewsShell.test.tsx` — header rendering, refresh callback, loading state
- `NewsSentimentPanel.test.tsx` — score display, regime badge, counters
- `NewsCard.test.tsx` — source, title, tickers, link, sentiment coloring

### Full suite gate
- `npm --prefix frontend run test -- --runInBand` (target: 424+ tests passing)
