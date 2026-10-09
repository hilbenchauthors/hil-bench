# PROBLEM STATEMENT
##Scanner gain handling does not fully align across supported tag formats##

**Description**

The metadata scanner currently reads gain-related tags but does not consistently interpret all formats used in modern audio files. Different tagging schemes may represent loudness adjustment values differently, and the scanner should recognize these formats while keeping a consistent loudness reference with existing outputs.

**Steps to reproduce**
	1.	Add an audio file (for example, OPUS) that includes gain-related tags in a format different from the traditional ReplayGain fields.
	2.	Run a library scan.
	3.	Check the track/album gain reported by the application or by the metadata layer.

**Actual Behavior**
- Gain values may be missing or inconsistent depending on the tag format used in the file.

**Expected Behavior**
- The scanner recognizes gain information from the supported tag formats for both track and album gain.
- Reported gain uses a loudness reference consistent with what the application expects.
- Behavior is consistent across files regardless of which supported gain tag format is used.
- Invalid gain inputs do not break scanning and are handled safely.


# REQUIREMENTS
- The scanner must support reading gain values from both traditional ReplayGain-style tags and alternative gain tag formats commonly used in modern codecs, for both album and track gain fields.
- Tag keys must be treated as lowercase strings when looking up gain values. The alternative gain tags use the lowercase keys `r128_track_gain` and `r128_album_gain`.
- Gain tag keys may occur multiple times for the same logical field and yield multiple candidate values. The scanner must handle such multi-valued gain tags consistently.
- When multiple gain formats are present for the same logical field, the scanner must prefer the alternative gain format.
- When multiple gain formats are present for the same logical field, the scanner must prefer the ReplayGain-style value.
- Gain tag values may be expressed in different numeric representations depending on the tag format. The scanner must interpret these values correctly and normalize them to the loudness reference expected by the application.
- Gain handling must remain compatible with the application’s existing loudness model and user expectations.
- The scanner must avoid introducing changes that could alter the externally observed gain behavior for files that already rely on the existing gain format handling.
- If the value of any gain tag is missing, not a valid number, or not a finite value, the scanner must return a safe default gain value and must not raise an error.
- If none of the candidate gain tags yields a valid value (including when all candidate tags are absent), return 0.0 and emit a warning log entry.



# PUBLIC INTERFACES
No new interfaces are introduced.

Existing behavior is surfaced through the metadata tag accessors in `scanner/metadata/metadata.go`, including:
- `Tags.RGTrackGain()` and `Tags.RGAlbumGain()` for gain values
- `Tags.RGTrackPeak()` and `Tags.RGAlbumPeak()` for peak values
