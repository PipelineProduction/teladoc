---
slug: 20261106-mailing-contact-views
status: complete
date: 2026-11-06
---

# Add Mailing Contact Views & Prepare Workflow Validation

## Objective
Make all 69 custom fields visible on the `mailing.contact` form view in Odoo 20 Community Edition without altering baseline fields or breaking existing mass_mailing functionality, and provide sample CSV test data for validating the three import workflows.

## Tasks
1. [x] Analyze Odoo 20 `mass_mailing.mailing_contact_view_form` architecture.
2. [x] Create `custom_addons/vhealth_email_marketing/views/mailing_contact_views.xml` with inherited form and list views organized into 4 structured tabs (Personal Information, AETNA Information, vHealth Status, Products & Other Fields).
3. [x] Register new view and bump version to `20.0.1.0.1` in `__manifest__.py`.
4. [x] Create sample test CSVs for Eligibility, Weekly Registration, and Member Removal in `sample_data/`.
5. [x] Add automated smoke test assertions in `tests/test_smoke.py`.
