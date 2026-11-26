import logging
import os
import re
import urllib.parse

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)

VHEALTH_STATIC_IMG_BASE = "/vhealth_email_marketing/static/src/img/email"

# Maps lowercased original / URL-decoded attachment filenames to clean static asset filenames
VHEALTH_IMAGE_FILENAME_MAP = {
    "aetna_logo_24 (2).png": "Aetna_logo_24.png",
    "aetna_logo_24 (1).png": "Aetna_logo_24.png",
    "aetna_logo_24.png": "Aetna_logo_24.png",
    "vhealth-email-head_launch-01_es-v3.jpg": "vhealth-email-head_launch-01_es-v3.jpg",
    "vhealth-email-head_launch-01_en-v3.jpg": "vhealth-email-head_launch-01_en-v3.jpg",
    "vhealth-email-head_launch-02_en-v3.jpg": "vhealth-email-head_launch-02_en-v3.jpg",
    "vhealth-email-head_launch-02_es-v3.jpg": "vhealth-email-head_launch-02_es-v3.jpg",
    "vhealth-email-head_launch-03_en-v3.jpg": "vhealth-email-head_launch-03_en-v3.jpg",
    "vhealth-email-head_launch-04_en-v3.jpg": "vhealth-email-head_launch-04_en-v3.jpg",
    "vhealth-email-head_launch-04_es-v3.jpg": "vhealth-email-head_launch-04_es-v3.jpg",
    "instructions-1_es-v3.png": "instructions-1_es-v3.png",
    "instructions-2_es (1).png": "instructions-2_es.png",
    "instructions-2_es.png": "instructions-2_es.png",
    "instructions-1_en.png": "instructions-1_en.png",
    "instructions-2_en (1).png": "instructions-2_en.png",
    "instructions-2_en.png": "instructions-2_en.png",
    "vhealth-video_email_v2 (1).gif": "vhealth-video_email_v2.gif",
    "vhealth-video_email_v2.gif": "vhealth-video_email_v2.gif",
    "vhealth_register-book-now_es.png": "vhealth_register-book-now_es.png",
    "vhealth_watch-video_es.png": "vhealth_watch-video_es.png",
    "vhealth_register-book-now_en.png": "vhealth_register-book-now_en.png",
    "vhealth_watch-video_en.png": "vhealth_watch-video_en.png",
    "download-app-store-badge-es-2.png": "download-app-store-badge-es-2.png",
    "google-play-badge-es.png": "google-play-badge-es.png",
    "vhealth-access-via-website-es.png": "vhealth-access-via-website-es.png",
    "download-app-store-badge-en-2.png": "download-app-store-badge-en-2.png",
    "google-play-badge-en.png": "google-play-badge-en.png",
    "vhealth-access-via-website-v2.png": "vhealth-access-via-website-v2.png",
    "20-vh_0395-new-app-tile-1024x1024.png": "20-vH_0395-New-App-Tile-1024x1024.png",
    "20-vh_0395-new-app-tile-1024x1024 (1).png": "20-vH_0395-New-App-Tile-1024x1024.png",
    "teladochealth_logo_plum_aqua_rgb (1).png": "teladochealth_logo_plum_aqua_rgb.png",
    "teladochealth_logo_plum_aqua_rgb (2).png": "teladochealth_logo_plum_aqua_rgb.png",
    "teladochealth_logo_plum_aqua_rgb.png": "teladochealth_logo_plum_aqua_rgb.png",
}

# Target display widths for bundled images so Gmail never renders 2000px/1200px/660px assets at native size
_IMAGE_WIDTH_RULES = [
    ("20-vh_0395-new-app-tile", ("120", "width: 120px; max-width: 120px; height: auto; display: block; margin: 0 auto; border: 0;")),
    ("aetna_logo_24", ("200", "width: 200px; max-width: 100%; height: auto; display: block; border: 0;")),
    ("teladochealth_logo_plum_aqua_rgb", ("200", "width: 200px; max-width: 100%; height: auto; display: block; margin: 0 auto; border: 0;")),
    ("vhealth-email-head_", ("600", "width: 100%; max-width: 600px; height: auto; display: block; margin: 0 auto; border: 0;")),
    ("instructions-", ("274", "width: 100%; max-width: 274px; height: auto; display: block; border: 0;")),
    ("vhealth-video_email", ("260", "width: 100%; max-width: 260px; height: auto; display: block; border: 0;")),
    ("vhealth_register-book-now", ("250", "width: 100%; max-width: 250px; height: auto; display: block; border: 0;")),
    ("vhealth_watch-video", ("220", "width: 88%; max-width: 220px; height: auto; display: block; border: 0;")),
    ("download-app-store-badge", ("165", "width: 100%; max-width: 165px; height: auto; display: inline-block; border: 0;")),
    ("google-play-badge", ("165", "width: 100%; max-width: 165px; height: auto; display: inline-block; border: 0;")),
    ("vhealth-access-via-website", ("165", "width: 100%; max-width: 165px; height: auto; display: inline-block; border: 0;")),
]

