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
