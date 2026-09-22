# EGX Price Action Operator Guide

Date: 2026-04-28
Audience: Horus operator
Scope: Running the EGX price action pack from research to live scanner profile

## 1. Purpose

This guide explains the normal operator flow for the EGX price action pack.

Use it when you want to:

1. review the available price action setups
2. preview signal behavior for a ticker
3. backtest a setup on an EGX market slice
4. promote a passing setup into a scanner profile
5. activate that profile for scanner use

The pack is EGX-only in v1. Tradable entries are long-only. Bearish concepts
appear as warnings, blockers, or avoidance labels rather than short trades.

## 2. Before You Start

Before running the workflow, keep these boundaries in mind:

1. Intraday setups are present in the catalog, but they stay data-gated until
   reliable intraday EGX data is available and operationally acceptable for
   backtesting.
2. Warning-only strategies are for caution and filtering. They are not meant to
   be promoted as trade profiles.
3. A setup should be backtested before you trust it for scanner use.
4. Promotion and activation are separate steps. Promotion creates a scanner
   profile. Activation makes that profile the live scanner choice.

## 3. Main Workflow

### Step 1: Open the Strategy page

Go to the Strategy surface in the frontend and find the **Price Action Lab**
panel.

This panel is the main control point for the pack. It lets you:

- filter strategies by family
- inspect the selected setup
- run evaluation
- run backtests
- promote a profile
- activate a promoted profile

### Step 2: Pick a strategy family

Use the family buttons at the top of the lab:

- `ALL`
- `INTRADAY`
- `SWING`
- `POSITION`

Recommended first pass:

1. start with `SWING` or `POSITION`
2. leave `INTRADAY` for later unless you are specifically validating the data
   gate behavior

## 4. Evaluate a Setup

### Step 1: Select the setup

Click a strategy row in the catalog table.

Read the right-hand summary first:

- strategy name
- short description
- whether it is tradable or warning-only

### Step 2: Set the ticker

Enter an EGX ticker in the **Ticker** field.

Good examples for routine checks:

- `COMI`
- other liquid EGX30 names you already monitor

### Step 3: Run Evaluate

Click **Evaluate**.

Expected result:

1. a success message appears
2. the **Signal Preview** panel fills with one or more structured outputs

Read the preview in this order:

1. `signal_type`
2. score
3. explanation
4. warnings
5. avoidance flags
6. entry, stop, and target values if the setup is tradable

What the main signal states mean:

- `BUY`: strongest actionable long signal
- `BUY_CANDIDATE`: promising long setup that still needs judgment
- `WARNING_ONLY`: caution state, not a trade
- `BLOCKED`: setup matched partially, but Horus found a reason to stand down

## 5. Backtest a Setup

### Step 1: Set the market and date window

Choose:

- `EGX30`
- `EGX70`
- `EGX100`
- `ALL`

Then set:

1. `Date From`
2. `Date To`
3. `Capital`

Use a market and date range that match the kind of setup you are checking.

Practical default:

1. start with `EGX30`
2. use a broad daily date window
3. keep capital stable across strategy comparisons

### Step 2: Run Backtest

Click **Backtest**.

Expected result:

1. the **Backtest & Promotion** panel fills in
2. you get return, trade count, drawdown, profit factor, expectancy, and state
3. the promotion-gate section shows either:
   - `All gates passed`
   - one or more failed gate labels

How to read the result:

1. if the strategy is `READY`, it is eligible for promotion
2. if gates fail, treat the setup as research-only for now
3. if drawdown or trade count looks weak, do not promote just because the
   return number looks attractive

## 6. Promote a Passing Setup

### Step 1: Confirm the setup is tradable

Do not try to promote warning-only setups.

Promotion is meant for tradable profiles that passed the backtest gates.

### Step 2: Set the profile name

Enter a clear profile name in **Profile Name**.

Recommended style:

`EGX Price Action Pack`

Horus will append the selected strategy name during promotion.

### Step 3: Click Promote

Click **Promote**.

Expected result:

1. a success message appears
2. the **Promoted Profile** section appears in the backtest panel
3. the created profile shows source type, state, and market

If promotion fails, check:

1. whether the backtest gates actually passed
2. whether a profile with the same name or strategy already exists
3. whether you accidentally selected a warning-only setup

## 7. Activate the Profile

### Step 1: Confirm the promoted profile is visible

After promotion, the lab should show the created profile in the **Promoted
Profile** area.

### Step 2: Click Activate

Click **Activate**.

Expected result:

1. a success message confirms activation
2. the promoted profile becomes the scanner-ready default for that source path

Important:

Activation is the point where the profile becomes the selected live scanner
profile. Promotion alone is not enough.

## 8. Verify It from the Scanner

After activation, open the Scanner surface and inspect the strategy profile
controls.

What to check:

1. the selected profile name matches the profile you activated
2. the audit panel describes it as a `Price-action` scanner profile
3. the profile state looks correct
4. any promotion-margin warning is understandable

If you open **View Full Profile**, you should see:

1. a strategy-profile dialog
2. a `Price Action Profile Details` heading for price-action profiles
3. a direct link back to the Strategy lab

## 9. When to Stop and Not Promote

Do not promote a setup when any of these are true:

1. the backtest panel shows failed gates
2. the setup is warning-only
3. the strategy depends on intraday data that is not available
4. the preview is mostly `BLOCKED` or dominated by bearish warnings
5. the setup only looks acceptable on a very narrow date range

## 10. Recommended First Operating Routine

For the first few runs, use this routine:

1. start with one swing setup
2. run `Evaluate` on a liquid EGX ticker
3. run `Backtest` on `EGX30`
4. only `Promote` if the gates pass cleanly
5. `Activate` only after checking the profile details
6. verify the scanner profile wording and state in Scanner

This keeps the first live usage conservative and easy to audit.

## 11. Current Strategy Set

Tradable entries:

- `ascending_triangle_breakout`
- `bullish_channel_breakout`
- `box_consolidation_breakout`
- `trend_structure_continuation`
- `inside_bar_trend_breakout`
- `fakey_false_break_reversal`
- `symmetrical_triangle_expansion`
- `support_reclaim_bullish_engulfing`
- `double_bottom_neckline_reclaim`
- `inverse_head_and_shoulders_reclaim`
- `intraday_bullish_channel_reclaim`
- `breakout_retest_hold`
- `intraday_support_reclaim_bullish_confirmation`
- `intraday_resistance_break_retest_reentry`
- `intraday_higher_high_higher_low_continuation`
- `intraday_selling_trap_reclaim`
- `intraday_trendline_break_reversal`

Warning-only profiles:

- `descending_triangle_warning`
- `rising_wedge_warning`
- `failed_breakdown_trap_warning`
- `failed_breakout_warning`
- `bull_trap_breakout_warning`
- `double_top_neckline_failure`
- `reversal_structure_shift_warning`

### Backtestability note

- The six added swing and position entries above are backtestable through the
  normal price-action backtest flow.
- The seven current intraday entries are implemented and evaluable when
  intraday data is present, but broad intraday market-slice backtests are still
  heavier operationally than the daily pack.
- `bull_trap_breakout_warning` and `double_top_neckline_failure` are
  warning-only and cannot be promoted as trade profiles.

## 12. Related Notes

- [EGX Price Action Extraction Catalog](./2026-04-28-egx-price-action-extraction-catalog.md)
- [EGX Price Action Closeout](./2026-04-28-egx-price-action-closeout.md)
