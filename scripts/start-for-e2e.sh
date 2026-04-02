#!/usr/bin/env bash
# Minimal Clawvis stack for Playwright (Kanban API + Memory API + Vite Hub).
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export CLAWVIS_QUIET_START=1
export CLAWVIS_SKIP_START_ECHO=1
# Keep a shell around Vite so EXIT trap still kills Kanban + Memory uvicorn processes.
export CLAWVIS_NO_EXEC_VITE=1
exec bash "${ROOT_DIR}/scripts/start.sh"
