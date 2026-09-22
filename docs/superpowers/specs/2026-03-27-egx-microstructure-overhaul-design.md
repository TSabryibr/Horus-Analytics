# Horus Analytics II EGX Microstructure Overhaul Design

Date: 2026-03-27
Status: Proposed
Authoring mode: Brainstorming-approved design

## 1. Purpose

This design introduces an EGX-specific market microstructure layer for Horus Analytics II so that backtests, scanner outputs, and later live decisioning stop assuming deep-liquidity, low-friction execution.

The immediate goal is to harden three weak assumptions in the current system:

1. orders can always be filled at attractive prices
2. breakout signals are valid without institutional participation
3. EGX30 and EGX70 can share one signal and execution personality

The design is intentionally biased toward realism over headline backtest returns. Lower trade count, partial fills, higher slippage, and more idle cash are acceptable if the resulting system is more deployable on EGX.

## 2. Current Context

The current codebase already provides most of the raw ingredients, but they are not yet composed into a coherent EGX-specific control layer:

- `PortfolioSimulator.py` applies a flat slippage assumption and capital-based sizing rather than liquidity-aware execution
- `core/SignalEngine.py` uses relative volume and turnover, but volume remains a scoring input rather than a hard institutional-validation veto
- `MarketLists.py` and `SectorAnalysis.py` provide index and sector metadata, but there is no dedicated regime-routing seam that distinguishes EGX30 and EGX70 behavior
- `core/DailyScanner.py` still produces candidates before applying the kind of market-structure filters that would reject many unrealistic EGX trades

This means the system has data and metadata needed for the overhaul, but not the architectural boundaries required to keep the rules consistent across simulation, scan, and runtime surfaces.

## 3. Design Goals

The overhaul should leave five things true:

1. Execution realism is modeled through one reusable seam, not duplicated in simulator and runtime code.
2. Technical signals are only actionable when abnormal participation confirms them.
3. Sector-relative and index-relative context affect whether a trade is allowed, not just how it is described.
4. EGX30 and EGX70 behave as distinct route profiles rather than one blended universe.
5. The rollout can start in shadow mode and become enforceable in simulator first, then scanner/runtime later.

## 4. Non-Goals

This design does not attempt to:

- build a full intraday market-impact engine
- implement order-book replay
- add live broker execution in the same package
- redesign the full scoring philosophy of `SignalEngine.py`
- replace existing portfolio risk rules outside what is needed to support this EGX microstructure layer

Those are valid future packages, but they should not be bundled into the first overhaul slice.

## 5. Architectural Recommendation

The recommended approach is to introduce one EGX microstructure layer composed of four focused seams:

1. `core/market_profiles.py`
2. `core/regime_router.py`
3. `core/signal_validation.py`
4. `core/execution_model.py`

This is preferred over directly hard-coding new thresholds into `PortfolioSimulator.py`, `core/SignalEngine.py`, and scanner/runtime call sites because:

- it prevents rule drift between backtest and runtime paths
- it makes the new assumptions testable in isolation
- it allows different EGX profiles to be expressed as policy rather than scattered conditionals
- it creates a reusable extension point for later trap-risk, whale-tracking, and live execution work

## 6. Core Seams

### 6.1 `core/market_profiles.py`

This module owns policy only. It should not fetch data or decide membership. It defines reusable profile bundles such as:

- `EGX30_TREND_PROFILE`
- `EGX70_TACTICAL_PROFILE`
- `ILLIQUID_NO_TRADE_PROFILE`

Each profile should carry parameters such as:

- maximum ADV participation
- slippage thresholds
- holding horizon
- stop style
- sector RS minimum
- volume confirmation threshold
- trap-risk tolerance

### 6.2 `core/regime_router.py`

This module classifies a candidate and chooses the active policy.

Inputs:

- ticker
- sector
- EGX30 or EGX70 membership
- liquidity tier
- sector RS

