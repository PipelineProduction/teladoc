# Quick Task Summary: Implement SharpSpring-Style "Schedule Action Group for List" Drip Campaign Engine

**Date:** 2026-11-19
**Version:** 20.0.1.0.10
**Status:** complete

## What Was Done
1. **SharpSpring-Style Action Group Wizard (`vhealth.schedule.action.group.wizard`)**:
   - Replicated SharpSpring's "Schedule Action Group for List" modal popup.
   - User chooses Action Group (`NEW GROUP LAUNCH EMAILS`) and schedule timing:
     - "As Soon as Possible" (starts immediately)
     - "Schedule for later" with a Date/Time picker (user can set 2:00 PM UK time or any desired start).
   - Wizard shows dynamic summary detailing eligible unregistered members, registered members excluded, and the 5-week launch sequence.
   - Clicking "Schedule" creates and launches the campaign.

2. **Drip Campaign Engine (`vhealth.action.group.schedule`)**:
   - Manages state machine (`draft`, `running`, `completed`, `cancelled`) and isolated weekly schedules for each mailing list.
   - **Step 1 (Launch #1)**: Duplicates template `vHealth - Launch #1 (2025)` targeting the list, sends/queues email, and schedules Step 2 for +7 days.
   - **Step 2 (Launch #2)**: Sends `vHealth - Launch #2 (2025)` to remaining unregistered contacts on the list, schedules Step 3 for +7 days.
   - **Step 3 (Launch #3)**: Sends `vHealth - Launch #3 (2025)` to remaining unregistered contacts on the list, schedules Step 4 for +7 days.
   - **Step 4 (Engagement Check + Launch #4)**: Finds all eligible unregistered contacts on the list, sets contact field `x_studio_check_for_engagement = True`, sends `vHealth - Launch #4 (2025)`, and schedules Step 5 for +7 days.
   - **Step 5 (Final Archival to Non-Registered List)**: Finds contacts on the list who still have not registered (`x_studio_app_registered != 'Yes'`), automatically adds them to the list **"All non registered members"** (auto-creates list if missing), and marks campaign completed.

3. **Strict Registration Stop Condition**:
   - Inherited `mailing.mailing` to enforce that if a member registers (`x_studio_app_registered == 'Yes'`) at any point (via weekly registration import), they are immediately excluded from receiving subsequent launch emails (Launch 2, 3, 4).
   - If 100% of contacts register before a step, the step gracefully logs and skips the email without crashing.

4. **Automated Cron & Manual Test Controls**:
   - Created cron `ir_cron_vhealth_action_group_scheduler` running every 15 minutes to automatically advance due campaigns when `next_execution_date <= now()`.
   - Added a "Run Next Step Now" button on the campaign form view so users/admins can manually trigger the next step immediately for verification/testing without waiting 7 days.
   - Added campaign action buttons: Cancel, Resume, and full Execution Log tracking.

5. **Mailing List Integration & Navigation**:
   - Inherited `mailing.list` form view with:
     - Header button: **"Schedule Action Group"**
     - Stat button: **"Action Campaigns"** (showing campaign count)
     - Action menu item in list and form views: **"Schedule Action Group for List"**.
   - Added menu item: **"Scheduled Action Groups"** under **vHealth Process** (`vhealth_email_marketing.menu_vhealth_action_group_schedule`).

6. **Automated Tests**:
   - Expanded `tests/test_smoke.py` with `test_action_group_drip_campaign_flow` covering wizard initialization, step progression, engagement flag setting, non-registered list population, and registered contact exclusion.
