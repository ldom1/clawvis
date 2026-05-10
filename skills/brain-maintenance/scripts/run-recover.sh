#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_BRAIN="$SKILL_ROOT/core"
# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" dombot-log "ERROR" "cron:brain-maintenance" "system" "recover:fail" "Brain maintenance recover failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recover:start" "Brain maintenance recover started" 2>/dev/null || true

clawvis_uv_run_dir "$CORE_BRAIN" \
  python -m brain_maintenance recover

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recover:complete" "Brain maintenance recover finished" 2>/dev/null || true
