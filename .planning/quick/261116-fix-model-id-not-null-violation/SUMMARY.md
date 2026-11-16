# Quick Task Summary: Fix model_id Not-Null Violation on ir_model_fields for x_product_number

**Date:** 2026-11-16
**Version:** 20.0.1.0.7
**Commit:** 85512c8

## Root Cause Identified
- `ProductNumber` defined an `init(self)` method that invoked ORM operations (`search_count`, `search`, `create`) during `init_models`.
- In Odoo, `model.init()` runs before `_reflect_models` has inserted model records into `ir_model`.
- The premature ORM calls invoked security rule checks that queried `ir.model._get_id('x_product_number')`.
- Because the model did not exist yet in `ir_model`, `_get_id` returned `None`, and this negative result was cached by `@api.ormcache('name', cache='stable')`.
- Direct SQL insertion by `_reflect_models` did not invalidate this ormcache.
- As a result, when `_reflect_fields` queried `_get_id('x_product_number')`, it received `None` and attempted to insert rows into `ir_model_fields` with `model_id = NULL`, violating PostgreSQL's NOT NULL constraint.

## Key Changes
1. **Removed `def init(self)` from `ProductNumber`** (`models/product_number.py`).
2. **Created `data/product_number_data.xml`**:
   - Seeds products (`001`, `002`, `004`, `007`) with `noupdate="1"` standard data records.
3. **Added `post_init_hook`**:
   - Defined in `__init__.py` and registered in `__manifest__.py`.
   - Executes cleanly after the module is fully installed and models/fields are reflected in the database.
4. **Updated Smoke Test**:
   - `test_product_number_rec_name_and_display` now works idempotently with pre-seeded or dynamically created records.
5. **Rebuilt Package**:
   - Version bumped to `20.0.1.0.7`.
   - Rebuilt `custom_addons/vhealth_email_marketing.zip`.
