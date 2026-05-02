#!/usr/bin/env bash
# kanban-implementer — select a task and guide implementation
# Usage: run.sh [--project PROJECT_NAME]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"
# shellcheck disable=SC1091
source "$(cd "$SKILL_DIR/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true
LOG_DIR="${LOG_DIR:-${TMPDIR:-/tmp}/clawvis-logs}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/kanban-implementer-$(date +%Y-%m-%d-%H%M).log"

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" dombot-log "ERROR" "cron:kanban-implementer" "system" "impl:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

for envf in "$SKILL_DIR/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:kanban-implementer" "system" "impl:start" "Kanban Implementer started" 2>/dev/null || true

echo "[$(date)] Selecting task..." | tee -a "$LOG"
uv run --directory "$CORE_DIR" python -m kanban_implementer select "$@" 2>>"$LOG"

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:kanban-implementer" "system" "impl:task-selected" "Task selected" 2>/dev/null || true
