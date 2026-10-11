# PROBLEM STATEMENT
# Standardizing mail metrics helper functions.

## Description.

The mail web application needs helper functions that prepare mailbox identifiers and page size settings for metrics. Right now, the normalization rules are not clearly defined, which can lead to inconsistent metric labels across dashboards. To keep reporting reliable, these helpers must standardize mailbox IDs and page size values in a way that avoids fragmented labels.

## Actual Behavior.

Mailbox identifiers may be inconsistent for user-defined labels or blank inputs, and supported page size settings may produce labels that do not line up with the metric naming expected by the metrics pipeline.

## Expected Behavior. 

Mailbox identifiers and supported page size values should produce stable metric labels for both common and edge-case inputs, including custom labels and blank identifiers, so downstream metric analysis stays consistent.



# REQUIREMENTS
- Implement a helper method `getLabelID` that produces stable mailbox metric identifiers for blank identifiers and user-defined labels or folders.

- Custom labels and folders should collapse into one shared metrics token instead of using their original IDs directly.

- Blank mailbox identifiers should still normalize into one stable metrics category instead of fragmenting dashboards.

- Implement a helper method `getPageSizeString` that converts supported mail settings page size values into metric labels.

- Supported page size values should be emitted as their raw page-size numbers expressed as strings by comparing the raw `PageSize` numbers directly inside the helper.

- When the page size setting is missing or unsupported, return `page-size-other`.

- The helper functions should use existing shared imports where appropriate.



# PUBLIC INTERFACES
New public interfaces: 

- Type: New file 
Name: `mailMetricsHelper.ts` 
Path: `applications/mail/src/app/metrics/mailMetricsHelper.ts` 
Description: Provides helper functions for mail metrics, including functions that normalize mailbox identifiers and page size settings into stable metric labels. 

- Type: Function 
Name: `getPageSizeString` 
Path: `applications/mail/src/app/metrics/mailMetricsHelper.ts` 
Input: `settings` <MailSettings | undefined> 
Output: <string> 
Description: Converts the mail page size setting into prefixed metric bucket labels for supported page sizes, with the fallback label `page-size-other` when the setting cannot be classified. 

- Type: Function 
Name: `getLabelID` 
Path: `applications/mail/src/app/metrics/mailMetricsHelper.ts` 
Input: `labelID` <string> 
Output: <string> 
Description: Processes a mailbox identifier by normalizing blank identifiers and custom labels or folders into consistent metrics categories.
