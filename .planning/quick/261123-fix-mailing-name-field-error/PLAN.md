# Quick Task Plan: Fix ValueError Invalid field mailing.mailing.name on Start Campaign

## Problem
When clicking the "Start Campaign" button on `vhealth.action.group.schedule`:
```
ValueError: Invalid field mailing.mailing.name in condition ('name', '=ilike', 'vHealth - Launch #1 (2025)')
```
Caused by `KeyError: 'name'` in `odoo/orm/domains.py`.

## Root Cause
In Odoo's `mass_mailing` module, the model `mailing.mailing` does not have a `name` field.
Its display name and title is stored in the `subject` field (`_rec_name = "subject"`).
In `action_group_schedule.py`, `_find_template` searched `[("name", "=ilike", expected_name)]`, which triggers a domain error because `name` is not a valid field on `mailing.mailing`.
Similarly, `_create_and_send_launch_mailing` passed `"name": mailing_name` in `mailing_vals`.

## Objective
1. In `models/action_group_schedule.py`:
   - Replace all occurrences of `("name", ...)` with `("subject", ...)` in `_find_template`.
   - In `_create_and_send_launch_mailing`, pass `"subject": template.subject` (or keep the template subject) instead of `"name": mailing_name`.
2. In `tests/test_smoke.py`:
   - Update `Mailing.search` and `Mailing.create` to use `"subject"`.
3. Bump module version in `__manifest__.py` to `20.0.1.0.12`.
4. Verify syntax with `py_compile`.
