---
status: complete
date: 2026-11-23
commit: 8f2ae31
slug: 261123-fix-mailing-email-from-validation-error
---

# Quick Task Summary: Fix Mailing email_from Validation Error

## Overview
Fixed PostgreSQL / Odoo validation error on `vhealth.action.group.schedule` during "Start Campaign":
`Validation Error: The operation cannot be completed: email from is required for non-template 'mail' mailings`

## Root Cause
In Odoo 20 (`mass_mailing`), check constraint `_email_from`:
```python
CHECK(is_template = true OR email_from IS NOT NULL OR mailing_type != 'mail')
```
When cloning a template record (`is_template = True`), if `template.email_from` was not set, `template.copy()` copied `email_from = False`. Because `mailing_vals` set `is_template = False`, the created mailing violated the constraint because `email_from` was null/empty.

## Changes Made
1. **Model Update (`action_group_schedule.py`)**:
   - In `_create_and_send_launch_mailing`:
     - Explicitly resolved a non-empty `email_from` prior to calling `template.copy(...)`:
       Prioritized: `template.email_from` -> `user.email_formatted` -> `user.email` -> `company.email_formatted` -> `company.email` -> `ir.mail_server._get_default_from_address()` -> `"info@vhealth-teladochealth.com"`.
     - Explicitly set `mailing_vals["email_from"] = email_from`.
     - Preserved or defaulted `reply_to` and `reply_to_mode` (`"new"`).
2. **Smoke Tests (`test_smoke.py`)**:
   - Added assertions to check `step1_mailing_id.email_from` is populated and `step1_mailing_id.is_template` is `False`.
3. **Manifest Version**:
   - Bumped version in `__manifest__.py` to `20.0.1.0.13`.

## Verification
- Syntax checked with `python3 -m py_compile`.
- Removed `__pycache__` artifacts.
