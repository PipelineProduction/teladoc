from odoo import fields, models
class MailingContactLine(models.Model):
    _name = "x_mailing_contact_line_55a1f"
    _description = "Mailing Contact Line"
    _order = "x_studio_sequence, id"
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_name = fields.Char(string="Description")
    x_mailing_contact_id = fields.Many2one("mailing.contact", string="X Mailing Contact", ondelete="set null")
