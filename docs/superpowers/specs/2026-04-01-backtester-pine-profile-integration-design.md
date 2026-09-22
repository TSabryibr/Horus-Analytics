# Backtester Pine Profile Integration Design

Date: 2026-04-01
Status: Approved design

## Summary

The Optimization `Backtester` should support two backtest sources:

- `Horus Strategy`
- `Pine Profile`

This keeps the current Horus simulator flow intact while allowing saved Pine scanner profiles to be backtested from the same screen. Pine profile logic stays read-only in Backtester mode, while run settings such as market, date range, capital, commission, and slippage remain editable for the current run.

## Goals

- Reuse saved Pine profiles from Pine Lab in the Backtester.
- Preserve the existing Horus Backtester behavior without regressions.
- Allow all Pine profile states (`DRAFT`, `READY`, `ACTIVE`) to be selected for research.
- Show an explicit warning when a `DRAFT` profile is being backtested.
- Keep Backtester focused on research and execution, not profile management.

## Non-Goals

- Editing Pine script source from the Backtester.
- Activating or promoting Pine profiles from the Backtester.
- Replacing the existing Horus simulator flow.
- Merging Backtester and Pine Lab into one surface.

## Product Decisions

### Backtest Source

Backtester gets a source switch:

- `Horus Strategy`
- `Pine Profile`

`Horus Strategy` mode continues to use the existing native Horus parameterized simulator.

`Pine Profile` mode uses a selected saved Pine profile as the strategy logic source.

### Pine Logic Ownership

When `Pine Profile` mode is active:

- The saved profile provides the strategy logic only.
- The script is read-only in Backtester mode.
- Run settings remain editable for the current backtest session.

Editable run settings:

- market
- date range
- capital
- commission
- slippage

### Profile Eligibility

All Pine profiles can be selected:

- `DRAFT`
- `READY`
- `ACTIVE`

This keeps Backtester useful as a research surface rather than only a production-ready surface.

### Draft Profile Behavior

If the selected profile is `DRAFT`:

- show a visible amber warning banner
- allow the backtest to run
- do not require confirmation

## UX Design

## BacktestLabPanel changes

The existing [BacktestLabPanel](C:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/optimization/components/BacktestLabPanel.tsx) evolves into a dual-source control surface.

### New controls

Add a `Backtest Source` selector near the top of the panel:

- `Horus Strategy`
- `Pine Profile`

### Horus Strategy mode

Show the existing controls as-is:

- market universe selector
- Horus parameter sliders
- trailing-stop configuration
- `Init_Backtest`

### Pine Profile mode

Show:

- Pine profile selector
- selected profile state badge
- profile market/timeframe context
- warning banner for `DRAFT`
- editable run settings for the current backtest

Hide or disable Horus-only parameter sliders while Pine mode is active.

### Result labeling

When the current backtest source is Pine:

- show `Backtest Source: Pine Profile`
- show selected profile name
- show selected profile state

This should appear in the result area so the user can clearly see which engine produced the result.

## Data Flow

### Frontend

Extend [useBacktestLab](C:/Users/TSabr/Horus/Horus-Analytics-II/frontend/src/app/optimization/hooks/useBacktestLab.ts) with:

- `backtestSource: 'HORUS' | 'PINE_PROFILE'`
- `selectedPineProfileId`
- Pine profile registry loading for Backtester mode
- Pine run configuration fields

The hook becomes responsible for:

- switching between Horus and Pine execution paths
- loading the Pine profile registry
- validating Pine selection before run
- preserving existing Horus validation logic

### Pine registry loading

Reuse the existing Pine profile list endpoint:

- `GET /api/v1/strategy/pine/scanner-profiles`

Backtester mode should show all returned profiles.

The selector should expose enough context to distinguish profiles quickly:

- profile name
- profile state
- market
- timeframe
- optionally combined score as secondary context

### Execution routing

#### Horus Strategy mode

Continue using:

- `POST /api/v1/strategy/backtest`

#### Pine Profile mode

Use:

- `POST /api/v1/strategy/pine/backtest`

The frontend passes:

- selected profile script source
- editable run settings from the Backtester session

If the profile list payload already includes script source, the Backtester can use it directly.
If not, add the minimal profile-fetch capability needed to load the selected script source without broadening the payload unnecessarily.

## Backend impact

Preferred approach:

- reuse existing endpoints
- avoid creating a new dedicated Backtester-specific Pine endpoint

Possible backend adjustments only if required:

- expose script source for Backtester-selected Pine profiles
- or add a targeted profile fetch endpoint

The Pine backtest route remains the execution engine for Pine profile runs.

## States and Warnings

### No Pine profile selected

If `Pine Profile` mode is active and no profile is selected:

- disable `Init_Backtest`
- show a clear inline explanation

### Draft profile selected

If selected profile state is `DRAFT`:

- show amber warning banner
- example copy:
  - `Draft profile: this Pine strategy has not passed promotion gates yet.`
- still allow execution

### Ready or active profile selected

Show a quieter informational state instead of warning.

### Pine backtest failure

Use the same error-banner style already used by Backtester.

## Testing Strategy

### Frontend tests

Add coverage for:

- Backtest source toggle changes visible controls
- Pine registry loads when Pine source is selected
- `Init_Backtest` is disabled until a Pine profile is selected
- `DRAFT` warning appears for draft profiles
- Horus mode still calls `/api/v1/strategy/backtest`
- Pine mode calls `/api/v1/strategy/pine/backtest`
- selected Pine profile name/state appears in the result area

### Backend tests

If no backend contract changes are needed, keep backend impact minimal.
If profile payload or fetch behavior changes, add focused contract tests only for those changes.

### Regression expectations

All current Backtester tests must remain green.
All Pine Lab tests must remain green.

## Implementation Notes

- Keep Backtester and Pine Lab responsibilities distinct.
- Backtester is for running and comparing backtests.
- Pine Lab remains the place for preflight, profile creation, registry review, and activation.
- Prefer extending existing hooks/components over creating a third parallel runtime path.

## Recommended rollout order

1. Add source toggle and local UI state.
2. Load Pine profile registry into Backtester mode.
3. Route Pine runs through existing Pine backtest endpoint.
4. Add `DRAFT` warning and source/result labeling.
5. Add regression tests across Backtester and Pine Lab.

## Success Criteria

The feature is successful when:

- a user can switch Backtester to `Pine Profile`
- select any saved Pine profile, including `DRAFT`
- run a backtest with editable run settings
- see clear labeling of Pine source and profile state
- continue using the original Horus Backtester path unchanged