_WEB_IMAGE_URL_RE = re.compile(
    r"""(?P<attr>\b(?:src|data-original-src)\s*=\s*)(?P<quote>["'])(?P<origin>https?://[^"'/]+)?(?P<path>/web/image/[^"']+)(?P=quote)""",
    re.IGNORECASE,
)

_DESIGN_ELEMENT_STYLE_RE = re.compile(
    r"""<style\b[^>]*\bid\s*=\s*["']design-element["'][^>]*>.*?</style>""",
    re.IGNORECASE | re.DOTALL,
)

_SHARPSPRING_INVITE_RE = re.compile(
    r"""%7B%24family_invite_form_url_[^"']*https://info\.vhealth-teladochealth\.com/invite[^"']*""",
    re.IGNORECASE,
)


def rewrite_vhealth_image_urls(html):
    """Rewrite Odoo /web/image/... URLs matching bundled vHealth assets to public static URLs."""
    if not html or "/web/image/" not in html:
        return html

    def _replace(match):
        origin = match.group("origin") or ""
        path = match.group("path")
        raw_path = path.split("?", 1)[0].split("#", 1)[0]
        filename = urllib.parse.unquote(os.path.basename(raw_path)).strip().lower()
        clean_name = VHEALTH_IMAGE_FILENAME_MAP.get(filename)
        if not clean_name:
            return match.group(0)
        new_url = f"{origin}{VHEALTH_STATIC_IMG_BASE}/{clean_name}"
        return f"{match.group('attr')}{match.group('quote')}{new_url}{match.group('quote')}"

    return _WEB_IMAGE_URL_RE.sub(_replace, html)


def _merge_inline_style(existing_style, additions):
    """Merge CSS declarations into an inline style string without duplicating properties."""
    props = {}
    order = []
    for chunk in (existing_style or "").split(";"):
        if ":" not in chunk:
            continue
        k, v = chunk.split(":", 1)
        key = k.strip().lower()
        val = v.strip()
        if not key or not val:
            continue
        if key not in props:
            order.append(key)
        props[key] = val

    for chunk in (additions or "").split(";"):
        if ":" not in chunk:
            continue
        k, v = chunk.split(":", 1)
        key = k.strip().lower()
        val = v.strip()
        if not key or not val:
            continue
        if key not in props:
            order.append(key)
        props[key] = val

    return "; ".join(f"{k}: {props[k]}" for k in order) + (";" if order else "")


def _get_attr(tag_text, attr_name):
    m = re.search(rf"""\b{attr_name}\s*=\s*(?:"([^"]*)"|'([^']*)')""", tag_text, re.IGNORECASE)
    if not m:
        return None
    return m.group(1) if m.group(1) is not None else m.group(2)


def _set_attr(tag_text, attr_name, attr_value):
    pattern = re.compile(rf"""\b{attr_name}\s*=\s*(?:"[^"]*"|'[^']*')""", re.IGNORECASE)
    escaped = attr_value.replace('"', "&quot;")
    if pattern.search(tag_text):
        return pattern.sub(f'{attr_name}="{escaped}"', tag_text, count=1)
    if tag_text.endswith("/>"):
        return tag_text[:-2] + f' {attr_name}="{escaped}"/>'
    return tag_text[:-1] + f' {attr_name}="{escaped}">'


