---
status: complete
quick_id: 261127-jv2
date: 2026-11-27
commit: 6b0c330
---
# Quick Task Summary: Restore Odoo Visual Editor Editability Across All vHealth Templates

**Date:** 2026-11-27
**Version:** `20.0.1.0.23`
**Status:** complete

## Root Cause
In `20.0.1.0.20`–`20.0.1.0.22`, writing table-only Gmail HTML into `mailing.mailing.body_arch` stripped Odoo's Mass Mailing editor structure (`.o_layout`, `<style id="design-element">`, `.o_mail_wrapper`, `.o_mail_wrapper_td.oe_structure`, and `<section class="o_mail_snippet_general" data-snippet="...">`). Without `.oe_structure` and `<section data-snippet="...">`, Odoo disabled all `+ Blocks` (orange `!` warnings) and prevented visual block editing.

## Changes Made
1. **Added Native Odoo Visual-Editor `body_arch` Templates (`custom_addons/vhealth_email_marketing/data/templates_arch/`)**:
   - Created editable `body_arch` files for all 7 templates (`vhealth_launch_1.html`, `vhealth_launch_2.html`, `vhealth_launch_3.html`, `vhealth_launch_4.html`, `vhealth_family_invited.html`, `vhealth_register_email.html`, `vhealth_non_register_email.html`).
   - Preserved `.o_layout`, `<style id="design-element">`, `.o_mail_wrapper`, `.o_mail_wrapper_td.oe_structure`, and `<section data-snippet="...">` blocks so `+ Blocks`, `Style`, `Design`, inline text editing, and image replacement work natively in Odoo.
   - Replaced all `/web/image/...` URLs with public `/vhealth_email_marketing/static/src/img/email/...` URLs, removed `background: red`, fixed SharpSpring merge tags to QWeb, and added inline padding/colors/widths on cards, buttons, footer, and images.
2. **Dynamic `body_arch` → Gmail `<table>` Conversion & Upgrade Restoration (`models/mailing.py`, `models/action_group_schedule.py`)**:
   - Added `_convert_o_layout_sections_to_gmail_table()` in `models/mailing.py` and wired it into `fix_odoo_email_html_for_gmail()`, so any user-edited Odoo `.o_layout` + `<section>` HTML automatically converts into a centered `600px` Gmail-safe `<table>` layout when rendered/sent (`_render_field` and `_create_and_send_launch_mailing`).
   - Fixed `_get_attr()` / `_set_attr()` boundary regex (`(?<![a-zA-Z0-9_-])`) so `data-resize-width` no longer prevents setting explicit `width="120"` on the app tile image.
   - Updated `_upgrade_fix_vhealth_templates()` and `action_fix_gmail_layout()` to restore editable `body_arch` when `oe_structure` is missing (recovering templates overwritten by `.20`–`.22`) while keeping `body_html` Gmail-safe and preserving future edits once `oe_structure` is present.
3. **Manifest & Tests (`__manifest__.py`, `tests/test_smoke.py`)**:
   - Bumped version to `20.0.1.0.23`.
   - Updated `test_launch_1_template_upgrade_and_render` and `test_all_seven_bundled_templates_and_matching` to verify both `oe_structure` editability in `body_arch` and Gmail `<table>` conversion for `body_html`.
   - Verified Python AST (19 files), XML parsing (18 files), manifest (19 data files), and all 7 `templates_arch` files + dynamic Gmail table conversions (tag balance, 20 images each on disk). (Note: Odoo `TransactionCase` suite not executed in this container due to no Odoo runtime/DB.)
