import json, logging
import requests
from odoo import api, fields, models
_logger = logging.getLogger(__name__)

class GoogleSheetRegistration(models.Model):
    _name = "x_google_sheet_registr"
    _description = "Google Sheet Registration Queue"
    _order = "id"
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

    @api.model
    def _cron_send_registration_queue(self):
        endpoint = self.env["ir.config_parameter"].sudo().get_param("vhealth_email_marketing.google_sheet_webhook_url")
        if not endpoint:
            _logger.warning("vHealth Google Sheets webhook URL is not configured.")
            return
        for rec in self.search([("x_studio_sent", "=", False), ("retry_count", "<", 8)], limit=50):
            payload = {"email": rec.x_studio_email, "registration_date": rec.x_studio_registration_date or "", "prefix_phone": rec.x_studio_prefix_phone or "", "access_code": rec.x_studio_access_code or "", "queue_id": rec.id}
            try:
                response = requests.post(endpoint, json=payload, timeout=20)
                response.raise_for_status()
                try: body = response.json()
                except Exception: body = {}
                if body.get("success") is False:
                    raise ValueError(body.get("error") or "Webhook returned success=false")
                rec.write({"x_studio_sent": True, "last_error": False})
            except Exception as exc:
                rec.write({"retry_count": rec.retry_count + 1, "last_error": str(exc)})
                _logger.exception("Google Sheets queue record %s failed", rec.id)
