# Quick Task Summary: Fix ValueError Invalid field mailing.mailing.name on Start Campaign

**Date:** 2026-11-23
**Version:** 20.0.1.0.12
**Status:** complete

## What Was Done
1. **Root Cause Analysis**:
   - In Odoo `mass_mailing`, the model `mailing.mailing` does not define a `name` field.
   - Its primary record title and name is the `subject` field (`_rec_name = "subject"`).
   - Calling `Mailing.search([("name", "=ilike", ...)])` raised `KeyError: 'name'` and `ValueError: Invalid field mailing.mailing.name`.
2. **Fix**:
   - In `models/action_group_schedule.py`, replaced all search conditions on `mailing.mailing` to search by `subject`:
     - Exact subject: `("subject", "=ilike", expected_subject)`
     - Loose pattern fallback: `("subject", "ilike", f"Launch #{step_number}")`
   - In `_create_and_send_launch_mailing`, updated `mailing_vals` to use `"subject": template.subject` instead of `"name": mailing_name`.
   - In `tests/test_smoke.py`, updated mock template searches and creation to use `subject`.
3. **Module Version**:
   - Bumped version to `20.0.1.0.12` in `__manifest__.py`.
