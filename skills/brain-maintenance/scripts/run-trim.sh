#!/usr/bin/env bash
set -euo pipefail

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:brain-maintenance" "system" "trim:fail" "Brain maintenance trim failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "trim:start" "Brain maintenance trim started" 2>/dev/null || true

uv run --directory ~/.openclaw/skills/brain-maintenance/core \
  python -m brain_maintenance trim

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "trim:complete" "Brain maintenance trim finished" 2>/dev/null || true

