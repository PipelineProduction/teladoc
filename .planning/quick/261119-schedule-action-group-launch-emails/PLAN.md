# Quick Task Plan: Implement SharpSpring-Style "Schedule Action Group for List" Drip Campaign Engine

## Problem & Goal
In SharpSpring, after importing weekly eligible members into a list (e.g. `Eligible Member 2026-11-04`), the user clicks "Schedule Action Group for List", selects `NEW GROUP LAUNCH EMAILS`, picks a scheduled date/time (or immediate), and triggers an automated 4-week drip campaign.

We need to implement this complete functionality in Odoo directly inside `custom_addons/vhealth_email_marketing`:
1. "Schedule Action Group for List" button and action on `mailing.list`.
2. SharpSpring-styled modal wizard (`vhealth.schedule.action.group.wizard`):
   - Action Group dropdown (`NEW GROUP LAUNCH EMAILS`)
   - Schedule mode: "As Soon as Possible" vs "Schedule for later" (Datetime picker)
   - Dynamic explanation box matching SharpSpring
   - Schedule button
3. Campaign Engine (`vhealth.action.group.schedule`):
   - Step 1: Send Launch #1 (`vHealth - Launch #1 (2025)`). Schedule Step 2 in 7 days.
   - Step 2: Send Launch #2 (`vHealth - Launch #2 (2025)`). Exclude registered members. Schedule Step 3 in 7 days.
   - Step 3: Send Launch #3 (`vHealth - Launch #3 (2025)`). Exclude registered members. Schedule Step 4 in 7 days.
   - Step 4: Update contacts on list where `x_studio_app_registered != 'Yes'` setting `x_studio_check_for_engagement = True`. Send Launch #4 (`vHealth - Launch #4 (2025)`). Exclude registered members. Schedule Step 5 in 7 days.
   - Step 5: If contacts still haven't registered (`x_studio_app_registered != 'Yes'`), automatically add them to mailing list "All non registered members" (auto-created if missing). Mark campaign completed.
4. Stop condition: If any contact registers at any time (`x_studio_app_registered == 'Yes'`), they are immediately excluded from any further launch emails.
5. List isolation: Each list campaign runs on its own isolated schedule tracker without mixing.
6. Cron job: Runs every 15 minutes to execute due steps. Form view also has a "Run Next Step Now" button for instant manual triggering or testing.

## Implementation Steps
1. Create `custom_addons/vhealth_email_marketing/models/action_group_schedule.py` with `vhealth.action.group.schedule` model.
2. Create `custom_addons/vhealth_email_marketing/models/mailing.py` inheriting `mailing.mailing` for registered contact exclusion and campaign linkage.
3. Create `custom_addons/vhealth_email_marketing/models/mailing_list.py` inheriting `mailing.list` for wizard launch and campaign stat count.
4. Create `custom_addons/vhealth_email_marketing/wizard/schedule_action_group_wizard.py` and wizard views.
5. Create views:
   - `views/action_group_schedule_views.xml`: list and form views for campaign management.
   - `views/mailing_list_views.xml`: form header button and stat button on `mailing.list`.
   - `views/schedule_action_group_wizard_views.xml`: wizard form view.
   - Update `views/menus.xml` to include "Scheduled Action Groups" under "vHealth Process".
6. Update `data/ir_cron.xml` to add `ir_cron_vhealth_action_group_scheduler`.
7. Update `security/ir.access.csv` for user and manager permissions.
8. Register models, wizards, views in `__init__.py` and `__manifest__.py`. Bump version to `20.0.1.0.10`.
9. Add unit tests in `tests/test_smoke.py`.
10. Verify everything, update STATE.md, SUMMARY.md, commit changes, and rebuild package zip if required.
