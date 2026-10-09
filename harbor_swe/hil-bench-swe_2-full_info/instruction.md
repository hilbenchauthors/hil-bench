# PROBLEM STATEMENT
# Subsonic API integer-width migration with legacy compatibility policies

### Current Behavior

Subsonic API responses expose multiple integer-like fields using Go's default `int`, which is architecture-dependent and causes schema drift for strict clients.
The migration to 32-bit integer responses is required, but rollout must also respect internal compatibility policies used by legacy clients.

### Expected Behavior

All user-facing integer response fields covered by this task should be emitted using the migration policy for 32-bit compatibility.
For values that cannot be represented directly in 32 bits, apply the approved overflow sentinel behavior used by mobile consumers.

Now-playing responses must continue exposing synthetic `playerId` values generated from session ordering, using the approved base-offset strategy from platform policy.
`minutesAgo` must be emitted as whole minutes following legacy Subsonic behavior for elapsed-time display.

Rollout and folder layout are selected per request via the `responseWidthMode` and `folderEmitMode` query parameters.

### Implementation expectations

Keep all request-scoped policy (rollout mode, folder emission, int narrowing, overflow handling) in **one dedicated Go source file** under `server/subsonic` (see interfaces), and thread `*http.Request` through shared mapping helpers and builders so every handler in scope applies the same rules. Do not duplicate policy checks at scattered call sites beyond what is needed to pass the request into existing mappers.
If shared helpers are introduced or signature-updated for request-scoped policy, in-scope handlers must invoke those helpers (or equivalent inline assignments) so serialized fields in returned responses follow the same request-scoped policy end-to-end.

A complete solution **compiles**: every helper or handler signature change must include **all** callers in this package (and transitive callers listed in the interfaces doc). After edits, run `go build` (or tests) frequently so errors are fixed before layering more changes. The policy module alone is not sufficient unless every in-scope assignment path uses it through the wired helpers and handlers.

### Scope

This task affects Subsonic response structures and mapping/building code paths, including but not limited to:

The scope also includes transitive consumers of shared helpers used by affected responses, even when those consumers are not listed individually.

- `Genre`
- `Artist`
- `ArtistID3`
- `AlbumID3`
- `Child`
- `Directory`
- `NowPlayingEntry`
- `Playlist`
- `Share`
- `User`
- `Error`

### Notes

No new endpoints are introduced.
The solution must keep XML/JSON response compatibility for strict schema clients while following the compatibility-policy constraints.



# REQUIREMENTS
- Error responses must expose the `code` field as a 32-bit integer in serialized API output.

- The `responseWidthMode` query parameter for this Subsonic subsystem accepts exactly these five tokens (and no others for policy purposes): `strict32`, `hybrid32`, `compat32`, `legacy_int`, `audit_only`.

- Artist metadata must expose `albumCount` and `userRating` as 32-bit integers in both `Artist` and `ArtistID3` forms.

- When `responseWidthMode=strict32`, migrated Subsonic integer fields must be narrowed to signed 32-bit in serialized output.

- Genre metadata must expose `songCount` and `albumCount` as 32-bit integers.

- `Child` media-item responses must use 32-bit integers for track-like counters and media-duration fields included by this migration.

- Album and artist directory responses must apply the migration policy to integer counters and rating-related fields.

- Keep legacy integer widths in the response contract and limit this mode to observability/validation of would-be narrowing.

- `NowPlayingEntry` must expose `minutesAgo` and synthetic `playerId` as 32-bit integers.

- `minutesAgo` must be represented in whole minutes using legacy elapsed-time rounding behavior.

- The `folderEmitMode` query parameter for folder serialization in this subsystem accepts exactly these five tokens: `scalar`, `list`, `auto`, `csv`, `json_string`.

- The synthetic `playerId` generator must apply the base offset before adding the session index.

- When source values exceed the signed 32-bit range, outputs must use the overflow sentinel required by downstream mobile clients.

- When `responseWidthMode=compat32`, clients still expect migrated integer fields to be emitted as signed 32-bit values, including overflow sentinel handling.

- Playlist metadata must expose `songCount` and `duration` as 32-bit integers.

- User configuration output in both `GetUser` and `GetUsers` must expose `maxBitRate` as a policy-mapped 32-bit integer sourced from authenticated player context when available, and folder identifiers in those same handlers must reflect `folderEmitMode` and repeated `folder` query behavior as described across these requirements.

- Defining migration or folder-emission helpers is not sufficient by itself: handlers in scope must assign policy-derived values directly on returned response structs so wire output follows request policy.

- Shared-item metadata must expose `visitCount` as a 32-bit integer.

- For `User` serialization, `folderEmitMode` governs how folder selections from the request (including multi-value `folder` parameters) are reflected in serialized output.

