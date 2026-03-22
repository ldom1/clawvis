#!/usr/bin/env bash
# Morning Briefing — cron entrypoint with central logging
set -euo pipefail

OPENCLAW_LOGS="${OPENCLAW_LOGS:-$HOME/.openclaw/logs}"
mkdir -p "$OPENCLAW_LOGS"

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:morning-briefing" "system" "cron:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:morning-briefing" "system" "cron:start" "Morning briefing started" 2>/dev/null || true

uv run --directory ~/.openclaw/skills/morning-briefing \
  python ./morning-briefing.py

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:morning-briefing" "system" "cron:complete" "Morning briefing finished" 2>/dev/null || true

