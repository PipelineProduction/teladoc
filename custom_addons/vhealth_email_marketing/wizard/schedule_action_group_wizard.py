import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VHealthScheduleActionGroupWizard(models.TransientModel):
    _name = "vhealth.schedule.action.group.wizard"
    _description = "Schedule Action Group for List Wizard"

    mailing_list_id = fields.Many2one(
        "mailing.list",
        string="Mailing List",
        required=True,
        default=lambda self: self.env.context.get("active_id"),
    )
    action_group = fields.Selection(
        [("new_group_launch", "NEW GROUP LAUNCH EMAILS")],
        string="Action Group",
        default="new_group_launch",
        required=True,
    )
    schedule_type = fields.Selection(
        [
            ("now", "As Soon as Possible"),
            ("scheduled", "Schedule for later"),
        ],
        string="When would you like this action to take place?",
        default="now",
        required=True,
    )
    scheduled_datetime = fields.Datetime(
        string="Date and Time",
        default=fields.Datetime.now,
        help="Date and time when the first email should be sent. Subsequent emails will be sent at 7-day intervals at this same time.",
    )

    total_contacts = fields.Integer(string="Total Contacts", compute="_compute_list_summary")
    active_contacts = fields.Integer(string="Eligible Unregistered", compute="_compute_list_summary")
    registered_contacts = fields.Integer(string="Registered Members", compute="_compute_list_summary")
    summary_html = fields.Html(string="Summary", compute="_compute_list_summary")

    @api.depends("mailing_list_id", "action_group", "schedule_type", "scheduled_datetime")
    def _compute_list_summary(self):
        for rec in self:
            if not rec.mailing_list_id:
                rec.total_contacts = 0
                rec.active_contacts = 0
                rec.registered_contacts = 0
                rec.summary_html = _("<p>Please select a mailing list.</p>")
                continue

            contacts = rec.mailing_list_id.contact_ids
            total = len(contacts)
            registered = len(contacts.filtered(lambda c: c.x_studio_app_registered == "Yes"))
            active = total - registered
            rec.total_contacts = total
            rec.registered_contacts = registered
            rec.active_contacts = active

            timing_text = _("immediately upon scheduling") if rec.schedule_type == "now" else _("on <b>%s</b>") % (rec.scheduled_datetime or _("selected time"))

            html = f"""
            <div class="alert alert-info py-2 px-3 mb-2" role="alert">
                <p class="mb-1">
                    This action will schedule the <b>NEW GROUP LAUNCH EMAILS</b> drip campaign for
                    <b>{active}</b> eligible (unregistered) members of list <b>"{rec.mailing_list_id.name}"</b>
                    ({registered} already registered members will be excluded).
                </p>
                <p class="mb-1">
                    First email will be sent: <b>{timing_text}</b>.
                </p>
                <hr class="my-2"/>
                <p class="mb-0 small text-muted">
                    <b>Drip Workflow Sequence:</b><br/>
                    • <b>Week 1:</b> Launch #1 email sent<br/>
                    • <b>Week 2 (+7 days):</b> Launch #2 email sent (registered members excluded)<br/>
                    • <b>Week 3 (+7 days):</b> Launch #3 email sent (registered members excluded)<br/>
                    • <b>Week 4 (+7 days):</b> Contact field <i>"Check for engagement"</i> set to True + Launch #4 email sent<br/>
                    • <b>Week 5 (+7 days):</b> Unregistered members automatically added to list <i>"All non registered members"</i>
                </p>
            </div>
            """
            rec.summary_html = html

    def action_schedule(self):
        """Create and start the Action Group Schedule."""
        self.ensure_one()
        if not self.mailing_list_id:
            raise UserError(_("Please select a mailing list."))

        # Check for existing running campaign for this list
        existing_running = self.env["vhealth.action.group.schedule"].search([
            ("mailing_list_id", "=", self.mailing_list_id.id),
            ("action_group", "=", self.action_group),
            ("state", "=", "running"),
        ], limit=1)

        if existing_running:
            raise UserError(_(
                "A running campaign '%s' already exists for list '%s'. Please wait for it to complete or cancel it first."
            ) % (existing_running.name, self.mailing_list_id.name))

        schedule_vals = {
            "mailing_list_id": self.mailing_list_id.id,
            "action_group": self.action_group,
            "schedule_type": self.schedule_type,
            "scheduled_datetime": self.scheduled_datetime if self.schedule_type == "scheduled" else fields.Datetime.now(),
        }

        campaign = self.env["vhealth.action.group.schedule"].create(schedule_vals)
        campaign.action_start()

        return {
            "name": _("Scheduled Action Group"),
            "type": "ir.actions.act_window",
            "res_model": "vhealth.action.group.schedule",
            "res_id": campaign.id,
            "view_mode": "form",
            "target": "current",
        }
