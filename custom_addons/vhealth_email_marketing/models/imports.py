import base64, csv, io, logging, re
from datetime import datetime, date
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

LIVE_LIST_NAME = "All Live Contacts [SEND TO ALL]"
REGISTERED_LIST_NAME = "All REGISTERED members"
COHORT_LISTS = {"TH": "All Contacts - TH", "TH + MH": "All Contacts - TH + MH", "PC": "All Contacts - PC", "MH": "All Contacts - MH"}
PRODUCT_COHORT = {
    "aetna-prod-001": "TH + MH", "001": "TH + MH",
    "aetna-prod-002": "TH", "002": "TH",
    "aetna-prod-004": "MH", "004": "MH",
    "aetna-prod-007": "PC", "007": "PC",
}

def _read_csv(binary):
    try: text = base64.b64decode(binary).decode("utf-8-sig")
    except Exception as exc: raise UserError(_("Could not decode CSV: %s") % exc)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames: raise UserError(_("CSV has no header row."))
    return [{(k or "").strip(): (v or "").strip() for k, v in row.items()} for row in reader]

def _get(row, *keys):
    lookup = {k.strip().lower(): v for k, v in row.items()}
    for key in keys:
        value = lookup.get(key.lower())
        if value: return value.strip()
    return ""

def _as_date(value):
    if not value: return False
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"):
        try: return datetime.strptime(value[:10], fmt).date()
        except ValueError: pass
    raise ValueError("Invalid date: %s" % value)

