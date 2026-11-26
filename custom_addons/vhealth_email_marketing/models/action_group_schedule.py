import logging
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from .mailing import fix_odoo_email_html_for_gmail, load_bundled_launch_1_template

_logger = logging.getLogger(__name__)

ACTION_GROUP_SELECTION = [
    ("new_group_launch", "NEW GROUP LAUNCH EMAILS"),
]

STATE_SELECTION = [
    ("draft", "Draft"),
    ("running", "Running"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
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

    @api.model
    def _default_action_group_id(self):
        ag = self.env["vhealth.action.group"]._get_new_group_launch()
        if not ag:
            ag = self.env["vhealth.action.group"].sudo().search([("active", "=", True)], limit=1)
        return ag.id if ag else False

    name = fields.Char(string="Campaign Name", compute="_compute_name", store=True, readonly=False)
    mailing_list_id = fields.Many2one("mailing.list", string="Mailing List", required=True, ondelete="cascade", tracking=True)
    action_group_id = fields.Many2one(
        "vhealth.action.group",
        string="Action Group",
        required=False,
        ondelete="restrict",
        tracking=True,
        default=_default_action_group_id,
    )
    action_group = fields.Selection(
        ACTION_GROUP_SELECTION,
        string="Legacy Action Group Key",
        default="new_group_launch",
        required=False,
        tracking=True,
    )
    exclude_registered = fields.Boolean(
        string="Exclude Registered Members",
        compute="_compute_exclude_registered",
        store=True,
    )
    state = fields.Selection(STATE_SELECTION, string="Status", default="draft", required=True, tracking=True)

    schedule_type = fields.Selection([
        ("now", "As Soon as Possible"),
        ("scheduled", "Schedule for later"),
    ], string="Schedule Timing", default="now", required=True)
    scheduled_datetime = fields.Datetime(string="Scheduled Start Date/Time", default=fields.Datetime.now)
    next_execution_date = fields.Datetime(string="Next Scheduled Step", index=True, tracking=True)

    current_step = fields.Integer(string="Current Step", default=0, tracking=True)
    last_step_id = fields.Many2one("vhealth.action.group.step", string="Last Executed Step", readonly=True, ondelete="set null")
    step_status_description = fields.Char(string="Step Status", compute="_compute_step_status_description")

    # Legacy 5-step Execution Timestamps (preserved for existing views & reporting)
    step1_date = fields.Datetime(string="Launch #1 Date", readonly=True)
    step2_date = fields.Datetime(string="Launch #2 Date", readonly=True)
    step3_date = fields.Datetime(string="Launch #3 Date", readonly=True)
    step4_date = fields.Datetime(string="Launch #4 Date", readonly=True)
    step5_date = fields.Datetime(string="Completion Date", readonly=True)

    # Generated Mailings (steps 1-4)
    step1_mailing_id = fields.Many2one("mailing.mailing", string="Launch #1 Mailing", readonly=True, ondelete="set null")
    step2_mailing_id = fields.Many2one("mailing.mailing", string="Launch #2 Mailing", readonly=True, ondelete="set null")
    step3_mailing_id = fields.Many2one("mailing.mailing", string="Launch #3 Mailing", readonly=True, ondelete="set null")
    step4_mailing_id = fields.Many2one("mailing.mailing", string="Launch #4 Mailing", readonly=True, ondelete="set null")

    # Dynamic step execution log lines
    execution_line_ids = fields.One2many(
        "vhealth.action.group.schedule.line",
        "schedule_id",
        string="Executed Steps",
        readonly=True,
    )

    # Recipient stats
    total_contacts_count = fields.Integer(string="Total Contacts", compute="_compute_contact_counts")
    active_contacts_count = fields.Integer(string="Eligible Recipients", compute="_compute_contact_counts")
    registered_contacts_count = fields.Integer(string="Registered Contacts", compute="_compute_contact_counts")

    execution_log = fields.Text(string="Execution History", readonly=True)

    @api.depends("action_group_id", "action_group_id.exclude_registered")
    def _compute_exclude_registered(self):
        for rec in self:
            rec.exclude_registered = rec.action_group_id.exclude_registered if rec.action_group_id else True

    @api.depends("action_group_id", "action_group_id.name", "action_group", "mailing_list_id", "mailing_list_id.name")
    def _compute_name(self):
        group_labels = dict(ACTION_GROUP_SELECTION)
        for rec in self:
            if rec.action_group_id:
                label = rec.action_group_id.name
            else:
                label = group_labels.get(rec.action_group, "Action Group")
            list_name = rec.mailing_list_id.name or _("New List")
            rec.name = f"{label} - {list_name}"

    @api.depends("mailing_list_id", "mailing_list_id.contact_ids", "exclude_registered")
    def _compute_contact_counts(self):
        for rec in self:
            if not rec.mailing_list_id:
                rec.total_contacts_count = 0
                rec.active_contacts_count = 0
                rec.registered_contacts_count = 0
                continue
            contacts = rec.mailing_list_id.contact_ids
            total = len(contacts)
            registered = len(contacts.filtered(lambda c: c.x_studio_app_registered == "Yes"))
            rec.total_contacts_count = total
            rec.registered_contacts_count = registered
            rec.active_contacts_count = (total - registered) if rec.exclude_registered else total

    @api.depends("current_step", "state", "next_execution_date", "last_step_id", "last_step_id.name", "action_group_id", "action_group_id.code")
    def _compute_step_status_description(self):
        legacy_descriptions = {
            0: _("Not Started"),
            1: _("Launch #1 Sent (Waiting for Launch #2)"),
            2: _("Launch #2 Sent (Waiting for Launch #3)"),
            3: _("Launch #3 Sent (Waiting for Launch #4)"),
            4: _("Engagement Checked & Launch #4 Sent (Waiting for Completion)"),
            5: _("Completed - Unregistered Members Added to 'All non registered members'"),
        }
        for rec in self:
            if rec.state == "completed":
                rec.step_status_description = _("Campaign Completed")
                continue
            if rec.state == "cancelled":
                rec.step_status_description = _("Campaign Cancelled")
                continue

            ag = rec.action_group_id
            if (not ag or ag.code == "new_group_launch") and rec.current_step in legacy_descriptions:
                desc = legacy_descriptions[rec.current_step]
            elif rec.current_step == 0:
                desc = _("Not Started")
            elif rec.last_step_id:
                desc = _("Cycle %d Done (%s)") % (rec.current_step, rec.last_step_id.name)
            else:
                desc = _("Step %d In Progress") % rec.current_step

            if rec.next_execution_date:
                rec.step_status_description = f"{desc} | Next step due: {rec.next_execution_date}"
            else:
                rec.step_status_description = desc

    @api.model_create_multi
    def create(self, vals_list):
        Group = self.env["vhealth.action.group"]
        for vals in vals_list:
            if not vals.get("action_group_id"):
                if vals.get("action_group") == "new_group_launch":
                    ag = Group._get_new_group_launch()
                    if ag:
                        vals["action_group_id"] = ag.id
                else:
                    ag = Group._get_new_group_launch() or Group.sudo().search([("active", "=", True)], limit=1)
                    if ag:
                        vals["action_group_id"] = ag.id
            if vals.get("action_group_id") and "action_group" not in vals:
                ag = Group.browse(vals["action_group_id"])
                vals["action_group"] = ag.code if ag.code == "new_group_launch" else False
        return super().create(vals_list)

    def _get_effective_action_group(self):
        """Return the Action Group for this schedule, auto-linking legacy records if needed."""
        self.ensure_one()
        if self.action_group_id:
            return self.action_group_id
        ag = self.env["vhealth.action.group"]._get_new_group_launch()
        if ag:
            self.sudo().write({"action_group_id": ag.id})
        return ag

    def _log(self, message):
        now_str = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = f"[{now_str}] {message}\n"
        for rec in self:
            current = rec.execution_log or ""
            rec.write({"execution_log": current + entry})

    def action_start(self):
        """Start the campaign. If scheduled for now, immediately run Step 1."""
        for rec in self:
            ag = rec._get_effective_action_group()
            if ag and not ag.step_ids:
                raise UserError(_(
                    "Action Group '%s' has no steps configured. Please configure at least one step under Configuration > Action Groups."
                ) % ag.name)
            now = fields.Datetime.now()
            if rec.schedule_type == "now" or not rec.scheduled_datetime or rec.scheduled_datetime <= now:
                rec.write({"state": "running"})
                rec._log(_("Campaign started immediately."))
                rec._run_next_step()
            else:
                rec.write({
                    "state": "running",
                    "next_execution_date": rec.scheduled_datetime,
                })
                rec._log(_("Campaign scheduled. Step 1 will execute on %s.") % rec.scheduled_datetime)
        return True

    def action_run_step_now(self):
        """Allows manual triggering of the next step without waiting."""
        for rec in self:
            if rec.state != "running":
                raise UserError(_("Campaign must be in 'Running' state to execute steps."))
            rec._log(_("Manual step trigger initiated by user."))
            rec._run_next_step()
        return True

    def action_cancel(self):
        for rec in self:
            rec.write({
                "state": "cancelled",
                "next_execution_date": False,
            })
            rec._log(_("Campaign cancelled by user."))
        return True

    def action_resume(self):
        for rec in self:
            if rec.state == "cancelled":
                wait_days = 7
                if rec.last_step_id and rec.last_step_id.delay_days > 0:
                    wait_days = rec.last_step_id.delay_days
                rec.write({
                    "state": "running",
                    "next_execution_date": fields.Datetime.now() + timedelta(days=wait_days),
                })
                rec._log(_("Campaign resumed."))
        return True

    def _find_template_by_subject(self, expected_subject, step_number=None):
        """Find a mailing.mailing template strictly from Email Marketing > Templates by subject."""
        Mailing = self.env["mailing.mailing"].sudo()

        if expected_subject:
            tmpl = Mailing.search([
                ("is_template", "=", True),
                ("subject", "=ilike", expected_subject),
            ], limit=1)
            if tmpl:
                return tmpl

        if step_number:
            tmpl = Mailing.search([
                ("is_template", "=", True),
                ("subject", "ilike", f"Launch #{step_number}"),
            ], limit=1)
            if tmpl:
                return tmpl

        if expected_subject:
            tmpl = Mailing.search([
                ("subject", "=ilike", expected_subject),
            ], limit=1)
            if tmpl:
                return tmpl

        if step_number:
            tmpl = Mailing.search([
                ("subject", "ilike", f"Launch #{step_number}"),
            ], limit=1)
            if tmpl:
                return tmpl

        label = expected_subject or (f"Launch #{step_number}" if step_number else _("Unknown Template"))
        raise UserError(_(
            "Could not find template '%s' in Email Marketing > Templates. "
            "Please create or verify the template in Email Marketing -> Templates with the Subject '%s'."
        ) % (label, label))

    def _find_template(self, step_number):
        """Find the mailing.mailing template for Launch #step_number strictly from Email Marketing > Templates."""
        expected_subject = f"vHealth - Launch #{step_number} (2025)"
        return self._find_template_by_subject(expected_subject, step_number=step_number)

    def _find_template_for_step(self, step, cycle_number):
        if step.mailing_template_id:
            return step.mailing_template_id.sudo()
        return self._find_template_by_subject(
            step.template_subject_pattern,
            step_number=step.launch_step_number or cycle_number,
        )

    def _get_target_contacts(self):
        """Return mailing.contact records on this campaign's list, respecting exclude_registered."""
        self.ensure_one()
        domain = [("list_ids", "in", [self.mailing_list_id.id])]
        if self.exclude_registered:
            domain.append(("x_studio_app_registered", "!=", "Yes"))
        return self.env["mailing.contact"].sudo().search(domain)

    def _create_and_send_launch_mailing(self, step_number, template=None):
        """Duplicate template, configure for this mailing list, and queue for sending."""
        self.ensure_one()
        if template is None:
            template = self._find_template(step_number)

        eligible_contacts = self._get_target_contacts()
        if not eligible_contacts:
            self._log(_(
                "Step %d: No eligible contacts remaining on list '%s'. No email sent."
            ) % (step_number, self.mailing_list_id.name))
            return False

        mailing_model_id = self.env.ref("mass_mailing.model_mailing_list", raise_if_not_found=False)
        if not mailing_model_id:
            mailing_model_id = self.env["ir.model"]._get("mailing.list")

        # Resolve active mail server if available
        mail_server = template.mail_server_id or self.env["ir.mail_server"].sudo().search([("active", "=", True)], order="sequence", limit=1)

        # Resolve email_from: PostgreSQL constraint enforces email_from is required for non-template mailings
        email_from = (
            (template.email_from and template.email_from.strip())
            or (mail_server and mail_server.from_filter and "@" in mail_server.from_filter and mail_server.from_filter.strip())
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
            "keep_archives": True,
            "mailing_model_id": mailing_model_id.id,
            "contact_list_ids": [(6, 0, [self.mailing_list_id.id])],
            "vhealth_action_group_schedule_id": self.id,
            "vhealth_drip_step": step_number,
            "schedule_type": "now",
        }
        if mail_server:
            mailing_vals["mail_server_id"] = mail_server.id
        mailing_vals["reply_to"] = template.reply_to or email_from
        mailing_vals["reply_to_mode"] = template.reply_to_mode or "new"

        new_mailing = template.copy(default=mailing_vals)

        # Ensure outgoing mailing HTML is Gmail-compatible and uses public static image URLs
        raw_body = new_mailing.body_html or new_mailing.body_arch or ""
        is_broken_launch_1 = (
            "launch #1" in (template.subject or "").lower()
            and any(m in raw_body for m in ('id="design-element"', "id='design-element'", "o_mail_wrapper", "background: red"))
        )
        if is_broken_launch_1:
            fixed_body = load_bundled_launch_1_template()
            new_mailing.write({"body_html": fixed_body, "body_arch": fixed_body})
        elif raw_body:
            fixed_body = fix_odoo_email_html_for_gmail(raw_body)
            if fixed_body != raw_body:
                new_mailing.write({"body_html": fixed_body})

        # Warn if web.base.url is localhost/127.0.0.1 because Gmail image proxy cannot fetch local URLs
        try:
            ICP = self.env["ir.config_parameter"].sudo()
            base_url = ICP.get_str("web.base.url", "") if hasattr(ICP, "get_str") else ICP.get_param("web.base.url", "")
            if base_url and ("localhost" in base_url or "127.0.0.1" in base_url):
                _logger.warning(
                    "web.base.url is '%s'; external email clients like Gmail cannot load images hosted on localhost.",
                    base_url,
                )
        except Exception:
            pass

        filter_domain = [("list_ids", "in", [self.mailing_list_id.id])]
        if self.exclude_registered:
            filter_domain.append(("x_studio_app_registered", "!=", "Yes"))
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
                    raise UserError(_("Failed to dispatch Step #%d mailing: %s") % (step_number, exc3))

        # Trigger the mail queue manager cron so queued emails are dispatched without waiting
        try:
            mail_cron = self.env.ref("mail.ir_cron_mail_scheduler_action", raise_if_not_found=False)
            if mail_cron:
                mail_cron._trigger()
        except Exception as cron_exc:
            _logger.warning("Could not trigger mail.ir_cron_mail_scheduler_action: %s", cron_exc)

        self._log(_(
            "Step %d: Created and queued mailing '%s' (ID %d) for %d eligible recipients."
        ) % (step_number, new_mailing.subject, new_mailing.id, len(eligible_contacts)))

        return new_mailing

    def _execute_single_step(self, step, cycle_number, now):
        """Execute one vhealth.action.group.step and return (mailing, affected_count, note)."""
        self.ensure_one()
        Contact = self.env["mailing.contact"].sudo()

        if step.action_type == "send_email":
            template = self._find_template_for_step(step, cycle_number)
            eligible_count = len(self._get_target_contacts())
            mailing = self._create_and_send_launch_mailing(cycle_number, template=template)
            note = (
                _("Queued '%s' (Mailing ID %d) for %d recipients.") % (mailing.subject, mailing.id, eligible_count)
                if mailing
                else _("Skipped email (0 eligible recipients).")
            )
            return mailing, eligible_count if mailing else 0, note

        if step.action_type == "update_contact":
            contacts = self._get_target_contacts()
            fname = (step.field_id and step.field_id.name) or step.field_name
            parsed_val = step._parse_field_value(Contact)
            if contacts:
                contacts.write({fname: parsed_val})
            note = _("Updated '%s' = %r for %d contacts.") % (fname, parsed_val, len(contacts))
            self._log(_("Step %d: %s") % (cycle_number, note))
            return False, len(contacts), note

        if step.action_type == "add_to_list":
            contacts = self._get_target_contacts()
            target_list = step.target_mailing_list_id or _get_or_create_list(self.env, step.target_list_name)
            if contacts:
                contacts.write({"list_ids": [(4, target_list.id)]})
            note = _("Added %d contacts to list '%s'.") % (len(contacts), target_list.name)
            self._log(_("Step %d: %s") % (cycle_number, note))
            return False, len(contacts), note

        if step.action_type == "remove_from_list":
            contacts = self._get_target_contacts()
            target_list = (
                step.target_mailing_list_id
                or (step.target_list_name and self.env["mailing.list"].sudo().search([("name", "=", step.target_list_name)], limit=1))
                or self.mailing_list_id
            )
            if contacts and target_list:
                contacts.write({"list_ids": [(3, target_list.id)]})
            list_label = target_list.name if target_list else (step.target_list_name or self.mailing_list_id.name)
            note = _("Removed %d contacts from list '%s'.") % (len(contacts), list_label)
            self._log(_("Step %d: %s") % (cycle_number, note))
            return False, len(contacts), note

        return False, 0, _("No action executed.")

    def _resolve_next_step_index(self, steps, action_group):
        """Determine starting index in `steps` for the next execution cycle."""
        self.ensure_one()
        if self.last_step_id and self.last_step_id in steps:
            return steps.index(self.last_step_id) + 1

        # Legacy in-flight campaign support: campaigns created prior to action_group.step
        if self.current_step > 0 and action_group and action_group.code == "new_group_launch" and len(steps) >= 6:
            legacy_map = {1: 1, 2: 2, 3: 3, 4: 5}
            if self.current_step in legacy_map:
                return legacy_map[self.current_step]
            return len(steps)

        return 0

    def _run_next_step(self):
        """Execute the next configured step(s) in the Action Group and schedule the following cycle."""
        self.ensure_one()
        now = fields.Datetime.now()
        action_group = self._get_effective_action_group()
        steps = list(action_group.step_ids.sorted(key=lambda s: (s.sequence, s.id))) if action_group else []

        if not steps:
            raise UserError(_("Action Group has no steps configured."))

        start_idx = self._resolve_next_step_index(steps, action_group)
        if start_idx >= len(steps):
            self.write({"state": "completed", "next_execution_date": False})
            self._log(_("Campaign already completed all configured steps."))
            return True

        cycle_number = self.current_step + 1
        vals = {"current_step": cycle_number}
        if 1 <= cycle_number <= 5:
            vals[f"step{cycle_number}_date"] = now

        idx = start_idx
        last_executed = False
        next_date = False
        completed = False

        while idx < len(steps):
            step = steps[idx]
            mailing, affected_count, note = self._execute_single_step(step, cycle_number, now)
            last_executed = step

            self.env["vhealth.action.group.schedule.line"].sudo().create({
                "schedule_id": self.id,
                "cycle_number": cycle_number,
                "step_id": step.id,
                "step_name": step.name,
                "action_type": step.action_type,
                "executed_at": now,
                "affected_count": affected_count,
                "mailing_id": mailing.id if mailing else False,
                "note": note,
            })

            if mailing and 1 <= cycle_number <= 4 and not vals.get(f"step{cycle_number}_mailing_id"):
                vals[f"step{cycle_number}_mailing_id"] = mailing.id

            if idx == len(steps) - 1:
                completed = True
                next_date = False
                break
            elif step.delay_days > 0:
                next_date = now + timedelta(days=step.delay_days)
                break
            else:
                # delay_days == 0 chains immediately into the next step in this cycle
                idx += 1

        if last_executed:
            vals["last_step_id"] = last_executed.id

        if completed:
            vals["state"] = "completed"
            vals["next_execution_date"] = False
            self.write(vals)
            self._log(_("Campaign completed successfully."))
        else:
            vals["next_execution_date"] = next_date
            self.write(vals)
            self._log(_("Step %d executed successfully. Next step scheduled for %s.") % (cycle_number, next_date))

        return True

    @api.model
    def _migrate_legacy_action_groups(self):
        """Upgrade helper: link existing schedules and seeded update_contact field_id."""
        ag = self.env["vhealth.action.group"]._get_new_group_launch()
        if not ag:
            return

        # Link ir.model.fields for x_studio_check_for_engagement on the seeded step
        eng_field = self.env["ir.model.fields"].sudo().search([
            ("model", "=", "mailing.contact"),
            ("name", "=", "x_studio_check_for_engagement"),
        ], limit=1)
        if eng_field:
            steps_needing_field = ag.step_ids.filtered(
                lambda s: s.action_type == "update_contact" and not s.field_id and s.field_name == "x_studio_check_for_engagement"
            )
            if steps_needing_field:
                steps_needing_field.sudo().write({"field_id": eng_field.id})

        # Backfill action_group_id and last_step_id on existing schedule records
        steps = list(ag.step_ids.sorted(key=lambda s: (s.sequence, s.id)))
        schedules = self.sudo().search([("action_group_id", "=", False)])
        for sched in schedules:
            write_vals = {"action_group_id": ag.id}
            if not sched.last_step_id and sched.current_step > 0 and len(steps) >= 6:
                step_by_cycle = {1: steps[0], 2: steps[1], 3: steps[2], 4: steps[4], 5: steps[5]}
                target_step = step_by_cycle.get(min(sched.current_step, 5))
                if target_step:
                    write_vals["last_step_id"] = target_step.id
            sched.write(write_vals)

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


class VHealthActionGroupScheduleLine(models.Model):
    _name = "vhealth.action.group.schedule.line"
    _description = "vHealth Action Group Schedule Step Execution"
    _order = "cycle_number asc, id asc"

    schedule_id = fields.Many2one(
        "vhealth.action.group.schedule",
        string="Schedule",
        required=True,
        ondelete="cascade",
        index=True,
    )
    cycle_number = fields.Integer(string="Cycle #", readonly=True)
    step_id = fields.Many2one("vhealth.action.group.step", string="Configured Step", ondelete="set null", readonly=True)
    step_name = fields.Char(string="Action Executed", readonly=True)
    action_type = fields.Selection([
        ("send_email", "Send Email"),
        ("update_contact", "Update Contact Field"),
        ("add_to_list", "Add to Mailing List"),
        ("remove_from_list", "Remove from Mailing List"),
    ], string="Action Type", readonly=True)
    executed_at = fields.Datetime(string="Executed At", readonly=True)
    affected_count = fields.Integer(string="Contacts Affected", readonly=True)
    mailing_id = fields.Many2one("mailing.mailing", string="Generated Mailing", ondelete="set null", readonly=True)
    note = fields.Char(string="Details", readonly=True)
