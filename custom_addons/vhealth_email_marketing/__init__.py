from . import models
from . import wizard

def post_init_hook(*args, **kwargs):
    if args and hasattr(args[0], 'cr'):
        env = args[0]
    elif len(args) >= 2:
        from odoo import api, SUPERUSER_ID
        env = api.Environment(args[0], SUPERUSER_ID, {})
    else:
        return

    Product = env['x_product_number'].sudo()
    mapping = {
        "001": ("aetna-prod-001", 10),
        "002": ("aetna-prod-002", 20),
        "004": ("aetna-prod-004", 30),
        "007": ("aetna-prod-007", 40),
    }
    for name, (code, seq) in mapping.items():
        rec = Product.search([("x_name", "=", name)], limit=1)
        if rec:
            if not rec.x_studio_product_value:
                rec.write({"x_studio_product_value": code})
        else:
            Product.create({"x_name": name, "x_studio_product_value": code, "x_studio_sequence": seq})
