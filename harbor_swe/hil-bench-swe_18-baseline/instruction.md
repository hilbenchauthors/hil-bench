# PROBLEM STATEMENT
## Title: OCI bundle manifest compatibility is not configurable in OCI bundle creation

### Description

Flipt currently builds OCI bundles with a fixed manifest compatibility mode, which causes interoperability problems with registries that accept different manifest variants. Teams using OCI storage can succeed in one environment and fail in another even when the bundle contents are otherwise valid.

The product needs a user-configurable way to influence OCI bundle manifest compatibility so deployments can target different registry expectations. The configuration value should act as a named compatibility selector for supported manifest behaviors rather than assuming callers provide whatever raw OCI version spelling a library happens to use. Some teams reuse one configuration file across multiple processes, and not every process exercises OCI bundle creation on startup, so carrying this setting should not introduce unrelated startup failures before OCI bundle handling is actually used. Bundle creation must remain consistent for users and must fail clearly before an incompatible bundle is produced.



# REQUIREMENTS
- Add an optional string setting named `manifest_version` within the OCI configuration surface.
- The `manifest_version` field carries a manifest-compatibility selector token, not a generic free-form OCI version literal.
- Supported manifest compatibility selector tokens for the setting must be accepted as plain string values at that field.
- When `manifest_version` is set to a supported selector token, OCI bundle creation must use the compatibility behavior named by that token.
- When the setting is omitted, OCI bundle creation must still behave deterministically using one supported compatibility behavior.
- Unsupported `manifest_version` input must not be accepted silently and must surface a clear, human-readable failure that points to the manifest version setting before an incompatible bundle is produced.
- The schema-facing `manifest_version` field must reject any selector token other than the supported ones at the field boundary.



# PUBLIC INTERFACES
Path: internal/oci/file.go
Name: WithManifestVersion
Type: function (functional option)
Input: version string
Output: containers.Option[StoreOptions]
Description: Functional option that sets a manifest-version selector on the OCI store options for bundle creation.
