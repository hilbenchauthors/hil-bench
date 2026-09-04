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
