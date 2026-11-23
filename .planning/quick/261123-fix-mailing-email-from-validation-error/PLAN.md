# Quick Plan: Fix Mailing email_from Validation Error

## Goal
Resolve `ValidationError: The operation cannot be completed: email from is required for non-template 'mail' mailings` when clicking **Start Campaign** on `vhealth.action.group.schedule`.

## Context & Root Cause
In Odoo 20 (`mass_mailing/models/mailing.py`):
```python
_email_from = models.Constraint(
    "CHECK(is_template = true OR email_from IS NOT NULL OR mailing_type != 'mail')",
    "email from is required for non-template 'mail' mailings"
)
```
When master templates under **Email Marketing > Templates** are created, `email_from` can be left blank because `is_template = True` relaxes the constraint.
When `template.copy(default=mailing_vals)` was executed in `_create_and_send_launch_mailing`:
- `mailing_vals` set `is_template: False`
- `email_from` was not included in `default`, so `copy_data()` copied `email_from = False` from the master template
- This inserted a row with `is_template = False`, `email_from = NULL`, `mailing_type = 'mail'`, immediately triggering the DB constraint.

## Implementation Steps
1. **Model Update (`action_group_schedule.py`)**:
   - In `_create_and_send_launch_mailing(step_number)`:
     - Robustly resolve `email_from`:
       `template.email_from` -> `user.email_formatted` -> `user.email` -> `company.email_formatted` -> `company.email` -> `ir.mail_server._get_default_from_address()` -> fallback `"info@vhealth-teladochealth.com"`.
     - Explicitly pass `"email_from": email_from` in `mailing_vals`.
     - Also pass `reply_to` and `reply_to_mode` with clean fallbacks.
2. **Smoke Test Update (`test_smoke.py`)**:
   - Assert `campaign.step1_mailing_id.email_from` is populated.
   - Assert `campaign.step1_mailing_id.is_template` is `False`.
3. **Manifest Version Bump (`__manifest__.py`)**:
   - Bump version to `20.0.1.0.13`.
4. **Compile & Clean**:
   - Run `python3 -m py_compile`.
   - Remove `__pycache__`.
5. **Documentation & STATE**:
   - Create `SUMMARY.md` and update `STATE.md`.
