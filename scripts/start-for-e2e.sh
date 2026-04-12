#!/usr/bin/env bash
# Minimal Clawvis stack for Playwright (Kanban API + Memory API + Vite Hub).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# After load_env_file in start.sh, use repo-local writable roots (avoids 500 when .env PROJECTS_ROOT is not writable here).
export CLAWVIS_E2E_ISOLATE=1
export CLAWVIS_QUIET_START=1
export CLAWVIS_SKIP_START_ECHO=1
# Keep a shell around Vite so EXIT trap still kills Kanban + Memory uvicorn processes.
export CLAWVIS_NO_EXEC_VITE=1
export CLAWVIS_SKIP_AGENT=1
exec bash "${ROOT_DIR}/scripts/start.sh"
