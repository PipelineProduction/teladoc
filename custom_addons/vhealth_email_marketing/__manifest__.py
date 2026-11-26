{
    "name": "vHealth Email Marketing Processes",
    "summary": "Automated Member Onboarding, Launch Campaigns & Registration Management for vHealth",
    "version": "20.0.1.0.22",
    "category": "Marketing/Email Marketing",
    "license": "LGPL-3",
    "author": "Pipeline Digital",
    "website": "https://pipelinedigital.co.uk/",
    "description": """
vHealth Email Marketing & Member Automation
==========================================

Enterprise onboarding, membership lifecycle management, and automated drip campaign engine built specifically for vHealth and AETNA member operations.

Key Features & Capabilities:
-----------------------------
* **Eligibility & Launch Management**: Automated ingestion of weekly eligible members ("New Members to Launch") with dynamic cohort routing and language assignment (English / Spanish).
* **Automated Drip Engine (Scheduled Action Groups)**: Multi-week drip campaign engine mimicking SharpSpring action groups (Launch #1 to #4) with automated registration tracking, engagement value updates, and unregistered member list segregation.
* **Member Lifecycle Operations**:
  - Weekly vHealth Registration batch imports.
  - AETNA Member Removal processing.
  - Real-time Google Sheets registration queue synchronization.
* **Bilingual Dynamic Delivery**: Individualized multilingual email composition based on member language preferences.
* **vHealth Product Configuration**: Managed product numbering and mapping for Teladoc health plans.
    """,
    "depends": ["mass_mailing", "mail"],
    "data": [
        "security/security.xml",
        "security/ir.access.csv",
        "data/product_number_data.xml",
        "data/google_sheet_data.xml",
        "data/ir_cron.xml",
        "data/action_group_data.xml",
        "data/template_fix_data.xml",
        "views/product_number_views.xml",
        "views/import_views.xml",
        "views/member_removal_views.xml",
        "views/google_sheet_queue_views.xml",
        "views/mailing_contact_views.xml",
        "views/mailing_views.xml",
        "views/action_group_views.xml",
        "views/schedule_action_group_wizard_views.xml",
        "views/rebuild_mailing_lists_wizard_views.xml",
        "views/action_group_schedule_views.xml",
        "views/mailing_list_views.xml",
        "views/menus.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": True,
}
