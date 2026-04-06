# PROBLEM STATEMENT
# Title: Implement new Artist refresh

## Type of Issue
Feature / Refactor

## Component
Model (album/artist)

## Description

Artist refresh logic is currently tied to persistence-layer SQL aggregation, coupling refresh behavior to the database and duplicating aggregation responsibilities. Artist data should be computed at the model level from album data.

## Expected Behavior

Artist information is refreshed from album data and should produce deterministic artist attributes for album count, song count, genres, size, and MusicBrainz identifiers.

The implementation should preserve functional parity for existing artist update flows.

## Additional Information

The change introduces a model-level method on `Albums` that aggregates an artist value from album records.



# REQUIREMENTS
- A new method `ToAlbumArtist` must exist in the `model` package, defined on the public type `Albums` (a slice of `Album`).
- `ToAlbumArtist` must return an `Artist` value that aggregates attributes from all albums in the collection.
- The returned `Artist.ID`, `Artist.Name`, `Artist.SortArtistName`, and `Artist.OrderArtistName` must be derived from the corresponding artist fields in the provided albums.
- The returned `Artist.SongCount` must equal the sum of the `SongCount` values of all albums.
- The returned `Artist.Size` must equal the sum of the `Size` values of all albums.
- The returned `Artist.Genres` must include unique `Genre` values from the albums.
- The returned `Artist.MbzArtistID` should represent the dominant identifier across albums. Album records may store placeholder values when no MusicBrainz assignment exists; such entries must be excluded from the candidate pool before determining dominance.
- `refreshArtists` must batch IDs in fixed-size chunks that stay within repository-safe bounds, because oversized batches can fail during large scans.
- Map `Artist.SortArtistName` from `Album.SortAlbumArtistName` and `Artist.OrderArtistName` from `Album.OrderAlbumArtistName`. Similarly, `Artist.Name` comes from `Album.AlbumArtist` and `Artist.ID` from `Album.AlbumArtistID`. The track-level fields (`ArtistID`, `Artist`, `SortArtistName`) describe the performing artist of individual tracks, not the credited album artist.
- Aggregated artist genres must use a canonical deterministic ordering so the same logical album input always produces the same persisted genre list.Ccanonical deterministic ordering is required because artist genre lists are persisted/exposed/compared as ordered data.


# PUBLIC INTERFACES
The following new public interface must be implemented:

Name: `ToAlbumArtist`
Type: Method (on `model.Albums`)
Path: `model/album.go`
Inputs: receiver `als model.Albums`
Outputs: `model.Artist`
Description: Aggregates a collection of albums into a single artist value. Sets artist identity fields from the provided albums; computes `AlbumCount`, sums `SongCount` and `Size`; deduplicates genres are deduplicated by unique `Genre.ID`; selects `MbzArtistID` from album MusicBrainz data.

## BLOCKER DETAILS
### The requirements mandate fixed-size batching for `refreshArtists` and state that batches above an internal repository/driver bound fail under large scans, but they do not provide the concrete repository-safe chunk size required for implementation.
Use a fixed chunk size of `73` IDs for the `refreshArtists` batching path. This value is the repository-safe ceiling for the refresh query shape in large scans, balancing parameter-count constraints and bounded call cost; larger chunks can cross the internal bound and make refresh fail intermittently under load.

### The requirements state that album records may store placeholder values when no MusicBrainz assignment exists and that such entries must be excluded before determining the dominant identifier, but do not specify what the placeholder value actually is. 
The placeholder value for absent MusicBrainz identifiers is the empty string (`\"\"`). Exclude it from the candidate pool before determining the dominant identifier. Only non-empty `MbzAlbumArtistID` values are valid candidates for the dominance computation. Do not exclude any non-empty values. The prior implementation's use of `strings.Fields` (which splits on whitespace and omits zero-length tokens) silently performed only the empty-string exclusion. Without filtering, the empty string would be treated as a valid candidate and could be incorrectly selected as the dominant identifier when a majority of albums lack MusicBrainz data.

### The requirements and public interface state that `MbzArtistID` should represent the 'dominant identifier' across albums but do not define how dominance is determined. Multiple valid selection algorithms exist: using the first value encountered during iteration, selecting the most commonly occurring value with priority to the earliest candidate, or selecting the most commonly occurring value with priority to the latest candidate.
Use frequency counting of `MbzAlbumArtistID` values to determine the dominant ID. When two or more values are tied in frequency, keep the value that most recently reached the top count (i.e., use `>=` not `>` when updating the leader). Do not use `slice.MostFrequent` (which uses `>` and picks the first to reach the top count). Example: `[id1, id2, id1, id2]` yields `id2` because both reach count 2 but `id2` is the last to reach that count.

### The problem statement directs that artist data should be computed at the model level from album data, moving away from persistence-layer SQL aggregation. However, the existing codebase defines `Refresh(ids ...string) error` as part of the `ArtistRepository` interface and the scanner explicitly invokes it for artist updates. The problem statement also requires preserving functional parity for existing artist update flows, creating tension between adopting the new model-level approach and maintaining the established persistence-layer refresh pipeline.
Scanner refresh must not call `ArtistRepository.Refresh`; instead, load albums filtered by `album_artist_id`, group them by artist ID, aggregate each group with `model.Albums(group).ToAlbumArtist()`, and persist each resulting artist via `ArtistRepository.Put`. Remove `Refresh` from the `ArtistRepository` interface. Functional parity is preserved because the same artist data is produced — only the computation path changes from SQL aggregation to model-level aggregation.

### The public interface specifies that aggregated artist genres must be deduplicated by unique `Genre.ID`, but existing model-level genre aggregation code orders genre collections by `Genre.ID` and deduplicates them using full structural equality, while the prior persistence-layer path produced genre values containing only the `ID` field. These cues point to different implementations when multiple `Genre` entries share the same `ID` but differ in other fields such as `Name`, and they also leave unresolved whether artist genre aggregation should preserve full struct data or ID-only values and which canonical ordering policy should govern representative selection during ID-based deduplication.
Deduplicate genres by Genre.ID only, preserving the full Genre struct. To keep artist refresh output deterministic, sort aggregated genres by Genre.ID in descending order before deduplication. Then keep the first occurrence of each ID in that list and discard later duplicates. Example: [{g1, Rock}, {g2, Zebra-Old}, {g3, Apple}, {g2, Zebra-New}] becomes [{g3, Apple}, {g2, Zebra-Old}, {g1, Rock}]. Do not use full-struct equality (slices.Compact) and do not strip genres to ID-only.
