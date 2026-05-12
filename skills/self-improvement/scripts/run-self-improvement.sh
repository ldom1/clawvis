#!/bin/bash
# Self-Improvement Review (run from skill dir). Logs under ${CLAWVIS_ROOT}/logs/

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_clawvis_env.sh"

trap 'e=$?; [ $e -ne 0 ] && dombot_log_uv dombot-log "ERROR" "cron:self-improvement" "system" "cron:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

if ! clawvis_env_load; then
  LOGGER_CORE=""
  LOG_DIR="${TMPDIR:-/tmp}/clawvis-self-improvement-logs"
fi
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/self-improvement-$(date +%Y-%m-%d-%H%M).log"

CORE_DIR="$SCRIPT_DIR/../core"
SKILL_ROOT="$SCRIPT_DIR/.."

if [ -n "${CLAWVIS_ROOT:-}" ] && [ -f "${CLAWVIS_ROOT}/.env" ]; then
  set -a
  # shellcheck disable=SC1090
  . "${CLAWVIS_ROOT}/.env"
  set +a
fi
for envf in "$SKILL_ROOT/.env" "$CORE_DIR/.env"; do
  if [ -f "$envf" ]; then set -a; # shellcheck disable=SC1090
    . "$envf"; set +a; fi
done

echo "[$(date)] Starting Self-Improvement Review..." >>"$LOG"
dombot_log_uv dombot-log "INFO" "cron:self-improvement" "system" "cron:start" "Self-Improvement Review started" 2>/dev/null || true

if ! clawvis_uv_run_dir "$CORE_DIR" python -m self_improvment "$@" 2>>"$LOG"; then
  echo "[$(date)] ❌ python -m self_improvment failed (see log)." >>"$LOG"
  exit 1
fi

echo "[$(date)] ✅ Self-Improvement Review complete" >>"$LOG"
dombot_log_uv dombot-log "INFO" "cron:self-improvement" "system" "cron:complete" "Self-Improvement Review finished" 2>/dev/null || true