class EligibilityImport(models.Model):
    _name = "x_eligibility_import"
    _description = "Eligibility Import"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "x_studio_sequence, id desc"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True)
    x_active = fields.Boolean(default=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_import_file = fields.Binary(string="Import File", attachment=True)
    x_studio_import_file_filename = fields.Char(string="Filename for import file")
    x_studio_import_status = fields.Selection([("Draft", "Draft"), ("Processing", "Processing"), ("Completed", "Completed"), ("Error", "Error")], string="Import Status", default="Draft", required=True)
    x_studio_total_records = fields.Integer(string="Total Records", readonly=True)
    x_studio_processed_records = fields.Integer(string="Processed Records", readonly=True)
    x_studio_created_contacts = fields.Integer(string="Created Contacts", readonly=True)
    x_studio_updated_contacts = fields.Integer(string="Updated Contacts", readonly=True)
    x_studio_error_message = fields.Text(string="Error Message", readonly=True)

    @api.depends("x_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.x_name or _("New")

    def action_process_import(self):
        for rec in self:
            if not rec.x_studio_import_file: raise UserError(_("Upload an eligibility CSV first."))
            rows = _read_csv(rec.x_studio_import_file); created = updated = processed = 0; errors = []
            rec.write({"x_studio_import_status": "Processing", "x_studio_total_records": len(rows), "x_studio_processed_records": 0, "x_studio_created_contacts": 0, "x_studio_updated_contacts": 0, "x_studio_error_message": False})
            Contact = self.env["mailing.contact"].sudo(); List = self.env["mailing.list"].sudo()
            live = List.search([("name", "=", LIVE_LIST_NAME)], limit=1)
            for index, row in enumerate(rows, start=2):
                try:
                    with self.env.cr.savepoint():
                        email = _get(row, "Email", "ID").lower()
                        if not email: raise ValueError("Email is required")
                        cohort = _get(row, "Cohort Group")
                        vals = {"email": email, "x_studio_first_name": _get(row, "First Name"), "x_studio_last_name": _get(row, "Last Name"), "x_studio_aetna_language": _get(row, "Aetna Language", "Language") or "English", "x_studio_aetna_access_code": _get(row, "Aetna Access Code"), "x_studio_member_effective_date": _as_date(_get(row, "Member Effective Date")), "x_studio_cohort_group": cohort or False, "x_studio_launch_date": _as_date(_get(row, "Launch Date")), "x_studio_vhealth_contact": True}
                        vals = {k:v for k,v in vals.items() if v is not None}
                        contact = Contact.search([("email", "=ilike", email)], limit=1)
                        if contact: contact.write(vals); updated += 1
                        else: contact = Contact.create(vals); created += 1
                        launch = vals.get("x_studio_launch_date") or fields.Date.context_today(rec)
                        eligible = List.search([("name", "=", "Eligible Member %s" % launch)], limit=1)
                        if not eligible: eligible = List.create({"name": "Eligible Member %s" % launch})
                        target_lists = eligible | live
                        if cohort in COHORT_LISTS:
                            target_lists |= List.search([("name", "=", COHORT_LISTS[cohort])], limit=1)
                            old_cohorts = List.search([("name", "in", list(COHORT_LISTS.values()))])
                            contact.write({"list_ids": [(3, x.id) for x in (old_cohorts - target_lists)]})
                        contact.write({"list_ids": [(4, x.id) for x in target_lists]})
                    processed += 1
                except Exception as exc: errors.append("Row %s: %s" % (index, exc)); _logger.exception("Eligibility import row failed")
                rec.write({"x_studio_processed_records": processed, "x_studio_created_contacts": created, "x_studio_updated_contacts": updated})
            rec.write({"x_studio_import_status": "Error" if errors else "Completed", "x_studio_error_message": "\n".join(errors)})
        return True

class WeeklyVhealthRegistration(models.Model):
    _name = "x_weekly_vhealth_regis"
    _description = "Weekly vHealth Registration Import"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "x_studio_sequence, id desc"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", required=True)
    x_active = fields.Boolean(default=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_import_file = fields.Binary(string="Import File", attachment=True)
    x_studio_import_file_filename = fields.Char(string="Filename for import file")
    x_studio_import_status = fields.Selection([("draft", "draft"), ("processing", "processing"), ("completed", "completed"), ("error", "error")], string="Import Status", default="draft", required=True)
    x_studio_total_records = fields.Integer(string="Total Records", readonly=True)
    x_studio_processed_records = fields.Integer(string="Processed Records", readonly=True)
    x_studio_created_contacts = fields.Integer(string="Created Contacts", readonly=True)
    x_studio_updated_contacts = fields.Integer(string="Updated Contacts", readonly=True)
    x_studio_error_records = fields.Integer(string="Error Records", readonly=True)
    x_studio_error_message = fields.Text(string="Error Message", readonly=True)
    x_studio_import_result = fields.Text(string="Import Result", readonly=True)
    x_studio_google_sheet_payload = fields.Text(string="Google Sheet Payload", readonly=True)

    @api.depends("x_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.x_name or _("New")

    def action_process_import(self):
        for rec in self:
            if not rec.x_studio_import_file: raise UserError(_("Upload the weekly registration CSV first."))
            rows = _read_csv(rec.x_studio_import_file); created = updated = processed = 0; errors = []; queue_ids = []
            rec.write({"x_studio_import_status": "processing", "x_studio_total_records": len(rows), "x_studio_processed_records": 0, "x_studio_created_contacts": 0, "x_studio_updated_contacts": 0, "x_studio_error_records": 0, "x_studio_error_message": False})
            Contact = self.env["mailing.contact"].sudo(); List = self.env["mailing.list"].sudo(); Product = self.env["x_product_number"].sudo()
            registered = List.search([("name", "=", REGISTERED_LIST_NAME)], limit=1); live = List.search([("name", "=", LIVE_LIST_NAME)], limit=1)
            for index, row in enumerate(rows, start=2):
                try:
                    with self.env.cr.savepoint():
                        email = _get(row, "Client email", "Email").lower()
                        if not email: raise ValueError("Client email is required")
                        code_raw = _get(row, "Product Code")
                        codes = [c.strip().lower() for c in re.split(r'[,;]+', code_raw) if c.strip()]
                        if not codes: raise ValueError("Product Code is required")
                        products = self.env["x_product_number"]
                        cohorts = []
                        for code in codes:
                            c = PRODUCT_COHORT.get(code)
                            p = Product.search(["|", ("x_studio_product_value", "=", code), ("x_name", "=", code)], limit=1)
                            if not p: raise ValueError("Product code %s is missing from Product Number setup" % code)
                            products |= p
                            if not c and p.x_studio_product_value:
                                c = PRODUCT_COHORT.get(p.x_studio_product_value.lower())
                            if c: cohorts.append(c)
                        if "TH + MH" in cohorts or ("TH" in cohorts and "MH" in cohorts): cohort = "TH + MH"
                        elif cohorts: cohort = cohorts[0]
                        else: raise ValueError("Unknown Product Code %r" % code_raw)
                        country = _get(row, "Client Country")
                        first = _get(row, "Client Name"); surname = _get(row, "Client Surname")
                        # Client Name in source may contain the surname as its final token; avoid duplicating it.
                        if surname and first.lower().endswith(" " + surname.lower()): first = first[:-(len(surname)+1)].strip()
                        vals = {"email": email, "x_studio_aetna_access_code": _get(row, "Client Code"), "x_studio_first_name": first, "x_studio_last_name": surname, "x_studio_gender": _get(row, "Client Gender"), "x_studio_aetna_language": _get(row, "Client Language"), "x_studio_dob": _as_date(_get(row, "Client DOB")), "x_studio_registration_date": _as_date(_get(row, "Client Created Date")), "x_studio_vhealth_contact": True, "x_studio_app_registered": "Yes", "x_studio_app_unique_registered": "Yes", "x_studio_location_us_or_canada": country.strip().lower() in ("us", "usa", "united states", "canada"), "x_studio_aetna_status_live": True, "x_studio_cohort_group": cohort, "x_studio_products_2": [(4, p.id) for p in products]}
                        vals = {k:v for k,v in vals.items() if v is not None and v != ""}
                        contact = Contact.search([("email", "=ilike", email)], limit=1)
                        if contact: contact.write(vals); updated += 1
                        else: contact = Contact.create(vals); created += 1
                        target = List.search([("name", "=", COHORT_LISTS[cohort])], limit=1)
                        to_add = registered | live | target
                        contact.write({"list_ids": [(4, x.id) for x in to_add]})
                        Queue = self.env["x_google_sheet_registr"].sudo()
                        reg_date = _get(row, "Client Created Date")
                        prefix_phone = _get(row, "Client Prefix & Phone")
                        access_code = _get(row, "Client Code")
                        # Idempotency guard: avoid adding the same unsent registration payload again on re-import.
                        queue = Queue.search([("x_studio_email", "=ilike", email), ("x_studio_registration_date", "=", reg_date), ("x_studio_access_code", "=", access_code), ("x_studio_sent", "=", False)], limit=1)
                        if not queue:
                            queue = Queue.create({"x_studio_email": email, "x_studio_registration_date": reg_date, "x_studio_prefix_phone": prefix_phone, "x_studio_access_code": access_code})
                        queue_ids.append(queue.id)
                    processed += 1
                except Exception as exc: errors.append("Row %s (%s): %s" % (index, _get(row, "Client email"), exc)); _logger.exception("Weekly registration row failed")
                rec.write({"x_studio_processed_records": processed, "x_studio_created_contacts": created, "x_studio_updated_contacts": updated, "x_studio_error_records": len(errors)})
            rec.write({"x_studio_import_status": "error" if errors else "completed", "x_studio_error_message": "\n".join(errors), "x_studio_import_result": "Processed %s of %s rows; created %s; updated %s; errors %s." % (processed, len(rows), created, updated, len(errors)), "x_studio_google_sheet_payload": str(queue_ids)})
        return True
