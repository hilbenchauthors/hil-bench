# PROBLEM STATEMENT
## Title: Subsonic Router Wiring Updated for Shared Playback and Scanner Services

### Description

The Subsonic API router is being updated as part of a dependency-injection cleanup that introduces an additional playback collaborator and a shared scanner accessor. Application wiring, background startup, and test instantiation all need to stay consistent with the new construction flow. Existing lightweight and test-oriented setups still need to construct the same router entrypoint with the non-playback wiring they already use, while playback-dependent behavior and request-driven media access are expected to come only from the services assembled by the application.



# REQUIREMENTS
- Subsonic router construction must accept the additional playback collaborator everywhere the updated constructor is used.
- Existing lightweight and test-oriented router instantiations must remain valid without requiring playback wiring to be brought up first.
- Jukebox handling must use the playback service supplied during router construction when that service is available.
- Playback-backed request handling must remain usable before background startup begins.
- The shared scanner accessor must expose one process-wide scanner service for application wiring.
- Repeated application-setup calls must preserve consistent shared-scanner behavior.



# PUBLIC INTERFACES
- Path: /app/cmd/wire_gen.go
- Name: GetPlaybackServer
- Type: function
- Input: None
- Output: playback.PlaybackServer
- Description: Returns the playback service assembled for application wiring. The returned service is intended for router and startup integration.

- Path: /app/cmd/wire_injectors.go
- Name: GetPlaybackServer
- Type: function
- Input: None
- Output: playback.PlaybackServer
- Description: Declares the injector used to build the playback service for application wiring. It mirrors the generated helper used outside wire-inject mode.

- Path: /app/server/subsonic/api.go
- Name: New
- Type: function
- Input: the existing router collaborators, plus playback support passed through constructor wiring for playback-aware routes
- Output: *Router
- Description: Constructs the single Subsonic router entrypoint used by both legacy lightweight call sites and playback-aware routes.

- Path: /app/scanner/scanner.go
- Name: GetInstance
- Type: function
- Input: ds model.DataStore, playlists core.Playlists, cacheWarmer artwork.CacheWarmer, broker events.Broker
- Output: Scanner
- Description: Returns the shared scanner service used by application setup. The accessor is intended to provide one application-scoped scanner service.

## BLOCKER DETAILS
### The task expects playback-backed request handling to work as soon as application wiring is in place, but it does not identify the extra construction input needed to make that early access work.

Change the playback accessor to `playback.GetInstance(ds model.DataStore)` and construct the playback service with the datastore used by application wiring, keeping that datastore available for request-time media lookups before Run executes. Example: a media lookup can read an item that was inserted into that datastore before startup. Counterexample: leaving `GetInstance` as a no-argument singleton and waiting for background startup to establish data access.

### The new scanner accessor is shared across application wiring, but the task does not say how a later call with a different collaborator set should be handled once the shared scanner has already been established.

Implement this policy in `scanner.GetInstance(ds, playlists, cacheWarmer, broker)` itself. Return one process-wide Scanner instance. A later call with the same collaborator identities returns that shared instance. A later call with any different datastore, playlists service, cache warmer, or broker must fail immediately instead of silently reusing or rebuilding the shared scanner. Example: two calls with the same collaborator objects return the same scanner, while a later call with a different datastore panics. Counterexample: quietly keeping the old scanner when later calls supply different collaborators.

### The task says the same router entrypoint must remain valid for legacy lightweight call sites that do not bring playback wiring up first, while the updated requirements and constructor surface also say that router construction now accepts an added playback collaborator for playback-aware use.

Keep `subsonic.New(...)` callable without a playback collaborator, while also accepting a playback collaborator as the final optional constructor argument when playback-aware routes need it. Allow the router to be constructed without a playback service. Non-jukebox handlers remain callable in that state, including when jukebox support is enabled. Jukebox control must use the injected playback service when present and must return an error when none was supplied, rather than consulting package-global playback state. Example: ping succeeds without playback, while jukebox control errors until a playback service is injected. Counterexample: automatically falling back to package-global playback state for jukebox requests.
