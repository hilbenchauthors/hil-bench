# PROBLEM STATEMENT
# Inconsistent subscription modal messaging and inflexible layout logic for in-app purchases

## Description
The current in-app purchase warning flow mixes legacy prompt behavior with a newer structured modal direction, and the migration is blocked because both contracts are still referenced by internal guidance. The implementation must support store-aware copy, delegated-account handling, and localization-safe rendering for user-facing text, but several policy-controlled details are intentionally withheld and must be clarified before coding.



# REQUIREMENTS
- For externally managed mobile subscriptions, opening the subscription modal must show the in-app purchase warning surface; for non-eligible subscriptions, no warning surface should remain visible after the open attempt completes.

- To reduce rollout risk, the warning surface should preserve the legacy modal contract currently used by subscription flows.

- To satisfy current design-system migration goals, the warning surface must be implemented using the structured modal primitives currently used by newer subscription flows.

- All user-facing commerce copy must use approved channel naming tokens and account-navigation wording exactly as defined by policy.

- In delegated/admin context, render only the minimum policy-required body content.


# PUBLIC INTERFACES
No new public interfaces are introduced.
