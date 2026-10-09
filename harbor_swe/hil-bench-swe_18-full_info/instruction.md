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

## BLOCKER DETAILS
### The requirements say `manifest_version` accepts supported manifest-compatibility selector tokens as plain string input, but they do not specify which exact tokens are supported. A competent engineer could reasonably accept several different token sets that all sound compatible with the visible task, including raw version-like spellings, prefixed forms, or product-style aliases.

The only supported `manifest_version` selector tokens are exactly `oci-1.0` and `oci-1.1`. Inputs such as `1.0`, `1.1`, `v1.0`, or `v1.1` are unsupported.

### The requirements say omission must still behave deterministically using one supported compatibility behavior, but they do not define which observable bundle form omission should reuse. A competent engineer could still choose multiple omission behaviors, including matching one explicit supported form or keeping omission on its own stable bundle form.

When `manifest_version` is omitted, bundle creation must produce the same observable manifest structure as the explicit supported selection whose manifest omits the top-level `artifactType` field and keeps the feature media type in `config.mediaType`. Counterexample: an omitted-setting bundle manifest carries the feature media type in a top-level `artifactType` field.

### The problem statement says shared configuration should not cause unrelated startup failures before OCI bundle handling is actually used, because some deployments reuse one config file across processes that do not all exercise bundle creation on startup. The requirements also say the schema-facing `manifest_version` field must reject any selector token other than the supported ones at the field boundary. Those instructions conflict on whether unsupported literals may survive configuration intake for shared-config portability or must be rejected immediately during intake.

Unsupported `manifest_version` selector tokens must be preserved during schema validation and configuration loading so shared configuration can still be accepted before OCI bundle handling is used. Validation must occur when OCI bundle creation resolves the manifest compatibility mode: bundle creation must fail clearly before producing a bundle, and the failure must identify the manifest version setting in human-readable wording rather than only echoing the raw config key format. Unsupported input must not be normalized into a supported selector token or silently ignored.
