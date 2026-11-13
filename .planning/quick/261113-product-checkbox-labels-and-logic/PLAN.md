---
slug: 261113-product-checkbox-labels-and-logic
status: complete
date: 2026-11-13
---

# Fix Product Number Checkbox Labels and Multi-Product Logic

## Objective
Fix the Product Number checkboxes on the mailing contact form view so that the checkbox labels display short codes (`001`, `002`, `004`, `007`) instead of model fallback names (`x_product_number,1`, etc.), while preserving the actual product codes (`aetna-prod-001`, `aetna-prod-002`, `aetna-prod-004`, `aetna-prod-007`). Ensure the import engine handles multiple product selections without breaking existing cohort assignments, bump module version, and refresh the deployment zip.

## Tasks
1. [x] Configure `_rec_name = "x_name"` and `@api.depends` `_compute_display_name` in `custom_addons/vhealth_email_marketing/models/product_number.py`.
2. [x] Add auto-initialization in `ProductNumber.init()` to ensure standard product codes are safely mapped without creating duplicates on existing databases.
3. [x] Support multiple comma- or semicolon-separated product codes in `WeeklyVhealthRegistration.action_process_import` ([imports.py](file:///home/elsner/Documents/pipeline/teladoc/custom_addons/vhealth_email_marketing/models/imports.py)) and map compound cohorts ("TH + MH") when multiple products are attached.
4. [x] Add automated smoke tests in `custom_addons/vhealth_email_marketing/tests/test_smoke.py`.
5. [x] Bump module version to `20.0.1.0.3` in `__manifest__.py` and rebuild `vhealth_email_marketing.zip`.
