# Quick Task Plan: Configurable SharpSpring-Style Action Groups Master Setup

**Quick ID:** 261125-opq
**Date:** 2026-11-25

## Problem & Goal
Currently, `NEW GROUP LAUNCH EMAILS` is hardcoded as a single-item `Selection` field and a hardcoded 5-step Python branch in `vhealth.action.group.schedule`. In SharpSpring (`Automation > Action Groups`), users define reusable Action Groups in a central backend list and pick any of them when clicking "Schedule Action Group for List".

We need to introduce a configurable Action Groups master setup (`vhealth.action.group` & `vhealth.action.group.step`) in `custom_addons/vhealth_email_marketing` while preserving 100% backward compatibility with the existing `NEW GROUP LAUNCH EMAILS` flow, existing database records, and existing tests.

## Implementation Plan
1. **Master Models (`models/action_group.py`)**:
   - Create `vhealth.action.group` (name, code, active, description, `exclude_registered`, `step_ids`, `schedule_ids`).
   - Create `vhealth.action.group.step` supporting SharpSpring-style actions:
     - `send_email` (explicit `mailing_template_id` or fallback `template_subject_pattern`)
     - `update_contact` (`field_id` / `field_name` + typed `field_value` parser)
     - `add_to_list` (`target_mailing_list_id` or auto-create `target_list_name`)
     - `remove_from_list` (`target_mailing_list_id` or campaign's `mailing_list_id`)
     - `delay_days` (wait days after step; `0` chains immediately to the next step in the same execution cycle)
2. **Dynamic Campaign Engine (`models/action_group_schedule.py` & `models/mailing.py`)**:
   - Add `action_group_id` (`Many2one` to `vhealth.action.group`), `last_step_id`, `execution_line_ids` (`vhealth.action.group.schedule.line`), and `exclude_registered`.
   - Keep legacy `action_group` selection field synced and optional, plus `_migrate_legacy_action_groups()` for seamless upgrade of in-flight records.
   - Refactor `_run_next_step()` to execute configured `action_group_id.step_ids` dynamically while continuing to populate `current_step`, `step1_date..step5_date`, and `step1_mailing_id..step4_mailing_id`.
   - Update `mailing.py` `_get_recipients_domain()` to respect `exclude_registered`.
3. **Wizard, Views, Menus, Seed Data & Security**:
   - Update `wizard/schedule_action_group_wizard.py` and `views/schedule_action_group_wizard_views.xml` to select from all active `vhealth.action.group` records and dynamically render the step summary.
   - Add `views/action_group_views.xml` and `Action Groups` menu under `vHealth Process -> Configuration`.
   - Add `data/action_group_data.xml` (`noupdate="1"`) seeding `NEW GROUP LAUNCH EMAILS` with its 5-week steps and calling `_migrate_legacy_action_groups`.
   - Update `security/ir.access.csv` and `__manifest__.py` (bump version to `20.0.1.0.19`).
4. **Verification**:
   - Expand `tests/test_smoke.py` to verify both existing `NEW GROUP LAUNCH EMAILS` drip flow and custom user-defined Action Groups.