def _apply_class_and_img_inline_styles(html):
    """Inline critical Odoo/Bootstrap classes and image sizing so Gmail renders consistently."""
    class_style_rules = {
        "o_layout": "background-color: #F7F7F7; margin: 0; padding: 16px 8px;",
        "o_mail_wrapper": "max-width: 600px; width: 100%; margin: 0 auto; background-color: #FFFFFF; font-family: Arial, Helvetica, sans-serif;",
        "o_mail_wrapper_td": "background-color: #FFFFFF; font-family: Arial, Helvetica, sans-serif;",
        "bg-o-color-5": "background-color: #363C44; color: #FFFFFF;",
        "text-o-color-3": "color: #FFFFFF;",
        "text-o-color-4": "color: #FFFFFF;",
        "border": "border: 1px solid #DEE2E6;",
        "pt40": "padding-top: 40px;",
        "pb40": "padding-bottom: 40px;",
        "pt32": "padding-top: 32px;",
        "pb32": "padding-bottom: 32px;",
        "pt16": "padding-top: 16px;",
        "pb16": "padding-bottom: 16px;",
        "pb24": "padding-bottom: 24px;",
        "pb4": "padding-bottom: 4px;",
        "py-4": "padding-top: 16px; padding-bottom: 16px;",
        "pt0": "padding-top: 0;",
        "pb0": "padding-bottom: 0;",
    }

    def _process_tag(match):
        tag = match.group(0)
        tag_name_m = re.match(r"<\s*([a-zA-Z0-9_-]+)", tag)
        if not tag_name_m:
            return tag
        tag_name = tag_name_m.group(1).lower()
        if tag_name in ("t", "style", "script"):
            return tag

        classes_raw = _get_attr(tag, "class") or ""
        classes = classes_raw.split()
        style = _get_attr(tag, "style") or ""
        # Strip debug red background
        style = re.sub(r"\bbackground(?:-color)?\s*:\s*red\s*;?", "", style, flags=re.IGNORECASE).strip()

        additions = []
        for cls in classes:
            if cls in class_style_rules:
                additions.append(class_style_rules[cls])

        if tag_name == "a" and "btn" in classes and "btn-primary" in classes:
            additions.append(
                "display: inline-block; background-color: #7C3F96; color: #FFFFFF; "
                "border: 1px solid #7C3F96; border-radius: 50px; padding: 12px 28px; "
                "font-family: Arial, Helvetica, sans-serif; font-size: 18px; font-weight: bold; "
                "text-decoration: none; line-height: 1.4;"
            )

        if tag_name == "hr":
            additions.append("border: 0; border-top: 1px solid #212529; width: 100%; margin: 16px 0;")

        if tag_name == "img":
            src = (_get_attr(tag, "src") or "").lower()
            matched_width = None
            for prefix, (w_attr, w_style) in _IMAGE_WIDTH_RULES:
                if prefix in src:
                    matched_width = (w_attr, w_style)
                    break
            if matched_width:
                w_attr, w_style = matched_width
                if not _get_attr(tag, "width"):
                    tag = _set_attr(tag, "width", w_attr)
                additions.append(w_style)
            else:
                additions.append("max-width: 100%; height: auto; border: 0;")

        if additions:
            merged = _merge_inline_style(style, " ".join(additions))
            tag = _set_attr(tag, "style", merged)
        elif style != (_get_attr(tag, "style") or ""):
            tag = _set_attr(tag, "style", style)

        return tag

    # Process start/self-closing HTML tags, avoiding </closing> tags and comments
    html = re.sub(r"<(?!/|!)[a-zA-Z][^>]*>", _process_tag, html)
    return html


def _propagate_colgroup_widths(html):
    """Copy <colgroup><col style='width: X%'></colgroup> widths onto <td> cells for Gmail."""
    table_re = re.compile(r"(<table\b[^>]*>.*?</table>)", re.IGNORECASE | re.DOTALL)

    def _fix_table(match):
        tbl = match.group(1)
        cg_m = re.search(r"<colgroup\b[^>]*>(.*?)</colgroup>", tbl, re.IGNORECASE | re.DOTALL)
        if not cg_m:
            return tbl
        col_widths = re.findall(r"""width\s*:\s*([0-9.]+%)""", cg_m.group(1), re.IGNORECASE)
        if not col_widths:
            return tbl

        tr_re = re.compile(r"(<tr\b[^>]*>)(.*?)(</tr>)", re.IGNORECASE | re.DOTALL)

        def _fix_tr(tr_m):
            tr_open, tr_body, tr_close = tr_m.group(1), tr_m.group(2), tr_m.group(3)
            idx = 0

            def _fix_td(td_m):
                nonlocal idx
                td_tag = td_m.group(0)
                if idx < len(col_widths):
                    w = col_widths[idx]
                    if not _get_attr(td_tag, "width"):
                        td_tag = _set_attr(td_tag, "width", w)
                    style = _get_attr(td_tag, "style") or ""
                    td_tag = _set_attr(td_tag, "style", _merge_inline_style(style, f"width: {w};"))
                idx += 1
                return td_tag

            tr_body = re.sub(r"<td\b[^>]*>", _fix_td, tr_body, flags=re.IGNORECASE)
            return tr_open + tr_body + tr_close

        return tr_re.sub(_fix_tr, tbl)

    return table_re.sub(_fix_table, html)


def fix_odoo_email_html_for_gmail(html):
    """Ensure Odoo mass_mailing HTML uses public image assets and Gmail-compatible inline styles."""
    if not html:
        return html

    html = rewrite_vhealth_image_urls(html)
    html = _SHARPSPRING_INVITE_RE.sub("https://info.vhealth-teladochealth.com/invite", html)

    needs_layout_fix = any(
        marker in html
        for marker in ('id="design-element"', "id='design-element'", "o_mail_wrapper", "bg-o-color-5", "text-o-color-3", "background: red")
    )
    if needs_layout_fix:
        html = _DESIGN_ELEMENT_STYLE_RE.sub("", html)
        html = _apply_class_and_img_inline_styles(html)
        html = _propagate_colgroup_widths(html)

    return html


