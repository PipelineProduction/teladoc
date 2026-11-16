# Quick Task Plan: Fix model_id Not-Null Violation on ir_model_fields for x_product_number

## Problem
During module installation/upgrade on Odoo.sh:
```
psycopg2.errors.NotNullViolation: null value in column "model_id" of relation "ir_model_fields" violates not-null constraint
DETAIL: Failing row contains (..., id, x_product_number, ..., integer, ..., base, ...)
```

## Root Cause
In `ProductNumber.init()`, `self.search_count([])`, `self.search()`, and `self.create()` were being called during table initialization.
In Odoo's registry initialization lifecycle (`init_models`), `model.init()` runs *before* `_reflect_models(model_names)` has registered the models into `ir_model`.
The ORM search and create calls in `init()` triggered internal security checks (`ir.rule`) which queried `self.env['ir.model']._get_id('x_product_number')`.
Because the model wasn't registered in `ir_model` yet, `_get_id` returned `None`, and because of `@api.ormcache('name', cache='stable')`, `None` was cached.
When `_reflect_models` later inserted `x_product_number` using direct SQL (`upsert_en`), the cache was not invalidated.
Then `_reflect_fields` called `_get_id('x_product_number')`, retrieved the cached `None`, and attempted to insert all fields with `model_id = NULL`, triggering the PostgreSQL NOT NULL constraint error.

## Objective
1. Remove `def init(self)` from `ProductNumber`.
2. Move seed records to `data/product_number_data.xml` (`noupdate="1"`).
3. Add a safe `post_init_hook` in `__manifest__.py` and `__init__.py` to ensure product mapping is maintained cleanly after models/fields are fully reflected.
4. Update tests, bump version to `20.0.1.0.7`, and rebuild package.
