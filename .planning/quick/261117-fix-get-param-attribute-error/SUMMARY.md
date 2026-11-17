# Quick Task Summary: Fix get_param AttributeError on ir.config_parameter and Enable Automatic Google Sheets Push

**Date:** 2026-11-17
**Version:** 20.0.1.0.9
**Commit:** 4107018

## What Was Done
1. **Fixed `AttributeError: 'ir.config_parameter' object has no attribute 'get_param'`**:
   - In Odoo 20, `ir.config_parameter` uses `get_str(key, default="")` instead of `get_param`.
   - Updated `_get_endpoint` in `models/google_sheet_registration.py` to check `hasattr(Config, "get_str")`, fallback to `get_param`, search directly in `ir.config_parameter`, and finally fallback to `DEFAULT_WEBHOOK_URL`.
2. **Automatic Google Sheets Push on Import**:
   - In `models/imports.py`, `WeeklyVhealthRegistration.action_process_import` now automatically triggers `_cron_send_registration_queue(limit=500)` immediately after queuing imported records.
   - Updated the import result summary to display: `Processed X rows; created Y; updated Z; errors 0. Google Sheets: N sent, 0 errors.`
   - Users no longer need to manually click any button; importing the CSV pushes to Google Sheets immediately.
3. **Database Savepoints**:
   - Wrapped each record send in `with self.env.cr.savepoint():` so that each row is safely committed without aborting the entire transaction.
4. **Packaged**:
   - Version bumped to `20.0.1.0.9`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
