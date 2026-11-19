from odoo import api, fields, models, _


class MailingList(models.Model):
    _inherit = "mailing.list"

    vhealth_action_group_schedule_ids = fields.One2many(
        "vhealth.action.group.schedule",
        "mailing_list_id",
        string="Action Group Schedules",
    )
    vhealth_action_group_count = fields.Integer(
        string="Action Groups",
        compute="_compute_vhealth_action_group_count",
    )

    @api.depends("vhealth_action_group_schedule_ids")
    def _compute_vhealth_action_group_count(self):
        for rec in self:
            rec.vhealth_action_group_count = len(rec.vhealth_action_group_schedule_ids)

    def action_open_schedule_action_group_wizard(self):
        """Open the SharpSpring-style Schedule Action Group wizard for this list."""
        self.ensure_one()
        return {
            "name": _("Schedule Action Group for List"),
            "type": "ir.actions.act_window",
            "res_model": "vhealth.schedule.action.group.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_mailing_list_id": self.id,
            },
        }

    def action_view_vhealth_action_group_schedules(self):
        """View all Action Group Schedule campaigns for this list."""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "vhealth_email_marketing.action_vhealth_action_group_schedule"
        )
        action["domain"] = [("mailing_list_id", "=", self.id)]
        action["context"] = {
            "default_mailing_list_id": self.id,
        }
        return action
