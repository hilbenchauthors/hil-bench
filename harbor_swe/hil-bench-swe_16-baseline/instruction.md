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
