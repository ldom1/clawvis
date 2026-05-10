#!/usr/bin/env bash
# hub-refresh — run hub_core as dombot ORCHESTRATOR
# Injects RBAC identity so hub_core logs the correct agent context.

set -e
export PATH="${HOME}/.local/bin:${PATH}"
# hub-core requires Python >=3.11 — let uv pick/install via project metadata (no hardcoded interpreter).
if [ -n "${UV_PYTHON:-}" ] && [ ! -x "$UV_PYTHON" ]; then
  unset UV_PYTHON
fi
export UV_PROJECT_ENVIRONMENT="${UV_PROJECT_ENVIRONMENT:-${TMPDIR:-/tmp}/clawvis-venvs/hub-core}"

_resolve_clawvis_root() {
  if [ -n "${CLAWVIS_ROOT:-}" ] && [ -d "${CLAWVIS_ROOT}/hub-core" ]; then
    printf '%s\n' "${CLAWVIS_ROOT}"
    return 0
  fi
  # Prefer lowercase lab (WSL / Linux convention)
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
LOG_DIR="${CLAWVIS_LOG_DIR:-${CLAWVIS_ROOT}/logs}"
TIMESTAMP=$(date '+%Y-%m-%d-%H%M')
LOG_FILE="$LOG_DIR/hub-refresh-$TIMESTAMP.log"

mkdir -p "$LOG_DIR" 2>/dev/null || true
if ! touch "$LOG_FILE" 2>/dev/null; then
  LOG_DIR="${TMPDIR:-/tmp}/clawvis-logs"
  mkdir -p "$LOG_DIR"
  LOG_FILE="$LOG_DIR/hub-refresh-$TIMESTAMP.log"
fi

export AGENT_ID="dombot"
export AGENT_ROLE="ORCHESTRATOR"
export AGENT_MODEL="${AGENT_MODEL:-system}"
export NETWORK_MODE="allowlist"
export NETWORK_ALLOWLIST="api.mammouth.ai,api.anthropic.com,localhost"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hub Refresh START — AGENT_ID=$AGENT_ID AGENT_ROLE=$AGENT_ROLE CLAWVIS_ROOT=$CLAWVIS_ROOT" >>"$LOG_FILE"

cd "$HUB_CORE_DIR"
if timeout 300 env VIRTUAL_ENV="" uv run python -m hub_core.main "$@" >>"$LOG_FILE" 2>&1; then
  EXIT_CODE=0
  STATUS="SUCCESS"
else
  EXIT_CODE=$?
  STATUS="FAILED"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Hub Refresh END — STATUS=$STATUS EXIT_CODE=$EXIT_CODE" >>"$LOG_FILE"

if [ "$EXIT_CODE" -ne 0 ]; then
  echo "hub-refresh: FAILED (exit $EXIT_CODE). See log: $LOG_FILE" >&2
fi

if [ -d "$LOGGER_CORE" ]; then
  _lvl="INFO"
  [ "$EXIT_CODE" -ne 0 ] && _lvl="ERROR"
  UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/logger-core" \
    VIRTUAL_ENV="" \
    uv run --directory "$LOGGER_CORE" dombot-log "$_lvl" "cron:hub-refresh" "system" "cron:complete" "Hub Refresh executed ($STATUS)" "{\"exit_code\": $EXIT_CODE, \"log_file\": \"$LOG_FILE\"}" || true
else
  echo "hub-refresh: logger core missing at $LOGGER_CORE — skip dombot-log" >>"$LOG_FILE"
fi

exit $EXIT_CODE
