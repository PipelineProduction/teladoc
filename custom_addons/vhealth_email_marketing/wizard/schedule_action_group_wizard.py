import logging
from markupsafe import escape
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class VHealthScheduleActionGroupWizard(models.TransientModel):
    _name = "vhealth.schedule.action.group.wizard"
    _description = "Schedule Action Group for List Wizard"

    @api.model
    def _default_action_group_id(self):
        ag = self.env["vhealth.action.group"]._get_new_group_launch()
        if not ag:
            ag = self.env["vhealth.action.group"].sudo().search([("active", "=", True)], limit=1)
        return ag.id if ag else False

    mailing_list_id = fields.Many2one(
        "mailing.list",
        string="Mailing List",
        required=True,
        default=lambda self: self.env.context.get("active_id"),
    )
    action_group_id = fields.Many2one(
        "vhealth.action.group",
        string="Action Group",
        required=True,
        domain="[('active', '=', True)]",
        default=_default_action_group_id,
    )
    # Legacy selection kept optional for backward compatibility with callers passing action_group='new_group_launch'
    action_group = fields.Selection(
        [("new_group_launch", "NEW GROUP LAUNCH EMAILS")],
        string="Legacy Action Group",
        default="new_group_launch",
        required=False,
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
        help="Date and time when the first step should execute. Subsequent steps will follow the configured wait days.",
    )

    total_contacts = fields.Integer(string="Total Contacts", compute="_compute_list_summary")
    active_contacts = fields.Integer(string="Eligible Recipients", compute="_compute_list_summary")
    registered_contacts = fields.Integer(string="Registered Members", compute="_compute_list_summary")
    summary_html = fields.Html(string="Summary", compute="_compute_list_summary")

    def _resolve_action_group(self):
        self.ensure_one()
        if self.action_group_id:
            return self.action_group_id
        if self.action_group == "new_group_launch":
            return self.env["vhealth.action.group"]._get_new_group_launch()
        return self.env["vhealth.action.group"].sudo().search([("active", "=", True)], limit=1)

    @api.depends("mailing_list_id", "action_group_id", "action_group", "schedule_type", "scheduled_datetime")
    def _compute_list_summary(self):
        for rec in self:
            if not rec.mailing_list_id:
                rec.total_contacts = 0
                rec.active_contacts = 0
                rec.registered_contacts = 0
                rec.summary_html = _("<p>Please select a mailing list.</p>")
                continue

            ag = rec._resolve_action_group()
            exclude_reg = ag.exclude_registered if ag else True

            contacts = rec.mailing_list_id.contact_ids
            total = len(contacts)
            registered = len(contacts.filtered(lambda c: c.x_studio_app_registered == "Yes"))
            active = (total - registered) if exclude_reg else total
            rec.total_contacts = total
            rec.registered_contacts = registered
            rec.active_contacts = active

            ag_name = escape(ag.name if ag else "NEW GROUP LAUNCH EMAILS")
            list_name = escape(rec.mailing_list_id.name or "")
            timing_text = (
                _("immediately upon scheduling")
                if rec.schedule_type == "now"
                else _("on <b>%s</b>") % escape(str(rec.scheduled_datetime or _("selected time")))
            )

            exclusion_note = (
                _(" (%d already registered members will be excluded)") % registered
                if exclude_reg
                else _(" (all members included)")
            )

            # Build dynamic step summary from the configured Action Group steps
            step_lines = []
            if ag and ag.step_ids:
                steps = ag.step_ids.sorted(key=lambda s: (s.sequence, s.id))
                day_offset = 0
                for idx, step in enumerate(steps):
                    when_label = _("Start") if day_offset == 0 else _("+%d days") % day_offset
                    step_lines.append(
                        f"• <b>{escape(when_label)}:</b> {escape(step._describe_step())}<br/>"
                    )
                    if idx < len(steps) - 1 and step.delay_days > 0:
                        day_offset += step.delay_days
            else:
                step_lines.append(f"• {escape(_('No steps configured yet on this Action Group.'))}<br/>")

            steps_html = "".join(step_lines)
            html = f"""
            <div class="alert alert-info py-2 px-3 mb-2" role="alert">
                <p class="mb-1">
                    This action will schedule the <b>{ag_name}</b> workflow for
                    <b>{active}</b> eligible members of list <b>"{list_name}"</b>{escape(exclusion_note)}.
                </p>
                <p class="mb-1">
                    First step will run: <b>{timing_text}</b>.
                </p>
                <hr class="my-2"/>
                <p class="mb-0 small text-muted">
                    <b>Action Group Workflow Sequence:</b><br/>
                    {steps_html}
                </p>
            </div>
            """
            rec.summary_html = html

    def action_schedule(self):
        """Create and start the Action Group Schedule."""
        self.ensure_one()
        if not self.mailing_list_id:
            raise UserError(_("Please select a mailing list."))

        ag = self._resolve_action_group()
        if not ag:
            raise UserError(_("Please select an Action Group."))
        if not ag.step_ids:
            raise UserError(_(
                "Action Group '%s' has no steps configured. Please add at least one step in Configuration > Action Groups."
            ) % ag.name)

        # Check for existing running campaign for this list + action group
        existing_running = self.env["vhealth.action.group.schedule"].search([
            ("mailing_list_id", "=", self.mailing_list_id.id),
            ("action_group_id", "=", ag.id),
            ("state", "=", "running"),
        ], limit=1)

        if existing_running:
            raise UserError(_(
                "A running campaign '%s' already exists for list '%s'. Please wait for it to complete or cancel it first."
            ) % (existing_running.name, self.mailing_list_id.name))

        schedule_vals = {
            "mailing_list_id": self.mailing_list_id.id,
            "action_group_id": ag.id,
            "action_group": ag.code if ag.code == "new_group_launch" else False,
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
