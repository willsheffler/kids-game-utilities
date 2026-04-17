# Kids Game Utilities Implementation Architecture V1

Status: CAP-reviewed working draft
Created: 2026-04-17
Maintainer: Will + Lattice

## Purpose

Capture the current implementation-facing architecture for the first dogfood build.

This doc is more concrete than the family/policy docs in `sheffler-standards`.
It is the working technical plan for frontend/backend boundary review and implementation planning.

## Context

The broader product intent and teaching standards live in:

- `sheffler-standards/KIDS_GAME_DEV_V1.md`
- `sheffler-standards/KIDS_GAME_DEV_DOGFOOD_V1.md`

This repo is the technical home for:

- app/tooling architecture
- shared component boundaries
- artifact model
- implementation planning

## Current build target

The first dogfood app is a flexible dev shell intended to exercise the new tooling.

It is not locked to one highly specific final product.
Near-term expected use is likely:

- light content annotation
- image picking / visual workflow
- game-like or creative tooling that lets Will dogfood with Madeira

The tooling should still support multi-project development from the start.

## Product shape

One app/workspace with:

- one shared visible chat timeline
- one active agent context
- multi-project support from the start
- inline trigger-mode control near the composer
- visible screenshot suggestion queue / artifact tray
- lightweight report viewing/editing loop

## Multi-project stance

We are explicitly exercising multi-project support from the start because:

- the kids are likely to switch projects often
- the tooling should support flexible dev use, not only one fixed app

Current default:

- shared timeline remains visible by default
- project filtering stays loose for now
- project selection/context exists, but deep project partitioning is deferred

## Artifact model

Artifacts are first-class.

Not all artifacts go into reports.

Important consequences:

- screenshots are stored as artifacts first
- reports select from artifacts rather than owning all artifacts by default
- artifact history should remain visible and inspectable

### Current storage direction

- configurable deliverables root
- likely centered around `session-logs/`
- screenshots should render in GitHub-friendly markdown
- a global manifest per app/workspace is acceptable for now

### Early manifest direction

The first pass uses one global manifest per app/workspace.

Artifacts are effectively chronological.
There is no separate meaningful artifact ordering model in v1.

Report display order is defined by markdown prose and embedded image placement in the report document.

The manifest is mainly an artifact index and linkage record.

## Report flow

Report content is agent-drafted and iterated with user feedback.

Backend responsibility:

- persist markdown
- persist artifact linkage/manifest data
- persist active project and per-user global trigger mode

Agent responsibility:

- draft report content
- update report text with user feedback

Useful UI direction:

- a report viewer modal/tab/pane
- rendered markdown with embedded images
- visible alongside or replacing the main content area while chat stays visible
- user can request report changes in chat and see live updates

## Screenshot flow

The system should support agent-facing screenshot nomination rather than exposing rich passive-capture tuning to users yet.

Minimum behavior:

- agent can nominate/request a screenshot
- frontend shows a visible suggestion
- candidate label is proposed
- user can quick-accept, edit, dismiss
- accepted screenshots enter visible artifact history

### Stable contract needed

Before dogfood, document a stable agent/frontend contract for screenshot suggestions, for example:

- `[suggest-screenshot: "label"]`

The frontend should interpret that into a visible suggestion item.

## Settings direction

Current direction:

- trigger mode is a primary inline control, not buried in settings
- passive-capture tuning is not yet a user-facing setting
- tiny SettingsDrawer remains for non-primary settings

Likely early contents:

- mic/device placeholder
- session-mode hint or summary preference
- maybe dev-tools visibility or a similarly secondary shell setting

Trigger mode:

- persists per user
- global for now
- controlled inline near the composer rather than primarily through the drawer

## Frontend / backend split

Initial ownership intent:

- Loom: frontend / UI / shell / shared component boundaries
- Rivet: backend / API / persistence / tooling contracts

Both should review and comment on boundaries.

## Code placement direction

Current working split:

- game-dev / learning-specific code: this repo
- common reusable components: `agent-common-base/components` for now
- backend service migration: separate concern, not coupled to first component work

This means:

- start reusable components where useful
- do not force immediate backend migration just to start building

## CAP-converged boundary decisions

Shared reusable code in `agent-common-base/components` for now:

- chat transcript primitives
- composer/message rendering
- runtime/agent-status badge model
- auth gate
- status dot
- mic button UI shell
- generic modal/pane scaffolding when actually reusable

Keep app-specific in `kids-game-utilities`:

- project selector/context model
- screenshot suggestion UX
- screenshot capture flow
- artifact tray/manifest UI
- report viewer/editor shell
- game-dev / dev-shell layout
- deliverable/session-log behaviors
- trigger-mode inline control

