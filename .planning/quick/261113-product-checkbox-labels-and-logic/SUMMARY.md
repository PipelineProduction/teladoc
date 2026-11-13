---
slug: 261113-product-checkbox-labels-and-logic
status: complete
date: 2026-11-13
---

# Summary: Fix Product Number Checkbox Labels and Multi-Product Logic

## Root Cause Analysis
In `custom_addons/vhealth_email_marketing/models/product_number.py`, the model `x_product_number` defined `x_name` as the description field without specifying `_rec_name = "x_name"`. Odoo defaulted to `_rec_name = 'name'`, which did not exist on the model, causing the relational checkbox widget `many2many_checkboxes` to fall back to `x_product_number,1`, `x_product_number,2`, etc.

## Key Changes Implemented
1. **Model Display Configuration (`custom_addons/vhealth_email_marketing/models/product_number.py`)**:
   - Added `_rec_name = "x_name"` so Odoo uses `001`, `002`, `004`, `007` as the record title.
   - Added `_compute_display_name` with `@api.depends("x_name", "x_studio_product_value")` for full version compatibility across Odoo 16, 17, 18, 19, and 20.
   - Added idempotent `init()` helper to ensure records have their `x_studio_product_value` populated (`aetna-prod-001`, `aetna-prod-002`, `aetna-prod-004`, `aetna-prod-007`) without duplicating existing database rows.
2. **Multi-Product CSV Import Engine (`custom_addons/vhealth_email_marketing/models/imports.py`)**:
   - Updated `PRODUCT_COHORT` to recognize both short labels (`001`, `002`, `004`, `007`) and full codes (`aetna-prod-001`, etc.).
   - Updated `WeeklyVhealthRegistration.action_process_import` to parse multiple product codes separated by comma or semicolon (e.g. `aetna-prod-001, aetna-prod-004`).
   - Automatically detects compound cohorts (e.g. both `TH` and `MH` mapped to `TH + MH`).
   - Attaches all matching products to `x_studio_products_2` via ORM command `(4, product.id)`.
3. **Smoke Tests (`custom_addons/vhealth_email_marketing/tests/test_smoke.py`)**:
   - Added assertions verifying `_rec_name == "x_name"` and display name evaluation.
4. **Packaging & Versioning**:
   - Bumped version to `20.0.1.0.3` in `__manifest__.py`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
