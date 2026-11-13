---
slug: 261113-fix-rec-names-and-field-labels
status: complete
date: 2026-11-13
---

# Summary: Fix Record Names, Field Labels, and Form Layouts Across Custom Models

## Root Cause Analysis
1. Custom Studio models (`x_eligibility_import`, `x_weekly_vhealth_regis`, `x_aetna_member_removal`, `x_google_sheet_registr`, etc.) use `x_name` as their title field instead of standard Odoo `name`. Because `_rec_name = "x_name"` was omitted, Odoo defaulted to `f"{model_name},{id}"` for breadcrumbs (e.g. `x_eligibility_import,NewId_0x7fb04e3626c0` on new records).
2. Several model fields lacked explicit `string="..."` arguments, which caused Odoo to auto-capitalize the Python attribute names, generating `X Studio Total Records`, `X Studio Processed Records`, etc.

## Key Changes Implemented
1. **Model Titles & Display Names**:
   - Added `_rec_name = "x_name"` and `@api.depends("x_name") def _compute_display_name` across `EligibilityImport`, `WeeklyVhealthRegistration`, `AetnaMemberRemoval`, `GoogleSheetRegistration`, and `MailingContactLine`.
   - Displays clean `New` on unsaved new records and the record's title on saved records.
2. **Field Labels Cleaned**:
   - Explicitly defined `string` attributes on all fields: `Total Records`, `Processed Records`, `Created Contacts`, `Updated Contacts`, `Error Records`, `Import File`, `Import Status`, `Error Message`.
3. **Form View Architecture (`import_views.xml`, `member_removal_views.xml`, `product_number_views.xml`)**:
   - Added `<div class="oe_title"><h1><field name="x_name" placeholder="Name..."/></h1></div>` for prominent name entry matching Odoo Online Studio.
   - Updated primary action button to `Process Eligibility`.
   - Added `<chatter/>` for communication and activity logs.
4. **Smoke Tests & Verification**:
   - Added unit test assertions in `tests/test_smoke.py` validating `_rec_name` and display name for `x_eligibility_import`.
5. **Release & Packaging**:
   - Bumped version to `20.0.1.0.4` in `__manifest__.py`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
