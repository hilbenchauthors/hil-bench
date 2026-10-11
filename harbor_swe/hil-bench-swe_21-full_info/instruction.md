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

## BLOCKER DETAILS
### The text requires gain values from multiple tag formats to be normalized to the application's expected loudness reference, but it does not define the exact conversion rule between the numeric representations. Multiple mathematically reasonable conversions exist, which blocks a uniquely correct implementation.
R128 gain tag values are Q7.8 fixed-point integers and must be converted to dB by dividing by 256.0, then applying a fixed +4.637 dB offset to align with the application's ReplayGain reference. ReplayGain gain tag values are already in the application's reference and must be used directly as parsed floats (no additional offset).

### Gain tags may contain multiple values for the same key. The text does not define which value should be used for gain calculation, and multiple reasonable choices exist (first value, last value, or rejecting multi-valued tags), which leads to incompatible behavior.
If a gain tag key contains multiple values, the scanner must use the last value in the list for parsing and normalization.

### The requirements state that when both gain formats are present the scanner must prefer the alternative format, and also that it must prefer the ReplayGain-style value to preserve existing externally observed behavior. When both formats are present for the same logical field, these instructions cannot both be satisfied without a defined preference policy.
When both formats are present, the preference policy is field-specific: album gain must prefer ReplayGain, while track gain must prefer R128. If the preferred format for a field is absent, the scanner must use the other format.
