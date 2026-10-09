# PROBLEM STATEMENT
## Title: Consolidate delegated host label rendering in the default callback plugin

### Description

The default stdout callback plugin still rebuilds host labels in several result handlers, especially for delegated task results. That duplication makes the output harder to maintain and allows callback paths to drift when delegated metadata is incomplete, when integrations surface more than one delegated identity hint, or when operators still expect the long-standing raw `primary -> delegated` presentation even in environments where a host name can itself contain separator-like characters. The callback layer should use a single reusable formatter on `CallbackBase` so every affected result path renders the same canonical host label while keeping delegated output recognizable to operators and predictable across callback paths.



# REQUIREMENTS
- A static method `host_label` must exist on `CallbackBase`.
- `CallbackBase.host_label(result)` must return the originating host name when no delegation metadata is present.
- When delegation metadata is present, the formatter must return a combined primary/delegated label as a plain string, and every callback path that currently renders delegated host labels must use that shared formatter.
- Delegated metadata is not always normalized, so the formatter must choose one canonical delegated display identity and ignore blank values.
- If delegation metadata is present but the delegated identity data is incomplete, the formatter should still render a delegated form rather than silently falling back to the primary-only label.
- Unusually long host names should be rendered compactly and consistently in both the primary and delegated positions.
- Delegated labels should preserve the historical raw `primary -> delegated` presentation that operators already recognize in normal callback output.
- The shared formatter must still return an unambiguous combined label when either rendered side contains delimiter-like or escape-sensitive text.



# PUBLIC INTERFACES
- Path: /app/lib/ansible/plugins/callback/__init__.py
- Name: host_label
- Type: function
- Input: result object exposing result._host.get_name() and result._result, including optional delegated metadata with one or more delegated identity hints
- Output: str
- Description: Builds the canonical callback label for a task result. The formatter always includes the originating host name and, when delegation metadata is present, produces the delegated display label using the task's shared rendering rules.

## BLOCKER DETAILS
### Delegated execution must still render a delegated label even when delegation metadata is present but none of the delegated identity candidates yields a displayable value. The public task surface leaves that fallback delegated token unspecified.

When delegation metadata is present but no delegated identity can be derived, render the delegated side as unavailable. Delegation metadata is considered present whenever `_ansible_delegated_vars` exists in the result and is not `None`, even if it is an empty dict. Example: `web1 -> unavailable`. Counterexample: `web1`

### Very long host names still need a compact, stable rendering rule in the shared formatter, but the public task surface does not define the exact per-side display budget or the concrete shortening formula that should be used once a name grows too long.

Shorten each label side independently to at most 18 visible characters. If a side exceeds 18 characters, keep the first 15 characters and append `...`. Example: `abcdefghijklmnopqrst` becomes `abcdefghijklmno...`. Counterexample: truncating the whole combined label instead of each side.

### Delegated metadata may expose more than one candidate identity for the delegated side, but the public task surface does not define which candidate becomes canonical when several are present. Several reasonable precedence policies remain plausible.

Choose the first non-empty delegated identity in this order: `delegated_host_name`, `ansible_hostname`, `ansible_delegated_host`. No other keys, including `ansible_host`, are consulted. Trim surrounding whitespace from each candidate before testing for emptiness, and use the trimmed value as the returned identity. Example: if `delegated_host_name` is relay and `ansible_delegated_host` is `delegate.example.com`, use relay. If `ansible_delegated_host` is `delegate-host`, use delegate-host (trimmed).

### The public task surface simultaneously asks the formatter to preserve the historical raw `primary -> delegated` presentation operators recognize in normal callback output and to emit an unambiguous combined label when a rendered side itself contains delimiter-like or escape-sensitive text. Those instructions cannot both be satisfied by leaving every delegated label side unwrapped in all cases.

Render simple names as `primary -> delegated`. If a final label side contains ` -> `, a backslash, or a single quote, wrap that side in single quotes and escape backslashes as `\\` and single quotes as `\'` before joining. Example: `db -> 'edge\'one'`. Counterexample: leaving `db -> edge -> one` unquoted.
