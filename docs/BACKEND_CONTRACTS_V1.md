# Backend Contracts V1

Status: working draft
Owner: Rivet

This is the narrow persistence contract for the first dogfood build.

## Persistence roots

Repo-local state lives under:

- `.kids-game-utilities/prefs.json`
- `.kids-game-utilities/artifacts.json`
- `.kids-game-utilities/reports.json`

Writes should be atomic file replacements.

## Prefs

Prefs are per-user and separate from content records.

Fields:

- `active_project`
- `trigger_mode`

Operations:

- `get_active_project(user_id)`
- `set_active_project(user_id, project_slug | null)`
- `get_trigger_mode(user_id)`
- `set_trigger_mode(user_id, mode)`

Valid trigger modes:

- `auto`
- `mention`
- `manual`

## Artifact manifest

Global manifest per workspace.

Each artifact record:

- `id`
- `project_slug`
- `kind`
- `status`
- `label`
- `description?`
- `path`
- `mime_type?`
- `created_at`
- `updated_at`
- `linked_report_ids[]`

Status values:

- `suggested`
- `accepted`
- `dismissed`
- `deleted`

Operations:

- `create_artifact(...)`
- `update_artifact(id, ...)`
- `get_artifact(id)`
- `list_artifacts(project_slug?, include_deleted?, status?, linked_report_id?)`

Notes:

- dismissed suggestions remain in the manifest
- deletion is soft-delete only via `status=deleted`
- list APIs filter by project, but the manifest remains global

## Reports

Each report record:

- `id`
- `project_slug`
- `title`
- `markdown`
- `artifact_ids[]`
- `created_at`
- `updated_at`

Operations:

- `create_or_update_report(...)`
- `get_report(id)`
- `list_reports(project_slug?)`

Notes:

- `artifact_ids[]` are explicit linkage, not ordering
- markdown defines displayed artifact order through prose and embedded image placement
- backend must keep report linkage and artifact `linked_report_ids[]` consistent
