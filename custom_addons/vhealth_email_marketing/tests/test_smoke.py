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
        self.assertIn("studio_page_78d_1k07lgra7", form_view.arch, "Studio page should match online setup")
        self.assertNotIn("x_studio_char_field_4r7_1k0uuh7ae", form_view.arch, "Artifact text fields should not be in form view")
        list_view = self.env.ref("vhealth_email_marketing.mailing_contact_view_tree_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(list_view, "Inherited list view should be loaded")

    def test_product_number_rec_name_and_display(self):
        Product = self.env["x_product_number"]
        self.assertEqual(Product._rec_name, "x_name", "Rec name should be x_name to display 001/002 labels")
        p = Product.create({"x_name": "001", "x_studio_product_value": "aetna-prod-001"})
        self.assertEqual(p.display_name, "001", "Display name should resolve to x_name (001)")

        Elig = self.env["x_eligibility_import"]
        self.assertEqual(Elig._rec_name, "x_name", "Eligibility import rec_name should be x_name")
        e = Elig.new({})
        self.assertEqual(e.display_name, "New", "Unsaved record display name should be 'New'")

