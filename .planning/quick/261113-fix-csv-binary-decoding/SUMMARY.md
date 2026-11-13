# Quick Task Summary: Fix CSV Binary Decoding for Odoo.sh

**Date:** 2026-11-13
**Version:** 20.0.1.0.6
**Commit:** 2ea4ed1

## Root Cause
The error:
`Could not decode CSV: Invalid base64-encoded string: number of data characters (737) cannot be 1 more than a multiple of 4`
occurred because modern Odoo ORM stores/returns `fields.Binary` as a `BinaryValue` representing raw binary bytes (already decoded). Calling `base64.b64decode` on raw CSV bytes failed because raw CSV is not base64-encoded.

## Key Changes
1. **Implemented `_decode_binary_to_text(binary)`** in `models/imports.py`:
   - Inspects whether input is `BinaryValue`, raw `bytes`, base64 `str`, or data URL.
   - Detects whether bytes/str are already raw CSV text (detecting delimiters like `,`, `;`, or newlines) and decodes using `utf-8-sig`, `utf-8`, `cp1252`, or `latin1`.
   - Handles base64 decoding safely as a fallback for legacy base64-encoded RPC uploads.
2. **Updated `_read_csv`**:
   - Used by both `EligibilityImport` and `WeeklyVhealthRegistration`.
3. **Updated `member_removal.py`**:
   - Replaced direct `base64.b64decode` with `_decode_binary_to_text`.
4. **Added Unit Tests**:
   - Added `test_csv_binary_decoding_variants` to `test_smoke.py`.
5. **Rebuilt Package**:
   - Bumped manifest version to `20.0.1.0.6`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
