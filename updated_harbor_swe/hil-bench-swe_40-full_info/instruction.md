# PROBLEM STATEMENT
## Problem Statement

Standardize the flags representation used for password-related behavior in ShareLink/ShareURL utilities to eliminate inconsistent naming conventions and legacy variants, and ensure deterministic, reliable flag detection and password-splitting behavior across the codebase.

## Motivation

Today, flag access depends on whether an object exposes the canonical `flags` representation or a legacy variant used by older payloads, which can lead to incorrect detection and inconsistent behavior. The goal is to converge on `flags` as the standard, but the expected behavior for legacy input shapes (including cases where more than one representation is present) remains undefined and must be clarified.

Separately, Drive link passwords include a generated segment with a fixed length that has recently changed under an internal security policy update. Any logic that generates, slices, or re-combines generated/custom password segments must follow the updated length requirement.

## Requirements

- Standardize reads/writes to use `flags` as the canonical representation.
- Note: Do not persist any non-canonical flags representation in returned domain objects; emit only the canonical `flags` shape.
- Define the compatibility and conflict-handling rule for inputs that provide legacy flags representations (including cases where multiple representations coexist).
- Define how the incoming flags value is normalized/coerced prior to bit evaluation.
- Note: Flags values must be treated as already-valid integers; do not coerce or normalize them.
- Ensure password splitting and recombination (when generated + custom segments coexist) follows the updated fixed generated-password length and uses the correct flags source and deterministic conflict handling.


# REQUIREMENTS
- The function `hasCustomPassword` must determine whether the `CustomPassword` flag is set in the `flags` property of the input object and return `true` only in that case. 

- The function `hasGeneratedPasswordIncluded` must determine whether the `GeneratedPasswordIncluded` flag is set in the `flags` property of the input object and return `true` only in that case. 

- The functions `hasCustomPassword` and `hasGeneratedPasswordIncluded` must accept an object with a numeric `flags` property and evaluate it against `SharedURLFlags`.

- Note: Implementations must treat `flags` as the canonical representation and must not persist any non-canonical flags representation in returned domain objects.
- Note: Some inputs may still expose flags metadata via a legacy representation (e.g., `Flags`) and may even include multiple representations simultaneously; the expected compatibility behavior must be defined.
- Note: If multiple flags representations are present on the same input and disagree, the expected policy must be defined. Do not assume a default.

- Note: The flags value must be used as provided and must not be coerced or normalized (e.g., do not accept floats or numeric strings as flags).

- The function `splitGeneratedAndCustomPassword` must accept a password string and an object with a numeric `flags` property. 

- When the `flags` property indicates no custom password, the function must return the entire string as the generated password and an empty string for the custom password. 

- When the `flags` property indicates only a custom password, the function must return an empty string for the generated password and the entire string as the custom password. 

- When the `flags` property indicates both a generated and a custom password, the function must split the string into (generated, custom) using the fixed generated-password length required by the current security policy.


# PUBLIC INTERFACES
New public interfaces:

Type: Function
Name: shareUrlPayloadToShareUrl
Path: applications/drive/src/app/store/_api/transformers.ts
Input: shareUrl (ShareURLPayload)
Output: ShareURL
Description: Transforms a ShareURLPayload API response object into a ShareURL domain object by mapping API field names to camelCase and adding computed properties like hasCustomPassword and hasGeneratedPasswordIncluded.

Type: Function
Name: useShareURLView
Path: applications/drive/src/app/store/_views/useShareURLView.tsx
Input: shareId (string), linkId (string)
Output: Object containing isDeleting, isSaving, name, initialExpiration, customPassword, sharedLink, loadingMessage, confirmationMessage, errorMessage, sharedInfoMessage, hasCustomPassword, hasGeneratedPasswordIncluded, hasExpirationTime, saveSharedLink, deleteLink
Description: A React hook that manages the complete state and business logic for ShareURL operations including loading, saving, deleting links and handling all related UI states and error conditions.

Type: Function
Name: hasCustomPassword
Path: applications/drive/src/app/store/_shares/shareUrl.ts
Input: sharedURL?: { flags?: unknown; Flags?: unknown }
Output: boolean
Description: Returns whether the ShareURL-like object has the "custom password" flag enabled.

Type: Function
Name: hasGeneratedPasswordIncluded
Path: applications/drive/src/app/store/_shares/shareUrl.ts
Input: sharedURL?: { flags?: unknown; Flags?: unknown }
Output: boolean
Description: Returns whether the ShareURL-like object has the "generated password included" flag enabled.
Type: Function
Name: splitGeneratedAndCustomPassword
Path: applications/drive/src/app/store/_shares/shareUrl.ts
Input: password: string, sharedURL?: { flags?: unknown; Flags?: unknown }
Output: [generatedPassword: string, customPassword: string]
Description: Splits the stored password into generated and custom segments based on the password-related flags. When both segments are present, the generated segment uses a fixed generated-password length.

## BLOCKER DETAILS
### The Drive sharing flow relies on a fixed generated-password length for generating and splitting ShareURL passwords, but the current policy value is not specified. The wrong length will cause incorrect generated/custom segmentation and inconsistent behavior across helpers.
Set `SHARE_GENERATED_PASSWORD_LENGTH` to exactly 18. When both CustomPassword and GeneratedPasswordIncluded flags are set, split as: generated = password.substring(0, SHARE_GENERATED_PASSWORD_LENGTH) and custom = password.substring(SHARE_GENERATED_PASSWORD_LENGTH). Example: password '1234567890abcdefghXYZ' to generated '1234567890abcdefgh', custom 'XYZ'. Counter-example: do NOT use 12 or 16.

### There is conflicting guidance about whether the incoming flags value should be normalized/coerced prior to bit evaluation or treated as an already-valid integer without any coercion. These instructions conflict and lead to incompatible implementations.
Normalize any present flags value to an unsigned 32-bit integer before evaluating bits. Specifically: treat undefined/null as missing (ignore that representation). For any present value, compute normalizedFlags = (Number(flagsValue) >>> 0). Use normalizedFlags for all bit checks. Examples: NaN to 0; 3.9 to 3; '5' to 5; -1 to 4294967295 (all bits set). Counter-example: do NOT throw on numeric strings like '5' and do NOT leave floats untruncated.

### Inputs may provide flags metadata via more than one representation at the same time. It is unclear how the helpers should behave when multiple representations coexist and disagree, since multiple deterministic policies are plausible and lead to different results.
Maintain write standardization while defining deterministic conflict handling: the helpers must accept input objects that may contain canonical flags and may also contain legacy Flags. Treat undefined/null as missing for each representation, but treat 0 as a present value. If both representations are present and their flag values differ, treat the effective flags value as 0 for bit evaluation and password splitting. If only one representation is present, use that value; if both are present and equal, use that value. Examples: { flags: 1, Flags: 4 } to effective flags 0; { Flags: 1 } to effective 1; { flags: 2 } to effective 2; { flags: 1, Flags: 1 } to effective 1. Counter-example: do NOT merge/OR values and do NOT pick one representation over the other when they disagree.
