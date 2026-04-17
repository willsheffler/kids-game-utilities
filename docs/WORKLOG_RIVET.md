# Rivet Work Log

## Current

- task: Backend lane complete for the current v1 shell cut. Persistence, HTTP routes, upload/static serving, chat/history/poll bridge, runtime/session helpers, and report-linkage behavior are implemented and verified.
- assumption changes:
  - Backend implementation can start as repo-local file-backed Python modules and tests without waiting for service migration or frontend integration.
  - Canonical trigger-mode values remain `auto|mention|manual` on the backend contract.
  - No web framework is preinstalled here, so the first HTTP surface should use the Python standard library rather than adding framework/dependency work.
  - Port `8765` is already in use locally during smoke testing, so ad hoc verification may need another port even though the default runner/docs still use `8765`.
  - Artifact payloads now explicitly include `url` and `filename`; frontend should treat `url` as canonical rather than reconstructing upload paths from basename.
  - Report persistence should tolerate loose all-project mode: if `projectSlug` is empty, backend should allow an unscoped report instead of failing.
  - Report linkage should not depend entirely on the frontend sending `artifactIds`; backend should derive artifact linkage from markdown image paths when possible.
- tests run:
  - `PYTHONPATH=/home/sheffler/.openclaw/workspace:/home/sheffler/.openclaw/workspace/submodules/kids-game-utilities python -m unittest discover -s /home/sheffler/.openclaw/workspace/submodules/kids-game-utilities/tests -p 'test_*.py'` -> 43 tests passed
  - `PYTHONPATH=/home/sheffler/.openclaw/workspace/submodules/kids-game-utilities python -m backend.server --help` -> OK
  - ephemeral-port smoke: `/bootstrap`, `/artifacts` upload, and `/uploads/*` static serving all returned 200
  - `cd app && npm run build` -> OK (minor Svelte warnings only)
  - `PYTHONPATH=/home/sheffler/.openclaw/workspace:/home/sheffler/.openclaw/workspace/submodules/kids-game-utilities python -m backend.smoke --root /home/sheffler/.openclaw/workspace/submodules/kids-game-utilities` -> OK
  - `bash smoke.sh` -> OK (backend smoke + frontend build)
  - post-Loom wiring recheck: `bash smoke.sh` -> still OK after status/session integration
  - `uv run --with pytest pytest tests/frontend/test_fix_batch.py -v` -> 15 passed
- blocker:
- next:
  - Backend is intentionally held stable for Loom's current frontend fix batch.
  - Support only if Loom finds a real seam; otherwise limit backend changes to narrow defensive tests/docs.

## Notes

- Added `backend/store.py` with atomic JSON persistence for:
  - per-user prefs: `active_project`, `trigger_mode`
  - global artifact manifest with soft-delete/dismissed retention
  - report persistence with explicit `artifact_ids[]` linkage
- Added `docs/BACKEND_CONTRACTS_V1.md`
- Added `backend/api.py` for stable frontend-facing payloads
- Added `backend/http_api.py` and `backend/server.py` for a runnable stdlib HTTP surface
- Added compatibility aliases for `/bootstrap` and `/artifacts`
- Added JSON base64 image upload handling and `/uploads/*` static file serving
- Added `backend/chat_bridge.py` and HTTP routes for `/chat`, `/history/:session`, and `/poll/:session`
- Added `backend/runtime_bridge.py` and HTTP routes for `/health`, `/sessions`, and `/agent-status/:session`
- Added direct bridge tests in:
  - `tests/test_chat_bridge.py`
  - `tests/test_runtime_bridge.py`
- Tightened artifact payloads with explicit `url` and `filename` fields after spotting a preview-path mismatch in the current frontend scaffold
- Tightened report persistence so markdown image paths auto-link artifacts and empty `projectSlug` saves as an unscoped report instead of failing
- Added repo-level `smoke.sh` so the current backend/frontend slice can be re-verified in one command
- Loom replied and aligned trigger-mode values to canonical backend names `auto|mention|manual`
- Loom also wired StatusDot to `/agent-status/:session` and session auto-discovery from `/sessions`; current frontend build still passes
- Holding backend contracts stable during the current frontend correctness batch; added one store-level regression test to ensure repeated saves of the same markdown-linked report do not duplicate artifact linkage
- Independent backend-side recheck of Loom's frontend fix batch passed under `uv`/`pytest`: 15 fix-batch tests green against the live backend
- Backend/backend-pointer commits were pushed:
  - kids-game-utilities: `8c157e4` (`Add kids-game backend API and smoke coverage`)
  - kids-game-utilities: `b79e452` (`Tolerate unscoped reports and derive artifact links`)
  - parent workspace pointer: `ba92b53` (`Update kids-game-utilities backend API submodule`)
  - parent workspace pointer: `354bf9f` (`Update kids-game-utilities report flow submodule`)
- Added `backend/smoke.py` for repeatable backend route smoke verification
- Added non-deferrable contract tests in:
  - `tests/test_store.py`
  - `tests/test_api.py`
  - `tests/test_http_api.py`
