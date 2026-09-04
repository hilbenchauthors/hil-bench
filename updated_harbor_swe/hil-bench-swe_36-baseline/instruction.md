# PROBLEM STATEMENT
# Title

Inconsistent Use and Legacy Dependency on the Collection ABC Compatibility Shim

## Description

Several affected files still import collection ABCs such as `Mapping`, `Sequence`, and related view types from the internal compatibility shim `ansible.module_utils.common._collections_compat`. This includes runtime code under `lib/ansible/modules` and `lib/ansible/module_utils`, and controller-side code that should not continue depending on that legacy shim path.

This continued usage creates inconsistent contributor guidance, keeps avoidable dependencies in module preparation flows, and leaves automatic checks partially misaligned with the active import policy for collection ABCs.

## Steps to Reproduce

1. Inspect affected runtime and controller-side files that import collection ABCs.
2. Observe that some imports still target `ansible.module_utils.common._collections_compat`.
3. Trace module dependency preparation for a simple module path and observe that the shim can still be pulled into dependency expectations through legacy import usage patterns.
4. Inspect sanity guidance for bad import sources and confirm it still references legacy guidance.

## Expected Behavior

Affected runtime and controller-side files stop importing collection ABCs from the legacy shim and migrate to their approved context-specific import locations.

`_collections_compat.py` remains available as a transitional compatibility layer for unmigrated callers, while clearly signaling its transitional role and guiding contributors toward migration.

Dependency discovery for module preparation no longer carries the shim indirectly once migrated runtime imports no longer require it, and sanity guidance reflects the current migration policy rather than legacy shim usage.

## Additional Information

The task scope includes:

- runtime and controller-side import cleanup in affected files,
- transitional compatibility behavior for `_collections_compat.py`,
- dependency-packaging impact of removing indirect shim dependency pull-through after migration,
- transitional packaging safeguards for unmigrated callers during the migration window,
- sanity guidance updates so checks stop recommending legacy shim imports.


# REQUIREMENTS
- In affected files under `lib/ansible/modules/**` and `lib/ansible/module_utils/**`, collection ABC imports must stop using `ansible.module_utils.common._collections_compat` and migrate to the approved runtime-safe import path for collection ABCs.

- In affected controller-side files (for example, `lib/ansible/plugins/shell/__init__.py`), collection ABC imports must stop using `ansible.module_utils.common._collections_compat` and migrate to the approved controller-side import path for collection ABCs.

- `lib/ansible/module_utils/common/_collections_compat.py` must remain available as a transitional compatibility layer for callers that have not yet migrated, and it must continue exporting the public ABC names existing callers rely on (`MappingView`, `ItemsView`, `KeysView`, `ValuesView`, `Mapping`, `MutableMapping`, `Sequence`, `MutableSequence`, `Set`, `MutableSet`, `Container`, `Hashable`, `Sized`, `Callable`, `Iterable`, `Iterator`).

- The `_collections_compat.py` module docstring must be updated to describe its transitional role, include migration guidance for callers, and reference the ansible-core version from which migration away from direct shim imports becomes available.

- Transitional signaling for the shim must be consistent with project expectations while preserving compatibility for existing callers.

- During the transition window, runtime module artifacts must remain compatible with third-party content that still imports `ansible.module_utils.common._collections_compat`.

- Dependency discovery outputs used by tooling and tests must be derived from explicit source-level imports and must not retain legacy shim pull-through once affected runtime imports are migrated.

- The `ansible-bad-import-from` sanity rule must stop recommending `ansible.module_utils.common._collections_compat` and align with the current import policy for collection ABCs.

- Existing shim references in affected files should be replaced without changing public names, function signatures, or externally observed behavior.


# PUBLIC INTERFACES
No new interfaces are introduced.
