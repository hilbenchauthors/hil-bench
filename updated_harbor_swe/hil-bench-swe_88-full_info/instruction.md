# PROBLEM STATEMENT
## Title:

Eligibility regression in summer-2023 operation

### Description:

The `summer-2023` eligibility computation returns incorrect results for users whose free period started recently. The campaign gate must consistently apply the correct app scope restriction and the campaign-specific cooling-off policy for free users who previously held a paid subscription.

### Expected behavior:

Only users who satisfy all campaign policy conditions should be eligible for `summer-2023`. This includes app scope restrictions and a verified cooling-off period since the last paid subscription ended.

### Actual behavior:

Some users who do not meet the campaign conditions are currently returned as eligible. The app scope is broader than intended and the cooling-off enforcement does not apply the correct campaign-specific threshold.

### Step to Reproduce:

1. Sign in with a free user whose paid subscription ended recently.
2. Open the `summer-2023` offer flow.
3. Observe the returned eligibility decision.

### Additional Context:

The logic is implemented in `isEligible` within `packages/components/containers/offers/operations/summer2023/eligibility.ts` and takes `user`, `subscription`, `protonConfig`, and `lastSubscriptionEnd` as inputs. The summer-2023 campaign was initially launched targeting a single application as part of a phased rollout.



# REQUIREMENTS
- In `isEligible`, evaluate the `summer-2023` operation using `{ user, protonConfig, subscription, lastSubscriptionEnd }`.

- `lastSubscriptionEnd` is a Unix-time timestamp in seconds from the billing ledger representing when the user's most recent paid subscription ended.

- This eligibility rule is evaluated for `ProtonConfig.APP_NAME` matching `APPS.PROTONMAIL` or `APPS.PROTONCALENDAR`; other apps are out of scope for this operation.

- A free user is eligible under the cooling-off rule only if their paid subscription ended far enough in the past to satisfy the campaign-mandated cooling-off interval; users whose subscription ended more recently than the required threshold are not eligible under this rule.

- A non-free (paid) user who is not on a trial subscription must not be considered eligible through the cooling-off rule.

- Existing eligibility gates such as the delinquency check remain active and unchanged by this specification.

- The `isTrial` and `isManagedExternally` helpers from `@proton/shared/lib/helpers/subscription` are available for subscription checks.



# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The requirements reference a campaign-mandated cooling-off interval that free users must satisfy after their last paid subscription ended, but the specific duration of this cooling-off period is not stated anywhere in the problem statement or requirements.
The cooling-off period is exactly 90 days. Compute the cutoff as `Math.floor(Date.now() / 1000) - 90 * 86400` (current UTC Unix timestamp minus 90 days in seconds). The user's `lastSubscriptionEnd` must be strictly less than this cutoff to satisfy the cooling-off requirement. Do NOT use 30 days, 'one calendar month', or calendar-month offset semantics. Example: if current time is `2026-03-13T10:00:00Z` (Unix 1773572400), then cutoff = `1773572400 - 7776000 = 1765796400` (i.e. `2025-12-13T10:00:00Z`). A `lastSubscriptionEnd` of `1765796400` (exactly at cutoff) does NOT satisfy the check; `1765796399` (one second earlier) does.

### The requirements state that a free user is eligible under the cooling-off rule only if their paid subscription ended far enough in the past to satisfy the campaign-mandated cooling-off interval. The `lastSubscriptionEnd` parameter is described as a Unix-time timestamp in seconds from the billing ledger. However, the requirements do not address the semantic meaning of `lastSubscriptionEnd` when it is `0`, `undefined`, or otherwise absent. The existing code defaults `lastSubscriptionEnd` to `0` and checks `lastSubscriptionEnd > 0` as part of the eligibility condition. This creates ambiguity because a free user who has never held a paid subscription—and therefore has no billing ledger entry—could reasonably be considered either (a) ineligible, since no cooling-off period can be verified against the threshold, or (b) eligible, since the cooling-off restriction logically applies only to users who previously held a paid subscription and no recent cancellation exists to enforce against. The distinction between 'never subscribed' (no data) and 'subscription data unavailable' (missing data) is not addressed.
When `lastSubscriptionEnd` is `undefined`, `0`, `NaN`, or otherwise not a valid positive finite number, treat it as 'no known previous paid subscription' and bypass the cooling-off restriction entirely—the user is eligible through the cooling-off path. Implement a dedicated timestamp validation guard (`isKnownTimestamp`) that returns `true` only when the value is of type `number`, passes `Number.isFinite`, and is greater than `0`. In the cooling-off verification function (`hasVerifiedCooldown`), if `isKnownTimestamp` returns `false`, return `true` (eligible) without performing any duration calculation. Remove the default value of `0` for `lastSubscriptionEnd` in the `isEligible` function signature to avoid conflating 'not provided' with 'epoch timestamp'. Only apply the cooling-off duration check when the timestamp is known and valid. Example: `isEligible({ user: freeUser, protonConfig: validAppConfig })` with no `lastSubscriptionEnd` → should return `true`; `isEligible({ user: freeUser, protonConfig: validAppConfig, lastSubscriptionEnd: 0 })` → should also return `true`.

### The requirements state that the eligibility rule is evaluated for `APPS.PROTONMAIL` or `APPS.PROTONCALENDAR`, while the problem statement notes that the summer-2023 campaign was initially launched targeting a single application as part of a phased rollout. These statements conflict because the requirements permit two apps while the deployment context indicates only one was targeted.
Only `APPS.PROTONCALENDAR` is in scope for the summer-2023 operation. Any other app identifier, including `APPS.PROTONMAIL`, must cause `isEligible` to return `false` immediately at the app-scope check. Example: `protonConfig.APP_NAME === APPS.PROTONMAIL` -> return `false`; `protonConfig.APP_NAME === APPS.PROTONCALENDAR` -> proceed to downstream eligibility checks.
