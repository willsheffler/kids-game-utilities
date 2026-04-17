# Kids Game Utilities Implementation Plan V1

Status: ready
Created: 2026-04-17
Maintainer: Will + Lattice

## Purpose

Turn the CAP-converged architecture into a concrete execution plan for the first dogfood build.

This doc is the handoff surface for:

- Loom: frontend
- Rivet: backend

Primary architecture/spec inputs:

- `docs/IMPLEMENTATION_ARCHITECTURE_V1.md`
- `sheffler-standards/KIDS_GAME_DEV_DOGFOOD_V1.md`

## Build target

Build a flexible dev shell that can dogfood the new tooling with Madeira over the next few days.

The first app does not need to be a polished final kids-game product.
It needs to exercise:

- shared chat
- inline trigger control
- screenshot suggestion/capture
- artifact history
- report persistence/viewing
- narrow multi-project support

## Out of scope for first pass

- auth
- DM/private routing
- deep multi-project partitioning
- per-project chats/manifests/runtime state
- rich report editing UI
- user-facing passive-capture tuning
- advanced mic/device work beyond a placeholder
- backend service migration beyond the minimum needed contracts

## Role split

### Loom

Own:

- UI shell
- shared chat integration on the frontend side
- DevPanel
- inline trigger control
- screenshot suggestion UI
- artifact tray/history UI
- report viewer shell
- project selector UI

Comment on:

- shared component extraction boundaries
- frontend-facing API ergonomics

### Rivet

Own:

- persisted prefs
- artifact manifest and CRUD
- report persistence
- project filtering
- contract docs for screenshot suggestions / report persistence

Comment on:

- boundary discipline
- persistence semantics
- sequencing risks

## Concrete work phases

### Phase 1: Contracts and shell scaffolding

Goal:

- get stable frontend/backend shapes before building too much UX

Loom:

- scaffold app shell in `kids-game-utilities`
- render:
  - shared chat timeline
  - composer
  - inline trigger control placeholder
  - empty artifact tray
  - empty report pane
  - project selector placeholder

Rivet:

- define minimal persisted prefs contract:
  - active project
  - trigger mode
- choose file locations / JSON persistence layout
- document minimal API contract shape

Deliverable:

- shell running with mocked or placeholder state
- written contract for prefs

### Phase 2: Artifact lifecycle

Goal:

- make screenshot artifacts real before report work

Loom:

- screenshot capture UI
- suggestion queue
- accept/edit/dismiss flow
- artifact tray/history rendering
- project tag display

Rivet:

- artifact manifest persistence
- artifact CRUD/list APIs
- project filtering in list APIs
- soft-delete and dismissed state handling

Deliverable:

- end-to-end screenshot capture
- end-to-end suggestion -> accept/edit/dismiss flow
- manifest-backed artifact history

### Phase 3: Report persistence and viewer

Goal:

- make the report loop usable with chat-mediated edits

Loom:

- rendered markdown report viewer
- refresh/update loop
- report open/view affordance in the DevPanel

Rivet:

- report persistence
- `artifact_ids[]` linkage
- list/get/update report APIs

Deliverable:

- agent can draft report
- backend persists markdown + linkage
- frontend shows rendered markdown with embedded images

### Phase 4: Narrow multi-project support

Goal:

- support project switching without deep partitioning

Loom:

- real project selector
- loose filtering controls only

Rivet:

- persisted active project
- artifact/report filtering by project

Deliverable:

- one active project can be selected and remembered
- artifact/report queries can filter by project
- shared timeline remains the default

### Phase 5: Polish for dogfood

Goal:

- remove obvious rough edges before Will + Madeira use it

Loom:

- inline trigger control fully wired
- tiny non-primary settings drawer
- mic/device placeholder
- basic visual polish and mobile sanity check

Rivet:

- tighten persistence behavior
- lock/atomic writes where needed
- verify path handling for markdown image rendering

Deliverable:

- usable dogfood build for real sessions

## Minimal backend contracts to settle early

### Prefs

Per user, global for now:

- `active_project`
- `trigger_mode`

### Artifacts

