import json, logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

DEFAULT_WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbze84DjgKTMAGVuDpepchYgXrPzxmF0LwOmwcUEobVBuqR1EZvZZGyZZCS-ueG5OF6k/exec"

class GoogleSheetRegistration(models.Model):
    _name = "x_google_sheet_registr"
    _description = "Google Sheet Registration Queue"
    _order = "id desc"
    _rec_name = "x_name"

    x_name = fields.Char(string="Name", default="Registration")
    x_active = fields.Boolean(default=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_email = fields.Char(string="Email", required=True, index=True)
    x_studio_registration_date = fields.Char(string="Registration Date")
    x_studio_prefix_phone = fields.Char(string="Prefix & Phone")
    x_studio_access_code = fields.Char(string="Access Code")
    x_studio_sent = fields.Boolean(string="Sent", default=False, index=True)
    retry_count = fields.Integer(default=0)
    last_error = fields.Text()

    @api.depends("x_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.x_name or "Registration"

    def _get_endpoint(self):
        Config = self.env["ir.config_parameter"].sudo()
        param = ""
        # Support Odoo 20 (get_str) as well as older Odoo (get_param)
        if hasattr(Config, "get_str"):
            param = Config.get_str("vhealth_email_marketing.google_sheet_webhook_url", default="")
        elif hasattr(Config, "get_param"):
            param = Config.get_param("vhealth_email_marketing.google_sheet_webhook_url", default="")
        if not param:
            rec = Config.search([("key", "=", "vhealth_email_marketing.google_sheet_webhook_url")], limit=1)
            if rec and rec.value:
                param = rec.value
        return (param or DEFAULT_WEBHOOK_URL).strip()

    def _send_record(self, endpoint=None):
        self.ensure_one()
        url = endpoint or self._get_endpoint()
        if not url:
            raise UserError(_("Google Sheets webhook URL is not configured."))
        # Format registration date as YYYY-MM-DD to match the spreadsheet format
        reg_date = (self.x_studio_registration_date or "").split(" ")[0].strip()
        payload = {
            "email": self.x_studio_email,
            "registration_date": reg_date,
            "prefix_phone": self.x_studio_prefix_phone or "",
            "access_code": self.x_studio_access_code or "",
            "queue_id": self.id,
        }
        response = requests.post(url, json=payload, timeout=25)
        response.raise_for_status()
        try:
            body = response.json()
        except Exception:
            body = {}
        if body.get("success") is False:
            raise ValueError(body.get("error") or "Webhook returned success=false")
        self.write({"x_studio_sent": True, "last_error": False})
        return body

    def action_send_now(self):
        self.ensure_one()
        try:
            self._send_record()
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Google Sheets"),
                    "message": _("Sent %s successfully to Google Sheets!") % self.x_studio_email,
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as exc:
            self.write({"retry_count": self.retry_count + 1, "last_error": str(exc)})
            raise UserError(_("Failed to send to Google Sheets: %s") % exc)

    def action_send_selected(self):
        endpoint = self._get_endpoint()
        count = 0
        errors = []
        for rec in self:
            try:
                with self.env.cr.savepoint():
                    rec._send_record(endpoint=endpoint)
                count += 1
            except Exception as exc:
                errors.append(f"{rec.x_studio_email}: {exc}")
                try:
                    with self.env.cr.savepoint():
                        rec.write({"retry_count": rec.retry_count + 1, "last_error": str(exc)})
                except Exception:
                    pass
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Google Sheets"),
                "message": _("Sent %s records. Errors: %s") % (count, len(errors)),
                "type": "success" if not errors else "warning",
                "sticky": bool(errors),
            },
        }

    def action_process_queue(self):
        success_count, error_count = self._cron_send_registration_queue(limit=500)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Google Sheets Sync"),
                "message": _("Processed pending queue: %s sent successfully, %s errors.") % (success_count, error_count),
                "type": "success" if error_count == 0 else "warning",
                "sticky": False,
            },
        }

    @api.model
    def _cron_send_registration_queue(self, limit=100):
        endpoint = self._get_endpoint()
        if not endpoint:
            _logger.warning("vHealth Google Sheets webhook URL is not configured.")
            return 0, 0
        success_count = 0
        error_count = 0
        domain = [("x_studio_sent", "=", False), ("retry_count", "<", 8)]
        records = self.search(domain, limit=limit)
        for rec in records:
            try:
                with self.env.cr.savepoint():
                    rec._send_record(endpoint=endpoint)
                success_count += 1
            except Exception as exc:
                error_count += 1
                try:
                    with self.env.cr.savepoint():
                        rec.write({"retry_count": rec.retry_count + 1, "last_error": str(exc)})
                except Exception:
                    pass
                _logger.exception("Google Sheets queue record %s failed", rec.id)
        return success_count, error_count
