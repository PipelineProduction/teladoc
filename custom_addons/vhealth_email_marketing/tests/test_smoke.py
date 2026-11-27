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
        self.assertIn("vhealth.action.group", self.env)
        self.assertIn("vhealth.action.group.step", self.env)
        self.assertIn("vhealth.action.group.schedule", self.env)
        self.assertIn("vhealth.action.group.schedule.line", self.env)
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
        ag_master_list = self.env.ref("vhealth_email_marketing.view_vhealth_action_group_list", raise_if_not_found=False)
        self.assertTrue(ag_master_list, "Action group master list view should be loaded")
        ag_master_form = self.env.ref("vhealth_email_marketing.view_vhealth_action_group_form", raise_if_not_found=False)
        self.assertTrue(ag_master_form, "Action group master form view should be loaded")
        ag_list = self.env.ref("vhealth_email_marketing.view_vhealth_action_group_schedule_list", raise_if_not_found=False)
        self.assertTrue(ag_list, "Action group schedule list view should be loaded")
        ag_form = self.env.ref("vhealth_email_marketing.view_vhealth_action_group_schedule_form", raise_if_not_found=False)
        self.assertTrue(ag_form, "Action group schedule form view should be loaded")
        wiz_form = self.env.ref("vhealth_email_marketing.view_vhealth_schedule_action_group_wizard_form", raise_if_not_found=False)
        self.assertTrue(wiz_form, "Schedule action group wizard form view should be loaded")
        ml_form = self.env.ref("vhealth_email_marketing.mailing_list_view_form_inherit_vhealth", raise_if_not_found=False)
        self.assertTrue(ml_form, "Inherited mailing list form view should be loaded")

        # Menu structure verification
        m_root = self.env.ref("vhealth_email_marketing.menu_vhealth_process_root", raise_if_not_found=False)
        self.assertTrue(m_root, "Root menu should exist")
        self.assertEqual(m_root.name, "vHealth Process")

        m_proc = self.env.ref("vhealth_email_marketing.menu_vhealth_process_category", raise_if_not_found=False)
        self.assertTrue(m_proc, "VHealth Process category should exist")
        self.assertEqual(m_proc.name, "VHealth Process")

        m_elig = self.env.ref("vhealth_email_marketing.menu_vhealth_eligibility", raise_if_not_found=False)
        self.assertTrue(m_elig, "Eligibility menu should exist")
        self.assertEqual(m_elig.name, "Eligibility - New Members to launch")

        m_removal = self.env.ref("vhealth_email_marketing.menu_vhealth_member_removal", raise_if_not_found=False)
        self.assertTrue(m_removal, "AETNA Member Removal menu should exist")

        m_weekly = self.env.ref("vhealth_email_marketing.menu_vhealth_weekly_registration", raise_if_not_found=False)
        self.assertTrue(m_weekly, "Weekly vHealth Registrations menu should exist")
        self.assertEqual(m_weekly.name, "Weekly vHealth Registrations")

        m_queue = self.env.ref("vhealth_email_marketing.menu_vhealth_google_sheet_queue", raise_if_not_found=False)
        self.assertTrue(m_queue, "Google Sheet Registration Queue menu should exist")

        m_model = self.env.ref("vhealth_email_marketing.menu_vhealth_model_category", raise_if_not_found=False)
        self.assertTrue(m_model, "Model category should exist")

        m_prod = self.env.ref("vhealth_email_marketing.menu_vhealth_product_number", raise_if_not_found=False)
        self.assertTrue(m_prod, "vHealth Product menu should exist")
        self.assertEqual(m_prod.name, "vHealth Product")

        m_conf = self.env.ref("vhealth_email_marketing.menu_vhealth_config_category", raise_if_not_found=False)
        self.assertTrue(m_conf, "Configuration category should exist")

        m_ag = self.env.ref("vhealth_email_marketing.menu_vhealth_action_group", raise_if_not_found=False)
        self.assertTrue(m_ag, "Action Groups menu should exist")

        m_sched = self.env.ref("vhealth_email_marketing.menu_vhealth_action_group_schedule", raise_if_not_found=False)
        self.assertTrue(m_sched, "Scheduled Action Groups menu should exist")

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
            tmpl = Mailing.search([("subject", "=ilike", tname)], limit=1)
            if not tmpl:
                tmpl = Mailing.create({
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
        self.assertTrue(campaign.step1_mailing_id, "Step 1 mailing should be created")
        self.assertFalse(campaign.step1_mailing_id.is_template, "Cloned mailing must not be a template")
        self.assertTrue(campaign.step1_mailing_id.email_from, "email_from must be populated to satisfy DB constraint")

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

    def test_language_normalization(self):
        from ..models.imports import _normalize_language
        self.assertEqual(_normalize_language("spanish"), "Spanish")
        self.assertEqual(_normalize_language("Spanish"), "Spanish")
        self.assertEqual(_normalize_language("SPANISH"), "Spanish")
        self.assertEqual(_normalize_language("es"), "Spanish")
        self.assertEqual(_normalize_language("español"), "Spanish")
        self.assertEqual(_normalize_language("english"), "English")
        self.assertEqual(_normalize_language("English"), "English")
        self.assertEqual(_normalize_language("ENGLISH"), "English")
        self.assertEqual(_normalize_language(""), "English")
        self.assertEqual(_normalize_language(None), "English")

    def test_template_lookup_strict_database(self):
        from odoo.exceptions import UserError
        Schedule = self.env["vhealth.action.group.schedule"]
        rec = Schedule.new({})
        # Searching for non-existent step 99 must raise UserError and never read disk
        with self.assertRaises(UserError):
            rec._find_template(99)

    def test_custom_action_group_execution(self):
        ActionGroup = self.env["vhealth.action.group"]
        List = self.env["mailing.list"]
        Contact = self.env["mailing.contact"]
        Mailing = self.env["mailing.mailing"]
        Wizard = self.env["vhealth.schedule.action.group.wizard"]

        # Seeded NEW GROUP LAUNCH EMAILS should exist
        seeded = ActionGroup._get_new_group_launch()
        self.assertTrue(seeded, "Seeded NEW GROUP LAUNCH EMAILS action group must exist")
        self.assertEqual(len(seeded.step_ids), 6)

        tmpl = Mailing.create({
            "subject": "Custom Welcome Email",
            "is_template": True,
            "body_html": "<p>Welcome</p>",
            "body_arch": "<p>Welcome</p>",
        })
        dest_list = List.create({"name": "Custom Followup List"})
        src_list = List.create({"name": "Custom Source List"})

        c1 = Contact.create({
            "name": "Custom Contact",
            "email": "custom1@example.com",
            "list_ids": [(4, src_list.id)],
            "x_studio_app_registered": "No",
        })

        custom_ag = ActionGroup.create({
            "name": "CUSTOM ONBOARDING FLOW",
            "exclude_registered": True,
            "step_ids": [
                (0, 0, {
                    "sequence": 10,
                    "action_type": "send_email",
                    "mailing_template_id": tmpl.id,
                    "delay_days": 3,
                }),
                (0, 0, {
                    "sequence": 20,
                    "action_type": "add_to_list",
                    "target_mailing_list_id": dest_list.id,
                    "delay_days": 0,
                }),
            ],
        })

        wiz = Wizard.create({
            "mailing_list_id": src_list.id,
            "action_group_id": custom_ag.id,
            "schedule_type": "now",
        })
        self.assertIn("CUSTOM ONBOARDING FLOW", wiz.summary_html)
        action = wiz.action_schedule()
        sched = self.env["vhealth.action.group.schedule"].browse(action["res_id"])
        self.assertEqual(sched.action_group_id, custom_ag)
        self.assertEqual(sched.state, "running")
        self.assertEqual(sched.current_step, 1)
        self.assertTrue(sched.step1_mailing_id)

        sched.action_run_step_now()
        self.assertEqual(sched.state, "completed")
        self.assertIn(dest_list.id, c1.list_ids.ids)
        self.assertEqual(len(sched.execution_line_ids), 2)

    def test_gmail_html_hardening_and_image_rewrite(self):
        from ..models.mailing import (
            fix_odoo_email_html_for_gmail,
            load_bundled_launch_1_template,
            rewrite_vhealth_image_urls,
        )

        raw = (
            '<div class="o_layout"><style id="design-element">.o_layout{}</style>'
            '<div class="container o_mail_wrapper"><div class="row" style="background: red;">'
            '<img src="/web/image/158-5cc5bc03/Aetna_logo_24%20%282%29.png?access_token=abc" class="img-fluid"/>'
            '<img src="https://example.odoo.com/web/image/195-75d5d0be/20-vH_0395-New-App-Tile-1024x1024.png?access_token=xyz"/>'
            '<a href="https://vhealth.app.link/gotostore" class="btn btn-lg rounded-circle btn-primary">Register</a>'
            '<div class="bg-o-color-5"><p style="color:#fff;">Legal</p></div>'
            '</div></div></div>'
        )
        rewritten = rewrite_vhealth_image_urls(raw)
        self.assertIn("/vhealth_email_marketing/static/src/img/email/Aetna_logo_24.png", rewritten)
        self.assertIn("https://example.odoo.com/vhealth_email_marketing/static/src/img/email/20-vH_0395-New-App-Tile-1024x1024.png", rewritten)
        self.assertNotIn("/web/image/", rewritten)

        fixed = fix_odoo_email_html_for_gmail(raw)
        self.assertNotIn("design-element", fixed)
        self.assertNotIn("background: red", fixed)
        self.assertIn("background-color: #363C44", fixed)
        self.assertIn("background-color: #7C3F96", fixed)
        self.assertIn('width="120"', fixed)
        self.assertIn("max-width: 600px", fixed)

        launch_1 = load_bundled_launch_1_template()
        self.assertNotIn("/web/image/", launch_1)
        self.assertNotIn("design-element", launch_1)
        self.assertIn("/vhealth_email_marketing/static/src/img/email/Aetna_logo_24.png", launch_1)
        self.assertIn("background-color: #363C44", launch_1)
        self.assertIn("background-color: #7C3F96", launch_1)
        self.assertIn('width="120"', launch_1)

    def test_launch_1_template_upgrade_and_render(self):
        Mailing = self.env["mailing.mailing"]
        tmpl = Mailing.search([("is_template", "=", True), ("subject", "ilike", "Launch #1")], limit=1)
        broken_html = (
            '<div class="o_layout"><style id="design-element">.x{}</style>'
            '<div class="o_mail_wrapper"><div class="row" style="background: red;">'
            '<img src="/web/image/158-5cc5bc03/Aetna_logo_24%20%282%29.png?access_token=abc"/>'
            '</div></div></div>'
        )
        if tmpl:
            tmpl.write({"body_html": broken_html, "body_arch": broken_html})
        else:
            tmpl = Mailing.create({
                "subject": "vHealth - Launch #1 (2025)",
                "is_template": True,
                "body_html": broken_html,
                "body_arch": broken_html,
            })

        Mailing._upgrade_fix_vhealth_templates()
        self.assertNotIn("/web/image/", tmpl.body_html)
        self.assertNotIn("background: red", tmpl.body_html)
        self.assertIn("/vhealth_email_marketing/static/src/img/email/Aetna_logo_24.png", tmpl.body_html)
        # body_arch must remain editable in Odoo Mass Mailing visual editor
        self.assertIn("oe_structure", tmpl.body_arch)
        self.assertIn("o_mail_snippet_general", tmpl.body_arch)
        self.assertIn('id="design-element"', tmpl.body_arch)

        # Custom edits + newly uploaded Odoo image on already-fixed template must NOT be overwritten
        custom_arch = tmpl.body_arch.replace("Talk to a doctor", "Custom Heading") + '<section class="o_mail_snippet_general"><img src="/web/image/999-abc/new_custom_banner.png"/></section>'
        tmpl.write({"body_arch": custom_arch, "body_html": custom_arch})
        Mailing._upgrade_fix_vhealth_templates()
        self.assertIn("Custom Heading", tmpl.body_arch)
        self.assertIn("Custom Heading", tmpl.body_html)
        self.assertIn("/web/image/999-abc/new_custom_banner.png", tmpl.body_arch)

    def test_all_seven_bundled_templates_and_matching(self):
        from ..models.mailing import (
            _BUNDLED_TEMPLATE_FILES,
            load_bundled_arch_template,
            load_bundled_template,
            match_bundled_template_key,
            fix_odoo_email_html_for_gmail,
        )

        self.assertEqual(match_bundled_template_key("vHealth - Launch #1 (2025)", ""), "launch_1")
        self.assertEqual(match_bundled_template_key("vHealth - Launch #2 (2025)", ""), "launch_2")
        self.assertEqual(match_bundled_template_key("vHealth - Launch #3 (2025)", "vhealth-email-head_launch-01_es-v3.jpg"), "launch_3")
        self.assertEqual(match_bundled_template_key("vHealth - Launch #4 (2025)", ""), "launch_4")
        self.assertEqual(match_bundled_template_key("vHealth Worldwide - Family Invited", ""), "family_invited")
        self.assertEqual(match_bundled_template_key("VHealth Register Email", ""), "register")
        self.assertEqual(match_bundled_template_key("VHealth Non-Register Email", ""), "non_register")

        for key in _BUNDLED_TEMPLATE_FILES:
            html = load_bundled_template(key)
            self.assertNotIn("/web/image/", html, f"{key} must not have /web/image/ URLs")
            self.assertNotIn("design-element", html, f"{key} must not have design-element")
            self.assertNotIn("{$", html, f"{key} must not have unconverted SharpSpring tags")
            self.assertIn("background-color: #363C44", html, f"{key} missing footer dark background")
            self.assertIn("background-color: #7C3F96", html, f"{key} missing purple CTA/banner")
            self.assertIn('width="120"', html, f"{key} missing 120px app tile width")

            arch = load_bundled_arch_template(key)
            self.assertIn("oe_structure", arch, f"{key} body_arch missing oe_structure for Odoo editor")
            self.assertIn("o_mail_snippet_general", arch, f"{key} body_arch missing snippet blocks")
            self.assertIn('id="design-element"', arch, f"{key} body_arch missing design-element")
            self.assertNotIn("/web/image/", arch, f"{key} body_arch must not have /web/image/")
            self.assertNotIn("background: red", arch, f"{key} body_arch must not have background: red")

            converted = fix_odoo_email_html_for_gmail(arch)
            self.assertIn("vh-container", converted, f"{key} converted arch must produce 600px table")
            self.assertNotIn("design-element", converted, f"{key} converted arch must strip design-element")
            self.assertNotIn("<section", converted, f"{key} converted arch must convert <section> to <tr><td>")

        # Verify SharpSpring tag cleanup in fix_odoo_email_html_for_gmail
        ss_raw = (
            '<div class="o_mail_wrapper">'
            '<a href="{$family_invite_form_url_5d11dd4d2ed3f!&quot;https://vhealth.app.link/gotostore&quot;}">click</a>'
            '<h2>{$firstName}, {$primary_member_email__1__5c2cc0c228ec8!"A family member"} has invited you</h2>'
            '</div>'
        )
        ss_fixed = fix_odoo_email_html_for_gmail(ss_raw)
        self.assertNotIn("{$", ss_fixed)
        self.assertIn("https://vhealth.app.link/gotostore", ss_fixed)
        self.assertIn("A family member has invited you", ss_fixed)

    def test_rebuild_mailing_lists_wizard_and_rules(self):
        from ..models.imports import _get_or_create_list

        List = self.env["mailing.list"]
        Contact = self.env["mailing.contact"]
        RebuildWizard = self.env["vhealth.rebuild.mailing.lists.wizard"]

        # Case-insensitive list reuse
        existing_reg = List.create({"name": "All Registered Members"})
        resolved_reg = _get_or_create_list(self.env, "All REGISTERED members")
        self.assertEqual(resolved_reg.id, existing_reg.id)

        # Create contacts covering all rule combinations
        c_th_us_reg = Contact.create({
            "name": "TH US Registered",
            "email": "th_us_reg@example.com",
            "x_studio_vhealth_contact": True,
            "x_studio_cohort_group": "TH",
            "x_studio_app_registered": "Yes",
            "x_studio_location_us_or_canada": True,
        })
        c_mh_us_uniq = Contact.create({
            "name": "MH US Unique Reg",
            "email": "mh_us_uniq@example.com",
            "x_studio_vhealth_contact": True,
            "x_studio_cohort_group": "MH",
            "x_studio_app_unique_registered": "Yes",
            "x_studio_location_us_or_canada": True,
        })
        c_pc_non_us_reg = Contact.create({
            "name": "PC Non-US Registered",
            "email": "pc_non_us@example.com",
            "x_studio_vhealth_contact": True,
            "x_studio_cohort_group": "PC",
            "x_studio_app_registered": "Yes",
            "x_studio_location_us_or_canada": False,
        })
        c_th_mh_non_vhealth = Contact.create({
            "name": "Non vHealth Contact",
            "email": "non_vh@example.com",
            "x_studio_vhealth_contact": False,
            "x_studio_cohort_group": "TH + MH",
            "x_studio_app_registered": "Yes",
            "x_studio_location_us_or_canada": True,
        })

        # Add a stale contact to existing_reg and verify rebuild removes it while keeping opt_out on valid ones
        existing_reg.write({"contact_ids": [(4, c_pc_non_us_reg.id)]})

        wiz = RebuildWizard.create({"require_vhealth_contact": True})
        self.assertEqual(wiz.list_registered_id.id, existing_reg.id)
        wiz.action_rebuild_lists()
        self.assertEqual(wiz.state, "done")

        # Live list: all vHealth contacts only
        self.assertIn(c_th_us_reg.id, wiz.list_live_id.contact_ids.ids)
        self.assertIn(c_mh_us_uniq.id, wiz.list_live_id.contact_ids.ids)
        self.assertIn(c_pc_non_us_reg.id, wiz.list_live_id.contact_ids.ids)
        self.assertNotIn(c_th_mh_non_vhealth.id, wiz.list_live_id.contact_ids.ids)

        # Registered list: vHealth + US/Canada + (App Registered == Yes OR App UNIQUE Registered == Yes)
        self.assertIn(c_th_us_reg.id, wiz.list_registered_id.contact_ids.ids)
        self.assertIn(c_mh_us_uniq.id, wiz.list_registered_id.contact_ids.ids)
        self.assertNotIn(c_pc_non_us_reg.id, wiz.list_registered_id.contact_ids.ids)
        self.assertNotIn(c_th_mh_non_vhealth.id, wiz.list_registered_id.contact_ids.ids)

        # Cohort lists
        self.assertIn(c_th_us_reg.id, wiz.list_th_id.contact_ids.ids)
        self.assertIn(c_mh_us_uniq.id, wiz.list_mh_id.contact_ids.ids)
        self.assertIn(c_pc_non_us_reg.id, wiz.list_pc_id.contact_ids.ids)
        self.assertNotIn(c_th_mh_non_vhealth.id, wiz.list_th_mh_id.contact_ids.ids)

        # Verify menu exists
        m_rebuild = self.env.ref("vhealth_email_marketing.menu_vhealth_rebuild_mailing_lists", raise_if_not_found=False)
        self.assertTrue(m_rebuild)

    def test_custom_delay_minutes_and_testing_override(self):
        from datetime import timedelta
        from odoo.exceptions import ValidationError, UserError

        ActionGroup = self.env["vhealth.action.group"]
        List = self.env["mailing.list"]
        Contact = self.env["mailing.contact"]
        Mailing = self.env["mailing.mailing"]
        Wizard = self.env["vhealth.schedule.action.group.wizard"]

        tmpl = Mailing.create({
            "subject": "Test Delay Email",
            "is_template": True,
            "body_html": "<p>Test Delay</p>",
            "body_arch": "<p>Test Delay</p>",
        })
        src_list = List.create({"name": "Test Delay Source List"})
        dest_list = List.create({"name": "Test Delay Dest List"})
        c1 = Contact.create({
            "name": "Delay Test Contact",
            "email": "delay_test@example.com",
            "list_ids": [(4, src_list.id)],
            "x_studio_app_registered": "No",
        })

        # Action group with 7-day wait after step 1, 0-delay chaining on step 2, and final email step 3
        ag = ActionGroup.create({
            "name": "TEST INTERVAL ACTION GROUP",
            "exclude_registered": True,
            "step_ids": [
                (0, 0, {
                    "sequence": 10,
                    "action_type": "send_email",
                    "mailing_template_id": tmpl.id,
                    "delay_days": 7,
                    "delay_minutes": 0,
                }),
                (0, 0, {
                    "sequence": 20,
                    "action_type": "add_to_list",
                    "target_mailing_list_id": dest_list.id,
                    "delay_days": 0,
                    "delay_minutes": 0,
                }),
                (0, 0, {
                    "sequence": 30,
                    "action_type": "send_email",
                    "mailing_template_id": tmpl.id,
                    "delay_days": 0,
                    "delay_minutes": 15,
                }),
            ],
        })

        # Negative values must be rejected
        with self.assertRaises(ValidationError):
            ag.step_ids[0].write({"delay_minutes": -1})

        # Schedule with custom 10-minute override for testing
        wiz = Wizard.create({
            "mailing_list_id": src_list.id,
            "action_group_id": ag.id,
            "schedule_type": "now",
            "custom_interval_minutes": 10,
        })
        self.assertIn("+10 min", wiz.summary_html)
        action = wiz.action_schedule()
        sched = self.env["vhealth.action.group.schedule"].browse(action["res_id"])
        self.assertEqual(sched.custom_interval_minutes, 10)
        self.assertEqual(sched.state, "running")
        self.assertEqual(sched.current_step, 1)
        self.assertTrue(sched.next_execution_date)
        delta_after_1 = sched.next_execution_date - fields.Datetime.now()
        self.assertGreaterEqual(delta_after_1, timedelta(minutes=8))
        self.assertLessEqual(delta_after_1, timedelta(minutes=11))

        # Running next step should execute step 2 (0-delay) AND immediately chain into step 3
        sched.action_run_step_now()
        self.assertEqual(sched.state, "completed")
        self.assertIn(dest_list.id, c1.list_ids.ids)
        self.assertEqual(len(sched.execution_line_ids), 3)

        # Verify negative custom_interval_minutes is rejected on schedule & wizard
        with self.assertRaises(ValidationError):
            sched.write({"custom_interval_minutes": -5})
        bad_wiz = Wizard.create({
            "mailing_list_id": src_list.id,
            "action_group_id": ag.id,
            "schedule_type": "now",
            "custom_interval_minutes": -5,
        })
        with self.assertRaises(UserError):
            bad_wiz.action_schedule()

        # Verify step-level delay_minutes works without custom_interval_minutes override
        ag_min = ActionGroup.create({
            "name": "STEP MINUTES ACTION GROUP",
            "exclude_registered": True,
            "step_ids": [
                (0, 0, {
                    "sequence": 10,
                    "action_type": "send_email",
                    "mailing_template_id": tmpl.id,
                    "delay_days": 0,
                    "delay_minutes": 15,
                }),
                (0, 0, {
                    "sequence": 20,
                    "action_type": "add_to_list",
                    "target_mailing_list_id": dest_list.id,
                    "delay_days": 0,
                    "delay_minutes": 0,
                }),
            ],
        })
        wiz2 = Wizard.create({
            "mailing_list_id": src_list.id,
            "action_group_id": ag_min.id,
            "schedule_type": "now",
            "custom_interval_minutes": 0,
        })
        self.assertIn("+15 min", wiz2.summary_html)
        action2 = wiz2.action_schedule()
        sched2 = self.env["vhealth.action.group.schedule"].browse(action2["res_id"])
        delta2 = sched2.next_execution_date - fields.Datetime.now()
        self.assertGreaterEqual(delta2, timedelta(minutes=13))
        self.assertLessEqual(delta2, timedelta(minutes=16))