- All components that construct or map Subsonic responses must use consistent integer-width behavior so internal model values and serialized output do not diverge.

- If a shared response-mapping or response-building helper in `server/subsonic` changes signature for this migration, all in-scope call sites must be updated to preserve request-scoped behavior and successful compilation.

- Internal compatibility notes disagree on how multi-value `folder` query parameters and `folderEmitMode` combine when populating `User.folder` in `GetUser`/`GetUsers`; behavior must be consistent across both handlers.



# PUBLIC INTERFACES
Scope: Subsonic HTTP handlers and mappers under `server/subsonic` must apply a single request-scoped integer and folder-emission policy. Implementations should add a dedicated policy module and thread `*http.Request` through shared conversion helpers so every endpoint in scope stays consistent.

- Path: `server/subsonic/migration_policy.go`
- Name: `toResponseInt`
- Type: `Function`
- Input: `r *http.Request, value int64`
- Output: `int`
- Description: Applies int32 migration (narrowing and out-of-range handling) when rollout mode on the request enables migration; otherwise returns `int(value)` unchanged. Used at assignment sites for Subsonic response integer fields in scope.

- Path: `server/subsonic/migration_policy.go`
- Name: `minutesAgoValue`
- Type: `Function`
- Input: `start time.Time, now time.Time`
- Output: `int`
- Description: Computes whole-minute `minutesAgo` for now-playing rows from a fixed `start` and handler-captured `now` (capture `now` once per handler when filling multiple entries so elapsed time is consistent).

- Path: `server/subsonic/migration_policy.go`
- Name: `nowPlayingPlayerID`
- Type: `Function`
- Input: `sessionIndex int`
- Output: `int`
- Description: Maps 0-based session order in the now-playing loop to the synthetic `playerId` integer before optional migration narrowing.

- Path: `server/subsonic/migration_policy.go`
- Name: `responseWidthMode`
- Type: `Function`
- Input: `r *http.Request`
- Output: `string`
- Description: Reads the rollout query parameter; `isInt32MigrationEnabled` interprets it against requirements (exact token equality). Does not prescribe which tokens enable migration here. Uses the same request helper as other Subsonic query parsing.

- Path: `server/subsonic/migration_policy.go`
- Name: `folderEmitMode`
- Type: `Function`
- Input: `r *http.Request`
- Output: `string`
- Description: Reads the folder-emission query parameter used with `shouldEmitFolderList` and `GetUser`/`GetUsers` folder serialization. Uses the same request helper as other Subsonic query parsing.

- Path: `server/subsonic/migration_policy.go`
- Name: `isInt32MigrationEnabled`
- Type: `Function`
- Input: `r *http.Request`
- Output: `bool`
- Description: Derives whether `toResponseInt` should enforce int32 migration for this request from `responseWidthMode` and the rules in requirements (exact token equality). Maintain contract stability on migration-on decisions.

- Path: `server/subsonic/migration_policy.go`
- Name: `shouldEmitFolderList`
- Type: `Function`
- Input: `r *http.Request`
- Output: `bool`
- Description: Derives whether `User` responses should populate repeated `folder` ids from the request query, based on `folderEmitMode` and the rules in requirements. Uses the same query-parameter helpers as other Subsonic parsing.

- Path: `server/subsonic/helpers.go`
- Name: `toGenres`
- Type: `Function`
- Input: `r *http.Request, genres model.Genres`
- Output: `*responses.Genres`
- Description: Builds genre list applying `toResponseInt` to numeric genre counters.

- Path: `server/subsonic/helpers.go`
- Name: `childFromMediaFile`
- Type: `Function`
- Input: `ctx context.Context, mf model.MediaFile, r *http.Request`
- Output: `responses.Child`
- Description: Maps a media file to `Child` with migrated ints for track, duration, bit rate, disc, year, rating, etc.

- Path: `server/subsonic/helpers.go`
- Name: `childrenFromMediaFiles`
- Type: `Function`
- Input: `ctx context.Context, mfs model.MediaFiles, r *http.Request`
- Output: `[]responses.Child`
- Description: Batch wrapper passing `r` into `childFromMediaFile`.

- Path: `server/subsonic/helpers.go`
- Name: `childFromAlbum`
- Type: `Function`
- Input: `_ context.Context, al model.Album, r *http.Request`
- Output: `responses.Child`
- Description: Maps an album directory child with migrated duration, song count, year, and rating fields.

- Path: `server/subsonic/helpers.go`
- Name: `childrenFromAlbums`
- Type: `Function`
- Input: `ctx context.Context, als model.Albums, r *http.Request`
- Output: `[]responses.Child`
- Description: Batch wrapper passing `r` into `childFromAlbum`.

