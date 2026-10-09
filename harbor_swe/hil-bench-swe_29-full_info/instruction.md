# PROBLEM STATEMENT
## Title:
PSRP connection plugin exhibits inconsistent configuration behavior when handling optional inputs.

### Description:
The PSRP connection plugin may accept and apply additional connection-related inputs beyond its documented configuration surface. This can result in ambiguous behavior, where the effective connection settings vary depending on how and where configuration values are provided.

Such behavior can lead to inconsistent outcomes across environments, reducing predictability and making it difficult to reason about which inputs ultimately influence the connection configuration. In some cases, different combinations of inputs may appear to overlap in purpose, while their interaction and precedence are not clearly defined.

### Actual Behavior:
Currently, the plugin may construct its effective connection configuration based on a combination of documented options and other available inputs. When multiple inputs influence the same aspect of the connection, the resulting behavior can differ depending on input shape, ordering, or environment, leading to outcomes that are not consistently reproducible.

### Expected Behavior:
The PSRP connection plugin should produce a deterministic and predictable connection configuration. The effective configuration should be derived from clearly defined inputs, with well-defined handling when multiple inputs influence the same behavior. Configuration that falls outside the documented surface should not introduce ambiguity or unpredictability in the resulting connection settings. Playbooks that rely solely on documented configuration should behave consistently across environments. The PSRP connection plugin may still accept and apply additional connection-related inputs beyond its documented configuration surface.


# REQUIREMENTS
- The PSRP connection plugin must derive its effective connection configuration from supported connection-related inputs in a deterministic manner, producing consistent results across environments.

- When more than one supported input influences the same aspect of the connection configuration, the plugin must apply a consistent precedence strategy to determine the final effective value.

- Connection-related boolean behaviors must be represented as boolean values in the effective configuration, even when the inputs originate from inventory or variables.

- The effective connection configuration should reflect the resolved values used to establish the connection, without depending on environment-specific behavior.


# PUBLIC INTERFACES
"No new interfaces are introduced"

## BLOCKER DETAILS
### The effective configuration relies on interpreting user-provided values that may be expressed in different forms, which can lead to different reasonable interpretations when mapping them into a boolean behavior.
For ignore_proxy, only the case-insensitive string values 'true' and 'y' must be interpreted as True. All other values must be interpreted as False, including the strings 'yes' and '1' (they must not be treated as True). Normalization for ignore_proxy must be applied to the raw value as supplied in inventory/vars, not to the value returned by get_option. The framework already coerces strings such as "yes" and "1" to boolean True before the plugin uses the value, so the plugin must capture the raw value (e.g. in set_options) and apply the strict rule (“only 'true' and 'y' → True”) to that raw value so that "yes" and "1" are not treated as True.

### Multiple supported inputs can influence certificate validation behavior, and different precedence choices can lead to materially different effective configurations.
If cert_validation is set to ignore set cert_validation to False otherwise if a certificate trust path is provided set cert_validation to that path else set cert_validation to True

### The problem statement indicates that the PSRP connection plugin may accept and apply additional connection-related inputs beyond its documented configuration surface. Then it says in expected behaviour that it may still accept and apply additional connection-related inputs but PSRP connection plugin should produce a deterministic and predictable connection configuration, which is contradictory.
Treat the documented PSRP connection plugin options as the ONLY supported inputs that may influence the effective connection configuration. Ignore any connection-related inputs provided outside the documented option set (including extra inventory vars/host vars/group vars not mapped to documented options). Do not fail the connection due to unknown/extra inputs; instead, emit a debug-level log entry indicating the ignored key(s).

Emit the “ignored key(s)” log using the Display.debug API (the Ansible debug-level method), not display.vvv, display.warning, or any other verbosity level.

Emit a single debug-level log entry that includes or lists all ignored key(s) (e.g. one message containing every key in _extras that is ignored), not one log entry per key.
