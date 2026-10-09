# PROBLEM STATEMENT
### Title

Package manager discovery assigns incorrect defaults on Red Hat family systems

### Description

The package manager fact collector does not consistently determine the correct default package manager across Fedora, Amazon Linux, and other Red Hat family systems. In some environments the reported `ansible_pkg_mgr` value does not match the distro-supported default, and in others the collector infers a manager when it should remain `unknown`.

### Expected Behavior

The discovery logic should report the distro-supported default package manager for supported Red Hat family versions and configurations, while avoiding unsupported inference when the available system state is insufficient.

### Actual Behavior

In some configurations, the reported package manager is incorrect or is inferred too aggressively, causing package installation and provisioning tasks to use the wrong backend.

### Impact

Playbooks fail during package installation and provisioning. Users cannot rely on `ansible_pkg_mgr` being accurate across supported Red Hat family environments.



# REQUIREMENTS
- The `collect` method of `PkgMgrFactCollector` must always return a dictionary that includes the key 'pkg_mgr'; when no valid manager can be inferred, the value must be 'unknown'.

- On Fedora systems (where 'ansible_distribution' equals 'Fedora'), the default package manager is determined by the major version:
  - If the major version is less than 23, the preferred package manager is `yum`.
  - For version 23 and later, Fedora uses the dnf family of package managers.
  - Fedora 39 and later may report `dnf5` when that is the installed default dnf-family manager.
  - When the preferred manager binary is not found, the collector must fall through to dnf-family binary detection rather than returning a hardcoded default.

- On Amazon Linux systems (where 'ansible_distribution' equals 'Amazon'), the default package manager is determined by the major version:
  - If the major version is less than 2022, the preferred package manager is `yum`.
  - For version 2022 and later, Amazon Linux uses the dnf family of package managers.
  - When the preferred manager binary is not found, the collector must fall through to dnf-family binary detection rather than returning a hardcoded default.

- On other Red Hat family systems (where 'ansible_os_family' equals 'RedHat' but 'ansible_distribution' is neither 'Fedora' nor 'Amazon'), the default package manager is determined by the major version:
  - If the major version is less than 8, the default package manager is `yum`.
  - Otherwise, the default package manager is `dnf`.

- When a system uses the dnf family, the collector should determine the active default from available system binaries.

- `collected_facts` must include keys 'ansible_distribution' and 'ansible_distribution_major_version'.

- `os.path.exists()` must be used to check whether a binary path exists.


# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The requirements mention that Fedora 39+ may report dnf5, but do not provide the specific comparison rule needed to distinguish dnf from dnf5, the path to resolve, the resolution function, and the target string are all unspecified. What concrete detection rule should be used?
When /usr/bin/dnf exists, resolve that path with os.path.realpath(). If os.path.basename() of the resolved path equals 'dnf5', return 'dnf5'; otherwise return 'dnf'. Dnf variant detection (dnf vs dnf5 via os.path.realpath('/usr/bin/dnf')) applies to all RedHat-family dnf-family outcomes, including non-Fedora/non-Amazon systems (RHEL/clones) when major version indicates dnf-family usage. Example: os.path.realpath('/usr/bin/dnf') is '/usr/bin/dnf-3' means pkg\_mgr is 'dnf'. Counter-example: do NOT infer the variant from the Fedora version number alone

### The requirements state that when the preferred manager binary is not found, the collector must fall through to dnf-family binary detection, but they do not specify which binaries the detection should check or what value to return when the primary dnf binary is absent but another dnf-family binary exists on the system.
If /usr/bin/dnf does not exist but /usr/bin/microdnf exists, return 'dnf' directly. The presence of microdnf is sufficient to confirm the system belongs to the dnf family. Example: Fedora 38 with only /usr/bin/microdnf installed — pkg_mgr is 'dnf'.

### The requirements state the collector returns 'unknown' when no valid manager can be inferred but do not define which specific binary paths qualify as primary defaults versus secondary variants excluded from inference. What is the exact boundary?
If /usr/bin/dnf does not exist, the collector must not infer pkg\_mgr from standalone secondary binaries such as /usr/bin/dnf-3 or /usr/bin/dnf5. In that situation, pkg\_mgr must be 'unknown'. Example: Fedora 38 with only /usr/bin/dnf5 installed, pkg\_mgr is 'unknown'.

### The requirements define behavior in terms of ansible\_distribution\_major\_version as a number, but do not say how to handle cases where that value cannot be parsed as an integer. Should the collector fall back to a family default, attempt partial interpretation, or return unknown?
Parse ansible\_distribution\_major\_version as a full integer. If parsing fails (e.g., 'rawhide'), do not fall back to a family default like 'dnf'; instead skip version-based logic and proceed with binary-based detection. If no valid binary is detected, return 'unknown'. Example: Fedora with version 'rawhide' and no dnf binary installed, pkg\_mgr is 'unknown'.

### The other Red Hat requirement says version-based defaults are authoritative and should be applied based on the version number, but the general requirement says pkg\_mgr must be 'unknown' when no valid manager can be inferred. Which rule takes precedence when the version-implied binary is absent?
The 'unknown' fallback rule takes precedence over the version-authority claim for non-Fedora, non-Amazon RedHat-family systems. Determine the version-preferred manager by major version (<8 => yum, >=8 => dnf), then verify that preferred manager's primary binary exists using os.path.exists(). If the preferred binary does not exist, return 'unknown' even if other package-manager binaries are present.