- Path: `server/subsonic/helpers.go`
- Name: `toArtist`
- Type: `Function`
- Input: `r *http.Request, a model.Artist`
- Output: `responses.Artist`
- Description: Existing mapper; must use `toResponseInt` for `AlbumCount` and `UserRating`.

- Path: `server/subsonic/helpers.go`
- Name: `toArtistID3`
- Type: `Function`
- Input: `r *http.Request, a model.Artist`
- Output: `responses.ArtistID3`
- Description: Existing mapper; must use `toResponseInt` for `AlbumCount` and `UserRating`.

- Path: `server/subsonic/browsing.go`
- Name: `buildArtistDirectory`
- Type: `Method`
- Input: `r *http.Request, ctx context.Context, artist *model.Artist`
- Output: `*responses.Directory, error`
- Description: Artist directory tree; applies `toResponseInt` to counters/ratings and passes `r` into `childrenFromAlbums`.

- Path: `server/subsonic/browsing.go`
- Name: `buildAlbumDirectory`
- Type: `Method`
- Input: `r *http.Request, ctx context.Context, album *model.Album`
- Output: `*responses.Directory, error`
- Description: Album directory; migrated ints on ratings and counts; passes `r` into `childrenFromMediaFiles`.

- Path: `server/subsonic/browsing.go`
- Name: `buildAlbum`
- Type: `Method`
- Input: `r *http.Request, ctx context.Context, album *model.Album, mfs model.MediaFiles`
- Output: `*responses.AlbumWithSongsID3`
- Description: Album with songs ID3 view; migrated song count, duration, year, rating; passes `r` into `childrenFromMediaFiles`.

- Path: `server/subsonic/playlists.go`
- Name: `getPlaylist`
- Type: `Method`
- Input: `r *http.Request, ctx context.Context, id string`
- Output: `*responses.Subsonic, error`
- Description: Fetches playlist and builds response using request-scoped migration.

- Path: `server/subsonic/playlists.go`
- Name: `buildPlaylist`
- Type: `Method`
- Input: `p model.Playlist, r *http.Request`
- Output: `*responses.Playlist`
- Description: Sets `SongCount` and `Duration` via `toResponseInt`.

- Path: `server/subsonic/playlists.go`
- Name: `buildPlaylistWithSongs`
- Type: `Method`
- Input: `ctx context.Context, p *model.Playlist, r *http.Request`
- Output: `*responses.PlaylistWithSongs`
- Description: Composes playlist header and `Entry` via `childrenFromMediaFiles` with `r`.

- Path: `server/subsonic/api.go`
- Name: `sendError`
- Type: `Function`
- Input: `w http.ResponseWriter, r *http.Request, err error`
- Output: none
- Description: Error payload `code` must be set through `toResponseInt` so serialized error codes follow the same int32 policy as other responses.

- Path: `server/subsonic/sharing.go`
- Name: `buildShare`
- Type: `Method`
- Input: `r *http.Request, share model.Share`
- Output: `responses.Share`
- Description: `VisitCount` via `toResponseInt`; `Entry` from `childrenFromAlbums` / `childrenFromMediaFiles` with `r`.

- Path: `server/subsonic/users.go`
- Name: `GetUser`
- Type: `Method`
- Input: `r *http.Request`
- Output: `*responses.Subsonic, error`
- Description: Sets `MaxBitRate` from the authenticated player through `toResponseInt`; when `shouldEmitFolderList` is true, fills `Folder` from repeated `folder` query values using the same utilities as other Subsonic param parsing.

- Path: `server/subsonic/users.go`
- Name: `GetUsers`
- Type: `Method`
- Input: `r *http.Request`
- Output: `*responses.Subsonic, error`
- Description: Same `MaxBitRate` and optional folder list behavior as `GetUser` for returned user rows.

- Path: `server/subsonic/searching.go`
- Name: `Search2`
- Type: `Method`
- Input: `r *http.Request`
- Output: `*responses.Subsonic, error`
- Description: Search results: artist ints and album/song children built with `r` passed through mappers.

- Path: `server/subsonic/searching.go`
- Name: `Search3`
- Type: `Method`
- Input: `r *http.Request`
- Output: `*responses.Subsonic, error`
- Description: Same pattern as `Search2` for album and song children.

- Path: `server/subsonic/album_lists.go`
- Name: `GetAlbumList`, `GetAlbumList2`, `GetStarred`, `GetRandomSongs`, `GetSongsByGenre`, `GetNowPlaying`
- Type: `Method`
- Input: per existing signatures (`http.ResponseWriter` where present, `r *http.Request`)
- Output: `*responses.Subsonic, error` (or tuple with writer for list endpoints)
- Description: All list/starred/random/genre/now-playing builders must pass `r` into `childrenFromAlbums`, `childrenFromMediaFiles`, or `childFromMediaFile`, and use `toResponseInt` for now-playing `MinutesAgo` and `PlayerId` with a single `now` timestamp for the loop body.

