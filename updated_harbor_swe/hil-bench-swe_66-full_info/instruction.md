# PROBLEM STATEMENT
# Title: `ansible.builtin.password` fails on subsequent runs when ident is saved in the password file.

## Description.
When using `lookup('ansible.builtin.password', ...)` with an encryption method that supports an `ident` parameter, the first run correctly saves the password along with its metadata in the file. However, on subsequent executions, the lookup fails because previously saved values are not correctly parsed from the file. This leads to unhandled exceptions when trying to re-encrypt using bcrypt or other algorithms.

## Actual Behavior.

1. First run creates the password file with the password and associated encryption metadata.

2. Second run fails with an unhandled exception when metadata is present in the saved file. Example:

 ---

$ ansible -m debug -a "msg={{lookup('ansible.builtin.password', 'password.txt encrypt=bcrypt')}}" localhost

[WARNING]: No inventory was parsed, only implicit localhost is available

localhost | FAILED! => {

 "msg": "An unhandled exception occurred while running the lookup plugin 'ansible.builtin.password'. Error was an unexpected exception related to invalid characters in bcrypt salt."

}

---

## Expected Behavior.
On subsequent runs, the lookup should read and interpret the password file correctly, handling all stored metadata appropriately for re-encryption.

## Additional Information.
- Tested with Ansible Core 2.14.3 on Arch Linux.
- Python version 3.10.10.


# REQUIREMENTS
- The password lookup plugin parses password files containing password and associated metadata values, returning parsed components and treating missing values as None.

- Password file operations are idempotent - repeated executions with the same parameters produce the same result without modifying the file content unnecessarily.

- When a password file contains an ident value, subsequent runs reuse that stored ident rather than generating a new one or duplicating the entry in the file.

- Password files are updated atomically to prevent corruption during concurrent access by multiple processes.

- The plugin handles empty or missing password files by generating appropriate password, salt, and ident values based on the encryption method specified.

- Password file format supports storing and retrieving password and metadata values in a way that allows reliable parsing on subsequent reads.

- Error handling should provide clear messages when password file processing or encryption operations encounter failures, wrapping underlying library exceptions into user-friendly errors.

- Providing an ident parameter to the lookup directs the plugin to use that identifier for the encryption algorithm.


# PUBLIC INTERFACES
No new interfaces are introduced.

## BLOCKER DETAILS
### The problem statement describes a crash caused by the hashing library receiving malformed salt input on subsequent runs. The fix requires intercepting this specific failure from passlib to convert it into a recoverable Ansible error, but the specific exception class that passlib raises for input validation failures is not documented in the problem statement or requirements. Catching the wrong exception class would either leave the original crash completely unfixed (if the actual exception type is not intercepted) or silently suppress unrelated programming errors by catching too broadly.
Passlib raises ValueError when it encounters invalid input parameters such as a malformed salt or ident value. Catch specifically ValueError in the PasslibHash._hash method's hashing calls and convert it to an AnsibleError. Catching a different type (e.g., TypeError, OSError) would fail to intercept the actual crash, and catching broadly (e.g., Exception) would mask unrelated bugs.

### The requirements specify that password files are updated atomically using file locking to prevent corruption during concurrent access. However, they do not specify the boundary of the lock-protected region — specifically whether the computationally expensive encryption/hashing operation should execute while the lock is held or only after the lock is released. The existing code performs lock acquisition, file I/O, lock release, and then encryption in sequence, but the requirements for atomic updates do not clarify which operations must be inside the critical section when the code is refactored to use try/finally for safe lock release.
The lock-protected region (try/finally block) must encompass only file operations: reading, parsing, and writing the password file. The encryption call (do_encrypt/passlib_or_crypt) must be placed outside and after the finally block that releases the lock. This preserves the original code's sequencing where the lock is released before encryption begins, preventing unnecessary lock contention during the expensive hashing operation.

### The requirements state that the password file format supports storing and retrieving metadata values alongside the password, and that parsing should be reliable on subsequent reads. However, neither the problem statement nor the requirements specify the correct search scope for extracting the ident field when the password body itself may contain substrings that resemble metadata markers. Multiple valid parsing strategies exist — searching the full content for each marker independently, restricting later extractions to a substring computed after earlier ones, or using a single-pass regex — and each can produce different results for the same file content.
The ident value must be extracted exclusively from the portion of file content that follows the salt delimiter, never from the original full content. First, locate the salt delimiter and separate everything after it from the password. Then, search for the ident marker only within that post-salt portion. If found, the ident value is the text after the ident marker and the salt is the text before it within that portion. If the ident marker is not found in the post-salt portion, the entire portion is the salt value and ident is None.

### The requirements contain conflicting guidance on ident value selection during password file processing. One requirement states that when a password file already contains an ident value, subsequent runs should reuse that stored value rather than generating a new one, implying stored values have persistence priority. A separate requirement states that when a user explicitly provides an ident parameter, that value directs the encryption algorithm identifier to use, implying user input should be authoritative. When the stored ident differs from the user-provided ident, these requirements directly conflict and there is no guidance on which takes priority or how the mismatch should be handled.
The stored ident from the password file takes precedence over both the user-provided ident parameter and the encryption algorithm's default. If a stored ident exists and the user provides a different ident, the plugin must raise an error indicating the conflict between the two values. If no stored ident exists, the user-provided ident is used. If neither a stored nor user-provided ident exists, the encryption algorithm's implicit default ident is used as a last resort, and the file should be marked as changed for rewriting.
