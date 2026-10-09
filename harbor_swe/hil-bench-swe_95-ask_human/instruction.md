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
