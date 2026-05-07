#!/usr/bin/env bash
# Morning Briefing — cron entrypoint with central logging
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MB_DIR="$SKILL_ROOT"
# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true
LOG_DIR="${LOG_DIR:-${TMPDIR:-/tmp}/clawvis-logs}"
mkdir -p "$LOG_DIR"

ENV_LOCAL="${HUB_ROOT:-$HOME/Lab/hub-ldom/instances/ldom}/.env.local"
[ -f "$ENV_LOCAL" ] && set -a && . "$ENV_LOCAL" && set +a

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" dombot-log "ERROR" "cron:morning-briefing" "system" "cron:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "cron:morning-briefing" "system" "cron:start" "Morning briefing started" 2>/dev/null || true

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
clawvis_uv_run_dir "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes
=======
UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/morning-briefing" \
  uv run --directory "$MB_DIR/core" python "$MB_DIR/morning-briefing.py"
>>>>>>> Stashed changes

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "cron:morning-briefing" "system" "cron:complete" "Morning briefing finished" 2>/dev/null || true