Need to support:

- create/upload
- list with optional project filter
- update label/status/linkage
- soft-delete

### Reports

Need to support:

- create
- get
- list with optional project filter
- update markdown and linkage

## Minimal schemas

### Artifact

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

### Report

- `id`
- `project_slug`
- `title`
- `markdown`
- `artifact_ids[]`
- `created_at`
- `updated_at`

## Important constraints

- report display order comes from markdown prose / image placement, not artifact ordering
- `artifact_ids[]` is linkage only, not ordering
- artifacts may appear in multiple reports
- deleted artifacts are soft-deleted, not hard-removed in v1
- dismissed suggestions remain in the manifest

## Main implementation risks

- ambiguous ownership between artifact linkage and report markdown
- over-extracting unstable app-specific flows into shared code too early
- making multi-project support too deep too early
- hidden artifact/capture behavior that erodes trust
- write conflicts on manifest/report persistence if file writes are not careful

## Testing strategy

Testing should happen at more than one layer.

The minimum useful stack is:

1. isolated unit tests
2. contract and integration tests
3. automated headless browser harness component tests
4. automated headless browser harness app tests
5. manual/agent-driven headless browser debugging sessions
6. in-situ full-app tests
7. manual dogfood checklist

### 1. Isolated unit tests

Required early backend-focused tests:

- prefs persistence:
  - active project save/load
  - trigger mode save/load
- artifact manifest behavior:
  - create artifact
  - update label
  - suggested/accepted/dismissed/deleted status transitions
  - linked report IDs update correctly
- report persistence:
  - create/update report
  - `artifact_ids[]` preserved correctly
- path/render helpers:
- markdown image path generation/resolution behaves as expected
- write discipline:
  - manifest/report writes are atomic enough for dogfood use

Required early frontend/unit-level tests:

- pure reducer/store logic behind:
  - chat state
  - capture queue
  - settings state
- small component-level logic that does not need a browser harness to validate

### 2. Contract and integration tests

These protect Loom/Rivet parallel work from drifting request/response shapes and broken joins.

Minimum contract coverage:

- prefs payloads
- artifact create/list/update payloads
- report create/get/update payloads
- screenshot suggestion contract shape
- report-save/update structured agent tag contract

Minimum integration coverage:

- screenshot suggestion -> accept/edit/dismiss -> manifest update
- screenshot capture -> upload -> artifact tray visible
- report create/update -> persisted markdown + rendered preview
- reload app -> active project + trigger mode restored
- project filtering works without breaking shared timeline assumptions

These tests should fail loudly if:

- a field is renamed
- a field disappears
- frontend and backend assume different payload shapes

### 3. Automated headless browser harness component tests

These are not full-app tests.
They are browser-level component tests with mocked data/contracts.

They should focus on components and interactions that are easier to reason about in isolation:

- chat panel rendering and send behavior
- message ordering / dedup behavior
- visible `will trigger / won't trigger` state rendering
- trigger control rendering and mode switching UI
- screenshot suggestion item / queue behavior
- accept / edit / dismiss transitions
- suggested-label editing
- artifact tray rendering
- report viewer rendering shell
- generic settings drawer shell
- mic/dictation control shell

Also:

- any reducer/store logic behind chat, capture queue, or settings should have pure tests separately from browser-rendered component tests

The goal is:

- prove component behavior without needing the entire app/backend running
- catch UI regressions and event-handling bugs early
- keep component development fast

Harness guidance:

- build a dedicated component testbed route with mocked backends and explicit knobs
- keep scenarios deterministic
- avoid relying on timing-sensitive ambient polling where possible
- do not let the harness become a second app

### 4. Automated headless browser harness app tests

These still run headlessly, but they exercise a larger assembled app surface rather than one isolated component.

Use them as smoke/regression coverage for real seams:

- chat + artifact tray
- suggestion flows
- report viewer rendering
- reload persistence
- project filter behavior

Important caution:

- these are not the primary place to validate persistence semantics
- contract/integration tests remain the stronger guardrail for v1

### 5. Manual / agent-driven headless browser debugging

