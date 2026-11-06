---
slug: 20261106-mailing-contact-views
status: complete
date: 2026-11-06
---

# Summary: Add Mailing Contact Views & Prepare Workflow Validation

## Changes Implemented
1. **Inherited Views (`views/mailing_contact_views.xml`)**:
   - `mailing_contact_view_tree_inherit_vhealth`: Adds `vHealth Contact`, `AETNA Member Status`, and `Cohort Group` as optional columns in the list view.
   - `mailing_contact_view_form_inherit_vhealth`:
     - Adds `x_studio_aetna_member_status` next to `tag_ids` and `x_studio_vhealth_contact` next to `create_date` in the main header.
     - Adds 4 clean tabs into `<notebook>`:
       1. **Personal Information**: 12 demographic and identity fields.
       2. **AETNA Information**: 13 AETNA access codes, IDs, cohort, and client metadata fields.
       3. **vHealth Status**: 14 registration, live status, and engagement fields.
       4. **Products & Other Fields**: 30 products, dependents, SMS, consultations, and auxiliary fields.
2. **Manifest Updated (`__manifest__.py`)**:
   - Added `views/mailing_contact_views.xml` to `data`.
   - Bumped version to `20.0.1.0.1`.
3. **Sample Test CSV Files (`sample_data/`)**:
   - `1_eligibility_sample.csv`: 2 test records for TH and TH + MH cohorts.
   - `2_weekly_registration_sample.csv`: 2 test records matching `aetna-prod-002` and `aetna-prod-001`.
   - `3_member_removal_sample.csv`: 1 test record with status `Remove` for safe permanent deletion verification.
4. **Smoke Tests Updated (`tests/test_smoke.py`)**:
   - Verifies models, fields, and view registrations.
