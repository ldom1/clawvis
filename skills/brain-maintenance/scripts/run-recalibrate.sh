#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_BRAIN="$SKILL_ROOT/core"
# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" dombot-log "ERROR" "cron:brain-maintenance" "system" "recalibrate:fail" "Brain maintenance recalibrate failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recalibrate:start" "Brain maintenance recalibrate started" 2>/dev/null || true

uv run --directory "$CORE_BRAIN" \
  python -m brain_maintenance recalibrate

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recalibrate:complete" "Brain maintenance recalibrate finished" 2>/dev/null || true
