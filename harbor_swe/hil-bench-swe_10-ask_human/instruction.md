# PROBLEM STATEMENT
## Title

Add support for collecting locally reachable IP address ranges

## Summary

Linux can mark IP addresses and prefixes as host-local reachable ranges (commonly used in anycast, CDN, and service binding scenarios). Today, fact gathering does not surface these locally reachable ranges, forcing users to derive them manually.

## Current behavior

- Fact gathering returns standard interface/address details but does **not** expose host-local reachable ranges.

- Users must issue ad-hoc commands or custom parsing to determine which prefixes/addresses are locally reachable.

## Expected behavior

Data is expected to include a dedicated, easy-to-use fact entry for locally reachable IP ranges on the system (for IPv4 and, where applicable, IPv6 when supported). The reported values should include locally reachable prefixes/addresses that the system considers reachable without external routing, based on host-local routing information. Depending on how route output is read, those values may be attributed to different columns on the same line; the implementation must choose one interpretation and apply it uniformly. The feature should integrate with Linux network fact gathering in the same manner as existing network facts.



# REQUIREMENTS
- Maintain a dedicated fact entry that exposes locally reachable IP ranges on the host, so playbooks can consume family-based local reachability data without custom discovery.

- On Linux, collect locally reachable ranges from `ip` route listings for the address families in scope, consistent with how on-host reachability is represented in the kernel routing tables.

- Route lines often include several address-like tokens (for example a prefix or host token early in the line and a `src` value later). The fact must use one consistent rule for which token represents the locally reachable destination for playbooks, applied the same way for IPv4 and IPv6.

- Ensure coverage for both IPv4 and, where applicable, IPv6 in environments that expose applicable host-local ranges, including loopback and locally scoped prefixes, independent of distribution or interface naming.

- Ensure addresses and prefixes derived from host-local routing data are normalized and de-duplicated, with a consistent representation policy that supports reliable comparisons and templating.

- Provide for graceful behavior when the platform lacks the concept or data (e.g., return empty family results and emit concise user-facing notice behavior as appropriate rather than failing), without impacting other gathered facts.

- Maintain compatibility with the existing fact-gathering workflow and schemas, avoiding breaking changes and unnecessary performance overhead during collection.


# PUBLIC INTERFACES
New function: get_locally_reachable_ips Method

File Path: lib/ansible/module_utils/facts/network/linux.py

Function Name: get_locally_reachable_ips

Inputs:

  - self: Refers to the instance of the class.

  - ip_path: The file system path to the `ip` command used to query host-local routing-related information.

Output:

  - dict: A dictionary with exactly two family specific keys, `ipv4` and `ipv6`. Each key is always present and maps to a list of locally reachable IP values for the family. Callers integrate this return value into gathered Linux network facts using the same patterns as other fields produced by the network collector.

Description:

  Initializes a dictionary to store reachable IPs and uses routing-related queries to populate IPv4 and IPv6 addresses or prefixes identified as local from routing output. Values are taken as-is from accepted routing-entry value fields. The result is structured for network fact consumption using a stable family based shape.
