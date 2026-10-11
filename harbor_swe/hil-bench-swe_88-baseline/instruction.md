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
