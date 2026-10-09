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

## BLOCKER DETAILS
### The requirements demand policy-approved commerce channel names and an account-navigation noun, but none of those exact tokens are provided.
Use exactly "Google Play" for `External.Android` and "Apple App Store" for `External.iOS`.

In non-delegated mode:
- The modal title must be exactly "Manage your subscription on {storeLabel}" using the store label above.
- The account-navigation noun is platform-specific:
  - Android: exactly "Payments & subscriptions" (ampersand, lowercase s)
  - iOS: exactly "Subscriptions" (capital S, plural)
- The helper sentence must render the navigation noun as bold text via translator-safe rich formatting (i.e., using `ttag` `.jt` with a `<span className="text-bold">...</span>` node).

Constraints:
- Do NOT use "Google Play store".
- Do NOT use a single shared navigation noun across platforms.

### Delegated/admin mode says to keep only minimum policy-required body content, but it does not define whether that means one paragraph or a multi-paragraph instructional layout.

Delegated/admin mode is resolved only by body layout/content.

It must render exactly one body paragraph and must omit the secondary instructional paragraph entirely.

The single paragraph must contain the delegated ownership statement in this exact format:
- "Subscription for user ID: {userId} was purchased via an in-app purchase."
  - Note the colon after "ID".

No other body paragraphs or helper lines are permitted in delegated/admin mode.

This entry does not define channel labels, navigation nouns, modal primitives, button text, or test IDs.

### The requirements simultaneously ask to preserve the prompt-style modal contract and to implement the same flow with two-section modal primitives.

Treat the two-section modal primitives as authoritative and implement the warning surface with:
- `ModalTwo` + `ModalTwoHeader` + `ModalTwoContent` + `ModalTwoFooter`
- No `Prompt` usage or wrapper

`ModalTwo` must be rendered with `size="large"`.

The first body paragraph must always exist and must carry `data-testid="InAppPurchaseModal/text"`.

The footer must render exactly one primary action button with:
- Label: "Got it"
- `data-testid="InAppPurchaseModal/onClose"`
- It calls `onClose`

For non-eligible subscriptions (External not Android/iOS), the component must immediately call `onClose` and render nothing (return `null`).
