# Quick Task Plan 261126-kmn: Fix Email Template Gmail Layout & Image Rendering

## Problem
1. **Broken Layout in Gmail**: `/home/elsner/Downloads/vHealth - Launch #1 (2025).html` contains raw Odoo `body_arch` designer HTML (`o_layout`, `o_mail_wrapper`, `<style id="design-element">` with CSS custom properties `var(--...)` and `:has()`, Bootstrap grid/utility classes like `container`, `row`, `col-md-*`, `btn-primary`, `rounded-circle`, `bg-o-color-5`, `text-o-color-3`, `pt32`, `pb32`, `img-fluid`, plus debug `style="background: red;"`). Gmail strips `<style>` rules with CSS variables/`:has()` and ignores Bootstrap/Odoo theme classes, causing full-width blowout, invisible white footer text on white background, unstyled links instead of buttons, and un-constrained 2000×2000 / 1200×575 / 660×423 native images breaking columns.
2. **Broken Images in Gmail**: All 20 `<img>` tags reference `/web/image/<id>-<hash>/...?access_token=...`, which fail in Gmail when attachment IDs/tokens do not exist across databases, `public=False`, or `web.base.url` is not resolved to accessible public assets.

## Tasks
1. **Bundle Email Static Assets**: Copy all 20 Launch #1 images (plus Launch #2-#4 header banners) into `custom_addons/vhealth_email_marketing/static/src/img/email/` with clean URL-safe filenames.
2. **Create Gmail-Safe Launch #1 Template**: Write `custom_addons/vhealth_email_marketing/data/templates/vhealth_launch_1.html` using 100% table-based layout (`600px` centered container on `#F7F7F7`), full inline CSS, explicit image dimensions, bulletproof `#7C3F96` pill button, `#363C44` legal footer, and safe QWeb bilingual fallbacks (`Spanish` vs `English` default).
3. **Harden Odoo Mailing & Action Group Pipeline**:
   - Update `custom_addons/vhealth_email_marketing/models/mailing.py` with `_vhealth_rewrite_image_urls`, `_vhealth_fix_gmail_html`, `_render_field` Gmail post-processing, `action_fix_gmail_layout`, and `_upgrade_fix_vhealth_templates`.
   - Update `custom_addons/vhealth_email_marketing/models/action_group_schedule.py` to normalize template HTML when cloning into campaign mailings and warn if `web.base.url` is localhost.
   - Add Server Action (`views/mailing_views.xml`) and upgrade hook (`data/template_fix_data.xml`), bump `__manifest__.py` to `20.0.1.0.20`.
4. **Tests & Verification**: Add unit tests in `tests/test_smoke.py` (including standalone-executable pure-Python HTML sanitizer tests) and validate Python AST, XML, manifest paths, and HTML rendering.
