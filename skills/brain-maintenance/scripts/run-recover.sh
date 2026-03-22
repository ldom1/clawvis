#!/usr/bin/env bash
set -euo pipefail

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/.openclaw/skills/logger/core dombot-log "ERROR" "cron:brain-maintenance" "system" "recover:fail" "Brain maintenance recover failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recover:start" "Brain maintenance recover started" 2>/dev/null || true

uv run --directory ~/.openclaw/skills/brain-maintenance/core \
  python -m brain_maintenance recover

uv run --directory ~/.openclaw/skills/logger/core \
  dombot-log "INFO" "cron:brain-maintenance" "system" "recover:complete" "Brain maintenance recover finished" 2>/dev/null || true

