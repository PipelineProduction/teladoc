import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

STEP_ACTION_TYPES = [
    ("send_email", "Send Email"),
    ("update_contact", "Update Contact Field"),
    ("add_to_list", "Add to Mailing List"),
    ("remove_from_list", "Remove from Mailing List"),
]


class VHealthActionGroup(models.Model):
    _name = "vhealth.action.group"
    _description = "vHealth Action Group"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence asc, name asc, id asc"
    _rec_name = "name"

    name = fields.Char(string="Action Group Name", required=True, tracking=True)
    code = fields.Char(
        string="Technical Code",
        index=True,
        copy=False,
        help="Optional internal code for system-seeded action groups (e.g. new_group_launch).",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    description = fields.Text(string="Description")
    exclude_registered = fields.Boolean(
        string="Exclude Registered Members",
        default=True,
        tracking=True,
        help="When enabled, contacts with App - Registered = 'Yes' are excluded from every email, update, and list action in this group.",
    )

    step_ids = fields.One2many(
        "vhealth.action.group.step",
        "action_group_id",
        string="Action Steps",
        copy=True,
    )
    step_count = fields.Integer(string="Steps", compute="_compute_step_count")

    schedule_ids = fields.One2many(
        "vhealth.action.group.schedule",
        "action_group_id",
        string="Scheduled Campaigns",
    )
    schedule_count = fields.Integer(string="Scheduled Campaigns", compute="_compute_schedule_count")

    @api.depends("step_ids")
    def _compute_step_count(self):
        for rec in self:
            rec.step_count = len(rec.step_ids)

    @api.depends("schedule_ids")
    def _compute_schedule_count(self):
        for rec in self:
            rec.schedule_count = len(rec.schedule_ids)

    @api.model
    def _get_new_group_launch(self):
        """Return the seeded 'NEW GROUP LAUNCH EMAILS' action group if present."""
        rec = self.env.ref("vhealth_email_marketing.action_group_new_group_launch", raise_if_not_found=False)
        if rec:
            return rec
        return self.sudo().search([("code", "=", "new_group_launch")], limit=1)

    def action_view_schedules(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "vhealth_email_marketing.action_vhealth_action_group_schedule"
        )
        action["domain"] = [("action_group_id", "=", self.id)]
        action["context"] = {"default_action_group_id": self.id}
        return action


class VHealthActionGroupStep(models.Model):
    _name = "vhealth.action.group.step"
    _description = "vHealth Action Group Step"
    _order = "sequence asc, id asc"

    action_group_id = fields.Many2one(
        "vhealth.action.group",
        string="Action Group",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Step #", default=10, required=True)
    name = fields.Char(string="Step Label", compute="_compute_name", store=True, readonly=False)
    action_type = fields.Selection(
        STEP_ACTION_TYPES,
        string="Action Type",
        required=True,
        default="send_email",
    )
    delay_days = fields.Integer(
        string="Wait Days After Step",
        default=7,
        help="Days to wait after this step runs before running the next step. Set 0 to run the next step immediately in the same cycle.",
    )
    delay_minutes = fields.Integer(
        string="Wait Minutes After Step",
        default=0,
        help="Additional minutes to wait after this step runs before running the next step (useful for testing when Wait Days is 0).",
    )

    # Send Email configuration
    mailing_template_id = fields.Many2one(
        "mailing.mailing",
        string="Email Template",
        domain="[('is_template', '=', True)]",
        ondelete="set null",
        help="Template from Email Marketing > Templates to duplicate and send.",
    )
    template_subject_pattern = fields.Char(
        string="Template Subject Lookup",
        help="Fallback subject lookup when no specific Email Template record is linked (e.g. 'vHealth - Launch #1 (2025)').",
    )
    launch_step_number = fields.Integer(
        string="Launch Number",
        default=0,
        help="Optional launch index used for looser subject lookup fallback (e.g. 'Launch #1').",
    )

    # Update Contact Field configuration
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Contact Field",
        domain="[('model', '=', 'mailing.contact'), ('store', '=', True), ('readonly', '=', False)]",
        ondelete="set null",
    )
    field_name = fields.Char(
        string="Field Technical Name",
        compute="_compute_field_name",
        store=True,
        readonly=False,
    )
    field_value = fields.Char(
        string="Value to Set",
        help="Value to write to the contact field (for booleans use True/False; for selections use the exact key or label).",
    )

    # List membership configuration
    target_mailing_list_id = fields.Many2one(
        "mailing.list",
        string="Target Mailing List",
        ondelete="set null",
    )
    target_list_name = fields.Char(
        string="Or List Name (Auto-create)",
        help="Used when Target Mailing List is empty; finds or creates a mailing list with this exact name.",
    )

    @api.depends("field_id")
    def _compute_field_name(self):
        for rec in self:
            if rec.field_id:
                rec.field_name = rec.field_id.name

    @api.depends(
        "action_type",
        "mailing_template_id",
        "mailing_template_id.subject",
        "template_subject_pattern",
        "field_id",
        "field_id.field_description",
        "field_name",
        "field_value",
        "target_mailing_list_id",
        "target_mailing_list_id.name",
        "target_list_name",
    )
    def _compute_name(self):
        for rec in self:
            if rec.action_type == "send_email":
                label = (
                    (rec.mailing_template_id and rec.mailing_template_id.subject)
                    or rec.template_subject_pattern
                    or (f"Launch #{rec.launch_step_number}" if rec.launch_step_number else _("Email"))
                )
                rec.name = _("Send Email: %s") % label
            elif rec.action_type == "update_contact":
                fname = (rec.field_id and rec.field_id.field_description) or rec.field_name or _("Field")
                rec.name = _("Set %s = %s") % (fname, rec.field_value or "")
            elif rec.action_type == "add_to_list":
                lname = (rec.target_mailing_list_id and rec.target_mailing_list_id.name) or rec.target_list_name or _("List")
                rec.name = _("Add to List: %s") % lname
            elif rec.action_type == "remove_from_list":
                lname = (rec.target_mailing_list_id and rec.target_mailing_list_id.name) or rec.target_list_name or _("Campaign List")
                rec.name = _("Remove from List: %s") % lname
            else:
                rec.name = _("Action Step")

    @api.constrains("delay_days", "delay_minutes", "action_type", "mailing_template_id", "template_subject_pattern", "launch_step_number", "field_id", "field_name", "target_mailing_list_id", "target_list_name")
    def _check_step_configuration(self):
        for rec in self:
            if rec.delay_days < 0 or rec.delay_minutes < 0:
                raise ValidationError(_("Wait Days and Wait Minutes After Step cannot be negative."))
            if rec.action_type == "send_email" and not (
                rec.mailing_template_id or rec.template_subject_pattern or rec.launch_step_number > 0
            ):
                raise ValidationError(_("A 'Send Email' step requires an Email Template or a Template Subject Lookup."))
            if rec.action_type == "update_contact" and not (rec.field_id or rec.field_name):
                raise ValidationError(_("An 'Update Contact Field' step requires a Contact Field."))
            if rec.action_type == "add_to_list" and not (rec.target_mailing_list_id or rec.target_list_name):
                raise ValidationError(_("An 'Add to Mailing List' step requires a Target Mailing List or List Name."))

    def _parse_field_value(self, ContactModel):
        """Convert stored string field_value into the appropriate Python value for ContactModel."""
        self.ensure_one()
        fname = (self.field_id and self.field_id.name) or self.field_name
        if not fname or fname not in ContactModel._fields:
            raise ValidationError(_("Field '%s' does not exist on mailing.contact.") % (fname or ""))

        field = ContactModel._fields[fname]
        raw = self.field_value
        raw_str = "" if raw is False or raw is None else str(raw).strip()

        if field.type == "boolean":
            return raw_str.lower() in ("1", "true", "yes", "y", "on")
        if field.type == "integer":
            return int(raw_str) if raw_str else 0
        if field.type in ("float", "monetary"):
            return float(raw_str) if raw_str else 0.0
        if field.type == "many2one":
            if not raw_str:
                return False
            if raw_str.isdigit():
                return int(raw_str)
            target = self.env[field.comodel_name].sudo().search([("display_name", "=", raw_str)], limit=1)
            return target.id if target else False
        if field.type == "selection":
            if not raw_str:
                return False
            selection = field.selection(ContactModel) if callable(field.selection) else field.selection
            keys = {k: k for k, _lbl in selection}
            labels = {str(lbl).lower(): k for k, lbl in selection}
            if raw_str in keys:
                return raw_str
            if raw_str.lower() in labels:
                return labels[raw_str.lower()]
            return raw_str
        return raw_str or False

    def _describe_step(self):
        """Return a concise description for summary previews."""
        self.ensure_one()
        if self.action_type == "send_email":
            target = (
                (self.mailing_template_id and self.mailing_template_id.subject)
                or self.template_subject_pattern
                or (f"Launch #{self.launch_step_number}" if self.launch_step_number else _("Email"))
            )
            return _("Send email \"%s\"") % target
        if self.action_type == "update_contact":
            fname = (self.field_id and self.field_id.field_description) or self.field_name
            return _("Set contact field \"%s\" to %s") % (fname, self.field_value or "")
        if self.action_type == "add_to_list":
            lname = (self.target_mailing_list_id and self.target_mailing_list_id.name) or self.target_list_name
            return _("Add contacts to list \"%s\"") % lname
        if self.action_type == "remove_from_list":
            lname = (self.target_mailing_list_id and self.target_mailing_list_id.name) or self.target_list_name or _("this list")
            return _("Remove contacts from list \"%s\"") % lname
        return self.name or _("Execute step")
