#!/usr/bin/env bash
# Diagnose why Discord receives nothing. Shows config and optionally sends a test message.
# Usage: discord-check.sh [--test]
#   --test  send a test message via uv run

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$(cd "$SCRIPT_DIR/../core" && pwd)"
# shellcheck disable=SC1091
source "$(cd "$SCRIPT_DIR/../.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true
CONFIG_JSON="${CLAWVIS_CONFIG_JSON:-}"
if [ -z "$CONFIG_JSON" ] && [ -n "${CLAWVIS_ROOT:-}" ] && [ -f "${CLAWVIS_ROOT}/config.json" ]; then
  CONFIG_JSON="${CLAWVIS_ROOT}/config.json"
fi

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [discord-check] $*"
}

if [ -f "$CORE_DIR/.env" ]; then
  log "Loading env from $CORE_DIR/.env"
  set -a
  # shellcheck disable=SC1090
  source "$CORE_DIR/.env"
  set +a
else
  log "No .env found at $CORE_DIR/.env (using current shell env only)"
fi

echo "=== Discord logger config ==="
echo ""
echo "1. Env (.env + shell):"
for k in DISCORD_BOT_TOKEN DISCORD_CHANNEL_ID_GENERAL DISCORD_CHANNEL_ID_LOGS DISCORD_CHANNEL_ID_PROJECTS DISCORD_CHANNEL_ID_OPS DISCORD_CHANNEL_ID_ALERTS DISCORD_CHANNEL_ID_INNOVATIONS DOMBOT_DISCORD_DM_ME; do
  v="${!k:-}"
  [ -z "$v" ] && echo "   $k = (not set)" || echo "   $k = ${v:0:20}..."
done
echo ""
echo "2. config.json channels.discord (optional mirror):"
if [ -n "$CONFIG_JSON" ] && [ -f "$CONFIG_JSON" ]; then
  if command -v jq &>/dev/null; then
    jq -r '.channels.discord | to_entries | map("   \(.key) = \(.value)") | .[]' "$CONFIG_JSON" 2>/dev/null || true
  else
    grep -A 20 '"discord"' "$CONFIG_JSON" | head -15
  fi
else
  echo "   (no CLAWVIS_ROOT/config.json — set CLAWVIS_CONFIG_JSON or CLAWVIS_ROOT)"
fi
echo ""
echo "3. Fix: set at least DISCORD_BOT_TOKEN and one DISCORD_CHANNEL_ID_* target in core/.env"
echo "   Channel ID: enable Developer Mode in Discord → right-click channel → Copy Channel ID."
echo "   Optional: mirror channel ids under channels.discord in repo config.json."
echo ""

if [ "${1:-}" = "--test" ]; then
  log "--test enabled"
  echo "4. Sending test message..."
  if [ -n "${DISCORD_CHANNEL_ID_GENERAL:-}" ]; then
    log "Calling discord-send.sh for general channel"
    "$SCRIPT_DIR/discord-send.sh" general "DomBot logger test — if you see this, Discord is OK."
    echo "   Sent to DISCORD_CHANNEL_ID_GENERAL via uv run."
    log "Test send completed"
  else
    echo "   Missing DISCORD_CHANNEL_ID_GENERAL in core/.env"
    log "Test send aborted: missing DISCORD_CHANNEL_ID_GENERAL"
    exit 1
  fi
fi
