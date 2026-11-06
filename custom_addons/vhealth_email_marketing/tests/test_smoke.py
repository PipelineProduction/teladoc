from odoo.tests import TransactionCase, tagged

@tagged("post_install", "-at_install")
class TestVHealthSmoke(TransactionCase):
    def test_models_available(self):
        self.assertIn("x_product_number", self.env)
        self.assertIn("x_eligibility_import", self.env)
        self.assertIn("x_weekly_vhealth_regis", self.env)
        self.assertIn("x_aetna_member_removal", self.env)
        self.assertIn("x_google_sheet_registr", self.env)

    def test_mailing_contact_custom_fields(self):
        Contact = self.env["mailing.contact"]
        self.assertIn("x_studio_aetna_access_code", Contact._fields)
        self.assertIn("x_studio_cohort_group", Contact._fields)
        self.assertIn("x_studio_vhealth_contact", Contact._fields)
        self.assertIn("x_studio_products_2", Contact._fields)

    def test_views_loaded(self):
        form_view = self.env.ref("vhealth_email_marketing.mailing_contact_view_form_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(form_view, "Inherited form view should be loaded")
        list_view = self.env.ref("vhealth_email_marketing.mailing_contact_view_tree_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(list_view, "Inherited list view should be loaded")

