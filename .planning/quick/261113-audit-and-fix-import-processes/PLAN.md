# Quick Task Plan: Audit and Fix Import Processes for Odoo.sh Compatibility

Audit and verify the 3 core operations against real Odoo Online / Studio data:
1. Eligibility CSV Import (`ODOO - AETNA Eligible Members Import File (v2 Dec 2025) - New members to launch (4).csv`)
2. AETNA Member Removal (`aetna.member.removal`)
3. Weekly vHealth Registrations (`weekly.vhealth.registration`)

## Key Objectives
- Support technical field headers (e.g. `x_studio_first_name`, `x_studio_last_name`, `x_studio_aetna_language`, `Name`, `isunsub`) as well as human labels in CSV imports.
- Ensure automated creation of required mailing lists (`All Live Contacts [SEND TO ALL]`, `All REGISTERED members`, cohort lists like `All Contacts - TH`) if they do not exist on a fresh Odoo.sh instance.
- Properly respect the `isunsub` flag during eligibility import to set `opt_out = True` on mailing list subscriptions.
- Align member removal wizard to recognize Studio status column headers (`x_studio_aetna_member_status`).
- Update smoke tests and package zip for Odoo.sh deployment.
