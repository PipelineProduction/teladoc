# vHealth Email Marketing Processes — Odoo Community 20.0

This is a **first-pass Community addon scaffold** rebuilt from the supplied Studio export and Server Action source. It is not a drop-in installation guarantee: validate against the exact Odoo 20.0 build and a disposable database before production.

## Included
- 69 `mailing.contact` custom fields recreated from the Studio field export.
- `x_product_number`, `x_mailing_contact_line_55a1f`, `x_eligibility_import`, `x_weekly_vhealth_regis`, `x_aetna_member_removal`, `x_google_sheet_registr`, and legacy `x_vhelth_contacts` models.
- Eligibility and weekly registration CSV processing with per-row savepoints.
- AETNA removal CSV processing that permanently deletes matching `mailing.contact` records only after the explicit checkbox and button confirmation.
- Google Sheets queue with retry counter, duplicate-payload guard for unsent registrations, queue view, and scheduled processor.
- Basic menus, views, and access groups.

## Intentionally excluded
- Mailing lists and email templates (configure manually as requested).
- Business/contact record migration.
- Studio internal helper model `x_ir_ui_view_line_787ca`.
- Legacy `x_vhelth_contacts` model pending confirmation that it is actively used.

## Before installing
1. Confirm your actual Odoo Community version is 20.0 and that `mass_mailing` is installed.
2. Install on a fresh disposable database first. The module inherits `mailing.contact`; do not install if your target Odoo build uses a different mass-mailing contact model.
3. Check the mailing list relation field in your exact Odoo build. This scaffold uses `mailing.contact.list_ids` and `mailing.list`.
4. Create/configure the six mailing lists manually using the exact names in `models/imports.py`.
5. Create Product Number records with exact values `aetna-prod-001`, `aetna-prod-002`, `aetna-prod-004`, `aetna-prod-007` in `x_studio_product_value` (or `x_name`).
6. Configure the Google Apps Script endpoint in Settings → Technical → Parameters → System Parameters using key `vhealth_email_marketing.google_sheet_webhook_url`. Keep different endpoints for development and production. Do not commit endpoint secrets to Git.
7. Review the exported custom fields for experimental/test fields and confirm the two company Many2one fields and self-referential Many2many relations behave as intended.
8. Run test imports with a tiny CSV and test deletion only against disposable contacts. Removal is permanent and `unlink()` cannot be undone without restoring a backup.

## Import headers
### Eligibility
`Email` (or `ID`), `First Name`, `Last Name`, `Aetna Language`, `Aetna Access Code`, `Member Effective Date`, `Cohort Group`, `Launch Date`.

### Weekly registration
`Client Code`, `Client Name`, `Client Surname`, `Client Gender`, `Client Language`, `Client DOB`, `Client Created Date`, `Client Prefix & Phone`, `Client Country`, `Client email`, `Product Code`.

### Removal
`Email` (or `Email Address`) and `AETNA Member Status` (or `Status`); only rows with status `Remove` are acted on.

## Known items requiring a validation pass
- Studio export includes a `res.partner` Many2one on the removal model, while the original process deletes `mailing.contact`; the legacy field is retained but is not used by the deletion process.
- `x_vhelth_contacts` is recreated as a legacy model because it is present in the Studio export; no import process currently depends on it.
- Studio export includes some experimental fields; all 69 were recreated as requested, but no attempt was made to infer their original business meaning.
- Google Sheets script should return HTTP 2xx and ideally JSON `{"success": true}`. Confirm your deployed Apps Script accepts the exact payload keys in `google_sheet_registration.py`.
- Verify whether the Google Sheet expects the `Aetna Registered` marker to be included; current payload matches the previously described four data fields plus `queue_id` and leaves sheet-row formatting to Apps Script.
- The original eligibility and weekly server actions have been simplified into regular Python methods. Compare the old source carefully before production, especially cohort membership cleanup and edge cases.

## Install
Copy this folder to `custom_addons/`, update the Apps list, then install **vHealth Email Marketing Processes** on the development database. Upgrade only this addon after code changes.


Odoo 20 menu compatibility note: the vHealth Process menu is declared as a top-level menu because the legacy external ID `mass_mailing.menu_mass_mailing` is not present in the target Odoo 20 Community database. It remains restricted to the Email Marketing user group.
