from odoo.tests import TransactionCase, tagged

@tagged("post_install", "-at_install")
class TestVHealthSmoke(TransactionCase):
    def test_product_number_model_available(self):
        self.assertIn("x_product_number", self.env)
