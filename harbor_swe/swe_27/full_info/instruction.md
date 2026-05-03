# PROBLEM STATEMENT
## Title: Revamp Contact Group Details modal

#### Description:

The Contact Group Details modal is outdated and needs a refresh. The current count label says "N members," which should say "N email addresses" with correct singular/plural forms. The modal should serve as a self-contained hub for group management — all group management workflows, including composition, should be completable within the modal itself without needing to open additional views or windows.

Users should be able to compose messages to group members, whether reaching out to everyone at once or to specific individuals.

#### Steps to Reproduce:

1. Open the Contact Group Details modal for any group with multiple email addresses.

2. Observe the count label uses generic "members" terminology.

3. Note there is no way to compose a message to the group from this modal.

#### Actual Behavior:

The label displays "N members" and there is no compose action available from the modal.

#### Expected Behavior:

The count label should display "N email addresses" (or "1 email address" for singular). Users should be able to compose a message to the group directly from the modal. Message composition must integrate with the application's standard compose pipeline for consistent behavior.


# REQUIREMENTS
- Ensure the Contact Group Details modal renders the count label using "email address" (singular) and "email addresses" (plural) according to the number of email addresses in the group.

- Ensure the label text updates consistently wherever this count is shown within that modal.

- Ensure the string is localized and pluralized correctly via the project's i18n mechanism.

- Add compose functionality for the group's email addresses. When composing, enforce the per-compose recipient ceiling to prevent mail delivery failures.

- Display each contact in the group using the existing recipient item component pattern for visual consistency with the rest of the application.


# PUBLIC INTERFACES
"No new interfaces are introduced."

## BLOCKER DETAILS
### The requirements mandate enforcing a per-compose recipient ceiling when composing to the group, but the specific ceiling value is not provided anywhere in the problem statement, requirements, or interfaces.
Exact ceiling: 25 recipients. Rule: when the user triggers compose to the whole group (e.g. the group-level compose action), build the full recipient list, then pass only `recipients.slice(0, 25)` as the first argument to `onCompose` (second argument: attachments array, e.g. `[]`). Per-contact compose to a single address may pass a one-element array and is not required to slice. Format: numeric literal `25` (or a named constant equal to 25) used as the slice end index. Example: group has 30 contacts → `onCompose` receives exactly 25 `Recipient` objects. Counter-example: passing 26 or 30 recipients for a single group-wide compose call, or omitting the slice so the handler receives every address when there are more than 25. Put `data-testid=\"group-summary:compose\"` on the group-wide compose control only (not on per-contact compose buttons) so it is unambiguous in the UI tree.

### The requirements specify displaying each contact using 'the existing recipient item component pattern for visual consistency' but this reference is ambiguous. Multiple components in the codebase render recipient or contact information in different formats, and the requirements do not clarify which component constitutes the pattern or how to integrate it within the group details modal.
Use the existing shared component only: import `RecipientDropdownItem` from the same contacts area as the modal, i.e. path `packages/components/containers/contacts/view/RecipientDropdownItem` (in `ContactGroupDetailsModal.tsx`: `import RecipientDropdownItem from '../view/RecipientDropdownItem'`). Remove the table-based list (`ContactGroupTable` or equivalent) and render one `RecipientDropdownItem` per group member (e.g. map over emails). Enable the simplified/list pattern via the `simple` prop where that is the established usage. Do not add a second, duplicate implementation of this UI under another package (e.g. a new file under `applications/mail` that reimplements the same row). Example: `emails.map((email) => <RecipientDropdownItem key={...} recipient={...} simple ... />)`. Counter-example: keeping the old table, or creating a new component that copies `RecipientDropdownItem` instead of importing the module above.

### The problem statement requires that 'all group management workflows, including composition, should be completable within the modal itself without needing to open additional views or windows.' However, the expected behavior requires that 'message composition must integrate with the application's standard compose pipeline for consistent behavior.' These two directives conflict because self-containment within the modal and integration with the standard compose pipeline suggest different handling of the compose action, and the expected modal behavior when compose is triggered is not specified.
Integration: call the standard compose callback `onCompose` with `(recipients, attachments)` and let the app open the composer as it usually does. Modal state: the modal component must not close itself when compose is initiated from its compose controls—do not call the modal `onClose` prop (or any prop whose sole purpose is closing this details modal) from the compose button/handler code path. The user can still close via the explicit Close control. Example: `onClick` on group compose runs `onCompose(recipients, [])` only; `onClose` is not invoked there. Counter-example: calling `onClose()` or any callback that dismisses this modal immediately after triggering compose so the group modal unmounts when composition starts.
