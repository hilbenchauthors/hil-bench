# PROBLEM STATEMENT
# Title: 
Incorrect information shown during subscription cancellation

## Description

Users report that subscription details displayed during the cancellation process appear to be inaccurate.

## Steps to reproduce
1. Have an active paid subscription.
2. Initiate the cancellation process.
3. Proceed through the cancellation flow to the final confirmation screens.
4. Observe the subscription details displayed.

## Actual Behavior
The subscription information shown during cancellation appears to be inaccurate.

## Expected behavior
During cancellation, the UI should display accurate subscription information that helps users understand the implications of their cancellation.

## Impact
Users may be confused about the details of their subscription during the cancellation process.


# REQUIREMENTS
- The expiry-calculation utility must support a cancellation-aware mode to reflect when a user has initiated cancellation or will not auto-renew.

- The utility must always incorporate any pending or scheduled subscription changes when available, as they represent the user's most current subscription configuration and are critical for accurate expiration calculations.

- When the cancellation-aware mode is engaged, the result must appropriately reflect the non-renewing state of the subscription. It also must include the end timestamp as the expiration date, and the plan display name for that term when available.

- The cancellation-aware mode interface should be designed to accommodate potential future parameters beyond the initial cancellation signal.

- Cancellation-flow screens must pass a cancellation-aware signal into the utility. Call sites outside the cancellation flow must continue to work without forcing a breaking change at every existing invocation.

- When the cancellation-aware mode is not engaged and auto-renew remains enabled, existing behavior must be preserved, including all existing subscription data considerations.

- Renewal-related fields in the utility result should remain consistent with the Renew state and analogous renewal signals on the subscription data returned by the billing system, unless another requirement explicitly requires a different presentation for a given mode.

- When the utility exposes multiple renewal-related fields together, they must present a coherent renewal picture relative to the same subscription snapshot, billing renewal signals, and cancellation-aware presentation rules.

- For free plans, behavior must remain unchanged; the cancellation-aware mode must not alter the output.

- All screens in the cancellation flow that currently compute or display expiration dates must be updated to invoke the utility in cancellation-aware mode rather than accessing subscription date properties directly. This includes any modal, configuration, or component in the cancellation flow path that reads `PeriodEnd` or `UpcomingSubscription.PeriodEnd` on the subscription object.


# PUBLIC INTERFACES
Relevant subscription and expiration APIs:

- **`subscriptionExpires`:** utility that computes expiration-related presentation from a subscription object. The product requirements call for cancellation-aware behavior at this boundary while keeping existing non-cancellation callers working; how that input is expressed in the signature follows normal extension practice for utilities in this codebase.

- **`UpcomingSubscription`:** optional subscription payload field for pending or scheduled subscription changes, matching the requirements’ wording.

- **`latestSubscription`:** the subscription snapshot used as primary when resolving period end, plan naming, and renewal-related fields from the subscription object and optional scheduled-change data.

- **Renewal-related utility outputs:** `renewEnabled`, `renewDisabled`, and `subscriptionExpiresSoon`, read alongside billing `Renew` according to the product requirements.
