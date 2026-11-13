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

    def init(self):
        super().init()
        mapping = {
            "001": ("aetna-prod-001", 10),
            "002": ("aetna-prod-002", 20),
            "004": ("aetna-prod-004", 30),
            "007": ("aetna-prod-007", 40),
        }
        total_count = self.search_count([])
        for name, (code, seq) in mapping.items():
            rec = self.search([("x_name", "=", name)], limit=1)
            if rec:
                if not rec.x_studio_product_value:
                    rec.x_studio_product_value = code
            elif total_count == 0:
                self.create({"x_name": name, "x_studio_product_value": code, "x_studio_sequence": seq})
