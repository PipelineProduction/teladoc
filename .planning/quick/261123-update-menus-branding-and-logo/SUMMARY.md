---
status: complete
date: 2026-11-23
commit: 104c906
slug: 261123-update-menus-branding-and-logo
---

# Quick Task Summary: Update Menus, App Metadata & Logo

## Overview
Implemented UI menu reorganization, updated module metadata to "Pipeline Digital", and added the app icon from `/home/elsner/Documents/pipeline/pipeline-logo-1.png`.

## Changes Made
1. **Menus ([menus.xml](file:///home/elsner/Documents/pipeline/teladoc/custom_addons/vhealth_email_marketing/views/menus.xml))**:
   - Organized into three top-level categories:
     - **VHealth Process**:
       - `Eligibility - New Members to launch`
       - `AETNA Member Removal`
       - Submenu: `Weekly vHealth Registrations` containing `Weekly vHealth Registrations` and `Google Sheet Registration Queue`
     - **Model**:
       - `vHealth Product`
     - **Configuration**:
       - `Scheduled Action Groups`
   - Bound app icon `vhealth_email_marketing,static/description/icon.png` to `menu_vhealth_process_root`.
2. **Metadata ([__manifest__.py](file:///home/elsner/Documents/pipeline/teladoc/custom_addons/vhealth_email_marketing/__manifest__.py))**:
   - Author: `Pipeline Digital`
   - Website: `https://pipelinedigital.com`
   - Version: `20.0.1.0.15`
   - Description: Added detailed overview of eligibility, drip campaign engine, member lifecycle, and product mappings.
3. **App Icon ([icon.png](file:///home/elsner/Documents/pipeline/teladoc/custom_addons/vhealth_email_marketing/static/description/icon.png))**:
   - Installed `/home/elsner/Documents/pipeline/pipeline-logo-1.png` into `static/description/icon.png`.
4. **Tests ([test_smoke.py](file:///home/elsner/Documents/pipeline/teladoc/custom_addons/vhealth_email_marketing/tests/test_smoke.py))**:
   - Added test assertions verifying menu existence and names.
