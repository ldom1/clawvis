#!/usr/bin/env bash
set -euo pipefail
trap 'e=$?; [ $e -ne 0 ] && uv run --directory ~/Lab/clawvis/skills/logger/core dombot-log "ERROR" "system:restart" "system" "restart:fail" "Script failed (exit $e)" 2>/dev/null || true; exit $e' EXIT
HUB="${HUB:-/home/lgiron/Lab/hub}"

echo "▶ Restarting Lab Hub (background)..."
cd "$HUB" && nohup ./restart.sh > /tmp/lab-hub.log 2>&1 &
sleep 18

echo ""
echo "▶ Healthcheck..."
"$HUB/healthcheck.sh" || true

echo ""
echo "▶ Restarting OpenClaw gateway..."
openclaw gateway restart || true

echo ""
echo "▶ System restart done."
uv run --directory ~/Lab/clawvis/skills/logger/core \
  dombot-log "INFO" "system:restart" "system" "restart:complete" "Full system restart finished" 2>/dev/null || true
