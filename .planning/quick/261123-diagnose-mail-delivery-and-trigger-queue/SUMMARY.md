---
status: complete
date: 2026-11-23
commit: 0213587
slug: 261123-diagnose-mail-delivery-and-trigger-queue
---

# Quick Task Summary: Diagnose Email Delivery & Trigger Outgoing Mail Queue

## Overview
User reported that Scheduled Actions completed Step 1 and the mailing shows "Sent", but no email has arrived in the recipient's inbox (`jenti@elsner.com`). In the Mailings list, the record shows `Status: Sent` but `Sent: 0`, `Delivered: 0%`.

## Diagnosis & Findings
1. **Mailing Generation Succeeded**:
   - In Contact view, chatter shows `Received the mailing vHealth - Launch #1 (2025)`.
   - The drip campaign successfully created the mailing and generated `mail.mail` records.
2. **Why `Sent: 0` in Odoo**:
   - In Odoo `mass_mailing`, when a mailing is processed, the status moves to `'done'` ("Sent") because mail generation is complete.
   - However, individual emails are placed in `mail.mail` in state `'outgoing'`.
   - The `Sent` counter on the mailing only updates when `mail.mail` is transmitted via SMTP.
3. **Queue Delay & SMTP Dependencies**:
   - The standard cron `Mail: Email Queue Manager` (`mail.ir_cron_mail_scheduler_action`) runs once every hour by default.
   - Furthermore, on test/development branches (`dev.skysize.io`), outgoing SMTP servers are often unconfigured or outgoing mail is blocked by default.

## Changes Made
- In `action_group_schedule.py`, added an immediate trigger `mail_cron._trigger()` for `mail.ir_cron_mail_scheduler_action` upon mailing dispatch.
- Bumped version to `20.0.1.0.14`.
