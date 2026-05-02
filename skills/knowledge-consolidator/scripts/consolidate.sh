#!/usr/bin/env bash
# Consolidate today's memory into MEMORY.md and re-embed with QMD.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_DIR="$SKILL_ROOT/core"
# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true
if [ -f "${CLAWVIS_ROOT:-}/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${CLAWVIS_ROOT}/.env"
  set +a
fi

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" dombot-log "ERROR" "cron:knowledge-consolidator" "system" "consolidate:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

MEMORY_DIR="$(uv run --directory "$CORE_DIR" python -c "from knowledge_consolidator.clawvis_paths import memory_root; print(memory_root())")"
MEMORY_FILE="$(uv run --directory "$CORE_DIR" python -c "from knowledge_consolidator.clawvis_paths import memory_root; print(memory_root() / 'MEMORY.md')")"

echo "[consolidate] Starting memory consolidation — $(date '+%Y-%m-%d %H:%M')"

[ -d "$MEMORY_DIR" ] || { echo "[consolidate] ERROR: $MEMORY_DIR not found"; exit 1; }
touch "$MEMORY_FILE"

echo "[consolidate] Running update…"
qmd update

echo "[consolidate] Running qmd embed…"
qmd embed

echo "[consolidate] Rebuilding Quartz site…"
if [ -x ~/Lab/quartz/rebuild.sh ]; then
  ~/Lab/quartz/rebuild.sh
else
  echo "[consolidate] skip Quartz (no ~/Lab/quartz/rebuild.sh)"
fi

echo "[consolidate] Done."
[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:knowledge-consolidator" "system" "consolidate:complete" "Memory consolidation finished" 2>/dev/null || true
