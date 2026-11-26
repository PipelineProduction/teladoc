---
status: complete
quick_id: 261126-nz1
date: 2026-11-26
commit: d76209d
---
# Quick Task Summary: Add Rebuild Mailing Lists Action Under Configuration Menu

**Date:** 2026-11-26
**Version:** `20.0.1.0.22`
**Status:** complete

## What Was Done
1. **Rebuild Mailing Lists Wizard (`wizard/rebuild_mailing_lists_wizard.py`, `views/rebuild_mailing_lists_wizard_views.xml`, `views/menus.xml`)**:
   - Added **vHealth Process > Configuration > Rebuild Mailing Lists** menu item opening `vhealth.rebuild.mailing.lists.wizard`.
   - Added default rule checkbox **`vHealth Contact == True (Default Rule)`** (`require_vhealth_contact`, enabled by default) applied to all rebuilt lists.
   - Pre-populates editable `Many2one("mailing.list")` selectors (auto-matched case-insensitively or auto-created on rebuild if missing) and displays a live rule preview comparing current vs matching contact counts.
   - Evaluates all `mailing.contact` records against the exact rules:
     - `All Live Contacts [SEND TO ALL]`: `x_studio_vhealth_contact == True`
     - `All REGISTERED members`: `x_studio_vhealth_contact == True` AND `((x_studio_app_unique_registered == 'Yes' AND x_studio_location_us_or_canada == True) OR (x_studio_app_registered == 'Yes' AND x_studio_location_us_or_canada == True))`
     - `All Contacts - TH`: `x_studio_vhealth_contact == True` AND `x_studio_cohort_group == 'TH'`
     - `All Contacts - TH + MH`: `x_studio_vhealth_contact == True` AND `x_studio_cohort_group == 'TH + MH'`
     - `All Contacts - PC`: `x_studio_vhealth_contact == True` AND `x_studio_cohort_group == 'PC'`
     - `All Contacts - MH`: `x_studio_vhealth_contact == True` AND `x_studio_cohort_group == 'MH'`
   - Performs differential sync (`(4, id)` / `(3, id)` on `contact_ids`) so existing `opt_out` flags and unrelated list memberships are preserved.
2. **Case-Insensitive Mailing List Lookup (`models/imports.py`, `models/action_group_schedule.py`)**:
   - Updated `_get_or_create_list` in `imports.py` (and reused it in `action_group_schedule.py`) to trim whitespace and fall back to `("name", "=ilike", clean_name)` before creating a new list, preventing duplicate lists when casing differs.
3. **Security, Manifest & Tests (`security/ir.access.csv`, `__manifest__.py`, `tests/test_smoke.py`)**:
   - Added ACL entries for `vhealth.rebuild.mailing.lists.wizard` (32 total rules).
   - Bumped module version to `20.0.1.0.22`.
   - Added `test_rebuild_mailing_lists_wizard_and_rules` in `tests/test_smoke.py`.
   - Verified Python AST (19 files), XML parsing (18 files), manifest data files (19 entries), and `ir.access.csv` schema (32 rules). (Note: Odoo `TransactionCase` suite not executed in this container due to no Odoo runtime/DB.)
