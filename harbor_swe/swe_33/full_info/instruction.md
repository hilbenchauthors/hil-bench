# PROBLEM STATEMENT
## Title: Improve return value structure for cached data retrieval functions

## Description

Functions in the Drive application's data store that retrieve and return cached link data currently use positional arrays (tuples) as their return type. Each position in the returned array represents a different piece of information, but this structure makes the relationship between each position and its semantic meaning implicit, which can lead to errors when accessing or destructuring the returned values.

**Expected Behavior**

These functions should return their outputs using a named-field structure (i.e., an object) so that each value is clearly associated with a descriptive identifier. The returned objects should be plain, easily destructurable data structures that consumers can freely work with without special access constraints. All existing consumer call sites must be updated to use object property access or object destructuring in place of tuple/index access.

**Actual Behavior**

The affected functions currently return tuples where the first element represents a collection of processed entities and the second element carries a status indicator. The meaning of each position is only known by convention and is not enforced by the return type itself.

**Impact**

This implicit structure reduces code readability and maintainability, particularly as these functions are consumed across multiple views and hooks in the application.


# REQUIREMENTS
- Functions that retrieve cached link data, including `getCachedChildren`, `getCachedTrashed`, `getCachedSharedByLink`, and `getCachedLinks`, must return an object instead of a tuple.
- The return object must use descriptive property names that clearly indicate what each value represents.
- The first property must be an array of self-contained data representations of the decrypted entities; the second property must indicate processing status.
- All call sites must switch from tuple/index access to object property access for these results.
- Any previous tuple defaults must be replaced with an appropriate object default.
- `useDownload.getChildren` must continue returning `DecryptedLink[]` by extracting the array from the updated result.
- `getLinkByName` must read from the array property of `getCachedChildren` when searching by name.
- Returned cache data must be protected against accidental consumer-side mutations that could corrupt the shared store.
- All affected views and hooks that consume these results must be updated to use the new object shape.


# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The requirements specify using 'descriptive property names' for the return object but do not specify what those exact names should be. Multiple valid naming conventions exist for the array of entities (e.g. links, items, data, results, entries, children, decryptedLinks, cachedLinks) and the status indicator (e.g. isDecrypting, loading, isLoading, pending, processing, decrypting).
Use the exact property names `cachedLinks` (array field) and `isDecrypting` (status field). `cachedLinks` comes from the requirements' domain term 'cached link data', and `isDecrypting` preserves the established status identifier already used by existing consumers. No alternative names are accepted.

### The requirements state that the returned array must contain 'self-contained data representations' of each cached entity. It is unclear whether 'self-contained' means each entity object in the array is a complete representation (i.e., the decrypted object reference itself, which is already complete), or whether each entity must be an isolated copy that does not share its object reference with the internal store. Multiple valid interpretations exist: returning the store's own references (simpler, no overhead), returning shallow copies via spread, returning deep clones via structuredClone, or serializing/deserializing via JSON.
Each entity in the returned array must be a shallow copy — a distinct object that does not share its reference with the store's internal cache. Use object spread (`{ ...entity }`) to create each copy. Consecutive calls to the same getCached* function with identical arguments must return entity objects that are content-equal but reference-distinct. Do NOT return direct references to the store's internal objects, and do NOT use structuredClone or JSON.parse/JSON.stringify.

### The requirements state that returned cache data must be 'protected against accidental consumer-side mutations,' but the problem statement says the returned objects should be 'plain, easily destructurable data structures that consumers can freely work with without special access constraints.' These two instructions directly conflict: one demands mutation protection while the other says no access constraints should be applied.
The requirements take precedence. Apply `Object.freeze()` to the entire returned result object so that its top-level properties become non-writable and non-configurable. Example: `return Object.freeze({ arrayProp: [...], statusProp: false })`. Do NOT leave the return value unfrozen. Do NOT use Proxy wrappers or TypeScript-only readonly types as the protection mechanism.
