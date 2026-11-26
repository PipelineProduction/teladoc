from markupsafe import escape
from odoo import api, fields, models, _
from ..models.imports import (
    COHORT_LISTS,
    LIVE_LIST_NAME,
    REGISTERED_LIST_NAME,
    _get_or_create_list,
)


class VHealthRebuildMailingListsWizard(models.TransientModel):
    _name = "vhealth.rebuild.mailing.lists.wizard"
    _description = "Rebuild vHealth Mailing Lists Wizard"

    @api.model
    def _find_existing_list(self, name):
        clean_name = (name or "").strip()
        if not clean_name:
            return False
        List = self.env["mailing.list"].sudo()
        rec = List.search([("name", "=", clean_name)], limit=1)
        if not rec:
            rec = List.search([("name", "=ilike", clean_name)], limit=1)
        return rec.id if rec else False

    state = fields.Selection(
        [("draft", "Configure"), ("done", "Completed")],
        default="draft",
        required=True,
    )
    require_vhealth_contact = fields.Boolean(
        string="vHealth Contact == True (Default Rule)",
        default=True,
        help="When enabled, every rebuilt list requires 'vHealth Contact' to be checked on the mailing contact.",
    )

    list_live_id = fields.Many2one(
        "mailing.list",
        string=LIVE_LIST_NAME,
        default=lambda self: self._find_existing_list(LIVE_LIST_NAME),
    )
    list_registered_id = fields.Many2one(
        "mailing.list",
        string=REGISTERED_LIST_NAME,
        default=lambda self: self._find_existing_list(REGISTERED_LIST_NAME),
    )
    list_th_id = fields.Many2one(
        "mailing.list",
        string=COHORT_LISTS["TH"],
        default=lambda self: self._find_existing_list(COHORT_LISTS["TH"]),
    )
    list_th_mh_id = fields.Many2one(
        "mailing.list",
        string=COHORT_LISTS["TH + MH"],
        default=lambda self: self._find_existing_list(COHORT_LISTS["TH + MH"]),
    )
    list_pc_id = fields.Many2one(
        "mailing.list",
        string=COHORT_LISTS["PC"],
        default=lambda self: self._find_existing_list(COHORT_LISTS["PC"]),
    )
    list_mh_id = fields.Many2one(
        "mailing.list",
        string=COHORT_LISTS["MH"],
        default=lambda self: self._find_existing_list(COHORT_LISTS["MH"]),
    )

    preview_html = fields.Html(string="Rule Preview", compute="_compute_preview_html")
    result_html = fields.Html(string="Rebuild Summary", readonly=True)

    def _get_rule_definitions(self):
        """Return ordered rule definitions for all 6 vHealth mailing lists."""
        self.ensure_one()
        base_domain = [("x_studio_vhealth_contact", "=", True)] if self.require_vhealth_contact else []
        vhealth_prefix = "vHealth Contact = True AND " if self.require_vhealth_contact else ""

        return [
            {
                "key": "live",
                "field": "list_live_id",
                "default_name": LIVE_LIST_NAME,
                "list_rec": self.list_live_id,
                "domain": list(base_domain),
                "rule_text": (
                    "vHealth Contact == True"
                    if self.require_vhealth_contact
                    else "All contacts (default filter disabled)"
                ),
            },
            {
                "key": "registered",
                "field": "list_registered_id",
                "default_name": REGISTERED_LIST_NAME,
                "list_rec": self.list_registered_id,
                "domain": list(base_domain) + [
                    ("x_studio_location_us_or_canada", "=", True),
                    "|",
                    ("x_studio_app_unique_registered", "=", "Yes"),
                    ("x_studio_app_registered", "=", "Yes"),
                ],
                "rule_text": (
                    f"{vhealth_prefix}((App - UNIQUE Registered == Yes AND Location US or Canada? == True) "
                    "OR (App - Registered == Yes AND Location US or Canada? == True))"
                ),
            },
            {
                "key": "th",
                "field": "list_th_id",
                "default_name": COHORT_LISTS["TH"],
                "list_rec": self.list_th_id,
                "domain": list(base_domain) + [("x_studio_cohort_group", "=", "TH")],
                "rule_text": f"{vhealth_prefix}Cohort Group == 'TH'",
            },
            {
                "key": "th_mh",
                "field": "list_th_mh_id",
                "default_name": COHORT_LISTS["TH + MH"],
                "list_rec": self.list_th_mh_id,
                "domain": list(base_domain) + [("x_studio_cohort_group", "=", "TH + MH")],
                "rule_text": f"{vhealth_prefix}Cohort Group == 'TH + MH'",
            },
            {
                "key": "pc",
                "field": "list_pc_id",
                "default_name": COHORT_LISTS["PC"],
                "list_rec": self.list_pc_id,
                "domain": list(base_domain) + [("x_studio_cohort_group", "=", "PC")],
                "rule_text": f"{vhealth_prefix}Cohort Group == 'PC'",
            },
            {
                "key": "mh",
                "field": "list_mh_id",
                "default_name": COHORT_LISTS["MH"],
                "list_rec": self.list_mh_id,
                "domain": list(base_domain) + [("x_studio_cohort_group", "=", "MH")],
                "rule_text": f"{vhealth_prefix}Cohort Group == 'MH'",
            },
        ]

    @api.depends(
        "require_vhealth_contact",
        "list_live_id",
        "list_registered_id",
        "list_th_id",
        "list_th_mh_id",
        "list_pc_id",
        "list_mh_id",
    )
    def _compute_preview_html(self):
        Contact = self.env["mailing.contact"].sudo()
        for rec in self:
            rows = []
            for spec in rec._get_rule_definitions():
                target_list = spec["list_rec"]
                list_label = escape(target_list.name) if target_list else escape(f"{spec['default_name']} (will auto-create)")
                current_count = len(target_list.contact_ids) if target_list else 0
                matching_count = Contact.search_count(spec["domain"])
                rows.append(
                    f"<tr>"
                    f"<td><b>{list_label}</b></td>"
                    f"<td class='small text-muted'>{escape(spec['rule_text'])}</td>"
                    f"<td class='text-end'>{current_count}</td>"
                    f"<td class='text-end'><b>{matching_count}</b></td>"
                    f"</tr>"
                )
            rec.preview_html = (
                "<table class='table table-sm table-bordered mb-0'>"
                "<thead><tr>"
                "<th>Mailing List</th><th>Active Rule</th>"
                "<th class='text-end'>Current</th><th class='text-end'>Matching</th>"
                "</tr></thead>"
                f"<tbody>{''.join(rows)}</tbody>"
                "</table>"
            )

    def action_rebuild_lists(self):
        """Rebuild all 6 vHealth mailing lists from mailing.contact rules while preserving opt_out flags."""
        self.ensure_one()
        Contact = self.env["mailing.contact"].sudo()
        summary_rows = []
        assign_vals = {}

        for spec in self._get_rule_definitions():
            target_list = spec["list_rec"] or _get_or_create_list(self.env, spec["default_name"])
            if not spec["list_rec"]:
                assign_vals[spec["field"]] = target_list.id

            matching_ids = set(Contact.search(spec["domain"]).ids)
            current_ids = set(target_list.contact_ids.ids)
            to_add = sorted(matching_ids - current_ids)
            to_remove = sorted(current_ids - matching_ids)

            commands = [(4, cid) for cid in to_add] + [(3, cid) for cid in to_remove]
            if commands:
                target_list.sudo().write({"contact_ids": commands})

            summary_rows.append(
                f"<tr>"
                f"<td><b>{escape(target_list.name)}</b></td>"
                f"<td class='text-end text-success'>+{len(to_add)}</td>"
                f"<td class='text-end text-danger'>-{len(to_remove)}</td>"
                f"<td class='text-end'><b>{len(matching_ids)}</b></td>"
                f"</tr>"
            )

        assign_vals.update({
            "state": "done",
            "result_html": (
                "<div class='alert alert-success py-2 px-3 mb-2' role='alert'>"
                "<b>Mailing lists rebuilt successfully</b> based on main Mailing Contacts."
                "</div>"
                "<table class='table table-sm table-bordered mb-0'>"
                "<thead><tr>"
                "<th>Mailing List</th><th class='text-end'>Added</th>"
                "<th class='text-end'>Removed</th><th class='text-end'>Total</th>"
                "</tr></thead>"
                f"<tbody>{''.join(summary_rows)}</tbody>"
                "</table>"
            ),
        })
        self.write(assign_vals)

        return {
            "name": _("Rebuild Mailing Lists"),
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }
