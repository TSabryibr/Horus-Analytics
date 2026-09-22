# Signal Follow-Ups and Channel Broadcast Policy Design

## Summary

Horus has three subscriber service tiers:

- Type 1: Market Signals
- Type 2: Market Signals + Portfolio Recommendations
- Type 3: Market Signals + Managed Advisory

The system currently sends signal cards for generated signals, but Type 1 subscribers need follow-up cards for each published signal lifecycle. The same publishing model also needs an admin-controlled main Telegram channel policy that can mirror automated service content by tier.

This design adds:

- Type 1 follow-up cards for `TP1_HIT`, `TP2_HIT`, `STOP_LOSS_HIT`, and `EXPIRED`.
- Follow-up creation from both automatic lifecycle monitoring and manual admin lifecycle overrides.
- A cumulative main-channel broadcast policy across Type 1, Type 2, and Type 3 services.
- Durable per-destination delivery records so retries, suppression, and duplicate prevention remain auditable.

## Goals

- Send every Type 1 subscriber follow-up cards for signals they are entitled to receive.
- Allow follow-ups to be triggered by both market-data lifecycle detection and admin correction.
- Keep Type 1 follow-ups actionable without implying Horus opened a position for the subscriber.
- Let admins decide which automated service tiers are mirrored to the main Telegram channel.
- Keep manual admin channel posts independent from automated channel broadcast settings.
- Prevent duplicate follow-up cards for the same signal state and destination.

## Non-Goals

- Do not open, manage, or close real subscriber positions for Type 1.
- Do not convert Type 1 subscribers into managed advisory users.
- Do not change manual admin broadcast behavior.
- Do not make follow-up delivery depend on whether a subscriber still has the same tier after the original signal was published.

## Recommended Approach

Use entitlement-driven publishing with separate subscriber and channel policies.

Every automated signal is tagged with the service tier it belongs to. Subscriber delivery is based on subscriber entitlement. Main-channel delivery is based on a global admin-configured broadcast level. Follow-ups inherit the service tier and eligible destinations from the original published signal.

This approach matches the existing signal lifecycle model, keeps routing rules explicit, and gives the system durable records for retries, audit logs, manual resend, and suppression.

## Subscriber Routing

Subscriber delivery remains tied to each subscriber's own plan.

Type 1 subscribers receive Type 1 market signal cards and Type 1 follow-up cards. Type 2 and Type 3 subscribers continue to receive the services they are entitled to according to the existing subscription model.

For follow-ups, destination eligibility should be frozen at original publish time. If a subscriber was entitled to the original signal, that subscriber remains eligible for the follow-ups for that signal even if their subscription changes afterward. This avoids cases where a subscriber receives an opening signal but not the closure or risk update.

## Main Channel Routing

The main Telegram channel should be controlled by a global admin setting. This setting applies only to automated service content. Manual admin posts remain separate and can still be sent to the channel when automated broadcasting is disabled.

The main-channel broadcast level is cumulative:

- `none`: no automated service signals or follow-ups go to the main channel.
- `type_1`: Type 1 service content goes to the main channel.
- `type_2`: Type 1 and Type 2 service content go to the main channel.
- `type_3`: Type 1, Type 2, and Type 3 service content go to the main channel.

For example, if the admin chooses `type_2`, the channel receives Type 1 market signal service content and Type 2 service content, but not Type 3 service content.

Channel eligibility should also be frozen at original publish time for follow-ups. If the main channel was eligible for the original signal, it should continue receiving that signal's follow-ups even if the global channel setting changes later.

## Type 1 Follow-Up Behavior

Type 1 follow-ups are tied to the published signal lifecycle. A follow-up card is sent when the lifecycle reaches one of these states:

- `TP1_HIT`: TP1 reached. The card instructs the subscriber to move stop loss to breakeven and keep TP2 active.
- `TP2_HIT`: Final target reached. The card marks the signal as fully closed with no further action.
- `STOP_LOSS_HIT`: Stop loss hit. The card marks the signal as fully closed with no further action.
- `EXPIRED`: Signal expired. The card marks the signal as closed with no further action.

The wording should be clear that Horus is following up on a published signal, not managing a real open subscriber position.

## Lifecycle Sources

Follow-ups can be created from two lifecycle sources:

- Automatic monitoring: market data detects that a lifecycle state has changed.
- Manual admin action: an admin overrides or corrects a lifecycle state.

Both sources must use the same follow-up creation path. This ensures automatic and manual outcomes produce the same delivery records, message text, duplicate protection, and audit trail.

## Data Flow

1. The system publishes an automated signal and tags it with a service tier.
2. The publishing layer records the subscriber destinations entitled to receive the signal.
3. The publishing layer records whether the main channel was entitled to receive that signal under the current global broadcast setting.
4. A published signal lifecycle record tracks the signal's state.
5. The lifecycle monitor or admin override moves the lifecycle into `TP1_HIT`, `TP2_HIT`, `STOP_LOSS_HIT`, or `EXPIRED`.
6. The follow-up service creates one follow-up delivery per eligible destination for that lifecycle state.
7. Telegram delivery sends each queued follow-up card and records success, failure, retry count, and provider message id.

## Reliability

Follow-up delivery should be durable and auditable.

Each destination should have at most one follow-up record per lifecycle and trigger state. This prevents duplicate `TP1`, `TP2`, `SL`, or expiry cards from being sent to the same destination.

Failed Telegram sends should remain visible to admins with retry count, last attempted time, and last error. Admins should be able to resend or suppress a follow-up without changing the underlying signal lifecycle.

## Admin Controls

The implementation should expose these controls:

- Global automated main-channel broadcast level: `none`, `type_1`, `type_2`, or `type_3`.
- Follow-up queue visibility by state, ticker, destination, and delivery status.
- Manual resend for failed or selected follow-ups.
- Manual suppress for follow-ups that should not be sent.
- Audit events explaining why each destination was selected or skipped.

## Testing Requirements

Tests should cover:

- Type 1 lifecycle transitions create follow-up deliveries for `TP1_HIT`, `TP2_HIT`, `STOP_LOSS_HIT`, and `EXPIRED`.
- Automatic lifecycle detection and admin overrides use the same follow-up creation path.
- Duplicate lifecycle transitions do not create duplicate follow-up cards.
- The main channel receives automated content only according to the cumulative setting.
- `type_2` includes Type 1 and Type 2 service content.
- `type_3` includes Type 1, Type 2, and Type 3 service content.
- `none` blocks automated main-channel delivery while preserving manual admin channel posts.
- Follow-up retry, resend, and suppress actions preserve lifecycle state.

## Open Implementation Notes

The current codebase already contains published signal lifecycle and follow-up models. The implementation should prefer extending those existing records and services instead of adding a parallel notification system.

The exact storage shape for frozen destination eligibility should be decided during implementation planning after reviewing the existing signal delivery tables and Telegram send path in detail.
