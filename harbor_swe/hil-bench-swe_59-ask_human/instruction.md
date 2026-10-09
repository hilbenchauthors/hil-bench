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