Outputs:

- profile name
- allowed or blocked decision
- routing reason
- regime metadata

This is where index bifurcation becomes explicit instead of being implied by ad hoc threshold choices.

### 6.3 `core/signal_validation.py`

This module evaluates whether a raw technical setup is market-structure credible.

Inputs:

- price bar or vectorized universe slice
- volume statistics
- turnover
- EFI or money-flow proxies
- sector RS
- selected market profile

Outputs:

- `is_valid`
- veto reasons
- validation metrics
- trap-risk score

`SignalEngine` remains responsible for technical setup generation. This module is the institutional truth gate layered on top.

### 6.4 `core/execution_model.py`

This module owns fill realism.

Inputs:

- desired order size
- price
- volume or ADV measures
- selected market profile

Outputs:

- fillable shares
- rejected shares
- slippage percentage
- effective fill price
- liquidity-cap flags

It should be usable first by `PortfolioSimulator.py`, then later by runtime paths if needed.

## 7. Data Flow

The preferred control flow is:

1. `SignalEngine` generates raw technical candidates.
2. `signal_validation` applies VSA and market-structure validation.
3. `regime_router` selects the active market profile and route.
4. `execution_model` applies liquidity and slippage realism.
5. `PortfolioSimulator.py` consumes the validated, routed, execution-aware candidates.
6. `core/DailyScanner.py` and runtime paths adopt the same seams later.

This ordering matters:

- setup truth first
- routing second
- execution truth last

It keeps technical logic, profile logic, and fill logic separate and debuggable.

## 8. Rules Contract

### 8.1 Execution Realism

The primary liquidity unit should be 10-day ADV in notional value:

- `adv_10_notional = rolling_mean(Close * Volume, 10)`

An optional secondary metric may also be carried:

- `adv_10_shares = rolling_mean(Volume, 10)`

The execution model should measure participation as:

- desired order notional divided by `adv_10_notional`

Base behavior:

- low participation: light slippage
- mid participation: heavy slippage
- above hard cap: partial fill plus rejection of the remainder

Execution realism must apply to both:

- entry
- exit

Backtests should no longer assume same-bar close execution after the signal is observed. The default fill model should be:

- signal on bar `t`
- execution on bar `t + 1` open, adjusted by slippage

### 8.2 VSA / Smart-Money Validation

Long setups must be vetoed unless abnormal participation confirms them.

Base rule:

- `volume_mult_20 = Volume / SMA20(Volume)`
- candidate must exceed the profile threshold

Recommended supporting checks:

- close in the upper portion of the candle range
- EFI positive
- turnover above floor

This moves volume from a soft score component into a hard validation gate.

### 8.3 Sector Relative Strength

Sector RS should compare sector performance with EGX30 over a rolling window.

Base calculation:

- sector basket rolling return over 14 trading days
- EGX30 benchmark rolling return over 14 trading days
- `sector_rs = sector_return_14d - benchmark_return_14d`

Longs are allowed only when:

- `sector_rs > 0` for trend-oriented profiles

Looser thresholds can be introduced later for tactical bounce profiles, but not in the first slice.

### 8.4 Index Routing

Routing rules should be explicit:

- ticker in `EGX30` -> trend-following profile
- ticker in `EGX70` -> tactical / fast-risk profile
- unknown or illiquid ticker -> fallback conservative or no-trade profile

The routing decision should not depend on index membership alone. Liquidity tier and sector state should be allowed to downgrade a nominal EGX30 or EGX70 name into a more conservative route.

### 8.5 Trap-Risk Metadata

The system should carry a trap-risk score even before it uses that score as a hard veto.

Trap risk should increase for conditions such as:

- low ADV
- weak sector RS
- breakout with poor close location
- high volume without meaningful range expansion
- EGX70 candidates that require excessive participation to size

The first release should use trap risk as metadata and diagnostics. Enforcement can follow after observation confirms its value.

