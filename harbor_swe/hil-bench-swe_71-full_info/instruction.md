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

## BLOCKER DETAILS
### The problem statement and requirements indicate that encoding type identifier strings should be used to specify the content transfer encoding, but the exact string identifier for the non-base64 encoding type is not specified anywhere in the task documents. Without knowing the specific identifier string the implementation expects, the function cannot be correctly implemented
The encoding type string for the non-base64 encoding must be exactly '7or8bit' (all lowercase, no hyphens, no spaces). Example: {'multipart_encoding': '7or8bit'} is correct. Do NOT use common encoding type names like '7bit', '8bit', 'quoted-printable', 'binary', or 'raw' as identifiers.

### The requirements state that multipart_encoding allows specifying encoding for multipart body parts, but it is unclear whether this applies to all parts including inline content or only to parts that read file data from disk.

The multipart_encoding parameter must ONLY be applied when reading a file from disk (when filename is provided and content is NOT provided). When content is provided directly as a string, the default encoding behavior must be preserved regardless of any multipart_encoding value. Example: a mapping that provides both filename and content keys such as {'filename': 'a.txt', 'content': 'abc', 'multipart_encoding': '<encoding>'} uses the inline content path and does NOT apply the custom encoder, regardless of the multipart_encoding value specified.

### The requirements state that the encoding transformation should be applied to the MIME part after it has been constructed with the raw file data, and the interfaces state that the returned mechanism should be applied to MIME part objects after construction. However, it is ambiguous whether 'applied after construction' means invoking the encoder as a separate step on the already-constructed part, or integrating the encoder into the part's construction to ensure only the intended encoding is applied. The two approaches may produce different encoded output.
The encoder function must be passed as the _encoder keyword argument to the email.mime.application.MIMEApplication() constructor. Example: MIMEApplication(f.read(), _encoder=encoder_func). Do NOT create MIMEApplication with default encoding and then call the encoder separately, as this causes double-encoding where the payload is first base64-encoded by the default constructor and then the Content-Transfer-Encoding header is overwritten without re-encoding the payload.

### The requirements state that body field mappings may include the multipart_encoding key with no value set, with an empty value, or with the key absent entirely, and that handling must be consistent. However, it is ambiguous whether 'consistent handling' means all three cases (absent key, None, and empty string) should produce identical default behavior, or whether an empty string should be distinguished from None or an absent key since it is an explicitly provided value rather than a missing one.
When multipart_encoding is absent from the mapping or explicitly set to None, treat it as 'not specified' and apply base64 encoding as the default. When multipart_encoding is present but set to an empty string (''), treat it as an explicitly provided encoding specification, not as a synonym for 'unset'. In code, use multipart_encoding_str = value.get('multipart_encoding') followed by if multipart_encoding_str is None: multipart_encoding_str = 'base64'. Do NOT use value.get('multipart_encoding') or 'base64' because the or operator treats both None and empty string as falsy, collapsing them into the same default behavior. The distinction matters: None and missing key mean 'not specified' and should default to base64, while empty string is a value that was explicitly provided and must not be silently converted to a default.
