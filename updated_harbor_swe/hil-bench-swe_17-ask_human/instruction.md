# PROBLEM STATEMENT
# Configuration loading can outlive caller cancellation.

## Description
Configuration loading is not consistently bounded by caller lifecycle signals. When configuration is fetched from slow sources, startup and command execution may continue after the caller has already timed out or canceled.

## Actual behavior
Cancellation and timeout propagation during configuration loading is inconsistent, so work may continue even when upstream execution has already been interrupted.

## Expected behavior
Configuration loading should stop promptly when cancellation or timeout is observed. When a caller does not provide an explicit deadline, loading must still run within an operationally bounded window. Loading should also avoid inheriting stale deadlines from long-lived parent contexts.


# REQUIREMENTS
- Configuration loading must be callable in a context-aware mode so that cancellation and timeout signals from the caller can be honored during source access and parsing.
- When no explicit caller deadline exists, configuration loading must still execute within an operationally bounded time window.
- Under non-canceled conditions, loading results must remain functionally equivalent to current behavior across defaults, environment overrides, and filesystem paths.
- Context-aware invocation must apply the project-standard input normalization rules before starting configuration loading.
- Each configuration loading invocation must construct a fresh context internally to prevent inheriting stale deadlines or pre-existing cancellation signals from parent operations.
- After each major processing stage within the `Load` function, specifically after applying the timeout, before and after `ReadConfig`, after the deprecation check loop, after each defaulter iteration, after `Unmarshal`, and after each validator iteration; `ctx.Err()` must be checked and its error returned immediately if non-nil. This ensures prompt propagation of cancellations or deadline expirations that occur during or between processing stages, including cases where a source opener triggers cancellation as a side effect but still returns successfully.


# PUBLIC INTERFACES
No new interfaces are introduced.
