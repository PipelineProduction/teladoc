---
slug: 261113-fix-rec-names-and-field-labels
status: complete
date: 2026-11-13
---

# Fix Record Names, Field Labels, and Form Layouts Across Custom Models

## Objective
Fix breadcrumb display titles (replacing `x_eligibility_import,NewId_...` with clean `New` or record name) and replace unlabelled `X Studio ...` field titles with human-friendly labels (`Total Records`, `Processed Records`, `Created Contacts`, `Updated Contacts`, `Import File`, `Import Status`, `Error Message`). Align form views with Odoo Online Studio structure (title block `<h1><field name="x_name" placeholder="Name..."/></h1>`, button `Process Eligibility`, and chatter).

## Tasks
1. [x] Add `_rec_name = "x_name"` and `_compute_display_name` across `EligibilityImport`, `WeeklyVhealthRegistration`, `AetnaMemberRemoval`, `GoogleSheetRegistration`, and `MailingContactLine`.
2. [x] Add explicit `string` labels to all `x_studio_` fields in `imports.py`, `member_removal.py`, and `google_sheet_registration.py`.
3. [x] Update form views in `import_views.xml`, `member_removal_views.xml`, and `product_number_views.xml` to include `oe_title` header block and chatter.
4. [x] Add automated smoke test assertions in `tests/test_smoke.py`.
5. [x] Bump module version to `20.0.1.0.4` in `__manifest__.py` and rebuild `vhealth_email_marketing.zip`.
