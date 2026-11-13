from odoo import api, fields, models

class MailingContactLine(models.Model):
    _name = "x_mailing_contact_line_55a1f"
    _description = "Mailing Contact Line"
    _order = "x_studio_sequence, id"
    _rec_name = "x_name"

    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_name = fields.Char(string="Description")
    x_mailing_contact_id = fields.Many2one("mailing.contact", string="Contact", ondelete="set null")

    @api.depends("x_name")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.x_name or ("%s,%s" % (rec._name, rec.id))
