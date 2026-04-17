# Kids Game Utilities

Shared tooling for kids' AI-assisted web game development and adjacent dogfood apps.

Current status:

- backend persistence/contracts/http surface implemented
- frontend shell wired to the current backend surface
- smoke checks are in place and currently green
- ready for dogfood on the current v1 shell cut

Key docs:

- `docs/IMPLEMENTATION_ARCHITECTURE_V1.md`
- `docs/CAP_BRIEF_LOOM_RIVET_V1.md`
- `docs/IMPLEMENTATION_PLAN_V1.md`
- `docs/BACKEND_CONTRACTS_V1.md`

## Current backend slice

Backend modules:

- `backend/store.py` — file-backed persistence for prefs, artifacts, reports
- `backend/api.py` — stable frontend-facing payload adapter
- `backend/http_api.py` — stdlib HTTP layer exposing `/api/*`
- `backend/server.py` — runner entrypoint

Run it:

```bash
cd /home/sheffler/.openclaw/workspace/submodules/kids-game-utilities
python -m backend.server --root . --host 127.0.0.1 --port 8765
```

Then point the frontend at:

```bash
VITE_BACKEND_URL=http://127.0.0.1:8765 npm run dev
```

Quick smoke:

```bash
cd /home/sheffler/.openclaw/workspace/submodules/kids-game-utilities
python -m backend.smoke --root .
```

Combined backend + frontend smoke:

```bash
cd /home/sheffler/.openclaw/workspace/submodules/kids-game-utilities
bash smoke.sh
```

Current HTTP routes:

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

Compatibility aliases for the current frontend scaffold:

- `GET /bootstrap?userId=...`
- `GET|POST /artifacts`

Note:

- the backend now includes a narrow harness/chatlog/spool bridge for the existing shared chat panel
- runtime/session helper routes are also available for status dots and backend-target discovery
