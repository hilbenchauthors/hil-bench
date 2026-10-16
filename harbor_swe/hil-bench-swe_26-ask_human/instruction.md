# PROBLEM STATEMENT
## Title: Notifications with HTML content display incorrectly and duplicate messages clutter the UI

### Description

Notifications generated from API responses may contain simple HTML, such as links or formatting. These are currently rendered as plain text, so links are not clickable and formatting is lost. Repeated identical notifications can also appear, leading to clutter and poor user experience.

The intended behavior is that notifications display HTML in a way that supports both safety and interactivity. Links in notifications should open in a secure and predictable manner; anchor elements in notification content should carry appropriate attributes for safe navigation. Duplicate notifications for the same content should be suppressed to reduce clutter, while success-type notifications may appear multiple times when triggered repeatedly. Deduplication uses a stable key: when a key is provided explicitly, it is used; when the notification text is a string, the text may serve as the key; otherwise the notification identifier may be used. When multiple notifications share the same key, exactly one remains in the list. The system must support creating notifications whose text is either a plain string or a React element. When the text is a string containing HTML markup, it should be rendered as HTML rather than raw text.

To ensure no executable code reaches the user, HTML content in notifications should be sanitized at the point of creation—that is, in the notification manager, when the notification is first stored. The sanitizer should address script tags and event-handler attributes to mitigate potential code execution risks. Safe structural and formatting tags, as well as link markup, should be preserved. The sanitized result should be stored immediately as a React element rather than as a raw HTML string.


# REQUIREMENTS
- Maintain support for creating notifications with a `text` value that can be plain strings or React elements.
- When `text` is a string containing HTML markup, the notification must render the markup so that it is safe and usable (links and formatting preserved where appropriate). Use the `dompurify` package (already installed in the project) with `{ RETURN_DOM: true, ADD_ATTR: ['onclick', 'onchange', 'onsubmit'] }` to parse and sanitize HTML strings, yielding a DOM element for further processing. Use the `isElement` helper from `@proton/shared/lib/helpers/dom` to detect whether any child node of the sanitized DOM output is an HTML element (indicating the input had actual markup).
- All `<a>` elements in notification content must support safe navigation; the implementation must ensure that appropriate attributes for safe external navigation (such as `rel` and `target`) are applied to anchor elements.
- When the sanitized HTML is ready to store, wrap it in a `<div>` element with `dangerouslySetInnerHTML` containing the sanitized HTML string (obtained from `innerHTML` of the sanitized DOM element), and assign this React element to the notification's `text` field. Do not store raw HTML strings as `text` when the input contains markup.
- Compute the deduplication key from the original `text` value before performing any sanitization or transformation. Add a `key` property (typed as React's `Key`) to `CreateNotificationOptions` in the interfaces file (`interfaces.ts`) to allow explicit key provision.
- Maintain deduplication for non-success notifications by comparing a stable `key` property. If a `key` is explicitly provided, it must be used. If `key` is not provided and `text` is a string, the text itself must be used as the key. If `key` is not provided and `text` is not a string, the notification identifier must be used as the key.
- When deduplication applies for a given key, exactly one notification must remain. The handling of duplicate entries should be predictable and should preserve the most relevant user experience.
- Success-type notifications must be excluded from deduplication and may appear multiple times even when identical.
- When HTML content is detected in a notification, set `disableAutoClose` to `true` and ensure `expiration` meets a minimum display threshold suitable for content requiring user interaction.
- Event-handler attributes on interactive elements in notification content must be retained through the sanitization process and present in the rendered output, ensuring that user-initiated actions bound to element-level events remain functional in the final notification.


# PUBLIC INTERFACES
No new interfaces are introduced
