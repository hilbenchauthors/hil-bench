# PROBLEM STATEMENT

# JSDOM compatibility for `ModalTwo` dialog behavior

## Description

When `ModalTwo` is exercised in a constrained DOM implementation such as JSDOM, the modal host does not behave the same way it does in a browser. Descendant semantics, DOM traversal, and interaction checks can diverge from browser behavior, which makes tests around open modal content unreliable.

The fix must preserve the current `ModalTwo` consumer surface and should not require modal callers to adopt a different API. Compatibility for constrained environments may be achieved either inside the abstraction itself or by substituting that abstraction through the project's environment-specific integration hooks, so long as consumers keep using the same `Dialog`-level contract.

## Impact

Automated tests around `ModalTwo` are unstable in non-browser environments, and developers receive false negatives during CI and local runs.

## Steps to Reproduce

1. Render `<ModalTwo open>` in a constrained DOM test environment.

2. Include an interactive descendant in the modal body.

3. Query or interact with that content using standard Testing Library semantics.

4. Observe that the content is not exposed consistently enough to match browser behavior.

## Expected Behavior

Open modal content should remain testable and operable in constrained DOM environments without requiring callers to mount a different host directly or rewrite individual modal tests. The production-facing `Dialog` abstraction should keep its existing consumer contract, while the constrained-environment compatibility path should preserve equivalent observable behavior for `ModalTwo`.

## Actual Behavior

The current `ModalTwo` implementation depends directly on browser dialog behavior, and constrained DOM environments do not expose that behavior consistently enough for the existing tests and hooks.



# REQUIREMENTS
- The UI should expose a `Dialog` abstraction that production callers use instead of mounting a host element directly.

- The production `Dialog` abstraction should continue to model a native dialog wrapper for consumers.

- Compatibility for constrained DOM environments may be provided either inside the `Dialog` abstraction or by substituting that abstraction through the project's environment-specific integration points, for example via runtime capability detection, shared bootstrap substitution, or module-level replacement, as long as consumer code does not change.

- Any constrained-environment implementation or substitute must preserve the same public import shape and ref-forwarding semantics that existing `ModalTwo` integrations expect, including compatibility with the current default-import usage pattern.

- `Dialog` should provide a reference to the actual rendered host element rather than an adapter or imperative proxy, while callers should still be able to use standard dialog operations whenever the rendered host genuinely supports them.

- `Dialog` should accept and forward standard `HTMLDialogElement` attributes and any `aria-*` or `data-*` attributes to the host chosen for that environment.

- `Dialog` should render its children unchanged so that interactive descendants retain their roles, semantics, and tab order.

- `ModalTwo` should depend on the `Dialog` abstraction for its container and should not mount a platform-specific host directly.

- The constrained-environment compatibility path should keep open modal descendants discoverable through standard Testing Library semantics and should not require per-test consumer rewrites.

- If the environment-substitution path is used, the supported package-level integration point is the shared Jest bootstrap at `packages/components/jest.setup.js`, and the substituted module is `packages/components/components/dialog/Dialog.tsx`. The substitution must be installed before `ModalTwo` imports are evaluated.



# PUBLIC INTERFACES
Path: `packages/components/components/dialog/Dialog.tsx`
Name: `Dialog `(default export from new file)
Type: function
Input: `props: HTMLAttributes<HTMLDialogElement>`, `ref: Ref<HTMLDialogElement>`
Output: `JSX.Element`
Description: Provides a reusable dialog component that forwards a ref and accepts standard HTML dialog attributes.

## BLOCKER DETAILS
### The specification requires the substitute to keep descendants discoverable via Testing Library semantics, but does not specify whether the substitute host should declare an explicit ARIA role. Adding `role=\"dialog\"` affects how assistive technologies and query utilities traverse the subtree.
The substitute host must NOT have `role=\"dialog\"` or `aria-modal` attributes. In JSDOM, a native `<dialog>` element does not fully implement the dialog role semantics, so adding an explicit role to the substitute would create a behavioral divergence from the native element in the test environment. The substitute should render a neutral container (e.g. `<div>`) without role attributes so that descendants remain directly queryable.

### The specification requires Dialog to forward standard `HTMLDialogElement` attributes to the host, and `open` is a standard attribute of the native `<dialog>` element that controls its visibility. However, the HTML specification defines `open` as a valid content attribute only on `<dialog>` and `<details>` elements. When the substitute renders a generic host element, forwarding `open` creates a non-standard attribute, directly contradicting the requirement to forward 'standard' attributes to the host.
The `open` prop must be intercepted and not forwarded to the substitute host, because it is not a standard attribute on the substitute's element type. Since `open` controls the native dialog's visibility, its semantics must be translated to a mechanism valid on the substitute. In JSDOM, a native `<dialog>` without `open` remains present and visible in the DOM because JSDOM does not implement the dialog user-agent stylesheet. The HTML `hidden` attribute would remove the element from rendering, which does not match this JSDOM behavior. `aria-hidden` is the only standard attribute that marks content as hidden while keeping it present and visible in the DOM, matching JSDOM's treatment of `<dialog>`. Set `aria-hidden=\"true\"` when `open` is explicitly `false`; do not set `aria-hidden` when `open` is `true` or not provided. Do not use the HTML `hidden` attribute, CSS-based hiding, or a custom `data-state` attribute.

### The public requirements allow compatibility to be implemented inside `Dialog`, but the public interface simultaneously defines `Dialog` as a native `<dialog>` wrapper with `Ref<HTMLDialogElement>`. Those two instructions cannot both hold for one production component once the host element type diverges.
Keep `packages/components/components/dialog/Dialog.tsx` as a production-native wrapper that always renders `<dialog>`, set its `displayName` to `'Dialog'`, and export it as the default forwarded-ref component. Correct example: `const Dialog = forwardRef((props: Props, ref: Ref<HTMLDialogElement>) => <dialog ref={ref} {...props} />); Dialog.displayName = 'Dialog';`; do not add runtime capability checks or render a non-dialog host from `Dialog.tsx`.

### The specification requires the substitute to preserve 'the same public import shape and ref-forwarding semantics that existing ModalTwo integrations expect, including compatibility with the current default-import usage pattern.' However, the specification does not define the concrete module shape that the mock factory must return to satisfy the default-import contract within the Jest module system.
The mock factory must return `{ __esModule: true, default: SubstituteDialog }`. In Jest, `import Dialog from '../dialog/Dialog'` compiles to a CommonJS require that reads the `default` property. Without the `__esModule: true` marker, Jest does not perform ES-module interop and the default import resolves to the entire module object rather than the intended component. The substitute must not be returned bare, must not omit `__esModule`, and must not use a named export instead of `default`.
