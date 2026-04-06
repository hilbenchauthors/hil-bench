# PROBLEM STATEMENT
## Title: Per-user UserPropsRepository access produces inconsistent results

### Description

The `UserPropsRepository` does not consistently operate on the correct user's data, which affects features that depend on isolated user state, including the LastFM integration. User identity scoping is not consistently enforced at repository boundaries, causing uncertainty about which users' properties are read or written across layers. The repository layer must be the canonical authority for user-scoping: it should derive the active user from the request context at its boundary, ensuring callers do not need to provide the user identity directly.

### Expected behavior

Operations must never return or modify data belonging to a different user. Any feature that persists or reads per-user state must never read or modify another user's state.

### Actual behavior

User property operations can cause reads or writes to target the wrong user or fail to retrieve the correct per-user data. This ambiguity is visible in flows that store, load, or clear user-specific LastFM state.


# REQUIREMENTS
- `UserPropsRepository` must be user-scoped, and all operations must be explicitly directed at a specific user.

- The repository implementation must isolate data between different users and avoid cross-user reads or writes.

- LastFM behavior across all components must be user-scoped, and operations must be performed on behalf of the correct user and must never affect another user's state.

- The scrobble operation must enforce a maximum number of entries processed per invocation and must silently truncate any excess entries beyond that limit.

- The scrobble operation must sort entries into a deterministic order before submitting them to the upstream API.


# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The requirements state that the scrobble operation must enforce a maximum number of entries and truncate excess entries, but do not specify what that maximum number is.
Truncate the scrobbles slice to a maximum of 80 entries before applying any sorting. If the input has more than 80 scrobbles, only the first 80 must be sent. Sorting is applied after truncation, not before. Example: a batch of 60 scrobbles must result in exactly 60 being submitted. Do NOT use any other value such as 30 or 100.

### The requirements state that scrobbles must be sorted into a deterministic order before submission, but do not specify which field to sort by or in which direction.
Sort scrobbles in descending order by their TimeStamp field (using its temporal comparison methods) before submitting to the LastFM API. Example: if input contains timestamps [300, 100, 200], they must be submitted in the order [300, 200, 100]. Do NOT sort ascending or by any other field, such as track title or artist name.

### The Problem Statement says the repository layer must derive user identity from the active request context at its own boundary, ensuring callers do not supply it, while the Requirements say operations must be explicitly directed at a specific user. These directives conflict on whether user identity is supplied by callers or determined inside the repository layer.
Resolve the contradiction by choosing the caller-supplied identity as the single source of truth for repository operations. UserPropsRepository methods (Put, Get, Delete, DefaultGet) must take explicit userId arguments and scope all reads and writes by that userId. The repository must work the same with or without an authenticated user in context, and operations for one userId must not affect another userId. All intermediate wrapper layers that call UserPropsRepository, including sessionKeys, must also be updated to accept userId as an explicit parameter and forward it to the repository; they must NOT extract userId from the context themselves. Callers of those wrappers must pass the userId argument they already receive directly to the wrapper methods.
