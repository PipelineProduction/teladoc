---
status: complete
date: 2026-11-24
commit: 14afc23
slug: 261124-diagnose-aws-ses-delivery-failure
---

# Quick Task Summary: Diagnose AWS SES Delivery Failure & Explicit Mail Server Binding

## Overview
User configured AWS SES SMTP in Outgoing Mail Servers (`ir.mail_server`), but emails showed "Delivery Failed" when sending.

## Root Cause & Solutions
1. **AWS SES Sender Verification**:
   - AWS SES requires the `From` email address / domain to be verified under AWS SES -> Verified Identities.
   - If the template under Email Marketing > Templates had no "Send From", Odoo was falling back to the admin user email, causing SES rejection.
2. **AWS SES Sandbox Mode**:
   - Accounts in Sandbox mode cannot send to unverified external recipients.
3. **Explicit Mail Server Binding**:
   - Cloned `mailing.mailing` records now explicitly receive `mail_server_id` matching the active `ir.mail_server`.

## Code Updates
- In `custom_addons/vhealth_email_marketing/models/action_group_schedule.py`:
  - Resolved active `mail_server` and explicitly populated `mailing_vals["mail_server_id"] = mail_server.id`.
  - Used `mail_server.from_filter` as a preferred fallback when `template.email_from` is blank.
- Bumped version in `__manifest__.py` to `20.0.1.0.17`.
