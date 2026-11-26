---
status: complete
quick_id: 261126-mg3
date: 2026-11-26
commit: 969c6cd
---
# Quick Task Summary: Fix Gmail Layout & Images for All Remaining vHealth Email Templates

**Date:** 2026-11-26
**Version:** `20.0.1.0.21`
**Status:** complete

## Issues Found in the 6 Templates
1. **Unbundled `/web/image/...` Hero Banners**:
   - `vHealth Worldwide - Family Invited`, `VHealth Register Email`, and `VHealth Non-Register Email` still referenced DB-specific `/web/image/...` URLs for their 6 bilingual hero banners (`1200x575`).
2. **Unconverted SharpSpring Merge Tags**:
   - `vHealth - Launch #2 (2025)` contained `href="{$family_invite_form_url_5d11dd4d2ed3f!&quot;https://vhealth.app.link/gotostore&quot;}"`.
   - `vHealth Worldwide - Family Invited` contained `{$firstName}, {$primary_member_email__1__5c2cc0c228ec8!"Your family member"}` / `"A family member"`.
3. **Un-tabled Odoo `<section>` / CSS Variable Markup & Missing Cohort Fallbacks**:
   - All 6 exported templates used `<section>`, `.container`, `.row`, `.col-md-12`, and CSS variables (`--box-border-*` on Launch #3/#4 cards without inner padding).
   - `VHealth Register Email` and `VHealth Non-Register Email` lacked Spanish/English fallbacks when `x_studio_cohort_group` did not match `TH`, `TH + MH`, `MH`, or `PC`.

## Changes Made
1. **Added 6 Hero Banner Assets (`custom_addons/vhealth_email_marketing/static/src/img/email/`)**:
   - Bundled `vHealth-worldwide_2026-09_Reg_es.jpg`, `vHealth-worldwide_2026-09_reg_en.jpg`, `vhealth-worldwide_family-invite-2025-es.jpg`, `vhealth-worldwide_family-invite-2025-en.jpg`, `vHealth-worldwide_2026-09_nonreg_es.jpg`, and `vHealth-worldwide_2026-09_nonreg_en.jpg` (31 total static email images).
2. **Created 6 Gmail-Safe Table-Based Templates (`custom_addons/vhealth_email_marketing/data/templates/`)**:
   - `vhealth_launch_2.html`
   - `vhealth_launch_3.html`
   - `vhealth_launch_4.html`
   - `vhealth_family_invited.html`
   - `vhealth_register_email.html`
   - `vhealth_non_register_email.html`
   - Each uses `600px` centered presentation tables on `#F7F7F7`, full inline CSS, explicit image sizing, `#363C44` footer, `#7C3F96` pill CTA button, `padding: 20px` on Launch #3/#4 feature/tip cards, QWeb replacements for SharpSpring tags (`x_studio_first_name`, `x_studio_dependent_first_name`, `x_studio_primary_member_first_name`, `x_studio_family_invite_form_url`), and full cohort (`TH`, `TH + MH`, `MH`, `PC`) + language fallbacks.
3. **Generalized Module Upgrade, Action & Runtime Support (`models/mailing.py`, `models/action_group_schedule.py`, `__manifest__.py`)**:
   - Added `load_bundled_template()` and `match_bundled_template_key()` supporting all 7 templates, plus `_clean_sharpspring_tags()` in `fix_odoo_email_html_for_gmail()`.
   - Updated `_upgrade_fix_vhealth_templates()`, `action_fix_gmail_layout()`, and `_create_and_send_launch_mailing()` to upgrade/normalize any of the 7 templates when broken designer/SharpSpring markers are present, while preserving future user edits once upgraded.
   - Bumped module version to `20.0.1.0.21`.
4. **Tests & Verification (`tests/test_smoke.py`)**:
   - Added `test_all_seven_bundled_templates_and_matching`.
   - Verified Python AST (18 files), XML parsing (17 files), manifest (18 data files), all 7 bundled HTML templates (20 images each + QWeb XML parse), and `match_bundled_template_key` + `fix_odoo_email_html_for_gmail` against all 7 exported Downloads HTML files. (Note: Odoo `TransactionCase` suite not executed in this container due to no Odoo runtime/DB.)
