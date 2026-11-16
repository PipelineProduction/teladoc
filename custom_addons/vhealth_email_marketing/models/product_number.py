from odoo import api, fields, models

class ProductNumber(models.Model):
    _name = "x_product_number"
    _description = "Product Number"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "x_studio_sequence, x_name"
    _rec_name = "x_name"

    x_name = fields.Char(string="Description", required=True)
    x_active = fields.Boolean(string="Active", default=True)
    x_studio_sequence = fields.Integer(string="Sequence", default=10)
    x_studio_product_value = fields.Char(string="Product Value", index=True)

    @api.depends("x_name", "x_studio_product_value")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.x_name or rec.x_studio_product_value or ("%s,%s" % (rec._name, rec.id))
