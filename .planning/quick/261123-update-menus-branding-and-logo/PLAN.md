# Quick Plan: Update Menus, App Metadata & Logo

## Goal
Restructure module menus according to user specifications, update app metadata (author "Pipeline Digital", description), and add the Pipeline logo to `static/description/icon.png`.

## Specification
1. **Menu Structure**:
   - Root: `vHealth Process` (with `web_icon="vhealth_email_marketing,static/description/icon.png"`)
   - Category 1: `VHealth Process`
     - `Eligibility - New Members to launch` (`action_eligibility_import`)
     - `AETNA Member Removal` (`action_member_removal`)
     - Submenu: `Weekly vHealth Registrations`
       - `Weekly vHealth Registrations` (`action_weekly_registration`)
       - `Google Sheet Registration Queue` (`action_google_sheet_queue`)
   - Category 2: `Model`
     - `vHealth Product` (`action_product_number`)
   - Category 3: `Configuration`
     - `Scheduled Action Groups` (`action_vhealth_action_group_schedule`)
2. **Branding & Metadata (`__manifest__.py`)**:
   - `author`: "Pipeline Digital"
   - `website`: "https://pipelinedigital.com"
   - `summary`: "Automated Member Onboarding, Launch Campaigns & Registration Management for vHealth"
   - `description`: Comprehensive authentic markdown description covering eligibility, drip campaign engine, lifecycle operations, bilingual delivery, and products.
3. **App Logo**:
   - Copied `/home/elsner/Documents/pipeline/pipeline-logo-1.png` to `custom_addons/vhealth_email_marketing/static/description/icon.png`.
4. **Smoke Test**:
   - Added assertions in `test_smoke.py` verifying all menu entries and their names.
