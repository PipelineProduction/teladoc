---
phase: quick-261127-mix
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - custom_addons/vhealth_email_marketing/__manifest__.py
  - custom_addons/vhealth_email_marketing/models/action_group.py
  - custom_addons/vhealth_email_marketing/models/action_group_schedule.py
  - custom_addons/vhealth_email_marketing/wizard/schedule_action_group_wizard.py
  - custom_addons/vhealth_email_marketing/views/action_group_views.xml
  - custom_addons/vhealth_email_marketing/views/action_group_schedule_views.xml
  - custom_addons/vhealth_email_marketing/views/schedule_action_group_wizard_views.xml
  - custom_addons/vhealth_email_marketing/tests/test_smoke.py
autonomous: true
requirements: []
must_haves:
  truths:
    - "Users can enter Custom Delay Between Steps (Minutes) (e.g., 10) on the Schedule Action Group wizard and scheduled campaign record without altering production 7-day Action Group defaults."
    - "Users can also set Wait Minutes After Step (delay_minutes) directly on individual Action Group steps."
    - "When custom_interval_minutes > 0, non-immediate steps wait custom_interval_minutes minutes while 0-delay steps (such as 4a update_contact -> 4b send_email) still chain immediately in the same cycle."
    - "Wizard schedule preview accurately renders +N min / +N days timing."
  artifacts:
    - path: custom_addons/vhealth_email_marketing/models/action_group.py
      provides: "delay_minutes field and non-negative validation on vhealth.action.group.step"
    - path: custom_addons/vhealth_email_marketing/models/action_group_schedule.py
      provides: "custom_interval_minutes field, _run_next_step and action_resume minute-based scheduling"
    - path: custom_addons/vhealth_email_marketing/wizard/schedule_action_group_wizard.py
      provides: "custom_interval_minutes field, minute/day timeline preview, and pass-through to schedule"
  key_links:
    - from: wizard/schedule_action_group_wizard.py
      to: models/action_group_schedule.py
      via: "action_schedule() passes custom_interval_minutes"
    - from: models/action_group_schedule.py
      to: models/action_group.py
      via: "_run_next_step() and action_resume() read delay_days and delay_minutes when custom_interval_minutes == 0"
---

<objective>
Add configurable minute-based delay fields (`custom_interval_minutes` override on schedule/wizard and `delay_minutes` on action group steps) so Launch Email Action Groups can be tested with short intervals (e.g., 10 minutes between #1, #2, #3, #4) without changing production 7-day defaults.
</objective>

<tasks>

<task type="auto">
  <name>Task 1: Add delay_minutes on Action Group steps and custom_interval_minutes on schedule & wizard</name>
  <files>
    custom_addons/vhealth_email_marketing/models/action_group.py
    custom_addons/vhealth_email_marketing/models/action_group_schedule.py
    custom_addons/vhealth_email_marketing/wizard/schedule_action_group_wizard.py
  </files>
  <action>
    1. On `VHealthActionGroupStep`, add `delay_minutes` (`fields.Integer`, default 0) and include non-negative validation in `_check_step_configuration`.
    2. On `VHealthActionGroupSchedule`, add `custom_interval_minutes` (`fields.Integer`, default 0, tracking=True) with a non-negative constraint, and update `_run_next_step()` and `action_resume()` to use `custom_interval_minutes` for any step that has a non-zero configured delay (`step.delay_days > 0 or step.delay_minutes > 0`), preserving immediate (`0`-delay) step chaining (e.g. step 4a -> 4b), and otherwise wait `timedelta(days=step.delay_days, minutes=step.delay_minutes)`.
    3. On `VHealthScheduleActionGroupWizard`, add `custom_interval_minutes` (`fields.Integer`, default 0), update `_compute_list_summary()` to display cumulative `+N min` / `+N days` timing in `summary_html`, and pass `custom_interval_minutes` in `action_schedule()`.
  </action>
</task>

<task type="auto">
  <name>Task 2: Expose custom delay fields in XML views, bump manifest, and add smoke tests</name>
  <files>
    custom_addons/vhealth_email_marketing/views/action_group_views.xml
    custom_addons/vhealth_email_marketing/views/action_group_schedule_views.xml
    custom_addons/vhealth_email_marketing/views/schedule_action_group_wizard_views.xml
    custom_addons/vhealth_email_marketing/__manifest__.py
    custom_addons/vhealth_email_marketing/tests/test_smoke.py
  </files>
  <action>
    1. Add `delay_minutes` to `step_ids` list and form views in `action_group_views.xml`.
    2. Add `custom_interval_minutes` to `action_group_schedule_views.xml` (editable while draft/running) and `schedule_action_group_wizard_views.xml`.
    3. Bump `__manifest__.py` version to `20.0.1.0.24`.
    4. Add unit tests in `tests/test_smoke.py` covering `custom_interval_minutes = 10`, immediate 0-delay step chaining preservation, `delay_minutes` step configuration, and negative value validation.
  </action>
</task>

</tasks>
