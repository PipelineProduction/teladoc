# Quick Plan: Diagnose AWS SES Delivery Failure & Explicit Mail Server Binding

## Goal
Diagnose why emails fail with "Delivery Failed" when sending via AWS SES SMTP, provide actionable steps to view the exact error log in Odoo, and explicitly wire `mail_server_id` and verified `from_filter` in `_create_and_send_launch_mailing`.

## Context & Root Cause Analysis
AWS SES is stricter than regular SMTP servers:
1. **Unverified Sender (`email_from`)**: AWS SES will immediately reject emails if the `From` header does not match a verified identity or domain in AWS SES. If the template's "Send From" field is blank, Odoo falls back to admin or system emails (e.g. `admin@example.com`), which are not verified in SES.
2. **AWS SES Sandbox Mode**: All new AWS SES setups start in Sandbox. In Sandbox mode, AWS rejects emails to ANY unverified recipient email!
3. **Mail Server Binding**: If `mail_server_id` is not explicitly set on the cloned `mailing.mailing`, Odoo relies on fuzzy domain matching against `from_filter`, which can fail if the sender domain doesn't match the server.

## Actions Taken
1. In `_create_and_send_launch_mailing`:
   - Resolve active `ir.mail_server` and explicitly bind `mailing_vals["mail_server_id"] = mail_server.id`.
   - Prefer `mail_server.from_filter` if template `email_from` is blank.
2. Bump version to `20.0.1.0.17`.
3. Provide the user with exact instructions to find the failure reason under **Settings > Technical > Emails** (`mail.mail`).
