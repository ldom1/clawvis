#!/usr/bin/env bash
# Fetch new knowledge sessions.
# Usage:
#   collect.sh                # runs all default sessions
#   collect.sh tech latest    # runs only given sessions
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOGGER_CORE="${SKILLS_ROOT}/logger/core"

_dombot_log() {
  [[ -d "${LOGGER_CORE}" ]] || return 0
  uv run --directory "${LOGGER_CORE}" dombot-log "$@" 2>/dev/null || true
}

trap 'e=$?; [ $e -ne 0 ] && _dombot_log "ERROR" "cron:knowledge-consolidator" "system" "collect:fail" "Script failed (exit $e)"; exit $e' EXIT

SESSIONS=("$@")
if [ "${#SESSIONS[@]}" -eq 0 ]; then
  SESSIONS=(mail tech geopolitics culture community latest tech_news)
fi

for session in "${SESSIONS[@]}"; do
  echo "[collect] curiosity session: $session"
  uv run --directory "$SKILL_DIR/core" python -m knowledge_consolidator "$session"
done

if [[ -x "${HOME}/Lab/quartz/rebuild.sh" ]]; then
  echo "[collect] Rebuilding Quartz site…"
  "${HOME}/Lab/quartz/rebuild.sh"
else
  echo "[collect] Skip Quartz rebuild (${HOME}/Lab/quartz/rebuild.sh missing or not executable)"
fi
_dombot_log "INFO" "cron:knowledge-consolidator" "system" "collect:complete" "Knowledge collection finished (${#SESSIONS[@]} sessions)"
