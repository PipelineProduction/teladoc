from odoo import fields, models
class VhelthContacts(models.Model):
    _name = "x_vhelth_contacts"
    _description = "Vhelth Contacts"
    _order = "x_studio_sequence, id desc"
    x_name = fields.Char(string="Description")
    x_active = fields.Boolean(string="Active", default=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_date_field_8ss_1k280l2am = fields.Date(string="New Date")
