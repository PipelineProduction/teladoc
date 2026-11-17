# Quick Task Plan: Fix Google Sheet Registration Sync for Odoo.sh

## Problem
In Odoo, the Google Sheet Registration Queue shows 7 records with `Sent = False` and `Retry Count = 0`, but the Google Sheet (`Dev - vHealth Aetna Master Group List (ALL GROUPS COMBINED)`) has not received the records.

## Investigation & Root Cause
1. **Google Apps Script is working**: Tested the webhook endpoint `https://script.google.com/macros/s/AKfycbze84DjgKTMAGVuDpepchYgXrPzxmF0LwOmwcUEobVBuqR1EZvZZGyZZCS-ueG5OF6k/exec`. Direct POST successfully added/updated records in sheet tab `Aetna Registered`.
2. **Missing Configuration in Odoo.sh**: `google_sheet_registration.py` was looking up `vhealth_email_marketing.google_sheet_webhook_url` in `ir.config_parameter`. Since this was not set in the database, `get_param(...)` returned `False` and the cron silently returned without attempting to send or logging an error on the records (which is why `retry_count` remained 0).
3. **No Manual Action in UI**: There was no button in the UI to manually send pending queue records or test individual items.
4. **No Auto-Trigger on Import**: Weekly Vhealth Registration Import populated `x_google_sheet_registr` but did not trigger the sync immediately.

## Plan
1. Add `data/google_sheet_data.xml` with `noupdate="0"` to pre-configure `vhealth_email_marketing.google_sheet_webhook_url`.
2. Add hardcoded fallback `DEFAULT_WEBHOOK_URL` in `google_sheet_registration.py` so it never silently skips.
3. Clean date string to `YYYY-MM-DD` (strip `00:00:00`) before sending payload.
4. Add `action_send_now`, `action_send_selected`, and `action_process_queue` on `x_google_sheet_registr` with buttons in list and form views.
5. In `imports.py`, trigger `_cron_send_registration_queue()` immediately upon completing weekly registration import.
6. Bump version to `20.0.1.0.8` and rebuild zip.