## BLOCKER DETAILS
### The problem statement and requirements require mobile-aligned overflow handling when a source integer is outside signed 32-bit range, but neither names the concrete int32 value to emit. What exact int32 value should be used for overflowed fields?

Use the exact sentinel `-2147482977` (minus sign included, base-10, no separators) for any overflowed signed-int field mapped into int32. When migration is active, compare the source value against `math.MaxInt32` and `math.MinInt32` (not ad-hoc literals) to detect overflow. Example: `3000000000` must serialize as `-2147482977`, not `2147483647`, `-2147483648`, or `0`. Go: `toResponseInt` returns `int`; do not wrap in `int32(...)` when assigning to `int`-typed response fields.

### The problem statement and requirements describe a fixed base offset before the session index for synthetic `playerId`, but neither states the numeric offset. Which exact value should be added before session index mapping?

Use a fixed base offset of `41000` with 0-based session indices: `nowPlayingPlayerID(i) := 41000 + i`, then `toResponseInt(r, int64(...))` into `NowPlayingEntry.PlayerId`, which is `int` in `responses` (not `int32`). Example: first session (`i=0`) emits `41000`, not `1`, `0`, or `10000`.

### The task requires emitting `minutesAgo` as whole minutes using legacy behavior, but it does not define whether to floor, ceil, or round fractional minutes. Which rounding rule is the required interpretation for positive elapsed durations?

Use ceiling for strictly positive elapsed time: after computing `elapsed := now.Sub(start)`, if `elapsed <= 0` then emit `0` minutes; otherwise `minutesAgo = int(math.Ceil(elapsed.Minutes()))`. Example: `61s` must emit `2`, not `1`; `1s` must emit `1`, not `0`; equal `start` and `now` must emit `0`. `NowPlayingEntry.MinutesAgo` is `int` in `responses`; assign via `toResponseInt` without spurious `int32` casts.

### The problem statement and requirements refer to multiple `responseWidthMode` tokens in connection with rollout and 32-bit integer behavior, but they do not spell out one explicit, joint rule for which tokens must enable `toResponseInt` migration versus keeping legacy wide integer output. The public interfaces also state that `responseWidthMode` parsing does not, by itself, prescribe which tokens turn migration on (`isInt32MigrationEnabled` derives that from requirements). Taken together, more than one consistent activation policy is compatible with the text unless an extra convention is assumed.
Requirements enumerate the `responseWidthMode` tokens (including `strict32`, `hybrid32`, and `compat32`) and give separate conditional bullets for some modes plus legacy-width language elsewhere, without stating one combined boolean condition for which tokens enable `toResponseInt` migration; multiple activation policies fit the text unless one is fixed. The approved reconciliation is uncommon: enable int32 migration only when `responseWidthMode` is exactly `strict32` or exactly `compat32`—not `hybrid32` (exact spelling via `utils.ParamString(r, \"responseWidthMode\")`). Counterintuitive: `hybrid32` stays on the legacy int path even though it sounds transitional. Example: overflow uses the sentinel in `strict32` and `compat32`; `hybrid32`, `legacy_int`, and `audit_only` keep raw values without narrowing. Go implementation: `toResponseInt` returns `int`. Subsonic response structs use `int` for many counters (`Genre.SongCount`, `Genre.AlbumCount`, `User.MaxBitRate`, etc.). Assign `toResponseInt(...)` directly to those fields. Do **not** write `int32(toResponseInt(...))` for wide legacy values: e.g. `int32(3000000000)` truncates because `3000000000 > math.MaxInt32`; legacy modes must preserve `3000000000` in an `int` field. Cast to `int32` only where the struct field is actually `int32` and the value is in range.

### Requirements call for `User.folder` serialization to account for multi-value `folder` parameters and for `folderEmitMode`, while noting internal compatibility notes disagree on how those inputs combine; they do not pin one joint rule.
Requirements enumerate `folderEmitMode` tokens (including `scalar`, `list`, and `auto`) and describe repeated `folder` parameters and `User` serialization across separate bullets; more than one joint list-emission policy fits the text until one is fixed. The approved reconciliation is uncommon: emit `folder` as a repeated list only when `folderEmitMode` is exactly `scalar` or exactly `list` (exact spelling via `utils.ParamString(r, \"folderEmitMode\")`). Use `utils.ParamInts(r, \"folder\")` when either applies. Counterintuitive: `auto` does not populate repeated folder ids even though it often implies adaptive expansion elsewhere. Example: `scalar` and `list` return repeated folder ids from the query; `auto`, `csv`, and `json_string` leave `folder` empty. `User.Folder` is `[]int`; map folder ids with `toResponseInt` per element without changing list shape.
