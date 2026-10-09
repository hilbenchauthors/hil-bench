# PROBLEM STATEMENT
# Add Referral Link Signature in Composer

## Description

The composer should route referral-enabled signatures through the existing signature pipeline so referral content is handled consistently across compose flows.

## Current Behavior

Referral-aware signature behavior is inconsistent. Depending on the active sender and compose path, referral output can appear for the wrong sender, use the wrong output form, rely on unsafe fallback settings, or disturb existing signature content during sender changes.

## Expected Behavior

Referral-aware compose behavior should stay consistent across signature build and sender-switch update paths. Compose flows should derive sender-scoped referral user settings through one shared helper before calling shared signature rendering helpers, so the same sender-aware input shape is reused in draft build, plain-text to HTML conversion, and sender-switch updates. The helper's caller must supply the externally known primary sender email and the active sender email instead of inferring sender scope from address ordering, and downstream shared signature helpers must receive the helper's output shape unchanged. Callers should not reconstruct sender-scoped signature inputs independently, and no-referral paths should still pass through that same helper contract before shared rendering helpers are called. The active sender should determine whether referral-aware behavior applies, the active signature format should determine how referral content is rendered, and that render choice should not be inferred from the current signature text alone. When sender eligibility changes, the update should preserve the visible integrity of the existing signature instead of introducing unrelated changes. Referral URLs should also satisfy the intended attribution and sanitization rules.

## Use Cases / Motivation

Consistent referral-aware signature behavior preserves attribution, avoids broken or duplicated signature output, and keeps sender changes from unexpectedly damaging user-visible signature content.



# REQUIREMENTS
- Shared signature rendering must honor sender-specific referral settings consistently across signature build and sender-switch update paths.

- Compose build paths and sender-switch update paths must derive sender-scoped referral user settings through the same exported helper before they call shared signature rendering helpers.

- The exported sender-settings helper is the sole contract for sender-scoped referral user-settings inputs; callers must not independently merge, preserve, or synthesize referral fields before invoking shared signature helpers.

- The sender-settings helper must receive the externally supplied primary sender email and the active sender email as explicit inputs. Callers must not infer the primary sender from address ordering, selected-address position, or signature contents.

- New-draft creation, plain-text to HTML conversion, and sender-switch update paths must forward the original compose `userSettings` object and the externally supplied primary sender email into the sender-settings helper without rewriting either input first.

- Shared signature helpers that consume sender-scoped referral settings must receive the helper's returned object unchanged; callers must not patch, merge, or normalize that returned object after the helper call.

- Referral-aware signature output must render in the correct form for the active signature format.

- The active signature format used for referral rendering must come from the compose path's format contract, not from inspecting whether the current signature body happens to contain HTML tags.

- HTML-mode and plain-text-mode compose paths must therefore pass enough format information into shared signature rendering so that render-mode selection does not depend on whether the current signature body happens to contain markup.

- Compose paths without referral-specific settings must pass one safe fallback user-settings shape into shared signature helpers.

- No-referral compose paths must still call shared signature helpers with the helper-derived sender-scoped fallback input rather than bypassing the helper or passing ad hoc empty settings.

- When sender eligibility changes from referral-enabled to no-referral, the signature update must preserve user-visible signature integrity.

- Sender-switch cleanup must update the current composer signature state consistently when referral support turns off, without introducing unrelated visible signature changes.

- Referral URL handling must satisfy both attribution-preservation and sanitization expectations.

- Referral URL canonicalization must be deterministic: shared helpers must return one stable rendered referral URL form for the same input URL, and callers must not perform their own query-key or fragment cleanup outside the shared URL helper.

- EO/default compose flows must use the same safe fallback user-settings shape when referral-specific settings are unavailable.

- Plain-text to HTML conversion, new-draft signature insertion, and sender-switch signature updates must all use the shared sender-settings helper contract rather than deriving sender-scoped signature inputs independently.



# PUBLIC INTERFACES
- Path: `/app/packages/shared/lib/mail/signature.ts`
  Name: `sanitizeReferralLink`
  Type: function
  Input: `input?: string`
  Output: `string`
  Description: Canonicalizes a referral URL into the single shared rendered form used by signature helpers, so callers do not perform their own query-key or fragment cleanup.

