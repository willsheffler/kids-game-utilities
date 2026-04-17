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

Frontend-facing payloads:

```json
{
  "ok": true,
  "result": {
    "userId": "will",
    "activeProject": "tower-defense"
  }
}
```

```json
{
  "ok": true,
  "result": {
    "userId": "will",
    "triggerMode": "auto"
  }
}
```

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
- `upload_artifact(image_b64, image_filename, ...)`
- `update_artifact(id, ...)`
- `get_artifact(id)`
- `list_artifacts(project_slug?, include_deleted?, status?, linked_report_id?)`

Frontend-facing artifact payload:

```json
{
  "ok": true,
  "result": {
    "artifact": {
      "id": "artifact_123",
      "kind": "screenshot",
      "projectSlug": "tower-defense",
      "status": "accepted",
      "label": "boss wave clear",
      "description": null,
      "path": "session-logs/assets/2026-04-17/boss-wave.png",
      "url": "session-logs/assets/2026-04-17/boss-wave.png",
      "filename": "boss-wave.png",
      "mimeType": "image/png",
      "createdAt": "2026-04-17T08:01:02+00:00",
      "updatedAt": "2026-04-17T08:01:05+00:00",
      "linkedReportIds": ["report_123"]
    }
  }
}
```

Upload request shape accepted by the HTTP layer:

```json
{
  "image_b64": "iVBORw0KGgoAAA...",
  "image_filename": "capture.png",
  "label": "boss wave clear",
  "projectSlug": "tower-defense",
  "mimeType": "image/png"
}
```

The stored artifact `path` is a served URL path like:

- `/uploads/tower-defense/capture_ab12cd34.png`

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

Frontend-facing report payload:

```json
{
  "ok": true,
  "result": {
    "report": {
      "id": "report_123",
      "projectSlug": "tower-defense",
      "title": "Session 1",
      "markdown": "![boss](session-logs/assets/2026-04-17/boss-wave.png)",
      "artifactIds": ["artifact_123"],
      "createdAt": "2026-04-17T08:02:00+00:00",
      "updatedAt": "2026-04-17T08:03:00+00:00"
    }
  }
}
```

Notes:

- `artifact_ids[]` are explicit linkage, not ordering
- markdown defines displayed artifact order through prose and embedded image placement
- backend must keep report linkage and artifact `linked_report_ids[]` consistent

## Bootstrap / project list

To simplify first frontend wiring, the adapter exposes:

- `get_bootstrap(user_id)`
- `list_projects()`

Bootstrap payload:

```json
{
  "ok": true,
  "result": {
    "prefs": {
      "activeProject": "tower-defense",
      "triggerMode": "auto"
    },
    "projects": [
      { "slug": "platformer", "label": "platformer" },
      { "slug": "tower-defense", "label": "tower-defense" }
    ]
  }
}
```

Current project list behavior:

- derived from known artifact/report project slugs
- no separate project registry yet

## HTTP route notes

Canonical routes:

- `GET /health`
- `GET /sessions`
- `GET /agent-status/:session`
- `POST /chat`
- `GET /history/:session`
- `GET /poll/:session`
- `GET /api/bootstrap?userId=...`
- `GET|POST /api/prefs/active-project`
- `GET|POST /api/prefs/trigger-mode`
- `GET /api/projects`
- `GET|POST /api/artifacts`
- `PATCH /api/artifacts/:id`
- `GET|POST /api/reports`
- `GET /api/reports/:id`
- `GET /uploads/...`

Compatibility aliases currently supported for the existing frontend scaffold:

- `GET /bootstrap?userId=...`
- `GET|POST /artifacts`

Chat payload shape:

```json
{
  "text": "please draft the session report",
  "session": "madeira"
}
```

Chat response shape:

```json
{
  "backendTarget": "madeira",
  "sessionId": "kgu_madeira",
  "reply": "..."
}
```

History response shape:

```json
{
  "messages": [
    { "role": "user", "text": "hi", "ts": "04/17 02:00" },
    { "role": "agent", "text": "hello", "ts": "04/17 02:01" }
  ],
  "total": 2,
  "has_more": false
}
```

Poll response shape:

```json
{
  "messages": [
    { "role": "agent", "text": "follow-up", "sender": "madeira" }
  ],
  "pending_sessions": ["madeira"]
}
```

Health response shape:

```json
{
  "status": "ok",
  "default_session": "madeira",
  "user": "sheffler",
  "host": "cake"
}
```

Sessions response shape:

```json
{
  "sessions": ["bella", "madeira", "pensieve-loom"],
  "default": "madeira"
}
```

Agent-status response shape:

```json
{
  "session": "madeira",
  "status": "busy",
  "busy_status": "running",
  "pane_command": "codex",
  "last_line": "working...",
  "runtime_family": "codex_cli",
  "logical_actor": "madeira"
}
```
