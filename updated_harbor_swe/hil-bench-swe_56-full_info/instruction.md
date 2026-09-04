# PROBLEM STATEMENT
# Title

Contact import mishandles date fields supplied as plain text

## Description

Date fields coming from CSV and related sources often arrive as unstructured text. The pipeline does not treat these values consistently: some never become real calendar dates, others lose information needed for stable display and export.

## Expected Behavior

Parsed dates should reflect the intended calendar day where the text is unambiguous. When interpretation fails, the product should not substitute a fabricated calendar date for the user’s original text anywhere dates flow from import into stored contact data.

## Actual Behavior

Behavior varies by format and code path; exported vCards and the contact UI do not always match user expectations.


# REQUIREMENTS
- Add an exported `guessDateFromText` in `packages/shared/lib/contacts/property.ts` that returns a valid `Date` when the input can be interpreted, or `undefined` when it cannot.

- Use that helper from `getDateValue` in `packages/shared/lib/contacts/helpers/csvFormat.ts` so CSV-derived dates are resolved through the same logic.

- Use the same helper in `getDateFromVCardProperty` for text-based values. All paths through `getDateFromVCardProperty` must yield a defined `Date` suitable for vCard field serialization.

- Ensure results do not shift calendar meaning for values that parse successfully.


# PUBLIC INTERFACES
Name: `guessDateFromText`

Type: Arrow function

Path: `packages/shared/lib/contacts/property.ts`

Description: Attempts to convert a string into a JavaScript `Date`. Parameters: `text` (`string`). Returns `Date` if a reliable parse exists, otherwise `undefined`.

## BLOCKER DETAILS
### Requirements say text inputs must parse when interpretable, but do not say how to treat invisible or non-printing characters that may appear at the boundaries of imported fields.
MUST remove leading and trailing U+FEFF (BYTE ORDER MARK) and U+200B (ZERO WIDTH SPACE) from the input string before any parsing attempt, using a single replace on both ends (e.g. /^[\\\\uFEFF\\\\u200B]+|[\\\\uFEFF\\\\u200B]+$/g), then apply String.prototype.trim() on the result. Only after that normalization should any date-parsing attempt be made. Counter-example: Do NOT attempt to parse the raw string when U+200B or U+FEFF remains at the start or end.

### Slash-separated numeric dates like 15/06/1969 versus 03/12/1969 admit more than one interpretation (day/month/year vs month/day/year). The requirements do not specify disambiguation rules.
When parseISO does not return a valid date for the same string value the function is already using for its ISO attempt, and that string matches /^\\d{1,2}\\/\\d{1,2}\\/\\d{4}$/ in full from first to last character, then: if the first segment is greater than 12, parse as day/month/year using date-fns parse with format 'd/M/yyyy'. If the first segment is at most 12 and the second is greater than 12, parse as month/day/year using parse with 'M/d/yyyy'. If both segments are at most 12, parse as day/month/year (European order) using parse with 'd/M/yyyy'. Validate each slash parse with isValid. If still unresolved, try new Date on that same string. Counter-example: Do NOT rely on new Date(text) alone for patterns such as 15/06/1969 or 03/06/1990. Do NOT use month-first (M/d/yyyy) as the default for ambiguous dates. Do not run this slash branch before attempting parseISO on that string.

### The problem statement prohibits substituting a fabricated calendar date when interpretation fails. The requirements state that all paths through getDateFromVCardProperty must yield a value suitable for vCard serialization, which needs a defined Date object. These two statements conflict when text cannot be parsed.
Return new Date(0) (Unix epoch: January 1, 1970 00:00:00 UTC) as the deterministic fallback in getDateFromVCardProperty when both the structured date field and text parsing fail. This provides a valid serializable Date for callers while avoiding the misleading use of the current timestamp. guessDateFromText still returns undefined on failure; getDateValue in csvFormat still returns { text }. Counter-example: Do NOT return new Date() (current timestamp) and do NOT return undefined."
