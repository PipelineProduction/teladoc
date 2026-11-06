from odoo import fields, models
class ProductNumber(models.Model):
    _name = "x_product_number"
    _description = "Product Number"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "x_studio_sequence, x_name"
    x_name = fields.Char(string="Description")
    x_active = fields.Boolean(string="Active", default=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_product_value = fields.Char(string="Product Value", index=True)
