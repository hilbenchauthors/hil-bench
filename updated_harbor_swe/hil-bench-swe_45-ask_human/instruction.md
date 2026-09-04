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
