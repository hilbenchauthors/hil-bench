# PROBLEM STATEMENT
## Title: Generic singleton helper for typed instance retrieval

### Description

The current singleton helper requires callers to pass a placeholder object and then cast from `interface{}`. This adds boilerplate and risks runtime cast errors.

Add a generic helper in `utils/singleton/singleton.go` that returns the concrete type directly from the singleton layer. It should still support callers that need separate logical singleton domains for the same static type.

Repeated calls targeting the same singleton key must reuse the existing instance instead of running the constructor again.

For pointer and interface constructors, a `nil` result should be treated as an unsuccessful construction attempt, so later calls are allowed to retry and eventually establish a usable singleton.


# REQUIREMENTS
- Implement a generic function in `utils/singleton/singleton.go` that returns the singleton instance as concrete type `T`, without placeholder objects or type assertions.

- The first call for a singleton key must execute the constructor once and reuse the created instance for subsequent calls targeting that same key.

- The singleton key must be type-derived via reflection and may include an optional caller namespace input for logical separation when needed.

- Namespace-qualified lookups must be handled consistently across repeated calls, including edge cases around blank input and invalid namespace usage.

- Pointer and interface constructors should treat a `nil` result as a valid singleton state and cache it on first construction.

- Calls with and without namespace input must not interfere with each other.

- The implementation must be concurrency-safe and must preserve single-constructor execution under high contention.


# PUBLIC INTERFACES
- Path: /app/utils/singleton/singleton.go
- Name: GetInstance
- Type: function
- Input: a constructor callback and optional namespace strings
- Output: value of the requested generic type
- Description: Returns a shared typed instance using type identity and any optional namespace input to distinguish logical singleton domains when needed.

## BLOCKER DETAILS
### The task allows optional namespace input to separate singleton domains, but it does not specify the exact cache-key format for combining the static type with the namespace. Different choices for type identity, whitespace normalization, blank namespace handling, and delimiters would all produce different reuse behavior.
Build `baseKey` from the static type only using `reflect.TypeOf((*T)(nil)).Elem().String()`. If a namespace string is provided, trim surrounding whitespace before building the storage key. If the trimmed namespace is empty, use `baseKey` only. If non-empty, append it using the exact delimiter `::` (two colons): `baseKey + \"::\" + trimmedNamespace`.

### The API allows optional namespace arguments but does not define behavior when callers pass more than one namespace argument. Reasonable implementations can ignore extras, merge values, use first/last, or reject the call, and each choice changes which singleton domain is selected and whether invalid input can silently create or reuse the wrong instance.
`GetInstance` accepts at most one namespace argument. If more than one namespace argument is supplied, it must panic immediately and must not execute the constructor or create or reuse any singleton for that call.

### The problem statement says a nil pointer/interface result should allow later retries, while the requirements state nil should be cached as a valid singleton state. These instructions directly conflict on whether nil marks successful singleton construction.
For nilable result kinds (`pointer`, `interface`, `map`, `slice`, `chan`, `func`), if the constructor returns nil, that result must not be cached. This includes interface-typed constructors that return `nil` directly, such as `func() error { return nil }`. Return nil to the caller, but keep the key unresolved so a later non-nil constructor result can establish the singleton.