def load_bundled_launch_1_template():
    """Load the Gmail-hardened Launch #1 HTML template from module data."""
    tmpl_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "templates",
        "vhealth_launch_1.html",
    )
    with open(tmpl_path, "r", encoding="utf-8") as f:
        return f.read()


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    vhealth_action_group_schedule_id = fields.Many2one(
        "vhealth.action.group.schedule",
        string="vHealth Action Group Schedule",
        index=True,
        ondelete="set null",
    )
    vhealth_drip_step = fields.Integer(string="vHealth Drip Step", default=0)

    def _get_recipients_domain(self):
        """Ensure contacts who have registered are excluded from vHealth drip campaign mailings when configured."""
        domain = super()._get_recipients_domain()
        should_exclude = (
            (self.vhealth_action_group_schedule_id and self.vhealth_action_group_schedule_id.exclude_registered)
            or self.env.context.get("vhealth_exclude_registered")
        )
        if should_exclude:
            try:
                from odoo.fields import Domain
                domain = domain & Domain([("x_studio_app_registered", "!=", "Yes")])
            except ImportError:
                from odoo.osv import expression
                domain = expression.AND([domain, [("x_studio_app_registered", "!=", "Yes")]])
        return domain

    def _render_field(self, field, res_ids, *args, **kwargs):
        """Post-process rendered body_html so Gmail receives working static image URLs and inline styles."""
        res = super()._render_field(field, res_ids, *args, **kwargs)
        if field == "body_html" and isinstance(res, dict):
            for rec_id, val in list(res.items()):
                if isinstance(val, str):
                    res[rec_id] = fix_odoo_email_html_for_gmail(val)
        return res

    def action_fix_gmail_layout(self):
        """Update selected mailings/templates with Gmail-compatible layout and public static images."""
        launch_1_html = load_bundled_launch_1_template()
        updated = 0
        for rec in self:
            subject_lower = (rec.subject or "").lower()
            body = rec.body_html or rec.body_arch or ""
            is_launch_1 = "launch #1" in subject_lower or "vhealth-email-head_launch-01" in body.lower()
            is_broken_layout = (
                "design-element" in body
                or "o_mail_wrapper" in body
                or "background: red" in body
                or not body.strip()
            )
            if is_launch_1 and is_broken_layout:
                rec.write({"body_html": launch_1_html, "body_arch": launch_1_html})
                updated += 1
            else:
                fixed_html = fix_odoo_email_html_for_gmail(rec.body_html) if rec.body_html else rec.body_html
                fixed_arch = fix_odoo_email_html_for_gmail(rec.body_arch) if rec.body_arch else rec.body_arch
                vals = {}
                if fixed_html != rec.body_html:
                    vals["body_html"] = fixed_html
                if fixed_arch != rec.body_arch:
                    vals["body_arch"] = fixed_arch
                if vals:
                    rec.write(vals)
                    updated += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Gmail Layout & Images Updated"),
                "message": _("%d mailing(s) updated with Gmail-compatible inline styles and static image URLs.") % updated,
                "type": "success",
                "sticky": False,
            },
        }

    @api.model
    def _upgrade_fix_vhealth_templates(self):
        """On module install/upgrade, upgrade broken un-inlined vHealth email templates in-place."""
        templates = self.sudo().search([
            ("is_template", "=", True),
            ("subject", "ilike", "vHealth"),
        ])
        if not templates:
            return
        launch_1_html = load_bundled_launch_1_template()
        for tmpl in templates:
            body = tmpl.body_html or tmpl.body_arch or ""
            is_broken_layout = any(
                marker in body
                for marker in ('id="design-element"', "id='design-element'", "o_mail_wrapper", "background: red")
            )
            if "launch #1" in (tmpl.subject or "").lower() and is_broken_layout:
                tmpl.write({"body_html": launch_1_html, "body_arch": launch_1_html})
                _logger.info("Upgraded vHealth Launch #1 template (ID %s) to Gmail-compatible HTML.", tmpl.id)
            elif is_broken_layout or "/web/image/" in body:
                vals = {}
                if tmpl.body_html:
                    fixed = fix_odoo_email_html_for_gmail(tmpl.body_html)
                    if fixed != tmpl.body_html:
                        vals["body_html"] = fixed
                if tmpl.body_arch:
                    fixed_arch = fix_odoo_email_html_for_gmail(tmpl.body_arch)
                    if fixed_arch != tmpl.body_arch:
                        vals["body_arch"] = fixed_arch
                if vals:
                    tmpl.write(vals)
                    _logger.info("Hardened vHealth template '%s' (ID %s) for Gmail.", tmpl.subject, tmpl.id)
