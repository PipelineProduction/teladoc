# Quick Task Summary: Fix Google Sheet Registration Sync for Odoo.sh

**Date:** 2026-11-17
**Version:** 20.0.1.0.8
**Commit:** bead86c

## Findings & Root Cause
1. **Google Apps Script Verification**:
   - The script `/home/elsner/Documents/pipeline/vhealth_migration/source/code/google_script.js` deployed at `https://script.google.com/macros/s/AKfycbze84DjgKTMAGVuDpepchYgXrPzxmF0LwOmwcUEobVBuqR1EZvZZGyZZCS-ueG5OF6k/exec` works properly.
   - Verified with test requests: HTTP 200 response received and records correctly create/update in the `Aetna Registered` tab in spreadsheet `1lMFNPP7WHJaYCwTQhAc0Km2_aPDJ884soPiOI3QJTrA`.
2. **Why Odoo Didn't Send**:
   - The system parameter `vhealth_email_marketing.google_sheet_webhook_url` was missing from `ir.config_parameter` in the Odoo.sh database.
   - When missing, `_cron_send_registration_queue()` silently returned without attempting to send, leaving `retry_count = 0` and `Sent = False`.
   - The user had no manual "Send" button in the interface to trigger or test the queue.

## Changes Implemented
1. **Auto-Populated Parameter & Fallback**:
   - Added `data/google_sheet_data.xml` registering `vhealth_email_marketing.google_sheet_webhook_url`.
   - Added `DEFAULT_WEBHOOK_URL` fallback in `google_sheet_registration.py` to ensure sending is never bypassed even if the database parameter is deleted.
2. **Payload Date Normalization**:
   - Extracted date part `YYYY-MM-DD` from registration timestamps so it matches the format of existing sheet rows.
3. **Manual Sync Buttons in UI**:
   - Added "Send Pending to Google Sheets" header button on the queue list view.
   - Added "Send to Google Sheets" / "Re-send" buttons on the queue form view.
   - Added "Send to Google Sheets" action in the Action dropdown for bulk selected records.
4. **Immediate Sync on Import**:
   - Updated `imports.py` so processing Weekly vHealth Registrations automatically triggers `_cron_send_registration_queue()` right after queuing.
5. **Rebuilt Package**:
   - Manifest bumped to `20.0.1.0.8`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
