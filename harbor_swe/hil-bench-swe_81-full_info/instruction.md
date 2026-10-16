# PROBLEM STATEMENT
# Title:
Authentication Bypass Vulnerability in Subsonic API

## Description:
There is an inconsistent behavior in how the Subsonic API processes certain authentication scenarios. Under some conditions, authentication failures may not be handled in a predictable manner. This fix should stay focused on authentication behavior rather than introducing new audit or analytics reporting.

## Current Behavior:
The authentication middleware allows some requests to continue processing even when authentication conditions are not fully satisfied, which can result in incorrect outcomes.

## Expected Behavior:
Authentication should behave consistently and align with the intended access control model. Requests that do not meet authentication requirements must be rejected with appropriate Subsonic error responses (code 40). The complete authentication lifecycle should be applied uniformly, regardless of which API surface processes the request. Token-based authentication must enforce salt security requirements per the organization's security policy.

## Steps to Reproduce:
1. Send requests to Subsonic API endpoints with varying authentication inputs (password, token, JWT, reverse proxy).
2. Attempt token-based authentication with short or missing salt values.
3. Compare the post-authentication processing behavior between the Native API and the Subsonic API for the same authenticated user.

## Impact:
Inconsistent authentication handling allows unauthorized access to protected API endpoints. Divergent post-authentication behavior between API surfaces can lead to inconsistencies in downstream systems that depend on the authentication lifecycle completing fully.



# REQUIREMENTS
- The Subsonic API authentication system properly validates all authentication attempts and rejects invalid credentials.

- Failed authentication attempts return appropriate Subsonic error responses with code 40.

- The authentication middleware consistently blocks unauthorized requests from proceeding to protected endpoints.

- The authentication system must handle all supported credential types: plaintext password, token-based (md5 hash with salt), JWT, and reverse proxy header-based authentication.

- Token-based authentication must enforce salt security requirements per the organization's security policy (e.g. minimum length or character set). Where a minimum length is specified by policy.

- Do not add new audit logs, analytics events, or historical authentication reporting as part of this fix.

- The post-authentication middleware chain on the Subsonic API must be functionally equivalent to the one on the Native API, ensuring no processing steps are omitted.



# PUBLIC INTERFACES
No new interfaces are introduced

## BLOCKER DETAILS
### The exact minimum salt length for token-based Subsonic authentication is not specified; security policies vary (e.g. 4, 6, 8, or 12 characters), and the correct value for this organization is not stated.

Token-based authentication must require `len(salt) >= 6`; a five-character salt must be rejected, and a six-character salt must be accepted when the rest of the credentials are valid.

### The requirements say to make the authentication lifecycle consistent across API surfaces, but they also say not to introduce new behavior or reporting. If a processing step exists on one API surface but not on another, does adding it to the second surface count as "new behavior" that should be avoided, or as a bug fix that restores intended parity?

Successful authentication must refresh an existing per-user activity state by calling UpdateLastLoginAt directly inside the authenticate middleware function after credentials are validated, rather than relying on a separate middleware in the router chain.

### The task requires invalid or incomplete authentication attempts to be rejected consistently, but it does not define whether authentication may continue when user resolution yields no concrete user record, such as a failed lookup, zero-value user, empty user, or placeholder state. Multiple handling strategies are possible from the visible text.
When user lookup fails, authentication must be rejected and must not succeed through a zero-value, empty, or placeholder user state. Additionally, after successful lookup and credential validation, the authenticate middleware must verify that the resolved user has a non-empty ID; a user with an empty ID must be rejected as a placeholder state even if the lookup returned no error.
