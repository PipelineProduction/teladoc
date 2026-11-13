# Quick Task Plan: Fix CSV Binary Decoding for Odoo.sh

## Problem
Processing eligibility CSV upload failed with:
`Invalid Operation: Could not decode CSV: Invalid base64-encoded string: number of data characters (737) cannot be 1 more than a multiple of 4`

## Root Cause
In modern Odoo (Odoo 18/20 and current Odoo.sh/Online), reading `rec.x_studio_import_file` returns a `BinaryValue` / raw bytes buffer containing the decoded file bytes directly.
The code previously unconditionally called `base64.b64decode(...)` on this value. Because the CSV is already raw text (922 bytes of text, 737 characters matching the base64 alphabet after stripping non-base64 characters like commas and newlines), `base64.b64decode` threw a `binascii.Error`.

## Objective
Implement `_decode_binary_to_text(binary)` to seamlessly detect and handle:
- Odoo `BinaryValue` / raw bytes (UTF-8, UTF-8 with BOM, Latin-1, CP1252)
- Legacy base64 encoded bytes
- Base64 encoded strings and Data URLs (`data:text/csv;base64,...`)
Apply across `EligibilityImport`, `WeeklyVhealthRegistration`, and `AetnaMemberRemoval`.
