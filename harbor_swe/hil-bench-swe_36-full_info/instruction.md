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

## BLOCKER DETAILS
### The problem statement says affected runtime files must migrate to approved context-specific import locations, and the requirements say they must migrate to the approved runtime-safe import path for collection ABCs, but neither specifies which fully-qualified import path should be used as the canonical runtime import source, including the source used by runtime-side compatibility re-exports.

The canonical runtime-side source for collection ABCs is `ansible.module_utils.six.moves.collections_abc`. For affected runtime files (under lib/ansible/modules and lib/ansible/module_utils), imports that currently use `ansible.module_utils.common._collections_compat` must migrate to that path. Example: `from ansible.module_utils.six.moves.collections_abc import Mapping` replaces `from ansible.module_utils.common._collections_compat import Mapping`. Counter-example: using `ansible.module_utils.common.collections` or keeping the legacy shim path is incorrect.

### The problem statement and requirements specify that affected controller-side files must stop importing collection ABCs from the legacy shim and migrate to an approved controller-side import path, but they do not specify which fully-qualified import path should be used as the replacement target for controller-side code.
For affected controller-side files, imports that currently use `ansible.module_utils.common._collections_compat` must migrate to `collections.abc` from the Python standard library. Example: `from collections.abc import Mapping, Sequence` replaces `from ansible.module_utils.common._collections_compat import Mapping, Sequence` in controller-side code. Counter-example: keeping the legacy shim path or using any other non-canonical controller-side import source is incorrect.

### The problem statement and requirements say the compatibility shim must remain transitional, continue exporting expected public ABC names, and signal its transitional status appropriately, but they do not define whether that signal is documentation-only or a runtime warning, and they do not define the exact migration-version text that must appear in the shim guidance.
For `lib/ansible/module_utils/common/_collections_compat.py`, transitional signaling is documentation-only. Do not emit runtime warnings and do not call `warnings.warn` or use `DeprecationWarning`. Replace the existing `try/except ImportError` fallback structure with one consolidated re-export block (single unconditional import block, no version-specific branching) while continuing to export the full required ABC name set. The shim docstring must include migration guidance and explicitly state that this migration path is available since ansible-core 2.11. Counter-example: keeping fallback branches, adding runtime warning behavior, or using a different ansible-core version string is incorrect.

### The problem statement and requirements combine two directives that can conflict in practice: dependency discovery outputs should follow explicit source-level imports and drop legacy shim pull-through after migration, while runtime artifacts must remain compatible with third-party callers that still import the shim during the transition period. In module paths without explicit shim imports, these directives point to different packaging outcomes unless a precedence rule is defined.

Use a two-surface precedence rule. For dependency discovery outputs (including recursive finder expectations), include `ansible/module_utils/common/_collections_compat.py` only when there is an explicit source-level import of `ansible.module_utils.common._collections_compat` in the analyzed graph. For final runtime module bundle assembly, keep bundling `ansible/module_utils/common/_collections_compat.py` during the transition window even when discovery output has no explicit shim import. In `lib/ansible/executor/module_common.py`, define a module-level constant `_TRANSITIONAL_COLLECTIONS_COMPAT_PATH = 'ansible/module_utils/common/_collections_compat.py'` and a function `_add_transitional_collections_compat_to_zip(zf)` that checks the zip's namelist and, if the shim is not already present, reads the shim from disk using the existing `_MODULE_UTILS_PATH` reference and `_slurp` helper, then writes it into the zip via `zf.writestr`. Call this function in `_find_module_utils` after `recursive_finder` completes. Do not treat comments, strings, or transitive references as explicit imports. Counter-example: applying one unconditional rule to both surfaces (always include everywhere or always exclude everywhere) is incorrect.
