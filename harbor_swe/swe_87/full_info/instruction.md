# PROBLEM STATEMENT
## Title 
Display methods in forked worker processes are not deduplicated globally

## Summary
When warnings messages are triggered inside worker processes, they are displayed directly by the fork rather than routed through the main process. This bypasses the global deduplication mechanism and causes duplicate or inconsistent output when multiple forks emit the same warnings.

## Current behavior

- display and warning called from a fork are written directly.
- Each forked process can emit its own copy of the same warning  message.
- reDeduplication only happens per-process, so duplicates appear when multiple workers are active.

## Expected behavior 
- Display-related calls (display, warning) in worker processes should be proxied to the main process.

- The main process should handle output consistently and apply global deduplication across all forks.

- Formatting of warning messages (e.g. prefixes, line wrapping) must be applied in the main process so that deduplication uses consistent content.

- Users should only see each unique warning once, regardless of how many worker processes trigger it.


# REQUIREMENTS
- The `Display` class should ensure that calls to the `display` and `warning` methods from forked processes are routed to the main process via `_final_q` in `proxy_display`, preserving the specific method context and associated arguments.

- When proxying Display.display(...) from a worker, the proxy must pass every display parameter (color, stderr, screen_only, log_only, newline) to send_display with the exact values received from the caller. Include every parameter even when the value is None or False. ‘Must not inject default/synthesized default kwargs’ means do not add or substitute parameters the caller did not supply; it does not mean omitting parameters whose value is default.

- A call to Display.warning(msg, …) inside a child process with _final_q defined must invoke _final_q.send_display(...) exactly once, passing the appropriate method-identifying literal as the first argument followed by the message and keyword arguments.

- A call to Display.warning(msg, …) inside a child process with _final_q defined must invoke _final_q.send_display(...) exactly once, passing the appropriate method-identifying literal as the first argument followed by the message and keyword arguments.

- When messages are sent via the display queue the timestamp of the time of occurrence of the message must be printed to console. The time must be represented in an ISO format.

- For `Display.warning(msg, formatted=...)`, the arguments the caller supplies are the raw message and the formatted flag. The proxy must forward these only; it must not add prefixes (e.g. a warning prefix) or apply line wrapping before sending. The main process applies such formatting when it invokes the Display method.

- The `Display` class must define callable attributes whose names are the same as the method identifiers used when proxying from workers (i.e. the same strings passed as the first argument to `send_display`), so that the main process can invoke them with `getattr(display, result.method)` and the attribute exists.

- Messages must be displayed with a /n at the end as per the current code, and should be displayed raw, without any additional formatting, to achieve maximum fidelity.



# PUBLIC INTERFACES
1. Type: Function

   Name: ``

   Path: ``

   Input:

   * ` (``): the original Display class method to wrap

   Output:

   * .

2. Type: Class (Display)

   The Display class must expose callable attributes whose names match the method identifiers used when proxying display calls from workers (the same values passed as the first argument to send_display). The main process invokes these attributes by name when handling DisplaySend; they are the entry points that receive the payload and optional default parameters.

## BLOCKER DETAILS
### The requirements state that display and warning calls from a child process must invoke _final_q.send_display with an appropriate method-identifying literal as the first argument, but do not specify what those literals are for either method.
The first argument for display calls is the literal 'displaytocurrentuser'. The first argument for warning calls is the literal 'sendwarningtouser'. These are the method-identifying strings passed as the first positional argument to _final_q.send_display when proxying from a worker process.

### The requirements state that messages must be displayed with a /n at the end as per the current code, and should be displayed raw, without any additional formatting, to achieve maximum fidelity.
Messages must be displayed raw, without any additional formatting, to achieve maximum fidelity. Do not implement the display of them with a /n at the end. When proxying display calls from a worker, the proxy must call _final_q.send_display(..., newline=False) so that the main process displays raw without adding a newline.

### The requirements state that when messages are sent via the display queue a timestamp of the time of occurrence must be printed to console in an ISO format, but do not specify which ISO format.
Use ISO 8601 ordinal date/time basic format: YYYY-DDDTHHmmssZ (e.g. 2025-071T143000Z). The timestamp must represent UTC time with no separators between time components. The timestamp must be generated inside FinalQueue.send_display and passed as a positional argument to the DisplaySend constructor (signature: DisplaySend(method, timestamp, *args, **kwargs)). DisplaySend must store but not compute the timestamp. In the main process, the timestamp must be written directly to stdout as a raw line before dispatching the message -- it must not be printed through any Display method, as that would subject it to formatting and deduplication.
