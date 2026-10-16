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

## BLOCKER DETAILS
### The problem requires bounded execution when no caller deadline is present, but omits the exact default bound value required by policy.



If the incoming context has no deadline, wrap it with a timeout of exactly 11 seconds (use `context.WithTimeout(ctx, 11*time.Second)`) and use that derived context for configuration source access and subsequent load stages.

### The input contract for context-aware invocation does not define how null-like context inputs should be interpreted during argument normalization. Specifically, it does not specify whether a context slot receiving no concrete context object is invalid or should be normalized.



During context-aware invocation argument normalization, any nil-equivalent context input (including typed-nil values carried through interface arguments) must normalize to `context.Background()`. Loading must not fail solely due to this input shape.

### The requirements simultaneously demand that the caller's context propagate for cancellation support, and that each configuration loading invocation use a clean context to avoid inheriting stale deadlines from parent operations. It is unclear which policy takes precedence.
Propagate the caller's context directly without creating a fresh context. The caller's cancellation and deadline signals must be preserved and propagated end-to-end through configuration loading. Each command handler must extract context via `cmd.Context()` and pass it through `buildConfig(ctx)` into `config.Load`. The existing backward-compatible call signature (path-only) must continue to work.
