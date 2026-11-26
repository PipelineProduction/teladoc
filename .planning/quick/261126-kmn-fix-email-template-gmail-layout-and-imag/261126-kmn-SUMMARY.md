---
status: complete
quick_id: 261126-kmn
date: 2026-11-26
commit: c6f10ba
---
# Quick Task Summary: Fix Email Template Gmail Layout & Image Rendering for vHealth Launch #1

**Date:** 2026-11-26
**Version:** `20.0.1.0.20`
**Status:** complete

## Root Causes Identified
1. **Un-inlined Odoo Designer Markup in Gmail**:
   - `/home/elsner/Downloads/vHealth - Launch #1 (2025).html` contained raw `o_layout` / `o_mail_wrapper` markup with `<style id="design-element">` CSS custom properties (`var(--...)`), `:has()` selectors, Bootstrap utility/grid classes (`container`, `row`, `col-*`, `btn-primary`, `rounded-circle`, `bg-o-color-5`, `text-o-color-3`, `pt32`, `pb32`, `img-fluid`), and a leftover `style="background: red;"`.
   - Gmail strips CSS variable/`:has()` style blocks and ignores Bootstrap/Odoo theme classes, causing full-width stretching, unstyled links instead of buttons, invisible white disclaimer text (`bg-o-color-5` lost), and native-size images (including the `2000x2000` app tile and `1200x575` hero banner) blowing out columns.
2. **Broken `/web/image/...` URLs in Gmail**:
   - All 20 `<img>` tags referenced database-specific `/web/image/<id>-<hash>/<filename>?access_token=...` paths, which fail in Gmail when attachment IDs/tokens differ across databases, `public=False`, or `web.base.url` is unreachable.

## Changes Made
1. **Public Static Email Image Assets (`custom_addons/vhealth_email_marketing/static/src/img/email/`)**:
   - Bundled all 20 Launch #1 images (plus Launch #2–#4 header banners) with clean URL-safe filenames so they are served publicly without database attachment IDs or `access_token`s.
2. **Gmail-Safe Table-Based Launch #1 Template (`custom_addons/vhealth_email_marketing/data/templates/vhealth_launch_1.html`)**:
   - Rebuilt `vHealth - Launch #1 (2025)` using nested `600px` presentation tables on `#F7F7F7`, full inline CSS, explicit `width` + `max-width` image sizing (`120px` app tile, `200px` logos, `600px` hero), bulletproof `#7C3F96` pill CTA button, `#363C44` legal disclaimer footer, `#F2F2F2` 2-column instructions, and case-insensitive bilingual QWeb (`Spanish` vs `English` default fallback) with `x_studio_family_invite_form_url` support.
3. **Mailing Hardening & Automatic Upgrade (`models/mailing.py`, `models/action_group_schedule.py`, `views/mailing_views.xml`, `data/template_fix_data.xml`)**:
   - Added `rewrite_vhealth_image_urls()` and `fix_odoo_email_html_for_gmail()` in `models/mailing.py`, hooked into `mailing.mailing._render_field()` and `action_group_schedule._create_and_send_launch_mailing()`.
   - Added `action_fix_gmail_layout()` + Server Action **Fix Gmail Layout & Images** on `mailing.mailing`, plus `_upgrade_fix_vhealth_templates()` in `data/template_fix_data.xml`.
   - Added warning log if `web.base.url` points to `localhost`/`127.0.0.1` (since Gmail's image proxy cannot fetch localhost URLs).
   - Bumped module version in `__manifest__.py` to `20.0.1.0.20`.
4. **Tests & Verification (`tests/test_smoke.py`)**:
   - Added `test_gmail_html_hardening_and_image_rewrite` and `test_launch_1_template_upgrade_and_render`.
   - Verified Python AST (18 files), XML parsing (17 files), manifest data files (18 entries), `vhealth_launch_1.html` (20/20 images on disk + QWeb XML parse), and `fix_odoo_email_html_for_gmail` directly against `/home/elsner/Downloads/vHealth - Launch #1 (2025).html`. (Note: no Odoo runtime/database is present in this workspace container to run Odoo `TransactionCase` tests directly.)
