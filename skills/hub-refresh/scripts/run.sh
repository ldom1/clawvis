#!/usr/bin/env bash
# hub-refresh — run hub_core as dombot ORCHESTRATOR
# Injects RBAC identity so hub_core logs the correct agent context.

set -e
export PATH="${HOME}/.local/bin:${PATH}"
# Pin Python to a stable system path so uv never rebuilds the venv due to a
# missing interpreter. /usr/bin/python3.11 is a real file (not a symlink chain)
# that survives uv cache cleans and pyenv updates.
export UV_PYTHON="${UV_PYTHON:-/usr/bin/python3.11}"
# Use a dedicated venv outside the workspace so the gateway's bundled uv
# cannot interfere with the script's execution environment.
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-$HOME/.venvs/hub-core}"

_resolve_clawvis_root() {
  if [ -n "${CLAWVIS_ROOT:-}" ] && [ -d "${CLAWVIS_ROOT}/hub-core" ]; then
    printf '%s\n' "${CLAWVIS_ROOT}"
    return 0
  fi
  for _p in "${HOME}/lab/clawvis" "${HOME}/Lab/clawvis"; do
    if [ -d "${_p}/hub-core" ]; then
      printf '%s\n' "${_p}"
      return 0
    fi
  done
  return 1
}

CLAWVIS_ROOT="$(_resolve_clawvis_root)" || {
  echo "hub-refresh: cannot find Clawvis repo (need hub-core/). Set CLAWVIS_ROOT." >&2
  exit 1
}

HUB_CORE_DIR="${CLAWVIS_ROOT}/hub-core"
LOGGER_CORE="${CLAWVIS_ROOT}/skills/logger/core"

LOG_DIR="${HOME}/.openclaw/logs"
TIMESTAMP=$(date '+%Y-%m-%d-%H%M')
LOG_FILE="$LOG_DIR/hub-refresh-$TIMESTAMP.log"

mkdir -p "$LOG_DIR"

export AGENT_ID="dombot"
export AGENT_ROLE="ORCHESTRATOR"
export AGENT_MODEL="${AGENT_MODEL:-system}"
export NETWORK_MODE="allowlist"
export NETWORK_ALLOWLIST="api.mammouth.ai,api.anthropic.com,localhost"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hub Refresh START — AGENT_ID=$AGENT_ID AGENT_ROLE=$AGENT_ROLE CLAWVIS_ROOT=$CLAWVIS_ROOT" >>"$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] hub-refresh START" >>/tmp/hub-refresh.log

cd "$HUB_CORE_DIR"
if timeout 300 uv run python -m hub_core.main "$@" >>"$LOG_FILE" 2>&1; then
  EXIT_CODE=0
  STATUS="SUCCESS"
else
  EXIT_CODE=$?
  STATUS="FAILED"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hub Refresh END — STATUS=$STATUS EXIT_CODE=$EXIT_CODE" >>"$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] hub-refresh done exit=$EXIT_CODE" >>/tmp/hub-refresh.log

if [ -d "$LOGGER_CORE" ]; then
  uv run --directory "$LOGGER_CORE" dombot-log "INFO" "cron:hub-refresh" "system" "cron:complete" "Hub Refresh executed ($STATUS)" "{\"exit_code\": $EXIT_CODE, \"log_file\": \"$LOG_FILE\"}" || true
else
  echo "hub-refresh: logger core missing at $LOGGER_CORE — skip dombot-log" >>"$LOG_FILE"
fi

exit $EXIT_CODE
