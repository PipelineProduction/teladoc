---
slug: 261113-fix-odoo-custom-fields
status: complete
date: 2026-11-13
---

# Align Mailing Contact View with Odoo Online Studio Layout

## Objective
Update `custom_addons/vhealth_email_marketing/views/mailing_contact_views.xml` to match the exact Odoo Online Studio layout provided by the user. Remove artificial 4-tab groupings and studio testing artifacts (`x_studio_products`, `x_studio_char_field_4r7_1k0uuh7ae`, `x_studio_html_field_5gi_1k0a9279h`, etc.) that were displaying unconfigured/dummy labels like "New Many2Many", "New Text", "New HTML", and "New CheckBox". Bump module version and refresh the installable zip package.

## Tasks
1. [x] Update `mailing_contact_view_form_inherit_vhealth` in `custom_addons/vhealth_email_marketing/views/mailing_contact_views.xml` to use the exact Odoo Online Studio XML (single `Email marketing` page with 5 structured groups: top header fields, Member data, Aetna, Aetna Dependent, and Uncategorized).
2. [x] Bump module version to `20.0.1.0.2` in `custom_addons/vhealth_email_marketing/__manifest__.py`.
3. [x] Verify view XML validity with Python XML parser and update smoke tests in `tests/test_smoke.py`.
4. [x] Refresh `custom_addons/vhealth_email_marketing.zip` package for deployment.
5. [x] Create summary and commit code changes.
