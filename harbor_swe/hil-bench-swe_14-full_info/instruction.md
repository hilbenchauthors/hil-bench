# PROBLEM STATEMENT
# Flipt Configuration Lacks Metadata Section

## Description

Flipt's current configuration structure does not include a metadata section for application-level settings, making it impossible for users to configure whether the application should check for version updates or manage persistent local data. Without this configuration capability, users cannot control update checking behavior, specify update check scheduling, or designate where application data should be stored.

## Current Behavior

The configuration system has no mechanism for users to specify metadata preferences like version checking behavior, check frequency, or local data storage options, forcing a single hardcoded approach for all users.

## Expected Behavior

The configuration structure should include a metadata section that allows users to configure application-level options, including version checking preferences, check scheduling, and local data management, with appropriate defaults when options are not explicitly specified.


# REQUIREMENTS
- The configuration structure should include a metadata section that contains application-level configuration options, including version checking preferences, check frequency settings, and local data management.

- The metadata section should provide a CheckForUpdates option that allows users to enable or disable version checking at application startup.

- The metadata section should include a configurable path for persistent data storage and a configurable interval for scheduling update checks.

- The configuration loading system should support the metadata section through standard JSON and YAML configuration file formats.

- The default configuration should enable version checking when no explicit metadata configuration is provided, ensuring backward compatibility.

- When loading from a config file, if the data path is set to an empty string or the update check interval is set to zero, the loader must replace those values with their respective defaults rather than using the empty or zero value directly.

- The metadata configuration should integrate seamlessly with existing configuration validation and loading mechanisms, including path validation and interval validation.

- To ensure misconfiguration is detected early, the configuration loader should verify that referenced directories exist on the filesystem before accepting the configuration as valid.

- For zero-configuration deployment scenarios, directory creation should be handled at runtime rather than requiring pre-existing directories during configuration loading.


# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The requirements mention a configurable path for persistent data storage and that sensible defaults should be used, but whether the default location should follow Linux FHS conventions (e.g., /var/opt), use application-local directories (e.g., /tmp), or align with other existing paths in the configuration is ambiguous.
The default data path must be "/var/opt/flipt/meta". This exact value must be used in `Default()` and as the fallback when `data_path` is empty. Example config default: `DataPath: "/var/opt/flipt/meta"`. Counter-example: do not use "/var/opt/flipt/data", "/tmp/flipt", or "/etc/flipt/meta".

### The requirements specify that a zero update check interval should be replaced with a default value, but the specific default duration is not stated anywhere in the problem statement or requirements.
The default update check interval MUST be 6 hours (6 * time.Hour). This exact value MUST be used in `Default()` and as the fallback when `update_check_interval` is zero. Example: setting `update_check_interval: 0` in config results in an effective interval of 6h. Counter-example: do not use 1h, 12h, or 24h.

### Whether the metadata data path must be an absolute filesystem path or can also be a relative path is unspecified, and different deployment scenarios could justify either approach.
Only absolute paths are accepted for the data storage path. Configuration validation must reject data paths that are not absolute. Example: "/opt/app/storage" is valid, "relative/path" is rejected.

### It is unclear whether the update check interval should be validated unconditionally or only when version checking is actively enabled, creating ambiguity about configuration strictness.
Interval validation must only be performed when CheckForUpdates is true. When CheckForUpdates is false, the interval value must not be validated; any interval is accepted. Example: `{CheckForUpdates: false, UpdateCheckInterval: -5 * time.Second}` passes validation; `{CheckForUpdates: true, UpdateCheckInterval: -5 * time.Second}` fails validation.

### One requirement specifies that directory existence should be verified during configuration loading for early failure detection, while another specifies directory creation should be deferred to runtime for zero-configuration deployments.
Directory existence must not be checked during configuration loading. The configuration validator must not verify whether the specified directory is present on the filesystem. The application is expected to create or locate the directory at runtime. Example: setting `data_path: "/nonexistent/flipt/data"` passes configuration validation even though the directory does not exist.
