#!/usr/bin/env bash
# hub-refresh — run hub_core as dombot ORCHESTRATOR
# Injects RBAC identity so hub_core logs the correct agent context.

set -e
export PATH="${HOME}/.local/bin:${PATH}"
# Pin Python to a stable system path so uv never rebuilds the venv due to a
# missing interpreter. /usr/bin/python3.11 is a real file (not a symlink chain)
# that survives uv cache cleans and pyenv updates.
export UV_PYTHON="/usr/bin/python3.11"
# Use a dedicated venv outside the workspace so the gateway's bundled uv
# (which always rebuilds ~/Lab/clawvis/.venv with a broken Python path)
# cannot interfere with the script's execution environment.
export UV_PROJECT_ENVIRONMENT="$HOME/.venvs/hub-core"

HUB_CORE_DIR="$HOME/Lab/clawvis/hub-core"
LOG_DIR="$HOME/.openclaw/logs"
TIMESTAMP=$(date '+%Y-%m-%d-%H%M')
LOG_FILE="$LOG_DIR/hub-refresh-$TIMESTAMP.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

export AGENT_ID="dombot"
export AGENT_ROLE="ORCHESTRATOR"
export AGENT_MODEL="${AGENT_MODEL:-system}"
export NETWORK_MODE="allowlist"
export NETWORK_ALLOWLIST="api.mammouth.ai,api.anthropic.com,localhost"

# Log start
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hub Refresh START — AGENT_ID=$AGENT_ID AGENT_ROLE=$AGENT_ROLE" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] hub-refresh START" >> /tmp/hub-refresh.log

# Run hub_core and capture exit code (hard cap to avoid hangs)
cd "$HUB_CORE_DIR"
if timeout 300 uv run python -m hub_core.main "$@" >> "$LOG_FILE" 2>&1; then
  EXIT_CODE=0
  STATUS="SUCCESS"
else
  EXIT_CODE=$?
  STATUS="FAILED"
fi

# Log completion
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hub Refresh END — STATUS=$STATUS EXIT_CODE=$EXIT_CODE" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] hub-refresh done exit=$EXIT_CODE" >> /tmp/hub-refresh.log

# Send to dombot-logger
uv run --directory "$HOME/Lab/clawvis/skills/logger/core" dombot-log "INFO" "cron:hub-refresh" "system" "cron:complete" "Hub Refresh executed ($STATUS)" "{\"exit_code\": $EXIT_CODE, \"log_file\": \"$LOG_FILE\"}" || true

exit $EXIT_CODE
