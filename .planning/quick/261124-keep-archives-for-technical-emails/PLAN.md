# Quick Plan: Enable keep_archives for Action Group Mailings

## Goal
Explain why `Settings -> Technical -> Emails` (`mail.mail`) is empty after successful delivery, and set `keep_archives = True` on cloned mailings so sent email records are retained in Technical > Emails for auditing/inspection.

## Root Cause
In standard Odoo mass mailing (`mailing.py`), `keep_archives` defaults to `False`.
When `keep_archives` is `False`, `composer_values['auto_delete']` is `True`.
When an email is successfully sent via SMTP, Odoo's `mail_mail._postprocess_sent_message()` automatically deletes (`unlink()`) the `mail.mail` record from the Technical menu to preserve database storage space.
If an email fails, it remains in `mail.mail` as "Delivery Failed".
Because the mailing succeeded and delivered all 8 emails to AWS SES with `250 OK`, Odoo automatically unlinked the queue records.

## Changes
- In `action_group_schedule.py`, set `"keep_archives": True` in `mailing_vals`.
- Bumped version to `20.0.1.0.18` in `__manifest__.py`.
