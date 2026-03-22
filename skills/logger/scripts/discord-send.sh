#!/usr/bin/env bash
# Send a message to Discord (no log file) via uv run discord-cli.
# Usage: discord-send.sh TARGET MESSAGE
#   TARGET: Discord channel ID, or one of: general | logs | projects | ops | alerts | dm | innovations
# Usage: discord-send.sh MESSAGE
#   If single arg, message is sent to general (DISCORD_CHANNEL_ID_GENERAL).
# Example: discord-send.sh general "Cron completed successfully"
# Example: discord-send.sh "Quick notification to general"

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$(cd "$SCRIPT_DIR/../core" && pwd)"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] [discord-send] $*"
}

mask() {
  local value="${1:-}"
  if [ -z "$value" ]; then
    echo "(empty)"
    return
  fi
  local len="${#value}"
  if [ "$len" -le 8 ]; then
    echo "$value"
    return
  fi
  echo "${value:0:4}...${value:len-4:4}"
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

resolve_channel_id() {
  case "${1:-}" in
    general)     echo "${DISCORD_CHANNEL_ID_GENERAL:-}" ;;
    logs)        echo "${DISCORD_CHANNEL_ID_LOGS:-}" ;;
    projects)    echo "${DISCORD_CHANNEL_ID_PROJECTS:-}" ;;
    ops)         echo "${DISCORD_CHANNEL_ID_OPS:-${DOMBOT_DISCORD_OPS:-}}" | sed 's/^channel://' ;;
    alerts)      echo "${DISCORD_CHANNEL_ID_ALERTS:-${DOMBOT_DISCORD_ALERTS:-}}" | sed 's/^channel://' ;;
    dm)          echo "${DOMBOT_DISCORD_DM_ME:-}" | sed 's/^user://' ;;
    innovations) echo "${DISCORD_CHANNEL_ID_INNOVATIONS:-${DOMBOT_DISCORD_INNOVATIONS:-}}" | sed 's/^channel://' ;;
    *)           echo "$1" ;;
  esac
}

if [ $# -eq 0 ]; then
  echo "Usage: discord-send.sh [TARGET] MESSAGE"
  echo "  TARGET: channel ID or general|logs|projects|ops|alerts|dm|innovations (default: general)"
  exit 1
fi

if [ $# -eq 1 ]; then
  log "Single argument mode -> default target: general"
  TARGET_ID="$(resolve_channel_id general)"
  MESSAGE="$1"
else
  TARGET_ID="$(resolve_channel_id "$1")"
  shift
  MESSAGE="$*"
fi

if [ -z "$TARGET_ID" ]; then
  echo "discord-send: empty channel (set DISCORD_CHANNEL_ID_GENERAL / DOMBOT_DISCORD_* or pass channel ID)" >&2
  exit 1
fi

log "Resolved target channel id: $(mask "$TARGET_ID")"
log "Message length: ${#MESSAGE}"
cd "$CORE_DIR"
log "Running: uv run discord-cli main --once --channel-id <id> --message <message>"
uv run discord-cli main --once --channel-id "$TARGET_ID" --message "$MESSAGE"
log "Done."
