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
