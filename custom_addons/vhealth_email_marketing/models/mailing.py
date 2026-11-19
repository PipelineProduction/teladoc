import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)


class MailingMailing(models.Model):
    _inherit = "mailing.mailing"

    vhealth_action_group_schedule_id = fields.Many2one(
        "vhealth.action.group.schedule",
        string="vHealth Action Group Schedule",
        index=True,
        ondelete="set null",
    )
    vhealth_drip_step = fields.Integer(string="vHealth Drip Step", default=0)

    def _get_recipients_domain(self):
        """Ensure contacts who have registered are strictly excluded from vHealth drip campaign mailings."""
        domain = super()._get_recipients_domain()
        if self.vhealth_action_group_schedule_id or self.env.context.get("vhealth_exclude_registered"):
            try:
                from odoo.fields import Domain
                domain = domain & Domain([("x_studio_app_registered", "!=", "Yes")])
            except ImportError:
                from odoo.osv import expression
                domain = expression.AND([domain, [("x_studio_app_registered", "!=", "Yes")]])
        return domain