- Path: `/app/packages/shared/lib/mail/signature.ts`
  Name: `getProtonSignature`
  Type: function
  Input: `mailSettings: Partial<MailSettings> = {}`, `userSettings: Partial<UserSettings> = {}`
  Output: `string`
  Description: Builds the Proton signature string from the compose path's mail settings and the sender-scoped user-settings object that callers pass through unchanged from the sender-settings helper.

- Path: `/app/applications/mail/src/app/helpers/message/messageSignature.ts`
  Name: `stripReferralFragments`
  Type: function
  Input: `content = ''`, `referralLink = ''`
  Output: `string`
  Description: Removes the trailing referral fragment from rendered signature content while preserving the remaining signature body.

- Path: `/app/applications/mail/src/app/helpers/message/messageSignature.ts`
  Name: `getSenderSignatureRetryOffsets`
  Type: function
  Input: none
  Output: `number[]`
  Description: Returns the retry schedule used by sender-signature rewrite helpers.

- Path: `/app/applications/mail/src/app/helpers/message/messageSignature.ts`
  Name: `executeSenderSignatureRewriteWithRetry`
  Type: function
  Input: `operation: () => void`, `wait?: (delay: number) => Promise<void>`
  Output: `Promise<boolean>`
  Description: Executes a sender-signature rewrite operation with the helper's retry behavior and reports whether it eventually succeeded.

- Path: `/app/applications/mail/src/app/helpers/message/messageSignature.ts`
  Name: `getSenderSignatureRewritePlan`
  Type: function
  Input: `now: number`, `history: number[] = []`, `lastExecution?: number`
  Output: `{ history: number[]; executeAt: number }`
  Description: Computes when the next sender-signature rewrite should execute based on the helper's rewrite history.

- Path: `/app/applications/mail/src/app/helpers/message/messageSignature.ts`
  Name: `scheduleSenderSignatureRewrite`
  Type: function
  Input: `state: SenderSignatureRewriteState`, `rewrite: SenderSignatureRewrite`, `now: number`, `setTimer: (callback: () => void, delay: number) => ReturnType<typeof setTimeout>`, `clearTimer: (timer: ReturnType<typeof setTimeout>) => void`, `runRewrite: (rewrite: SenderSignatureRewrite) => void`
  Output: `void`
  Description: Schedules a sender-signature rewrite using the exported rewrite-planning state and timer callbacks.

- Path: `/app/applications/mail/src/app/helpers/message/messageSenderReferral.ts`
  Name: `getSenderReferralUserSettings`
  Type: function
  Input: `primaryAddressEmail: string | undefined`, `senderAddressEmail: string | undefined`, `userSettings: Partial<UserSettings> = {}`
  Output: `Partial<UserSettings>`
  Description: Derives the sender-scoped user-settings object that compose build paths, plain-text to HTML conversion, and sender-switch update paths must obtain from explicit primary-sender and active-sender inputs, then pass unchanged into shared signature helpers.

## BLOCKER DETAILS
### The task says signature build and sender-switch update paths must apply sender-specific referral gating consistently, but it does not define which senders are actually referral-eligible. What exact sender scope should retain referral-aware settings?

Only the account primary sender is referral-eligible. When the active sender is any non-primary sender, the compose flow must use the no-referral path instead of preserving referral-aware settings.

### The task requires referral-enabled signatures to render consistently with the active signature format, but it does not define the exact render mapping for each format. What exact referral output form should each signature format use?

Use this render mapping: plain-text signatures append `REFERRAL_LINK` as raw text on its own new line; HTML signatures append exactly one anchor for that same `REFERRAL_LINK`.

### The task requires compose flows without referral-specific settings to behave safely, but it does not define the exact fallback user-settings shape that those flows should pass into shared signature helpers. What exact fallback shape should be used when referral-specific settings are unavailable?

Use the safe empty fallback shape `SAFE_EMPTY_USER_SETTINGS = { Referral: undefined }` whenever referral-specific settings are unavailable or intentionally disabled for a compose path.

### When sender eligibility changes from referral-enabled to no-referral, the task says signature updates should preserve user-visible integrity but does not define whether the flow should preserve the current rendered signature body or rebuild the signature from sender data.

Preserve the current non-referral signature body and container, and remove only the current referral addition instead of rebuilding the signature from sender data. This applies to both HTML and plain-text signatures.

### One requirement implies referral URLs should preserve attribution details, while another implies referral URLs should be sanitized before rendering. Which query-handling rule takes precedence when constructing referral output? 
Canonicalize referral URLs by preserving only query key `ref`, removing all other query keys and fragments, and keeping the original scheme, host, and path.
