---
phase: quick-261127-mix
plan: 01
type: execute
completed: "2026-11-27"
status: complete
commit: 69bb7b0
tags: [vhealth_email_marketing, action-groups, testing, scheduling]
---

# Quick Task 261127-mix Summary: Add Custom Step Delay (Minutes) Fields for Launch Testing

## What Was Built

Added configurable minute-based delay support to **vHealth Action Groups** so launch email drips (Launch #1 -> #2 -> #3 -> #4 -> non-registered segregation) can be tested at e.g. **10 minutes** between steps without modifying the production 7-day Action Group defaults:

1. **Per-Campaign Custom Delay Override (`custom_interval_minutes`)**:
   - Added `custom_interval_minutes` (`Custom Delay Between Steps (Minutes)`, default `0`) on both `vhealth.schedule.action.group.wizard` and `vhealth.action.group.schedule` (`models/action_group_schedule.py`, `wizard/schedule_action_group_wizard.py`).
   - When set `> 0` (e.g. `10`), `_step_wait_delta()` schedules `custom_interval_minutes` minutes after every step that has a wait (`delay_days > 0 or delay_minutes > 0`), while preserving `0`-delay immediate step chaining (such as step `4a update_contact` -> `4b send_email`).
   - Editable on Scheduled Action Group records while in `draft` or `running` state so test intervals can also be tuned mid-run, and honored by `action_resume()`.
   - `summary_html` in the scheduling wizard updates live (`@api.depends(..., "custom_interval_minutes")`) to show `+10 min`, `+20 min`, etc.

2. **Per-Step Wait Minutes (`delay_minutes`)**:
   - Added `delay_minutes` (`Wait Minutes After Step`, default `0`) on `vhealth.action.group.step` (`models/action_group.py`) and exposed it in both list and form views of Action Group steps (`views/action_group_views.xml`).
   - Added non-negative validation on `delay_minutes` and `custom_interval_minutes`.

3. **Tests & Module Version**:
   - Bumped `vhealth_email_marketing` version to `20.0.1.0.24`.
   - Added `test_custom_delay_minutes_and_testing_override` in `tests/test_smoke.py`.

## Verification

- Verified Python AST syntax across 19 `.py` files, XML well-formedness across 18 `.xml` files, and manifest `v20.0.1.0.24` consistency (19 data files).
- Full Odoo `TransactionCase` suite (`tests/test_smoke.py`) was not executed in this container because no Odoo/PostgreSQL runtime is installed locally; run on Odoo.sh / staging after upgrade.

## Notes on Scheduled Execution Cadence

- `ir_cron_vhealth_action_group_scheduler` (`data/ir_cron.xml`) is configured with a `15 minutes` interval (`noupdate="1"`). With `Custom Delay Between Steps (Minutes) = 10`, the next email sends automatically on the next cron tick (~10–25 minutes) — or immediately anytime via the **Run Next Step Now** button on the Scheduled Action Group form.
