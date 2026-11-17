# Quick Task Plan: Fix get_param AttributeError on ir.config_parameter and Enable Automatic Google Sheets Push

## Problem
1. When clicking "Send Pending to Google Sheets" or running the cron:
   `AttributeError: 'ir.config_parameter' object has no attribute 'get_param'`
2. User question: Can we automatically push to Google Sheet when importing the file without requiring a manual trigger?

## Root Cause
In Odoo 20 (and current master), `ir.config_parameter` replaced `get_param(key)` with type-safe accessors like `get_str(key, default='')`. Calling `get_param` raises an `AttributeError`.

## Objective
1. Make `_get_endpoint()` version-agnostic: check for `get_str`, fallback to `get_param`, search records directly, and fall back to `DEFAULT_WEBHOOK_URL`.
2. Connect `WeeklyVhealthRegistration.action_process_import` to trigger `_cron_send_registration_queue(limit=500)` immediately, updating the import result with the number of records pushed to Google Sheets so no manual action is needed.
3. Wrap individual row sends in `savepoint` so failures on individual items do not rollback successful ones.
4. Bump version to `20.0.1.0.9` and rebuild package.
