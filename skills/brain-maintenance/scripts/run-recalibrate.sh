#!/usr/bin/env bash
set -euo pipefail

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:brain-maintenance" "system" "recalibrate:fail" "Brain maintenance recalibrate failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recalibrate:start" "Brain maintenance recalibrate started" 2>/dev/null || true

uv run --directory ~/.openclaw/skills/brain-maintenance/core \
  python -m brain_maintenance recalibrate

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recalibrate:complete" "Brain maintenance recalibrate finished" 2>/dev/null || true

