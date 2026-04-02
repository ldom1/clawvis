#!/usr/bin/env bash
set -euo pipefail

trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/Lab/clawvis/skills/logger/core dombot-log "ERROR" "cron:brain-pulse" "system" "cron:fail" "BrainPulse send failed (exit $e)" 2>/dev/null || true; exit $e' EXIT

msg=$'🧠 BrainPulse — ta question du jour !\nhttps://lab.dombot.tech/brain-pulse/daily'

uv run --directory ~/Lab/clawvis/skills/logger/core \
  dombot-log "INFO" "cron:brain-pulse" "system" "cron:start" "BrainPulse send started" 2>/dev/null || true

openclaw message send --channel telegram --target 5689694685 --message "$msg" >/dev/null 2>&1 || true

uv run --directory ~/Lab/clawvis/skills/logger/core \
  dombot-log "INFO" "cron:brain-pulse" "system" "cron:complete" "BrainPulse send finished" 2>/dev/null || true

