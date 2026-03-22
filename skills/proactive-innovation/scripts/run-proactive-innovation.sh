#!/bin/bash
# Proactive innovation: scan projects + ideas. ONE message at end (prevents 100+ message loops).
# Run from skill root or cron. Report = stdout; script sends a single Telegram message.

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:proactive-innovation" "system" "cron:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

set -e
SKILL_SCRIPTS="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$(cd "$SKILL_SCRIPTS/../core" && pwd)"
SKILL_ROOT="$(cd "$SKILL_SCRIPTS/.." && pwd)"
OPENCLAW_LOGS="${OPENCLAW_LOGS:-$HOME/.openclaw/logs}"
mkdir -p "$OPENCLAW_LOGS"
LOG="$OPENCLAW_LOGS/proactive-innovation-$(date +%Y-%m-%d-%H%M).log"

# Load .env so API keys are available (skill root then core; Python also loads with override)
for envf in "$SKILL_ROOT/.env" "$CORE_DIR/.env"; do
  if [ -f "$envf" ]; then set -a; . "$envf"; set +a; fi
done

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:proactive-innovation" "system" "cron:start" "Proactive-Innovation scan started" 2>/dev/null || true

report=$(uv run --directory "$CORE_DIR" python -m proactive_innovation 2>>"$LOG") || { echo "[$(date)] Run failed" >>"$LOG"; exit 1; }
if [ -n "$report" ]; then
  echo "[$(date)] $report" >>"$LOG"
  openclaw message send --channel telegram --target 5689694685 --message "🔮 Innovation: $report" 2>>"$LOG" || true
fi
# Exit non-zero when report contains ERROR (e.g. 401) so DomBot/cron see failure
if echo "$report" | grep -q "ERROR"; then exit 1; fi

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:proactive-innovation" "system" "cron:complete" "Proactive-Innovation scan finished" 2>/dev/null || true
