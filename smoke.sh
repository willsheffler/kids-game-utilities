#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH_VALUE="$ROOT/..:$ROOT"

echo "[1/2] Backend smoke"
PYTHONPATH="$PYTHONPATH_VALUE" python -m backend.smoke --root "$ROOT"

echo "[2/2] Frontend build"
(
  cd "$ROOT/app"
  npm run build
)

echo "kids-game-utilities smoke: OK"
