#!/usr/bin/env bash
# Proactive innovation: scan projects + ideas. ONE message at end (prevents 100+ message loops).
# Run from skill root or cron. Report = stdout; script sends a single Telegram message via TELEGRAM_URL.

trap 'e=$?; [ $e -ne 0 ] && [ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" dombot-log "ERROR" "cron:proactive-innovation" "system" "cron:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

set -e
SKILL_SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$(cd "$SKILL_SCRIPTS/../core" && pwd)"
SKILL_ROOT="$(cd "$SKILL_SCRIPTS/.." && pwd)"
# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true
LOG_DIR="${LOG_DIR:-${TMPDIR:-/tmp}/clawvis-logs}"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/proactive-innovation-$(date +%Y-%m-%d-%H%M).log"

for envf in "$SKILL_ROOT/.env" "$CORE_DIR/.env"; do
  if [ -f "$envf" ]; then set -a; . "$envf"; set +a; fi
done

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:proactive-innovation" "system" "cron:start" "Proactive-Innovation scan started" 2>/dev/null || true

report=$(uv run --directory "$CORE_DIR" python -m proactive_innovation 2>>"$LOG") || { echo "[$(date)] Run failed" >>"$LOG"; exit 1; }
if [ -n "$report" ]; then
  echo "[$(date)] $report" >>"$LOG"
  _tg="${TELEGRAM_URL:-http://127.0.0.1:8094}"
  payload=$(REPORT="$report" python3 -c 'import json, os; print(json.dumps({"text": "🔮 Innovation: " + os.environ["REPORT"]}))')
  curl -fsS -X POST "${_tg%/}/send" -H "Content-Type: application/json" -d "$payload" 2>>"$LOG" || true
fi
if echo "$report" | grep -q "ERROR"; then exit 1; fi

[ -n "${LOGGER_CORE:-}" ] && [ -d "$LOGGER_CORE" ] && uv run --directory "$LOGGER_CORE" \
  dombot-log "INFO" "cron:proactive-innovation" "system" "cron:complete" "Proactive-Innovation scan finished" 2>/dev/null || true
