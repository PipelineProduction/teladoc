---
slug: 261113-fix-odoo-custom-fields
status: complete
date: 2026-11-13
---

# Summary: Align Mailing Contact View with Odoo Online Studio Layout

## Root Cause Analysis
In the previous implementation, all 69 fields from `STUDIO_FIELD_INVENTORY.txt` were placed into an artificial 4-tab form view layout. This caused unused Studio experiment/testing artifacts (`x_studio_products`, `x_studio_products_1`, `x_studio_many2many_field_3jv_1k0a84nt2`, `x_studio_company`, `x_studio_char_field_4r7_1k0uuh7ae`, `x_studio_html_field_5gi_1k0a9279h`, `x_studio_selection_field_4vn_1k0a88ot7`, etc.) to appear under "PRODUCTS" and "COMPANY & CUSTOM FIELDS" with unconfigured labels such as "New Many2Many", "New Text", "New HTML", and "New CheckBox" (as shown in https://prnt.sc/Dy25htL8MVDL).

## Key Changes
1. **Mailing Contact Form View (`custom_addons/vhealth_email_marketing/views/mailing_contact_views.xml`)**:
   - Replaced artificial 4-tab notebook layout with the exact Odoo Online Studio view structure provided by the user.
   - Header fields:
     - `x_studio_aetna_member_status` positioned after `tag_ids`.
     - `x_studio_vhealth_contact` positioned after `create_date`.
   - Single notebook page: `<page string="Email marketing" name="studio_page_78d_1k07lgra7">`:
     - Top group (`studio_group_78d`): First Name, Last Name, Cohort Group, Aetna Language.
     - `Member data` group (`studio_group_tj_1k0a6p200`): Access Code, Member Effective Date (`force_save="1"` `readonly="True"`), Products 2 (`widget="many2many_checkboxes"`), Sub-Client, Aetna ID, Launch Date, Member ID, Registration Date, Sub group.
     - `Aetna` group (`studio_group_3qs_1k0a9pu3r`): 1st email non-email, status live, app unique registered, client, children, DOB, gender, talent trust, nationality, launch SMS, SMS launch no, status, vHealth90, consultation, consultation video, email template (`widget="radio"`), app registered, registered with vHealth, created date import, family status, invalid phone number, member type, not registered anymore, sms stop opted-out, sms status report, marital status, consultation call back.
     - `Aetna Dependent` group (`studio_group_3hd_1k0adl6v9`): Dependent email, dependent mobile number, family member explicit consent 1 (`widget="radio"`), dependent first name, family invite form URL, is dependent from invite form, primary member first name.
     - `Uncategorized` group (`studio_group_1tp_1k0cl6teg`): Check for engagement, registered manual action, location US or Canada.
   - Removed all obsolete dummy/test studio fields from the view arch.
2. **Manifest Version Bump (`custom_addons/vhealth_email_marketing/__manifest__.py`)**:
   - Bumped version to `20.0.1.0.2` to ensure clean module upgrades in Odoo.
3. **Smoke Tests (`custom_addons/vhealth_email_marketing/tests/test_smoke.py`)**:
   - Added assertions to verify `studio_page_78d_1k07lgra7` is present and dummy artifact fields are absent from the view arch.
4. **Rebuilt Deployment Zip (`custom_addons/vhealth_email_marketing.zip`)**:
   - Repackaged `vhealth_email_marketing.zip` containing the updated files ready for direct installation/upgrade in Odoo.
