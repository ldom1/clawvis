#!/usr/bin/env bash
# project-init — bootstrap a new Clawvis project
# Usage: run.sh --slug <slug> --name <name> --description <desc>
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"
OPENCLAW_LOGS="${OPENCLAW_LOGS:-$HOME/.openclaw/logs}"
mkdir -p "$OPENCLAW_LOGS"
LOG="$OPENCLAW_LOGS/project-init-$(date +%Y-%m-%d-%H%M).log"

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "skill:project-init" "system" "init:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

for envf in "$SKILL_DIR/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "skill:project-init" "system" "init:start" "project-init started" 2>/dev/null || true

echo "[$(date)] Initializing project..." | tee -a "$LOG"
uv run --directory "$CORE_DIR" python -m project_init "$@" | tee -a "$LOG"