This is distinct from the automated harness layer above.

Use it when:

- debugging richer UI behavior
- exploring ambiguous interaction issues
- reproducing bugs before hardening them into automated tests
- letting an agent actively drive the browser harness to probe failures

This layer should sit below manual dogfood and above ordinary automated browser harness tests.

Important rule:

- manual/agent-driven browser debugging should often produce new automated headless-browser tests once a scenario is understood and worth preserving
- any reproducible bug found this way should usually yield either:
  - a new automated browser-harness test
  - or a short written reason it remains manual for now

Typical uses:

- reproduce a screenshot suggestion queue bug
- inspect a report-pane refresh issue
- debug trigger-mode UI confusion
- verify mocked browser-harness scenarios before promoting them into automated checks

### 6. In-situ full-app tests

These should run against the actual assembled app with real persistence behavior.

Minimum required flows before dogfood:

- chat loads, sends, receives replies
- screenshot capture -> upload -> manifest entry -> artifact tray visible
- suggestion -> accept/edit/dismiss -> persisted status change
- report create/update -> persisted markdown + rendered report visible
- reload app -> active project and trigger mode restore correctly
- project filtering works without breaking the shared-timeline assumption

### 7. Manual dogfood checklist

Before calling the build ready for real use with Madeira:

- run one real chat session
- accept one screenshot suggestion
- dismiss one screenshot suggestion
- create one report
- revise one report through chat
- reload and verify project + trigger persistence
- switch project once and verify filtering still behaves sensibly

## Test boundary guidance

Use isolated component/browser-harness tests for:

- presentation behavior
- local UI state transitions
- queue/list rendering
- simple interaction flows with mocked contracts

Use in-situ full-app tests for:

- persistence behavior
- real API integration
- manifest/report linkage
- reload/resume correctness
- any flow where frontend and backend state can drift
- routing/shared-state interactions across multiple surfaces
- project switching and context reset behavior
- real screenshot capture/upload behavior

Do not rely on only one layer.
If we only test in isolation, persistence drift slips through.
If we only test in the full app, iteration slows down and frontend regressions become harder to localize.
If we only do manual browser probing, known bugs will keep recurring because they were never turned into automated browser-harness checks.

## Non-deferrable required tests before dogfood

### Backend / contract tests

- `prefs_persist_active_project_across_restart`
- `prefs_persist_trigger_mode_across_restart`
- `artifact_create_suggested_then_accept_updates_manifest`
- `artifact_dismiss_preserves_manifest_entry`
- `artifact_soft_delete_hides_from_default_listing_but_preserves_record`
- `artifact_list_filters_by_project_slug`
- `report_create_persists_markdown_and_artifact_ids`
- `report_update_preserves_existing_linkage_when_expected`
- `report_and_manifest_linkage_remain_consistent`
- `markdown_image_paths_render_from_persisted_artifact_paths`

### Browser harness component tests

- `test_chat_panel_sends_message`
- `test_chat_panel_renders_history`
- `test_chat_panel_polls_push`
- `test_screenshot_capture_requires_label`

### Browser harness app tests

- `suggestion_accept_flow_shows_artifact_in_history`
- `suggestion_dismiss_flow_marks_item_dismissed_and_removes_from_active_queue`
- `report_viewer_renders_saved_markdown_with_embedded_image`
- `reload_restores_active_project_and_trigger_mode`
- `project_filter_changes_artifact_and_report_views_without_breaking_shared_chat`

### Non-deferrable full-flow checks

- screenshot round-trip
- one screenshot-to-report happy path
- verify chat still works in the new shell, not just in the old frontend

## First practical kickoff

If work starts immediately, the first useful tasks are:

1. Loom:
   - scaffold the shell and shared chat integration surface
   - add empty placeholders for artifact tray, report pane, project selector
2. Rivet:
   - define persisted prefs contract and file layout
   - define artifact/report JSON shapes and first API surface
3. Both:
   - agree on the screenshot suggestion contract
   - agree on minimal report API payloads before wiring UI to real endpoints
   - agree on the first contract tests before parallel implementation proceeds
