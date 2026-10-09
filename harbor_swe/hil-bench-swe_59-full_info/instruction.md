# PROBLEM STATEMENT
# Title

Harden "Subscribe to Calendar" URL validation

### Description

The modal for subscribing to calendars currently allows very long URLs, applies warnings inconsistently, and sometimes enables submission when it should not. Warning messages for different cases (Google/Outlook links without .ics, Google public links, and overly long URLs) do not have a clear priority order.

Google public calendar links can raise a privacy concern because subscribing to them may expose a calendar more broadly than intended. Overly long URLs are the most critical validation concern because the server cannot process the subscription when the link exceeds the supported length.

### Expected behavior

The modal should enforce a unified maximum length limit for calendar URLs using a centralized constant from `MAX_LENGTHS_API`. The submit control must use a single disabled state, shared between normal and error flows, and should only allow submission when the URL is non-empty, structurally valid, and within the maximum length limit. Local counters and redundant `maxLength` props should be removed in favor of centralized validation. Warning messages should show only one at a time, and Google public links should warn users appropriately when they are identified. The URL field must capture and validate the value exactly as provided by the user, without any preprocessing or transformation applied to the stored value.


# REQUIREMENTS
- Add a `CALENDAR_URL` entry to `MAX_LENGTHS_API` and remove all hardcoded constants for URL length, replacing them with this centralized value.

- In `SubscribeCalendarModal`, detect whether the entered URL belongs to Google Calendar by matching `^https?://calendar\.google\.com` or Outlook by matching `^https?://outlook\.live\.com`, and check whether it has an `.ics` extension. Determine whether a Google Calendar URL points to a public calendar feed using the appropriate path pattern.

- Compute a single disabled flag for the modal's submit button. Use this unified flag in both normal and error flows instead of repeating inline expressions.

- Provide a `getWarning` mechanism that returns only one message at a time, following this priority:

1: A Google or Outlook URL without .ics -> extension concern warning: "This link might be wrong"
2: A Google public URL with .ics -> privacy concern warning: "By using this link, Google will make the calendar you are subscribing to public"
3: An overly long URL -> length limit warning: "Calendar URL exceeds the maximum length"
4: Otherwise, no warning.

- Use the `getWarning` result directly as the field warning; remove character counters, `maxLength` attributes, and any visual hints based on length.

- Normalize input changes before storing them to avoid false validation states.


# PUBLIC INTERFACES
No new interfaces are introduced

## BLOCKER DETAILS
### The requirements state that the URL length must be centralized using MAX_LENGTHS_API.CALENDAR_URL, but do not specify the exact numeric value that CALENDAR_URL should be set to. Multiple plausible values exist depending on server limits, browser constraints, or organizational policy.
Set `CALENDAR_URL: 10000` in the `MAX_LENGTHS_API` object in `packages/shared/lib/calendar/constants.ts`. The value must be exactly `10000`. Do NOT use `10240`, `8192`, `4096`, `2048`, or any other value. Use `calendarURL.length > MAX_LENGTHS_API.CALENDAR_URL` (strictly greater-than, not >=) for the length check. This length check must be included in the unified disabled flag for the submit button, so that overly long URLs prevent submission.

### The problem statement and requirements both indicate that Google public calendar links must be identified and warned about, but neither specifies the exact URL path pattern that distinguishes a public Google Calendar feed from a private one. Without this specific pattern, it is impossible to reliably detect public feeds.

Detect Google public feed links with `calendarURL.match(/\/public\/\w+\.ics/)`. The `\w+` character class ensures only word characters (letters, digits, underscore) match the feed identifier segment — hyphens and other punctuation must not trigger the warning.

### The requirements describe warnings for URLs 'without .ics' but do not specify whether the extension check should inspect the full raw URL string or a parsed component such as the pathname. URLs with query strings or fragments after `.ics` behave differently depending on that choice.
Detect the `.ics` extension by parsing the URL and checking whether `new URL(calendarURL).pathname.endsWith('.ics')` inside a `try/catch`. Query strings and fragments must not affect the extension result, and the check must remain case-sensitive, so `.ICS` does NOT count. Do NOT use `calendarURL.endsWith('.ics')` on the full raw string.

### The problem statement says overly long URLs are the most critical validation concern because the server cannot process them, but the requirements enumerate warning priority as extension concern first, Google public link concern second, and length warning last. These instructions conflict on which warning category should appear first when more than one condition applies.
Follow the problem statement's criticality: `getWarning()` must check `isURLTooLong` first, then `shouldProbablyHaveIcsExtension`, then `googleWillPossiblyBeMakePublic`. The displayed warning order must therefore be: (1) length-limit, (2) extension-concern, (3) Google-public-privacy. The numbered priority list in the requirements (which lists extension first and length last) is the source of the contradiction and must be overridden by this resolution.

### The problem statement specifies that the URL field must store and validate the value exactly as the user provides it, without any preprocessing, while the requirements instruct that input changes must be normalized before storing. These instructions conflict on whether the URL value should be transformed before it is saved to state.
Follow the requirements: apply trim() in the onChange handler before storing the URL, using setCalendarURL(e.target.value.trim()). Do NOT preserve raw unprocessed values and defer normalization to the submission or validation step.
