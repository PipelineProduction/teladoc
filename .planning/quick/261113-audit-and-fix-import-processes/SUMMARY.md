# Quick Task Summary: Audit and Fix Import Processes for Odoo.sh Compatibility

**Date:** 2026-11-13
**Version:** 20.0.1.0.5

## What Was Done
1. **Audited Real Eligibility CSV File**:
   - Analyzed `/home/elsner/Documents/pipeline/ODOO - AETNA Eligible Members Import File (v2 Dec 2025) - New members to launch (4).csv`.
   - Identified that Odoo Studio / Online export files use technical field names (`x_studio_first_name`, `x_studio_last_name`, `x_studio_aetna_language`, `x_studio_aetna_access_code`, `x_studio_member_effective_date`, `x_studio_cohort_group`, `x_studio_launch_date`, `Name`, `isunsub`).
   - The previous codebase was looking only for human-friendly names (e.g. `First Name`, `Cohort Group`), which would have resulted in blank fields.

2. **Updated Import Logic (`models/imports.py`)**:
   - Expanded column resolution (`_get` helper) to seamlessly support technical Studio headers, human labels, and lower-case alternatives.
   - Added `_get_or_create_list` helper so missing mailing lists (e.g. `All Live Contacts [SEND TO ALL]`, `All REGISTERED members`, cohort lists) are created automatically on a fresh Odoo.sh database without failing silently.
   - Implemented `isunsub` handling: if `isunsub` is true/1/yes, the contact's subscription to the target mailing lists is automatically flagged with `opt_out = True`.
   - Set `x_studio_aetna_member_status = 'Eligible'` upon eligibility import.
   - Updated `WeeklyVhealthRegistration` to also accept technical studio headers (`x_studio_vhealth_contact`, `x_studio_app_registered`, `x_studio_registration_date`, `x_studio_aetna_id`, etc.) and ensure contacts are enrolled in `All REGISTERED members`.

3. **Updated Member Removal Wizard (`wizard/member_removal.py`)**:
   - Added support for `x_studio_aetna_member_status` in addition to `aetna member status`, `status`, and `member status`.

4. **Updated Smoke Tests (`tests/test_smoke.py`)**:
   - Added unit test `test_eligibility_import_flexible_helpers` validating resolution of technical field headers.

5. **Packaged and Versioned**:
   - Manifest bumped to `20.0.1.0.5`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
