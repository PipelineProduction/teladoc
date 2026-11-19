from odoo.tests import TransactionCase, tagged
from odoo import fields

@tagged("post_install", "-at_install")
class TestVHealthSmoke(TransactionCase):
    def test_models_available(self):
        self.assertIn("x_product_number", self.env)
        self.assertIn("x_eligibility_import", self.env)
        self.assertIn("x_weekly_vhealth_regis", self.env)
        self.assertIn("x_aetna_member_removal", self.env)
        self.assertIn("x_google_sheet_registr", self.env)
        self.assertIn("vhealth.action.group.schedule", self.env)
        self.assertIn("vhealth.schedule.action.group.wizard", self.env)

    def test_mailing_contact_custom_fields(self):
        Contact = self.env["mailing.contact"]
        self.assertIn("x_studio_aetna_access_code", Contact._fields)
        self.assertIn("x_studio_cohort_group", Contact._fields)
        self.assertIn("x_studio_vhealth_contact", Contact._fields)
        self.assertIn("x_studio_products_2", Contact._fields)
        self.assertIn("x_studio_check_for_engagement", Contact._fields)
        self.assertIn("x_studio_app_registered", Contact._fields)

    def test_views_loaded(self):
        form_view = self.env.ref("vhealth_email_marketing.mailing_contact_view_form_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(form_view, "Inherited form view should be loaded")
        self.assertIn("studio_page_78d_1k07lgra7", form_view.arch, "Studio page should match online setup")
        self.assertNotIn("x_studio_char_field_4r7_1k0uuh7ae", form_view.arch, "Artifact text fields should not be in form view")
        list_view = self.env.ref("vhealth_email_marketing.mailing_contact_view_tree_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(list_view, "Inherited list view should be loaded")

        # Action Group views
        ag_list = self.env.ref("vhealth_email_marketing.view_vhealth_action_group_schedule_list", raise_if_not_found=False)
        self.assertTrue(ag_list, "Action group schedule list view should be loaded")
        ag_form = self.env.ref("vhealth_email_marketing.view_vhealth_action_group_schedule_form", raise_if_not_found=False)
        self.assertTrue(ag_form, "Action group schedule form view should be loaded")
        wiz_form = self.env.ref("vhealth_email_marketing.view_vhealth_schedule_action_group_wizard_form", raise_if_not_found=False)
        self.assertTrue(wiz_form, "Schedule action group wizard form view should be loaded")
        ml_form = self.env.ref("vhealth_email_marketing.mailing_list_view_form_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(ml_form, "Inherited mailing list form view should be loaded")

    def test_product_number_rec_name_and_display(self):
        Product = self.env["x_product_number"]
        self.assertEqual(Product._rec_name, "x_name", "Rec name should be x_name to display 001/002 labels")
        p = Product.search([("x_name", "=", "001")], limit=1)
        if not p:
            p = Product.create({"x_name": "001", "x_studio_product_value": "aetna-prod-001"})
        self.assertEqual(p.display_name, "001", "Display name should resolve to x_name (001)")

        Elig = self.env["x_eligibility_import"]
        self.assertEqual(Elig._rec_name, "x_name", "Eligibility import rec_name should be x_name")
        e = Elig.new({})
        self.assertEqual(e.display_name, "New", "Unsaved record display name should be 'New'")

    def test_eligibility_import_flexible_helpers(self):
        from ..models.imports import _get
        row = {
            "email": "test@business.co.uk",
            "x_studio_first_name": "Test",
            "x_studio_last_name": "User",
            "x_studio_cohort_group": "TH",
        }
        self.assertEqual(_get(row, "x_studio_first_name", "first name"), "Test")
        self.assertEqual(_get(row, "x_studio_cohort_group", "cohort group"), "TH")

    def test_csv_binary_decoding_variants(self):
        import base64
        from ..models.imports import _decode_binary_to_text, _read_csv
        raw_csv = "email,Name\nuser@example.com,John Doe\n"
        # Test raw bytes (Odoo 18/20 BinaryValue)
        self.assertIn("user@example.com", _decode_binary_to_text(raw_csv.encode("utf-8")))
        # Test base64 bytes (legacy Odoo Binary)
        self.assertIn("user@example.com", _decode_binary_to_text(base64.b64encode(raw_csv.encode("utf-8"))))
        # Test base64 str
        self.assertIn("user@example.com", _decode_binary_to_text(base64.b64encode(raw_csv.encode("utf-8")).decode("ascii")))
        # Test _read_csv parse
        rows = _read_csv(raw_csv.encode("utf-8"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email"], "user@example.com")

    def test_google_sheet_queue_endpoint_and_payload(self):
        Queue = self.env["x_google_sheet_registr"]
        self.assertTrue(Queue._get_endpoint().startswith("https://script.google.com"))
        rec = Queue.new({
            "x_studio_email": "test@example.com",
            "x_studio_registration_date": "2026-11-10 00:00:00",
            "x_studio_prefix_phone": "819013748795",
            "x_studio_access_code": "FSBP",
        })
        reg_date = (rec.x_studio_registration_date or "").split(" ")[0].strip()
        self.assertEqual(reg_date, "2026-11-10")

    def test_action_group_drip_campaign_flow(self):
        List = self.env["mailing.list"]
        Contact = self.env["mailing.contact"]
        Mailing = self.env["mailing.mailing"]

        # Ensure mock templates exist
        for i in range(1, 5):
            tname = f"vHealth - Launch #{i} (2025)"
            tmpl = Mailing.search([("name", "=ilike", tname)], limit=1)
            if not tmpl:
                tmpl = Mailing.create({
                    "name": tname,
                    "subject": tname,
                    "is_template": True,
                    "body_html": f"<p>Body for Launch {i}</p>",
                    "body_arch": f"<p>Body for Launch {i}</p>",
                })

        # Create test mailing list
        mlist = List.create({"name": "Eligible Member 2026-11-04"})

        # Create contacts
        c1 = Contact.create({
            "name": "Eligible Unregistered 1",
            "email": "elig1@example.com",
            "list_ids": [(4, mlist.id)],
            "x_studio_app_registered": "No",
        })
        c2 = Contact.create({
            "name": "Eligible Unregistered 2",
            "email": "elig2@example.com",
            "list_ids": [(4, mlist.id)],
            "x_studio_app_registered": False,
        })
        c3 = Contact.create({
            "name": "Already Registered Contact",
            "email": "reg@example.com",
            "list_ids": [(4, mlist.id)],
            "x_studio_app_registered": "Yes",
        })

        # Test wizard summary computation
        Wizard = self.env["vhealth.schedule.action.group.wizard"]
        wizard = Wizard.new({
            "mailing_list_id": mlist.id,
            "action_group": "new_group_launch",
            "schedule_type": "now",
        })
        wizard._compute_list_summary()
        self.assertEqual(wizard.total_contacts, 3)
        self.assertEqual(wizard.registered_contacts, 1)
        self.assertEqual(wizard.active_contacts, 2)
        self.assertIn("Eligible Member 2026-11-04", wizard.summary_html)

        # Create campaign
        Schedule = self.env["vhealth.action.group.schedule"]
        campaign = Schedule.create({
            "mailing_list_id": mlist.id,
            "action_group": "new_group_launch",
            "schedule_type": "now",
        })

        # Start campaign -> runs Step 1 immediately
        campaign.action_start()
        self.assertEqual(campaign.state, "running")
        self.assertEqual(campaign.current_step, 1)
        self.assertTrue(campaign.step1_date)
        self.assertTrue(campaign.next_execution_date)

        # Step 2
        campaign.action_run_step_now()
        self.assertEqual(campaign.current_step, 2)
        self.assertTrue(campaign.step2_date)

        # Step 3
        campaign.action_run_step_now()
        self.assertEqual(campaign.current_step, 3)
        self.assertTrue(campaign.step3_date)

        # Step 4: Engagement flag check + Launch #4
        self.assertFalse(c1.x_studio_check_for_engagement)
        self.assertFalse(c2.x_studio_check_for_engagement)
        campaign.action_run_step_now()
        self.assertEqual(campaign.current_step, 4)
        self.assertTrue(campaign.step4_date)
        self.assertTrue(c1.x_studio_check_for_engagement, "Unregistered contact c1 should have check_for_engagement = True")
        self.assertTrue(c2.x_studio_check_for_engagement, "Unregistered contact c2 should have check_for_engagement = True")

        # Step 5: Add unregistered contacts to 'All non registered members' list
        non_reg_list = List.search([("name", "=", "All non registered members")], limit=1)
        campaign.action_run_step_now()
        self.assertEqual(campaign.current_step, 5)
        self.assertEqual(campaign.state, "completed")
        self.assertFalse(campaign.next_execution_date)

        non_reg_list = List.search([("name", "=", "All non registered members")], limit=1)
        self.assertTrue(non_reg_list, "'All non registered members' list should exist")
        self.assertIn(non_reg_list.id, c1.list_ids.ids)
        self.assertIn(non_reg_list.id, c2.list_ids.ids)
        self.assertNotIn(non_reg_list.id, c3.list_ids.ids, "Registered contact c3 must NOT be added to non-registered list")
