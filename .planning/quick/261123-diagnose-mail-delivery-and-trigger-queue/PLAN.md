# Quick Plan: Diagnose Email Delivery & Trigger Outgoing Mail Queue

## Goal
Explain how email delivery works in Odoo mass mailing, why the mailing shows "Sent: 0" / "Delivered: 0%", diagnose why emails have not reached the recipient's inbox yet, and trigger the outgoing mail queue immediately.

## Findings from Screenshots
1. **Screenshot 1 (`screen1.png`)**:
   - Campaign `NEW GROUP LAUNCH EMAILS - Eligible Member 2026-11-16` ran Step 1 successfully.
   - Status: `Running`, Next Step due in 7 days.
2. **Screenshot 2 (`screen2.png`)**:
   - Contact `Blaine Reddam` (`jenti@elsner.com`) shows in chatter: `Received the mailing vHealth - Launch #1 (2025)`.
   - The email record (`mail.mail`) was created and attached to the contact successfully.
3. **Screenshot 3 (`screen3.png`)**:
   - Mailing shows `Status: Sent` (state='done'), but `Sent: 0`, `Delivered: 0%`.
   - In Odoo, mass mailing creates `mail.mail` records in state `outgoing`.
   - The `Sent` counter only updates when `mail.mail` is physically pushed out by SMTP.
   - The standard cron `Mail: Email Queue Manager` (`mail.ir_cron_mail_scheduler_action`) runs every **1 hour** by default.
   - If no Outgoing Mail Server is configured (or on Odoo.sh dev environments), emails stay in `outgoing` or fail with an SMTP error.

## Actions
1. **Trigger Mail Queue Cron**:
   - In `_create_and_send_launch_mailing`, trigger `mail.ir_cron_mail_scheduler_action` right after launching so emails do not wait for the 1-hour interval.
2. **Detailed Troubleshooting Checklist for User**:
   - Check `Settings -> Technical -> Emails` (`mail.mail`).
   - Check `Settings -> Technical -> Outgoing Mail Servers` (`ir.mail_server`).
   - Check `Settings -> Technical -> Automation -> Scheduled Actions` (`Mail: Email Queue Manager`).
