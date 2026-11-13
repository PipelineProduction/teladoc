import base64, csv, io
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AetnaMemberRemoval(models.Model):
    _name = "x_aetna_member_removal"
    _description = "AETNA Member Removal"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "x_studio_sequence, id desc"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True)
    x_active = fields.Boolean(default=True)
    x_studio_partner_id = fields.Many2one("res.partner", string="Related Partner (legacy Studio field)")
    x_studio_partner_phone = fields.Char(string="Phone", related="x_studio_partner_id.phone", readonly=True)
    x_studio_partner_email = fields.Char(string="Email", related="x_studio_partner_id.email", readonly=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_import_file = fields.Binary(string="Import File", attachment=True)
    x_studio_import_file_filename = fields.Char(string="Filename for import file")
    x_studio_import_date = fields.Datetime(string="Import Date")
    x_studio_import_status = fields.Selection([("Draft", "Draft"), ("Processing", "Processing"), ("Completed", "Completed"), ("Error", "Error")], string="Import Status", default="Draft", required=True)
    x_studio_total_records = fields.Integer(string="Total Records", readonly=True)
    x_studio_removed_contacts = fields.Integer(string="Removed Contacts", readonly=True)
    x_studio_not_found = fields.Integer(string="Not Found", readonly=True)
    x_studio_error_message = fields.Text(string="Error Message", readonly=True)
    x_studio_aetna_mailing_list = fields.Many2one("mailing.list", string="AETNA Mailing List")
    confirm_permanent_delete = fields.Boolean(string="I confirm permanent contact deletion")

    @api.depends("x_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.x_name or _("New")

    def action_process_removal(self):
        for rec in self:
            if not rec.x_studio_import_file:
                raise UserError(_("Upload the AETNA removal CSV first."))
            if not rec.confirm_permanent_delete:
                raise UserError(_("Tick the permanent-deletion confirmation before continuing."))
            try:
                raw = base64.b64decode(rec.x_studio_import_file)
                text = raw.decode("utf-8-sig")
                reader = csv.DictReader(io.StringIO(text))
                if not reader.fieldnames:
                    raise UserError(_("The CSV is empty or has no header row."))
                headers = {h.strip().lower(): h for h in reader.fieldnames if h}
                email_col = headers.get("email") or headers.get("email address")
                status_col = headers.get("aetna member status") or headers.get("status")
                if not email_col or not status_col:
                    raise UserError(_("CSV must contain Email and AETNA Member Status columns."))
                rows = list(reader); removed = 0; not_found = 0; errors = []
                Contact = self.env["mailing.contact"].sudo()
                for line_no, row in enumerate(rows, start=2):
                    email = (row.get(email_col) or "").strip().lower()
                    status = (row.get(status_col) or "").strip().lower()
                    if status != "remove":
                        continue
                    if not email:
                        errors.append("Row %s: missing email" % line_no); continue
                    contacts = Contact.search([("email", "=ilike", email)])
                    if not contacts:
                        not_found += 1; continue
                    try:
                        with self.env.cr.savepoint():
                            contacts.unlink()
                        removed += len(contacts)
                    except Exception as exc:
                        errors.append("Row %s (%s): %s" % (line_no, email, str(exc)))
                rec.write({"x_studio_import_status": "Completed" if not errors else "Error", "x_studio_import_date": fields.Datetime.now(), "x_studio_total_records": len(rows), "x_studio_removed_contacts": removed, "x_studio_not_found": not_found, "x_studio_error_message": "\n".join(errors), "confirm_permanent_delete": False})
            except Exception as exc:
                rec.write({"x_studio_import_status": "Error", "x_studio_error_message": str(exc)})
                if isinstance(exc, UserError): raise
        return True
