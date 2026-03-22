#!/usr/bin/env bash
# Consolidate today's memory into MEMORY.md and re-embed with QMD.
# Meant to be called by the agent (phase consolidate) or directly.
set -euo pipefail
trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:knowledge-consolidator" "system" "consolidate:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

MEMORY_DIR="$HOME/.openclaw/workspace/memory"
MEMORY_FILE="$HOME/.openclaw/workspace/MEMORY.md"

echo "[consolidate] Starting memory consolidation — $(date '+%Y-%m-%d %H:%M')"

# Ensure targets exist
[ -d "$MEMORY_DIR" ] || { echo "[consolidate] ERROR: $MEMORY_DIR not found"; exit 1; }
[ -f "$MEMORY_FILE" ] || { echo "[consolidate] ERROR: $MEMORY_FILE not found"; exit 1; }

# Re-embed MEMORY.md + memory/ into QMD index
echo "[consolidate] Running update…"
qmd update

echo "[consolidate] Running qmd embed…"
qmd embed

echo "[consolidate] Rebuilding Quartz site…"
~/Lab/quartz/rebuild.sh

echo "[consolidate] Done."
uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:knowledge-consolidator" "system" "consolidate:complete" "Memory consolidation finished" 2>/dev/null || true
