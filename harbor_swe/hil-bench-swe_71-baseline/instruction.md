# PROBLEM STATEMENT
# Title: Add option to control multipart encoding type in URI module

### Summary

When using the URI module with form-multipart, the multipart body payload is always encoded using base64 encoding without any option to change this. However, some platforms don't correctly handle base64-encoded multipart data.

For example, when uploading settings and dashboards to OpenSearch using form-multipart, the operation fails with obscure errors like "Unexpected token in JSON" because OpenSearch can't properly process the base64-encoded content. The same upload works with curl, which uses a non-base64 content transfer encoding.

The proposed solution should allow specifying the content transfer encoding type per file in the body mapping, using encoding type identifiers to specify the desired content transfer encoding. The encoding specification may be omitted from body field mappings, may be present without a value assigned, or may be present with an empty value.

### Issue Type

Feature Idea

### Component Name

ansible.builtin.uri module, lib/ansible/module_utils/urls.py

### Additional Information

Current behavior results in errors when uploading to OpenSearch:

Error with default encoding:

"item": "dashboard.ndjson",
"json": {
  "error": "Bad Request",
  "message": "Unexpected token in JSON at position 4144",
  "statusCode": 400
},
"msg": "Status code was 400 and not [200]: HTTP Error 400: Bad Request"

Proposed solution would allow specifying encoding per file in the body mapping.

## Expected Results:

Multipart files should be able to upload successfully to platforms that require different encoding schemes.

## Actual Results:

Multipart files fail to upload to certain platforms due to the fixed base64 encoding, resulting in errors like "Unexpected token in JSON".


# REQUIREMENTS
- The prepare_multipart function must support an optional multipart_encoding parameter in body field mappings that allows specifying the content transfer encoding type for multipart body parts.

- The implementation must create a set_multipart_encoding function that accepts encoding type identifier strings and maps them to the appropriate encoding mechanisms for MIME multipart data.

- The encoding transformation should be applied to the MIME part after it has been constructed with the raw file data, to ensure the payload is first properly loaded before the desired encoding is applied.

- The function must raise a ValueError with a descriptive message when an unsupported encoding type is provided.

- Body field mappings may include the multipart_encoding key with no value set, with an empty value, or the key may be absent entirely. The handling of these cases must be consistent.


# PUBLIC INTERFACES
Type: Function

Name: set_multipart_encoding

Path: lib/ansible/module_utils/urls.py

Input: encoding (string) — a MIME content-transfer-encoding type name

Output: The appropriate encoding transformation for multipart data

Description: Takes a string specifying the MIME content-transfer-encoding type for multipart data and returns the corresponding encoding transformation mechanism. The returned mechanism should be applied to MIME part objects after construction. For unsupported encoding types, the function should handle them gracefully.
