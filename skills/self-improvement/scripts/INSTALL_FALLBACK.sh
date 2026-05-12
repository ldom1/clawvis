#!/bin/bash
# Install Self-Improvement cron wrapper (logs under ${CLAWVIS_ROOT}/logs when repo resolved)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/_clawvis_env.sh"

trap 'e=$?; [ $e -ne 0 ] && dombot_log_uv dombot-log "ERROR" "skill:self-improvement" "system" "install:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

clawvis_env_load || LOGGER_CORE=""
LOG_HINT="${LOG_DIR:-${TMPDIR:-/tmp}/clawvis-self-improvement-logs}"

echo "🔧 Self-Improvement runner: $SCRIPT_DIR/run-self-improvement.sh"
echo "   Logs: $LOG_HINT/"
echo ""
echo "To run via system crontab (e.g. 08:00):"
echo "  0 8 * * * $SCRIPT_DIR/run-self-improvement.sh"
echo ""
echo "Or use Clawvis scheduler job self-improvement / workflow knowledge-and-innovation."
dombot_log_uv dombot-log "INFO" "skill:self-improvement" "system" "install:instructions" "Self-Improvement install instructions shown" 2>/dev/null || true
