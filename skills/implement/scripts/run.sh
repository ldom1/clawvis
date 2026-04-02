#!/usr/bin/env bash
# implement — execute a single kanban task (called by kanban-implementer)
# Usage: run.sh --task-id <id>
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"
OPENCLAW_LOGS="${OPENCLAW_LOGS:-$HOME/.openclaw/logs}"
mkdir -p "$OPENCLAW_LOGS"
LOG="$OPENCLAW_LOGS/implement-$(date +%Y-%m-%d-%H%M).log"

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "skill:implement" "system" "impl:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

for envf in "$SKILL_DIR/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "skill:implement" "system" "impl:start" "implement started" 2>/dev/null || true

echo "[$(date)] Loading task context..." | tee -a "$LOG"
uv run --directory "$CORE_DIR" python -m implement "$@" | tee -a "$LOG"
