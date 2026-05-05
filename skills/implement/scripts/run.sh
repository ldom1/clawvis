#!/usr/bin/env bash
# implement — execute a single kanban task (called by kanban-implementer)
# Usage: run.sh --task-id <id>
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"
# shellcheck disable=SC1091
source "$(cd "$SKILL_DIR/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true
LOG_DIR="${LOG_DIR:-${TMPDIR:-/tmp}/clawvis-logs}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/implement-$(date +%Y-%m-%d-%H%M).log"

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" dombot-log "ERROR" "skill:implement" "system" "impl:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

for envf in "$SKILL_DIR/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && clawvis_uv_run_dir "$LOGGER_CORE" \
  dombot-log "INFO" "skill:implement" "system" "impl:start" "implement started" 2>/dev/null || true

echo "[$(date)] Loading task context..." | tee -a "$LOG"
clawvis_uv_run_dir "$CORE_DIR" python -m implement "$@" | tee -a "$LOG"
