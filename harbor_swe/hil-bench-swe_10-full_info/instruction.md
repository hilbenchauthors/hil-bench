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

## BLOCKER DETAILS
### The task requires querying Linux routing data with `ip`, but the public materials do not pin down the exact `ip route` subcommand verb or the table selector passed to `table` for IPv4 and IPv6. Different valid `ip` spellings exist, and the choice changes the argv sequence facts must use.
Use the subcommand verb exactly `list` (not `show` or `ls`) and the table selector exactly `255` (decimal string, not the symbolic table name). Run `ip -4 route list table 255` and `ip -6 route list table 255`. Example argv: `['ip', '-4', 'route', 'list', 'table', '255']`; counter-example: `route show table local` or `route list table local`.

### The problem statement and requirements call for a dedicated fact entry for locally reachable ranges and integration with Linux network fact gathering like other facts. The public interface says callers integrate the method return value into gathered Linux network facts the same way as other network collector fields, but none of those documents name the stable fact entry identifier playbooks should use for this new data.
When wiring the return value into gathered Linux network facts, use the fact entry identifier exactly `snr_scope_host_addrs` (spelling and underscores as given). Counter-example: `locally_reachable_ips`, `local_ips`, `reachable_ips`, or any name not matching that identifier.

### `ip` route stdout mixes several line kinds, and the requirements note that multiple address-like tokens can appear on one row. The public materials still do not pin down which lines are in scope nor which single token is the locally reachable value. Reasonable implementations differ on leading route-type filters, preferring `src` or other labeled fields, scanning the main table for `scope host`, or ingesting every line that looks address-bearing.
Accept a line only if the first whitespace-separated token is exactly `local` (lowercase). Extract the address value from the labeled `src` field on that line (the token immediately following the literal word `src`), not from the positional destination token (second token). If a qualifying `local` line has no `src` field, skip it. Apply the same acceptance and extraction rule to IPv4 and IPv6 stdout. Example: `local 10.0.0.5 dev eth0 proto kernel scope host src 203.0.113.99` -> extract `203.0.113.99` (the `src` value). Counter-example: extracting the second token `10.0.0.5` (the route destination) or using positional field extraction.

### Requirements require normalized and de-duplicated values with a consistent representation for comparisons and templating, while the public interface states values are taken as-is from accepted routing-entry value fields. Those instructions conflict whenever raw route field text is not already in one canonical spelling.
Satisfy the requirements over the interface wording: take each address string already selected from qualifying route lines, convert it to canonical textual form using `ipaddress.ip_address(value)` string form, de-duplicate within each family using that canonical form, then sort each family list ascending by Unicode code-point order of those final strings (e.g. Python `list.sort()`). Bare host addresses must remain without a prefix length suffix (do not force `/32` or `/128`). Example: `2A02:0123:0015::1` and `2a02:123:15::1` are two raw spellings of the same IPv6 address and collapse to one `2a02:123:15::1`; duplicate `10.0.0.44` entries collapse to one `10.0.0.44`. Counter-example: emitting as-printed route text when it differs from canonical form, deduplicating on raw spellings only, omitting a stable sort so order depends on discovery order alone, or appending `/32` to bare IPv4 addresses.
