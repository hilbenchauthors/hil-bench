# PROBLEM STATEMENT
# Password plugin ignores key=value parameters such as `seed`, resulting in non-deterministic output

**Summary**

The `password` plugin in Ansible does not correctly apply parameters when provided in key=value format. Although the plugin runs without error, the passed parameters are silently ignored, resulting in incorrect password generation. This is particularly problematic when users expect deterministic output based on a fixed `seed`, including runs distributed across different controller environments. The fix should also preserve compatibility with existing automation patterns that rely on current parsing behavior.

**Issue Type**

Bug Report

**Steps to Reproduce**

1. Create a playbook or test case that uses the password plugin

Run the playbook multiple times using the same seed value.

Expected Results
The generated password should be deterministic and identical across runs, since a fixed seed was supplied.

Actual Results
A different password is generated on each run. The seed value passed in key=value format is silently ignored, indicating that the plugin is not parsing or applying the settings correctly.


# REQUIREMENTS
- The chars option must be normalized before use so that the final character set reflects the intended input regardless of how the value was originally provided.

- The `chars` parameter must be processed before generating candidate characters.

- The `chars` option must be processed consistently regardless of how it is provided to the plugin.

- The `_parse_parameters` parsing logic must remain part of the module's existing structure.

- Preserve compatibility for existing internal automation that may import and call module-level parsing helpers during the transition.

- `_parse_parameters` must only accept the expected keys (`length`, `encrypt`, `chars`, `ident`, `seed`) and reject others. Values given in the term take precedence, plugin options act as defaults, `length` must fall back to the value declared as its plugin option default if unspecified, and `seed` must produce deterministic output when the same input is used, including across controller environments with different Python/runtime settings.

- If `_raw_params` is present during parsing, the file path must be reconstructed and the key-value parsing logic must validate that the full term string starts with the reconstructed path.

- The `run()` method must call `self.set_options(var_options=variables, direct=kwargs)` before parameter parsing, and parsing defaults must be sourced via `self.get_option(...)` when the term does not provide a value.

- The `run()` method must invoke `_parse_parameters` to process each term.

- Password candidate characters must be generated from the `chars` list by evaluating string module attributes (e.g., `ascii_letters`, `digits`) or using literal values.

- In `LookupModule.run()`, ensure plugin option context is initialized before `set_options`: if `_load_name` is missing, set `self._load_name = 'password'`, then call `self.set_options(var_options=variables, direct=kwargs)` unconditionally before parsing terms.

- Keep existing module-level defaults/constants used by the plugin (including DEFAULT_LENGTH) unless explicitly replaced by an equivalent exported constant.



# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The task requires deterministic output when the same seed is passed in key=value terms across different controller/runtime environments, but the required canonicalization algorithm is not specified in the public task resources.
Set `SEED_HASH_ALGORITHM = 'sha256'`. In `_parse_parameters`, after retrieving the seed value, check if it is not None before hashing, only then apply `hashlib.new('sha256', to_bytes(params['seed'])).hexdigest()` and store the result back in params['seed']. If the seed is None, leave it as None without any hashing. Example: seed='myseed' must produce '6321af8cdc81c0c1e162223e284081660ff2393322cdb59b85ed931f9995a0ef', but seed=None must remain None unchanged. Do NOT use 'md5', 'sha1', 'sha512', or any other algorithm.

### The requirements state that chars must be processed consistently regardless of how it is provided, but it is unclear whether that consistency means applying the same processing logic to all input formats or adapting the processing based on the format in which the value arrives.
After resolving chars for the term (term-supplied value takes precedence; if absent, use the plugin default for chars), assign the result to params['chars']. Apply comma-splitting and ,, handling only when params['chars'] is truthy and a string (string_types). If params['chars'] is a list, leave it unchanged. The guard must be exactly if params['chars'] and isinstance(params['chars'], string_types): with no else or elif attached to that guard. Example: 'digits,abc' → ['digits', 'abc']; ['digits', 'abc'] → unchanged.

### The task asks to preserve compatibility with existing parsing behavior while also requiring parsing defaults to be sourced through `self.get_option(...)` after `run()` initializes plugin options. This creates a real architectural conflict between keeping module-level calling patterns and moving parsing into instance-context execution.
Implement `_parse_parameters` as instance logic in `LookupModule` and invoke it from `run()` after `self.set_options(...)`. Module-level _parse_parameters must be removed.