Guiding rule:

- if it needs to understand artifacts, projects, reports, or game-like/dev-shell semantics, keep it app-specific

## Minimal multi-project model

Multi-project support is kept narrow in v1:

- one active project selector
- optional loose `all` view later
- shared timeline remains the default
- no per-project chat partitioning
- no per-project manifests
- no isolated runtime state per project

Project is effectively a persisted tag/filter model, not a deep partition.

## Backend contract direction

### Settings / prefs

Persist separately from artifacts and reports:

- active project
- trigger mode

These are per-user preferences, not content records.

### Artifacts

Backend owns:

- artifact IDs
- canonical file paths
- timestamps
- canonical metadata
- report linkage
- project association

Frontend owns:

- suggestion queue
- accept/edit/dismiss interactions
- capture UI
- local presentation of artifact history

### Reports

Backend owns:

- persisted markdown blobs
- report metadata
- explicit artifact linkage

Frontend owns:

- rendered markdown preview pane
- report-viewer shell
- chat-mediated edit request UX

The frontend is not the source of truth for report text.

## Minimal artifact manifest schema v1

Per artifact:

- `id`
- `project_slug`
- `kind`
- `status`
  - `suggested`
  - `accepted`
  - `dismissed`
  - `deleted`
- `label`
- `description?`
- `path`
- `mime_type?`
- `created_at`
- `updated_at`
- `linked_report_ids[]`

Notes:

- soft-delete is represented by `status`, not a separate deletion flag
- dismissed suggestions remain in the manifest
- provenance stays minimal in v1
- no `source_turn_id`/`source_message_id` required yet
- no meaningful separate artifact ordering model in v1

Example:

```json
{
  "id": "art_20260417_143522_a3f2",
  "project_slug": "rpsbattle",
  "kind": "screenshot",
  "status": "accepted",
  "label": "After adding jump physics",
  "description": "Character jumps and lands correctly after physics tweak",
  "path": "session-logs/assets/2026-04-17/screenshot_143522_a3f2.png",
  "mime_type": "image/png",
  "created_at": "2026-04-17T14:35:22Z",
  "updated_at": "2026-04-17T14:35:22Z",
  "linked_report_ids": ["report_20260417"]
}
```

## Minimal report record schema v1

- `id`
- `project_slug`
- `title`
- `markdown`
- `artifact_ids[]`
- `created_at`
- `updated_at`

Notes:

- `artifact_ids[]` is explicit inclusion/linkage only
- it does not imply ordering semantics
- report display order is defined by markdown prose and embedded image placement
- artifacts may appear in multiple reports

Example:

```json
{
  "id": "report_20260417",
  "project_slug": "rpsbattle",
  "title": "Session 2026-04-17",
  "markdown": "# Session Report\n\nImplemented jump physics.\n\n![After adding jump physics](assets/screenshot_143522_a3f2.png)\n",
  "artifact_ids": ["art_20260417_143522_a3f2"],
  "created_at": "2026-04-17T16:00:00Z",
  "updated_at": "2026-04-17T16:05:00Z"
}
```

## Remaining material risks

- hidden or unclear agent artifact actions would erode trust quickly
- report/artifact linkage could drift if writes are not done carefully
- global manifest can become noisy across projects, so project filtering must exist in APIs from day one
- over-extracting unstable dogfood flows into shared reusable code too early would freeze bad boundaries
- using the same simple backend path for chat, uploads, and report writes is acceptable for dogfood, but may become a concurrency bottleneck later

## Implementation order

### Phase 1: prefs + shell scaffolding

Rivet:

- active project persistence
- global per-user trigger-mode persistence

Loom:

- app shell
- shared chat timeline
- composer
- inline trigger control
- empty artifact tray
- empty report pane

### Phase 2: artifact lifecycle

Rivet:

- artifact manifest persistence
- artifact CRUD/list APIs

Loom:

- screenshot suggestion queue
- accept/edit/dismiss flow
- artifact tray/history
- project tag display

### Phase 3: report persistence and preview

Rivet:

- persisted report markdown
- explicit `artifact_ids[]` linkage

Loom:

- rendered markdown report viewer
- refresh/update loop driven by agent-edited report saves

### Phase 4: narrow multi-project UX

Rivet:

- persisted active project
- project filtering for artifacts and reports

Loom:

- project selector
- loose filtering only

### Phase 5: polish

- mic/device placeholder
- tiny non-primary settings drawer
- light reorder/polish only if still needed
- dogfood with Will + Madeira
