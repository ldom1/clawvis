#!/usr/bin/env bash
# kanban-implementer — select a task and guide DomBot through implementation
# Usage: run.sh [--project PROJECT_NAME]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"
OPENCLAW_LOGS="${OPENCLAW_LOGS:-$HOME/.openclaw/logs}"
mkdir -p "$OPENCLAW_LOGS"
LOG="$OPENCLAW_LOGS/kanban-implementer-$(date +%Y-%m-%d-%H%M).log"

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:kanban-implementer" "system" "impl:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

for envf in "$SKILL_DIR/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:kanban-implementer" "system" "impl:start" "Kanban Implementer started" 2>/dev/null || true

echo "[$(date)] Selecting task..." | tee -a "$LOG"
uv run --directory "$CORE_DIR" python -m kanban_implementer select "$@" 2>>"$LOG"

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:kanban-implementer" "system" "impl:task-selected" "Task selected, DomBot will implement" 2>/dev/null || true
