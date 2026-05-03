# PROBLEM STATEMENT
# Implement proper Punycode encoding for URLs to prevent IDN phishing attacks

## Description

The application must safely handle URLs with internationalized domain names (IDN) by converting hostnames to an ASCII-safe representation to reduce phishing risk from homograph domains. The current behavior does not consistently normalize external links before confirmation, especially when different URL representations are available from the clicked element. The link processing pipeline may also encounter malformed or unparseable URL strings from user-authored content.

## Steps to Reproduce

1. Navigate to a part of the application where external links are rendered.
2. Click a link containing Unicode hostname characters, for example `https://www.аррӏе.com/path/?a=1#x`.
3. Observe the confirmation flow when both browser-normalized link output and original authored `href` are present.

## Expected Behavior

External links should display an ASCII-safe hostname and preserve navigation intent for path, query, and fragment. Hostname extraction should produce the canonical matching key used by domain checks, including cases with nested subdomains and multi-level suffixes. Authored deep-link paths should remain intact while output URLs should be clean and normalized.

## Actual Behavior

Unicode hostnames may be shown without a fully consistent normalization path, and link processing can vary depending on which URL representation is used during handling. Hostname simplification for matching keys produces inconsistent results for structures like `www.mail.proton.me` or `secure.login.example.co.uk`, which can lead to incorrect external-link decisions. Unparseable URL strings passed through the pipeline may cause unexpected failures.


# REQUIREMENTS
- The `punycodeUrl` function must convert Unicode hostnames to ASCII-safe hostnames and keep protocol, path without trailing separator, query, and fragment unchanged.
- The hostname extraction helper must reduce the extracted hostname into the canonical matching key used by domain checks, including nested subdomains and multi-level public suffix structures.
- The `useLinkHandler` hook must apply punycode conversion using the canonical link source to external links before processing them.
- The output path must remain equivalent to the user-authored path so deep links keep their original navigation behavior.
- If no URL can be extracted from the link target, the hook must emit an error notification and stop external-link processing.


# PUBLIC INTERFACES
1. Type: Function

   Name: getHostnameWithRegex

   Path: packages/components/helpers/url.ts

   Input:

   url (string)

   Output: string

   Description: Extracts the hostname from a URL using a regular expression and returns the canonical matching key used by domain matching logic.

2. Type: Function

   Name: punycodeUrl

   Path: packages/components/helpers/url.ts

   Input:

   url (string)

   Output: string

   Description: Converts a URL with Unicode characters to ASCII punycode format while preserving the URL components.

## BLOCKER DETAILS
### The specs require hostname simplification for matching but never define how far the hostname should be reduced. Multiple reduction levels are valid and the correct matching key cannot be determined without an explicit policy.
Strip any leading www. prefix, then use the existing getSecondLevelDomain helper to obtain the registrable domain, applying it iteratively for multi-level public suffixes, and return only the leftmost label. Example: both `www.mail.proton.me` and `calendar.proton.me` yield `proton`; `secure.login.example.co.uk` yields `example`.

### The requirements specify how punycodeUrl should transform valid URLs but do not specify the exact fallback output value when the input string cannot be parsed as a URL. The required return format is not provided anywhere in the specifications.
Wrap the URL constructor in a try-catch. When parsing throws, return a data: URI (RFC 2397) containing the original input — specifically the string `'data:,'` followed by the original URL. Do not return the original URL unchanged, an empty string, or let the error propagate.

### The requirements specify trailing path separators must be cleaned from output, while also requiring the output path to remain equivalent to the user-authored path. These rules conflict for any URL whose authored path ends with a separator.
Apply trailing separator removal only to root paths. When the parsed pathname is exactly `'/'`, strip it to produce a clean domain-only URL. For all other paths, preserve the trailing separator as authored. Example: `https://example.com/` becomes `https://example.com` but `https://example.com/path/` stays unchanged.
