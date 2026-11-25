---
status: complete
quick_id: 261125-opq
date: 2026-11-25
commit: edb7790
---
# Quick Task Summary: Configurable SharpSpring-Style Action Groups Master Setup

**Date:** 2026-11-25
**Version:** 20.0.1.0.19
**Status:** complete

## What Was Done
1. **Action Groups Master Setup (`models/action_group.py`, `views/action_group_views.xml`, `views/menus.xml`)**:
   - Added `vhealth.action.group` and `vhealth.action.group.step` models under **vHealth Process -> Configuration -> Action Groups**.
   - Supports reusable multi-step Action Groups with step actions:
     - `send_email` (explicit `mailing_template_id` or fallback `template_subject_pattern` / `launch_step_number`)
     - `update_contact` (pick any writable `mailing.contact` field and value)
     - `add_to_list` (target `mailing.list` or auto-create by name)
     - `remove_from_list` (target `mailing.list` or campaign list)
   - Added configurable `delay_days` per step (`0` chains immediately into the next step in the same execution cycle) and `exclude_registered` toggle per Action Group.

2. **Dynamic Execution Engine & Upgrade Safety (`models/action_group_schedule.py`, `models/mailing.py`, `data/action_group_data.xml`)**:
   - Seeded `NEW GROUP LAUNCH EMAILS` (`action_group_new_group_launch`) with its exact 5-week workflow steps in `data/action_group_data.xml` (`noupdate="1"`).
   - Added `action_group_id`, `last_step_id`, `exclude_registered`, and `execution_line_ids` (`vhealth.action.group.schedule.line`) to `vhealth.action.group.schedule`.
   - Kept legacy `action_group` selection field, `step1_date..step5_date`, `step1_mailing_id..step4_mailing_id`, and `_find_template()` intact for full backward compatibility.
   - Added `_migrate_legacy_action_groups()` to automatically link existing schedule records and in-flight step progress on module upgrade.
   - Updated `mailing.py` `_get_recipients_domain()` to respect `exclude_registered`.

3. **Schedule Action Group Wizard (`wizard/schedule_action_group_wizard.py`, `views/schedule_action_group_wizard_views.xml`)**:
   - Updated wizard to list all active `vhealth.action.group` records in a dropdown (`action_group_id`, defaulting to `NEW GROUP LAUNCH EMAILS`).
   - Updated `summary_html` to dynamically render the selected Action Group's name, recipient exclusion counts, and configured steps.

4. **Security & Tests (`security/ir.access.csv`, `tests/test_smoke.py`)**:
   - Added ACL entries for `vhealth.action.group`, `vhealth.action.group.step`, and `vhealth.action.group.schedule.line`.
   - Verified Python AST (18 files), XML parsing (15 files), manifest data paths (16 entries), and `ir.access.csv` schema (29 rules); expanded `tests/test_smoke.py` with `test_custom_action_group_execution` alongside existing `test_action_group_drip_campaign_flow`. Note: no Odoo runtime/database is present in this workspace container to execute Odoo `TransactionCase` tests directly.
