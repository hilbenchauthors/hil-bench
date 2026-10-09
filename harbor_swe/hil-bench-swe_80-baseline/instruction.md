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
