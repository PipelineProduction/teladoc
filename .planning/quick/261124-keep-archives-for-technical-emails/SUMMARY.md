---
status: complete
date: 2026-11-24
commit: 044e525
slug: 261124-keep-archives-for-technical-emails
---

# Quick Task Summary: Enable keep_archives for Action Group Mailings

## Overview
Explained why `Settings -> Technical -> Emails` (`mail.mail`) was empty after delivery, and enabled `keep_archives = True` on cloned mailings so future sent emails remain visible in the Technical menu.

## Mechanism
- Odoo mass mailing has `keep_archives = False` by default.
- This sets `auto_delete = True` on `mail.mail`, which automatically permanently deletes sent records from `mail.mail` upon successful SMTP transmission to save storage.
- Setting `keep_archives = True` tells Odoo to retain the sent records in `mail.mail` under `Settings -> Technical -> Emails`.

## Changes Made
- In `custom_addons/vhealth_email_marketing/models/action_group_schedule.py`:
  - Added `"keep_archives": True` to `mailing_vals`.
- Bumped version in `__manifest__.py` to `20.0.1.0.18`.
