#!/usr/bin/env bash
# Fetch new knowledge sessions.
# Usage:
#   collect.sh                # runs all default sessions
#   collect.sh tech latest    # runs only given sessions
set -euo pipefail
trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:knowledge-consolidator" "system" "collect:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"

SESSIONS=("$@")
if [ "${#SESSIONS[@]}" -eq 0 ]; then
  SESSIONS=(mail tech geopolitics culture community latest tech_news)
fi

for session in "${SESSIONS[@]}"; do
  echo "[collect] curiosity session: $session"
  uv run --directory "$SKILL_DIR/core" python -m knowledge_consolidator "$session"
done

echo "[collect] Rebuilding Quartz site…"
~/Lab/quartz/rebuild.sh
uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:knowledge-consolidator" "system" "collect:complete" "Knowledge collection finished (${#SESSIONS[@]} sessions)" 2>/dev/null || true
