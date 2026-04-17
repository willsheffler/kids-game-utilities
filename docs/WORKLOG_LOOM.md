# Loom Work Log

## Current

- task: Lattice fix batch — all 5 fixes complete, all tests passing
- status: complete — ready for dogfood
- tests run: 73/73 (15 contract + 15 fix-batch + 43 backend)
- blocker: none
- next: dogfood with Will + Madeira

## Log

### 2026-04-17 07:30 — Fix batch complete (Lattice review)
All 5 fixes from the Lattice-assigned batch are done:

1. **History replay side effects** — ChatPanel.addMessage accepts `{ fromHistory }` option. When true, `dispatch('suggest-screenshot')` and `dispatch('save-report')` are suppressed. History loader passes `fromHistory: true`.

2. **userId consistency** — ProjectSelector accepts `userId` prop (no longer hardcoded 'will'). App.svelte passes `userId={user}` to ProjectSelector.

3. **Project switch refresh** — ProjectSelector dispatches `change` event. App.svelte reloads artifacts on change. ReportViewer is now reactive to `project` prop changes via `$:` block — reloads reports when project changes while viewer is open.

4. **Markdown rendering** — ReportViewer uses `{@html marked(activeReport.markdown || '')}` instead of `<pre>`. CSS updated for rendered HTML (headings, lists, images, code blocks). `marked` library installed and imported.

5. **Trigger mode enforcement** — ChatPanel accepts `triggerMode` prop. New `shouldSendToAgent(text)` function gates `send()`: auto=always, mention=requires `@word`, manual=never. App.svelte passes `{triggerMode}` to ChatPanel.

Tests added: `tests/frontend/test_fix_batch.py` — 15 tests covering all 5 fixes:
- 3 history replay side-effect tests (tag parsing, stripping, fromHistory semantics)
- 3 userId consistency tests (arbitrary userId, per-user trigger mode, per-user project)
- 2 project switch refresh tests (artifacts filter, reports filter)
- 3 markdown rendering tests (headings/lists, embedded images, upload path serves)
- 4 trigger mode enforcement tests (auto/mention/manual logic, backend round-trip)

Full suite: 73/73 passing. Build: clean, 98KB JS.

### 2026-04-17 01:40 — Phase 1 start
Starting app scaffold. Creating Svelte+Vite project, App.svelte shell with DevPanel layout, placeholder components for artifact tray, report pane, project selector, trigger control.

### 2026-04-17 02:00 — Phase 1 shell complete
Created:
- app/ — Svelte+Vite project
- App.svelte — grid layout with DevPanel, content area, responsive
- ChatPanel.svelte — full chat with history, send, polling, dedup, message labels
- DevPanel.svelte — side panel container
- ArtifactTray.svelte — placeholder thumbnail strip
- TriggerControl.svelte — inline always/mention/off toggle
- ProjectSelector.svelte — placeholder dropdown
- ReportViewer.svelte — placeholder toggle + viewer pane
- StatusDot.svelte — busy/idle/error indicator

Build: clean, 47KB JS, 5.7KB CSS

### 2026-04-17 02:15 — Phase 2+3 frontend wiring
- ScreenshotCapture wired to POST /api/artifacts (creates artifact via backend)
- ScreenshotSuggestion toast for agent-suggested screenshots
- ReportViewer wired to GET /api/reports, auto-refresh every 5s
- ProjectSelector wired to GET /api/projects, POST /api/prefs/active-project
- App.svelte bootstrap from GET /api/bootstrap
- ArtifactTray loads from GET /api/artifacts
- TriggerControl aligned to backend canonical values (auto|mention|manual)
- Seam note from Rivet: aligned on trigger mode values, bootstrap payload shape confirmed

Build: 54KB JS, 8.5KB CSS, clean

### 2026-04-17 02:05 — Dev server integration verified
- Vite dev proxy configured: /api → localhost:8790 (Rivet backend), /chat /poll /history → localhost:8767 (Pensieve)
- Backend running on 8790, all endpoints responding (bootstrap, projects, artifacts, reports)
- Frontend → Vite proxy → backend verified end-to-end
- Dev server running at http://localhost:5173/

Status: Phase 1-3 frontend complete. All components wired to backend contracts. Ready for integration testing with real data.

### 2026-04-17 02:15 — Contract tests + proxy consolidation
- 15 contract tests: bootstrap, artifacts (path + upload), prefs, reports, projects
- Screenshot field names aligned: image_b64, image_filename (matching Rivet's backend)
- All proxy routes consolidated to 8790 (Rivet's backend bridges chat to harness)
- Rivet confirmed: /chat, /history/:session, /poll/:session bridged through backend
- Backend test suite: 29 tests green

Phase 1-3 complete. Phases 4-5 remaining:
- Phase 4: Project selector wired, loose filtering
- Phase 5: Trigger control wired, visual polish, dogfood readiness
Tests: none yet (need contract tests from Rivet before integration tests)
Next: wire ChatPanel to real backend, start screenshot capture UI


### 2026-04-17 02:25 — Phase 4-5 complete
- TriggerControl now persists to backend via POST /api/prefs/trigger-mode
- ProjectSelector already wired from Phase 2 (loads from bootstrap, persists)
- All proxy routes consolidated to Rivet's backend (8790)
- Build: 54KB JS, clean

All 5 phases of frontend work complete:
1. Shell scaffold (App, DevPanel, placeholders)
2. Screenshot capture + suggestion toast + artifact creation via API
3. Report viewer wired to backend, auto-refresh
4. Project selector wired, trigger control persists
5. Contract tests (15), proxy config, build clean

Status: Frontend ready for integration testing and dogfood.
