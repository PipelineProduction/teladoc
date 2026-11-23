import logging
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

ACTION_GROUP_SELECTION = [
    ('new_group_launch', 'NEW GROUP LAUNCH EMAILS'),
]

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('running', 'Running'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


def _get_or_create_list(env, name):
    List = env["mailing.list"].sudo()
    rec = List.search([("name", "=", name)], limit=1)
    if not rec:
        rec = List.create({"name": name})
    return rec


class VHealthActionGroupSchedule(models.Model):
    _name = "vhealth.action.group.schedule"
    _description = "vHealth Action Group Schedule"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc, id desc"
    _rec_name = "name"

    name = fields.Char(string="Campaign Name", compute="_compute_name", store=True, readonly=False)
    mailing_list_id = fields.Many2one("mailing.list", string="Mailing List", required=True, ondelete="cascade", tracking=True)
    action_group = fields.Selection(ACTION_GROUP_SELECTION, string="Action Group", default="new_group_launch", required=True, tracking=True)
    state = fields.Selection(STATE_SELECTION, string="Status", default="draft", required=True, tracking=True)

    schedule_type = fields.Selection([
        ('now', 'As Soon as Possible'),
        ('scheduled', 'Schedule for later'),
    ], string="Schedule Timing", default="now", required=True)
    scheduled_datetime = fields.Datetime(string="Scheduled Start Date/Time", default=fields.Datetime.now)
    next_execution_date = fields.Datetime(string="Next Scheduled Step", index=True, tracking=True)

    current_step = fields.Integer(string="Current Step", default=0, tracking=True)
    step_status_description = fields.Char(string="Step Status", compute="_compute_step_status_description")

    # Step Execution Timestamps
    step1_date = fields.Datetime(string="Launch #1 Date", readonly=True)
    step2_date = fields.Datetime(string="Launch #2 Date", readonly=True)
    step3_date = fields.Datetime(string="Launch #3 Date", readonly=True)
    step4_date = fields.Datetime(string="Launch #4 Date", readonly=True)
    step5_date = fields.Datetime(string="Completion Date", readonly=True)

    # Generated Mailings
    step1_mailing_id = fields.Many2one("mailing.mailing", string="Launch #1 Mailing", readonly=True, ondelete="set null")
    step2_mailing_id = fields.Many2one("mailing.mailing", string="Launch #2 Mailing", readonly=True, ondelete="set null")
    step3_mailing_id = fields.Many2one("mailing.mailing", string="Launch #3 Mailing", readonly=True, ondelete="set null")
    step4_mailing_id = fields.Many2one("mailing.mailing", string="Launch #4 Mailing", readonly=True, ondelete="set null")

    # Recipient stats
    total_contacts_count = fields.Integer(string="Total Contacts", compute="_compute_contact_counts")
    active_contacts_count = fields.Integer(string="Eligible Unregistered", compute="_compute_contact_counts")
    registered_contacts_count = fields.Integer(string="Registered Contacts", compute="_compute_contact_counts")

    execution_log = fields.Text(string="Execution History", readonly=True)

    @api.depends("action_group", "mailing_list_id", "mailing_list_id.name")
    def _compute_name(self):
        group_labels = dict(ACTION_GROUP_SELECTION)
        for rec in self:
            label = group_labels.get(rec.action_group, "Action Group")
            list_name = rec.mailing_list_id.name or _("New List")
            rec.name = f"{label} - {list_name}"

    @api.depends("mailing_list_id", "mailing_list_id.contact_ids")
    def _compute_contact_counts(self):
        for rec in self:
            if not rec.mailing_list_id:
                rec.total_contacts_count = 0
                rec.active_contacts_count = 0
                rec.registered_contacts_count = 0
                continue
            contacts = rec.mailing_list_id.contact_ids
            total = len(contacts)
            registered = len(contacts.filtered(lambda c: c.x_studio_app_registered == 'Yes'))
            rec.total_contacts_count = total
            rec.registered_contacts_count = registered
            rec.active_contacts_count = total - registered

    @api.depends("current_step", "state", "next_execution_date")
    def _compute_step_status_description(self):
        step_descriptions = {
            0: _("Not Started"),
            1: _("Launch #1 Sent (Waiting for Launch #2)"),
            2: _("Launch #2 Sent (Waiting for Launch #3)"),
            3: _("Launch #3 Sent (Waiting for Launch #4)"),
            4: _("Engagement Checked & Launch #4 Sent (Waiting for Completion)"),
            5: _("Completed - Unregistered Members Added to 'All non registered members'"),
        }
        for rec in self:
            desc = step_descriptions.get(rec.current_step, _("In Progress"))
            if rec.state == 'completed':
                rec.step_status_description = _("Campaign Completed")
            elif rec.state == 'cancelled':
                rec.step_status_description = _("Campaign Cancelled")
            elif rec.next_execution_date:
                rec.step_status_description = f"{desc} | Next step due: {rec.next_execution_date}"
            else:
                rec.step_status_description = desc

    def _log(self, message):
        now_str = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = f"[{now_str}] {message}\n"
        for rec in self:
            current = rec.execution_log or ""
            rec.write({"execution_log": current + entry})

    def action_start(self):
        """Start the campaign. If scheduled for now, immediately run Step 1."""
        for rec in self:
            now = fields.Datetime.now()
            if rec.schedule_type == 'now' or not rec.scheduled_datetime or rec.scheduled_datetime <= now:
                rec.write({'state': 'running'})
                rec._log(_("Campaign started immediately."))
                rec._run_next_step()
            else:
                rec.write({
                    'state': 'running',
                    'next_execution_date': rec.scheduled_datetime,
                })
                rec._log(_("Campaign scheduled. Step 1 will execute on %s.") % rec.scheduled_datetime)
        return True

    def action_run_step_now(self):
        """Allows manual triggering of the next step without waiting 7 days."""
        for rec in self:
            if rec.state != 'running':
                raise UserError(_("Campaign must be in 'Running' state to execute steps."))
            rec._log(_("Manual step trigger initiated by user."))
            rec._run_next_step()
        return True

    def action_cancel(self):
        for rec in self:
            rec.write({
                'state': 'cancelled',
                'next_execution_date': False,
            })
            rec._log(_("Campaign cancelled by user."))
        return True

    def action_resume(self):
        for rec in self:
            if rec.state == 'cancelled':
                rec.write({
                    'state': 'running',
                    'next_execution_date': fields.Datetime.now() + timedelta(days=7),
                })
                rec._log(_("Campaign resumed."))
        return True

    def _find_template(self, step_number):
        """Find the mailing.mailing template for Launch #step_number strictly from Email Marketing > Templates."""
        Mailing = self.env["mailing.mailing"].sudo()
        expected_subject = f"vHealth - Launch #{step_number} (2025)"
        
        # 1. Search for template by exact subject
        tmpl = Mailing.search([
            ("is_template", "=", True),
            ("subject", "=ilike", expected_subject),
        ], limit=1)
        if tmpl:
            return tmpl

        # 2. Search template by looser pattern (e.g. Launch #1)
        tmpl = Mailing.search([
            ("is_template", "=", True),
            ("subject", "ilike", f"Launch #{step_number}"),
        ], limit=1)
        if tmpl:
            return tmpl

        # 3. Search non-template mailing by exact subject
        tmpl = Mailing.search([
            ("subject", "=ilike", expected_subject),
        ], limit=1)
        if tmpl:
            return tmpl

        # 4. Search any mailing by looser pattern
        tmpl = Mailing.search([
            ("subject", "ilike", f"Launch #{step_number}"),
        ], limit=1)
        if tmpl:
            return tmpl

        raise UserError(_(
            "Could not find template '%s' in Email Marketing > Templates. "
            "Please create or verify the template in Email Marketing -> Templates with the Subject '%s'."
        ) % (expected_subject, expected_subject))

    def _create_and_send_launch_mailing(self, step_number):
        """Duplicate launch template, configure for this mailing list, and queue for sending."""
        self.ensure_one()
        template = self._find_template(step_number)
        
        # Check remaining eligible contacts on list
        eligible_contacts = self.env["mailing.contact"].sudo().search([
            ("list_ids", "in", [self.mailing_list_id.id]),
            ("x_studio_app_registered", "!=", "Yes"),
        ])
        
        if not eligible_contacts:
            self._log(_(
                "Step %d: All contacts on list '%s' have already registered. No Launch #%d email sent."
            ) % (step_number, self.mailing_list_id.name, step_number))
            return False

        mailing_model_id = self.env.ref("mass_mailing.model_mailing_list", raise_if_not_found=False)
        if not mailing_model_id:
            mailing_model_id = self.env["ir.model"]._get("mailing.list")

        # Resolve email_from: PostgreSQL constraint enforces email_from is required for non-template mailings
        email_from = (
            (template.email_from and template.email_from.strip())
            or (self.env.user and self.env.user.email_formatted)
            or (self.env.user and self.env.user.email)
            or (self.env.company and self.env.company.email_formatted)
            or (self.env.company and self.env.company.email)
            or (hasattr(self.env.get("ir.mail_server", object), "_get_default_from_address") and self.env["ir.mail_server"]._get_default_from_address())
            or "info@vhealth-teladochealth.com"
        )

        mailing_vals = {
            "subject": template.subject,
            "email_from": email_from,
            "is_template": False,
            "mailing_model_id": mailing_model_id.id,
            "contact_list_ids": [(6, 0, [self.mailing_list_id.id])],
            "vhealth_action_group_schedule_id": self.id,
            "vhealth_drip_step": step_number,
            "schedule_type": "now",
        }
        if template.reply_to:
            mailing_vals["reply_to"] = template.reply_to
        else:
            mailing_vals["reply_to"] = email_from
        if template.reply_to_mode:
            mailing_vals["reply_to_mode"] = template.reply_to_mode
        else:
            mailing_vals["reply_to_mode"] = "new"

        new_mailing = template.copy(default=mailing_vals)
        
        # Explicitly set mailing domain filtering out registered contacts
        filter_domain = [
            ("list_ids", "in", [self.mailing_list_id.id]),
            ("x_studio_app_registered", "!=", "Yes"),
        ]
        new_mailing.write({"mailing_domain": repr(filter_domain)})

        # Launch / queue the mailing
        try:
            new_mailing.action_launch()
        except Exception as exc:
            _logger.warning("new_mailing.action_launch() failed (%s), trying action_put_in_queue()", exc)
            try:
                new_mailing.action_put_in_queue()
            except Exception as exc2:
                _logger.warning("new_mailing.action_put_in_queue() failed (%s), attempting action_send_mail()", exc2)
                try:
                    new_mailing.action_send_mail()
                except Exception as exc3:
                    _logger.exception("Failed to queue or send mailing %s: %s", new_mailing.id, exc3)
                    raise UserError(_("Failed to dispatch Launch #%d mailing: %s") % (step_number, exc3))

        self._log(_(
            "Step %d: Created and queued Launch #%d mailing '%s' (ID %d) for %d eligible recipients."
        ) % (step_number, step_number, new_mailing.subject, new_mailing.id, len(eligible_contacts)))

        return new_mailing

    def _run_next_step(self):
        """Execute the next step in the drip sequence and schedule following step +7 days."""
        self.ensure_one()
        now = fields.Datetime.now()
        step = self.current_step

        if step == 0:
            # Step 1: Send Launch #1 email
            mailing = self._create_and_send_launch_mailing(1)
            next_date = now + timedelta(days=7)
            vals = {
                "current_step": 1,
                "step1_date": now,
                "next_execution_date": next_date,
            }
            if mailing:
                vals["step1_mailing_id"] = mailing.id
            self.write(vals)
            self._log(_("Step 1 executed successfully. Step 2 scheduled for %s.") % next_date)

        elif step == 1:
            # Step 2: Send Launch #2 email
            mailing = self._create_and_send_launch_mailing(2)
            next_date = now + timedelta(days=7)
            vals = {
                "current_step": 2,
                "step2_date": now,
                "next_execution_date": next_date,
            }
            if mailing:
                vals["step2_mailing_id"] = mailing.id
            self.write(vals)
            self._log(_("Step 2 executed successfully. Step 3 scheduled for %s.") % next_date)

        elif step == 2:
            # Step 3: Send Launch #3 email
            mailing = self._create_and_send_launch_mailing(3)
            next_date = now + timedelta(days=7)
            vals = {
                "current_step": 3,
                "step3_date": now,
                "next_execution_date": next_date,
            }
            if mailing:
                vals["step3_mailing_id"] = mailing.id
            self.write(vals)
            self._log(_("Step 3 executed successfully. Step 4 scheduled for %s.") % next_date)

        elif step == 3:
            # Step 4: Change lead field check for engagement value to 1, then send Launch #4 email
            contacts_to_update = self.env["mailing.contact"].sudo().search([
                ("list_ids", "in", [self.mailing_list_id.id]),
                ("x_studio_app_registered", "!=", "Yes"),
            ])
            if contacts_to_update:
                contacts_to_update.write({"x_studio_check_for_engagement": True})
                self._log(_(
                    "Step 4: Set 'Check for engagement' = True for %d eligible contacts."
                ) % len(contacts_to_update))

            mailing = self._create_and_send_launch_mailing(4)
            next_date = now + timedelta(days=7)
            vals = {
                "current_step": 4,
                "step4_date": now,
                "next_execution_date": next_date,
            }
            if mailing:
                vals["step4_mailing_id"] = mailing.id
            self.write(vals)
            self._log(_("Step 4 executed successfully. Step 5 scheduled for %s.") % next_date)

        elif step == 4:
            # Step 5: Add to list "All non registered members" if no action is taken (not registered)
            unregistered_contacts = self.env["mailing.contact"].sudo().search([
                ("list_ids", "in", [self.mailing_list_id.id]),
                ("x_studio_app_registered", "!=", "Yes"),
            ])
            non_reg_list = _get_or_create_list(self.env, "All non registered members")
            
            if unregistered_contacts:
                for contact in unregistered_contacts:
                    contact.write({"list_ids": [(4, non_reg_list.id)]})
                self._log(_(
                    "Step 5: Added %d unregistered contacts to list '%s'."
                ) % (len(unregistered_contacts), non_reg_list.name))
            else:
                self._log(_(
                    "Step 5: No unregistered contacts remaining on list '%s'."
                ) % self.mailing_list_id.name)

            self.write({
                "current_step": 5,
                "step5_date": now,
                "next_execution_date": False,
                "state": "completed",
            })
            self._log(_("Campaign completed successfully."))

        return True

    @api.model
    def _cron_process_scheduled_action_groups(self):
        """Cron method executed periodically to advance due campaigns."""
        now = fields.Datetime.now()
        due_campaigns = self.search([
            ("state", "=", "running"),
            ("next_execution_date", "<=", now),
        ])
        _logger.info("vHealth action group scheduler: Found %d due campaigns.", len(due_campaigns))
        
        for campaign in due_campaigns:
            try:
                with self.env.cr.savepoint():
                    campaign._run_next_step()
            except Exception as exc:
                _logger.exception(
                    "vHealth action group schedule failed for campaign %s (ID %s): %s",
                    campaign.name, campaign.id, exc
                )
                campaign._log(_("CRON ERROR on step execution: %s") % str(exc))
