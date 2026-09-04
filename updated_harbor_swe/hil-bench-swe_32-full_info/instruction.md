# PROBLEM STATEMENT
## Title: Missing validation and consistent enforcement of task timeout limits in CLI execution

### Description

The command-line interfaces for running ad-hoc and console tasks allow setting a task timeout, but timeout values are not consistently validated or enforced.

Timeout value handling is inconsistent across CLI execution paths, and enabled timeout validation is not applied uniformly before task execution.

In addition, when both a task timeout and an asynchronous duration are provided, the effective timeout applied to the task is not clearly defined, leading to non-deterministic task termination behavior.

There is also a compatibility concern: existing runbooks and operators expect previously accepted positive integer timeout inputs to continue working unchanged across upgrades.


# REQUIREMENTS
- Ad-hoc and console CLIs must expose a '--task-timeout' option that accepts an integer value in seconds, uses the configured default when unspecified, and displays the help text: 'set task timeout limit in seconds', 'must be positive integer'.

- Timeout validation must be deterministic and consistent across ad-hoc and console execution paths so timeout enforcement behavior is predictable for operators and automation.

- For ad-hoc CLI behavior, timeout range and granularity validation must occur in `AdHocCLI._play_ds`, not in argparse type parsing. Values outside the supported runtime timeout set must be rejected there to keep execution behavior consistent with runtime enforcement. Validation failures must raise `AnsibleOptionsError` with a descriptive message that includes the invalid value.

- The `_play_ds(pattern, async_val, poll)` method signature must remain the same.

- Default semantics: `C.TASK_TIMEOUT` defaults to `0`, which disables the timeout. The effective timeout value can therefore be `0` (disabled) or a positive integer.

- Timeout enforcement message (exact): If a task exceeds the effective timeout (a value > 0), it must be terminated and emit exactly: `The command action failed to execute in the expected time frame (%d) and was terminated` where `%d` is replaced by the integer number of seconds.

- When a one-off task is constructed from ad-hoc or console, the resulting task payload must always include a `timeout` field alongside the existing module action and parsed arguments, even when the effective value is 0 (disabled).

- When a task has both a timeout value and async parameters (async_val/poll), the system must handle this configuration appropriately, as both mechanisms can limit task execution time. The interaction between these two timeout mechanisms should ensure reliable task termination. 

- Include-style tasks must accept 'timeout' as a valid key; the key mustn't be rejected or ignored during include validation.

- The console CLI must accept additional variables input in standard forms: 'key=value' pairs, YAML/JSON literals, and '@<filename>' to load from a file; values are cumulative and default to an empty list when none are provided.

- The console verbosity command must enforce these behaviors: with no argument, display 'Usage: verbosity <number>'; on success, set the verbosity level and log 'verbosity level set to %s'; on invalid (non-integer) input, display the exact error 'The verbosity must be a valid integer: %s'.

- In console mode, the session timeout must initialize from the CLI value on startup, and the interactive 'timeout' command must enforce these behaviors: with no argument to 'Usage: timeout <seconds>'; with a non-integer to 'The timeout must be a valid positive integer, or 0 to disable: %s'; with a negative integer to 'The timeout must be greater than or equal to 1, use 0 to disable'; with a non-negative integer, enforce the same timeout policy constraints as ad-hoc (propagating any validation error to the user via `display.error`) before applying the value to subsequent tasks.

- `ConsoleCLI` must override `parse()` to clear the `GlobalCLIArgs` singleton (`GlobalCLIArgs._Singleton__instance = None`) before calling `super().parse()`, ensuring each parse invocation starts from a clean global CLI state. After parsing, if `extra_vars` in `context.CLIARGS` is stored as a tuple (due to the `ImmutableDict` wrapper), it must be converted in-place to a mutable list via `context.CLIARGS._store['extra_vars'] = list(extra_vars)`.

- When `sys.stdin` is not a TTY, `ConsoleCLI.run()` must return `0` after initialization completes, before entering the interactive command loop. This enables non-interactive and test invocations to complete without blocking on `cmdloop()`.

- All timeout validation and effective timeout calculations must be stateless and must not rely on mutable global state persisting across CLI invocations. Any use of context.CLIARGS or other global CLI state must assume a fresh invocation context.


# PUBLIC INTERFACES
Type: Function
Name: `add_tasknoplay_options`
Location: `lib/ansible/cli/arguments/option_helpers.py`
Description: This function will register CLI options for commands that run a task without a defined play. It will augment the given parser by adding the `--task-timeout` option, which will set the maximum task runtime in seconds. The value will be parsed as an integer and will default to `C.TASK_TIMEOUT`, which may be `0` to disable the timeout. Policy-specific validity constraints are enforced later in runtime validation, not at parser registration time.

The effective `task_timeout` value exposed by the parser must be propagated into ad-hoc/console one-off task construction as the `timeout` field in the task payload, even when the value is `0` (disabled).