## 9. Recommended Default Profiles

### 9.1 EGX30 Trend Profile

Characteristics:

- moderate participation cap
- lower slippage curve than EGX70
- strong but not extreme volume confirmation
- wider stops
- longer hold horizon

Use case:

- institutional leadership names with cleaner trend continuation behavior

### 9.2 EGX70 Tactical Profile

Characteristics:

- strict participation cap
- harsh slippage curve
- very strong volume confirmation
- tighter stops
- shorter hold horizon
- low tolerance for dead-money drift

Use case:

- retail-dominated names where entry timing, liquidity, and exit speed matter far more

### 9.3 Illiquid / No-Trade Profile

Characteristics:

- used when ADV, turnover, or sector state is too weak
- blocks the trade rather than weakening confidence

Use case:

- names that the system should not pretend it can trade realistically

## 10. Rollout Strategy

The safest rollout is staged:

### Stage 1: Shadow Mode

Compute and log all new fields without blocking trades:

- liquidity caps
- expected slippage bucket
- VSA veto result
- sector RS result
- route profile
- trap-risk score

This creates before-and-after evidence without destabilizing production behavior.

### Stage 2: Simulator Enforcement

Apply the new rules inside `PortfolioSimulator.py` first:

- ADV-based participation cap
- slippage tiers
- partial fills
- next-bar execution

This makes backtests honest before scanner/runtime behavior changes.

### Stage 3: Scanner Enforcement

Push the same seams into `core/DailyScanner.py` and scanner-facing routes so candidate lists and operator views reflect the same reality the simulator now uses.

### Stage 4: Runtime / Live Follow-On

Only after simulator and scanner behavior are stable should runtime decision paths or any auto-execution-adjacent flows consume these rules.

## 11. Testing Strategy

Testing should follow the seam boundaries:

### 11.1 Seam-Level Tests

- execution model: liquidity caps, slippage tiers, partial fills, rejected notional
- validation model: VSA veto, turnover gate, EFI/candle-quality gate
- router: EGX30 vs EGX70 vs fallback routing
- sector RS: rolling relative performance correctness

### 11.2 Integration Tests

- simulator consumes routed and validated candidates correctly
- scanner surfaces new metadata consistently
- illiquid and no-trade cases behave deterministically
- profile routing stays aligned between signal and execution paths

### 11.3 Rollout Diagnostics

Add counters and summaries for:

- liquidity-cap hits
- rejected notional
- slippage bucket usage
- VSA veto count
- sector-RS veto count
- EGX30 and EGX70 route counts
- trap-risk distribution

This is required to prevent the stricter system from being misread as broken when it is simply being more honest.

## 12. Success Criteria

The overhaul is successful if:

- backtest returns become more realistic even if they decline
- trade count drops for the right reasons rather than from broken logic
- impossible fills are materially reduced
- thin, low-quality names receive less capital
- EGX30 and EGX70 behavior clearly diverges under test and in diagnostics
- operator-facing outputs can explain why trades were allowed, vetoed, or partially filled

## 13. Recommended Implementation Sequence

The safest execution order is:

1. measurement and diagnostics
2. market profile seams
3. simulator execution realism
4. signal-validation layer
5. routing layer
6. scanner/runtime integration
7. portfolio-level trap-risk and crowding follow-ons

The first implementation slice should cover:

- `core/market_profiles.py`
- `core/execution_model.py`
- simulator integration

The second slice should cover:

- `core/signal_validation.py`
- `core/regime_router.py`
- scanner-facing metadata

## 14. Follow-On Improvements

After the first slice stabilizes, the highest-value follow-ons are:

1. exit-side liquidation stress curves
2. whale accumulation and distribution scoring
3. time-of-day EGX70 risk filters
4. broader portfolio crowding and sector concentration throttles
5. live runtime enforcement where appropriate

These should remain follow-on packages rather than being folded into the initial overhaul.