Inputs: 

 - `parser` (`argparse.ArgumentParser`): CLI argument parser that will be augmented with the --task-timeout option.

Outputs:
 - `None` (the parser will be updated to include `--task-timeout` with default `C.TASK_TIMEOUT`).

Type: Function
Name: `do_timeout`
Location: `lib/ansible/cli/console.py`
Description: This function will handle the `timeout` console command. It will parse the provided argument as an integer number of seconds and will set `self.task_timeout` accordingly. A value of `0` will disable the timeout. It will reject negative values and non-integer input, reporting errors via `display.error`. If no argument is given, it will show usage guidance via `display.display('Usage: timeout <seconds>')`. For non-negative integer inputs, acceptance must follow the same runtime timeout policy validation used by ad-hoc execution before applying the value.
When a valid integer `>= 0` is accepted, the new `self.task_timeout` applies to subsequent tasks and is reflected in their payload as the `timeout` field, including when the value is `0` (disabled).

Inputs:

 - `arg` (`str`): The argument following the `timeout` command that will represent the desired timeout in seconds.

Outputs:

 - `None` (it will update `self.task_timeout` in place and will emit user-visible messages on errors or missing input).

## BLOCKER DETAILS
### The specs require timeout validation but do not define the exact maximum accepted timeout value.
Maximum timeout value is 7200 seconds (2 hours). Any --task-timeout value above 7200 must be rejected during validation in _play_ds. The validation error must be exactly: 'The task timeout value (%d) exceeds the maximum allowed timeout of 7200 seconds' where %d is the invalid value. Boundary examples: --task-timeout=7200 is valid; --task-timeout=7201 must be rejected. Place this rule in a shared `validate_task_timeout(value)` function in option_helpers.py (value is already an int from argparse; do not add string-to-int coercion). The console `do_timeout` must also call this function after its own basic input checks, catching any `AnsibleOptionsError` and forwarding the message via `display.error(to_text(exc))`.

### The specs do not define the exact minimum accepted timeout when timeout is enabled (non-zero).
Minimum timeout value when enabled is 5 seconds. Zero still means disabled. Positive values 1 through 4 must be rejected during validation in _play_ds, while 5 seconds is the smallest valid enabled timeout. The validation error must be exactly: 'The task timeout value (%d) is too small; enabled timeouts must be 0 (disabled) or at least 5 seconds' where %d is the invalid value. Examples: --task-timeout=0 disables timeout; --task-timeout=4 must be rejected; --task-timeout=5 is valid. Place this rule in a shared `validate_task_timeout(value)` function in option_helpers.py (value is already an int from argparse; do not add string-to-int coercion). The console `do_timeout` must also call this function after its own basic input checks, catching any `AnsibleOptionsError` and forwarding the message via `display.error(to_text(exc))`.

### The specs require reliable handling when both timeout controls are present, but they do not define the precedence rule used to compute the single effective timeout written to the task payload.
When both task_timeout and async_val are positive (> 0), task_timeout always takes precedence regardless of poll value. If async_val is 0, use task_timeout. If task_timeout is 0 and async_val is positive, use async_val. If both are 0, the effective timeout is 0. The task payload must preserve async_val exactly as provided by the caller; only the timeout field should reflect the effective timeout calculation. Do not rewrite async_val when both mechanisms are present, regardless of poll value. Implement this logic in a `get_effective_task_timeout(task_timeout, async_val, poll)` function in option_helpers.py. The poll parameter does not affect the timeout calculation. Examples: task_timeout=125, async_val=75, poll=2 results in timeout=125 and async_val=75; task_timeout=125, async_val=75, poll=0 results in timeout=125 and async_val=75; task_timeout=325 with async_val=0 results in timeout=325; task_timeout=0 with async_val=50 results in timeout=50 and async_val=50; task_timeout=0 with async_val=0 results in timeout=0.

### The interfaces describe timeout as a generic positive integer, but runtime validation accepts only a stricter subset of positive values for larger timeouts. The exact acceptance rule is not defined in the public specs.
Timeout granularity restriction applies only to values from 10 to 59 seconds inclusive: any timeout in this range must be a multiple of 10 seconds. The validation error must be exactly: 'The task timeout value (%d) must be a multiple of 10 for timeouts from 10 through 59 seconds' where %d is the invalid value. Examples within this rule's scope: --task-timeout=10, 20, 30, 40, and 50 are valid; --task-timeout=11, 15, 17, 25, 33, and 59 must be rejected. Place this rule in a shared `validate_task_timeout(value)` function in option_helpers.py (value is already an int from argparse; do not add string-to-int coercion). The console `do_timeout` must also call this function after its own basic input checks, catching any `AnsibleOptionsError` and forwarding the message via `display.error(to_text(exc))`.
