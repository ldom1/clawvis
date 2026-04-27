#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}" || {
  printf "[clawvis] Impossible d'accéder à %s\n" "${ROOT_DIR}" >&2
  exit 1
}
# shellcheck disable=SC1091
. "${ROOT_DIR}/scripts/lifecycle.sh"
load_env_file
if [ -n "${CLAWVIS_E2E_ISOLATE:-}" ]; then
  export MEMORY_ROOT="${ROOT_DIR}/.e2e-memory"
  export PROJECTS_ROOT="${ROOT_DIR}/.e2e-projects"
  export LINKED_INSTANCES=""
fi
# Non-compose/local runs: make CLI runtime explicit so agent-service can execute Claude CLI.
export HOME="${HOME:-/home/${USER:-$(id -un 2>/dev/null || echo lgiron)}}"
if [ -z "${CLI_BIN:-}" ] && [ -x "${HOME}/.local/bin/claude" ]; then
  export CLI_BIN="${HOME}/.local/bin/claude"
fi
# Local agent orchestration → Kanban (default matches KANBAN_API_PORT)
export KANBAN_URL="${KANBAN_URL:-http://127.0.0.1:${KANBAN_API_PORT:-8090}}"

PORT="${HUB_PORT:-8088}"
API_PORT="${KANBAN_API_PORT:-8090}"
MEM_API_PORT="${HUB_MEMORY_API_PORT:-8091}"
AGENT_PORT_VALUE="${AGENT_PORT:-8092}"

if [ -z "${CLAWVIS_SKIP_START_ECHO:-}" ]; then
  echo "Starting Clawvis dev server on http://localhost:${PORT}"
  echo "Starting Kanban API on http://localhost:${API_PORT}"
  echo "Starting Hub Memory API on http://localhost:${MEM_API_PORT}"
  if [ -z "${CLAWVIS_SKIP_AGENT:-}" ]; then
    echo "Starting Agent service on http://localhost:${AGENT_PORT_VALUE}"
  fi
  echo "Starting Vite Hub app (port ${PORT}, or next free if busy; URL in Vite output)"
  echo "Ensuring Brain runtime on http://localhost:${MEMORY_PORT:-3099}"
  echo "If port is busy, run: clawvis shutdown   (or: docker compose down)"
fi

init_instance_memory
# Memory API démarre plus bas (uvicorn hub_core.memory_api). Il n’y a pas de service compose nommé « memory ».

if [ -z "${CLAWVIS_SKIP_SETUP_SYNC:-}" ]; then
  UV_PROJECT_ENVIRONMENT="${ROOT_DIR}/hub-core/.venv" \
    uv sync --directory "${ROOT_DIR}/hub-core" --frozen --no-dev >/dev/null
  "${ROOT_DIR}/hub-core/.venv/bin/python" -m hub_core setup-sync-apply || true
fi

uvicorn_extra=()
if [ -n "${CLAWVIS_QUIET_START:-}" ]; then
  uvicorn_extra+=(--log-level warning --no-access-log)
fi

wait_uvicorn_openapi() {
  local pid="$1" port="$2" label="$3"
  local i=0
  local max=80
  while [ "${i}" -lt "${max}" ]; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      echo "[clawvis] ${label} (uvicorn) s'est arrêtée — port ${port} déjà pris ou erreur uv/Python ?" >&2
      return 1
    fi
    if command -v curl >/dev/null 2>&1 \
      && curl -fsS -m 1 "http://127.0.0.1:${port}/openapi.json" >/dev/null 2>&1; then
      return 0
    fi
    if (echo >/dev/tcp/127.0.0.1/"${port}") 2>/dev/null; then
      return 0
    fi
    sleep 0.25
    i=$((i + 1))
  done
  echo "[clawvis] Timeout: pas de réponse ${label} sur http://127.0.0.1:${port}/ (openapi.json)." >&2
  return 1
}

UV_PROJECT_ENVIRONMENT="${ROOT_DIR}/services/kanban/.venv" \
  uv sync --directory "${ROOT_DIR}/services/kanban" --frozen --no-dev >/dev/null
UV_PROJECT_ENVIRONMENT="${ROOT_DIR}/services/agent/.venv" \
  uv sync --directory "${ROOT_DIR}/services/agent" --frozen --no-dev >/dev/null

"${ROOT_DIR}/services/kanban/.venv/bin/python" -m uvicorn \
  kanban_api.server:app \
  --host 0.0.0.0 \
  --port "${API_PORT}" \
  --reload \
  --reload-dir "${ROOT_DIR}/services/kanban/kanban_api" \
  --reload-dir "${ROOT_DIR}/hub-core/hub_core" \
  "${uvicorn_extra[@]}" &
API_PID=$!

"${ROOT_DIR}/services/kanban/.venv/bin/python" -m uvicorn \
  hub_core.memory_api:app \
  --host 0.0.0.0 \
  --port "${MEM_API_PORT}" \
  --reload \
  --reload-dir "${ROOT_DIR}/hub-core/hub_core" \
  --reload-dir "${ROOT_DIR}/services/kanban/kanban_api" \
  "${uvicorn_extra[@]}" &
MEM_API_PID=$!

if [ -z "${CLAWVIS_SKIP_AGENT:-}" ]; then
  "${ROOT_DIR}/services/agent/.venv/bin/python" -m uvicorn \
    agent_service.main:app \
    --host 0.0.0.0 \
    --port "${AGENT_PORT_VALUE}" \
    --reload \
  --reload-dir "${ROOT_DIR}/services/agent/agent_service" \
    "${uvicorn_extra[@]}" &
  AGENT_PID=$!
else
  AGENT_PID=""
fi

VITE_PID=""

cleanup() {
  [ -n "${VITE_PID}" ] && kill "${VITE_PID}" >/dev/null 2>&1 || true
  [ -n "${AGENT_PID}" ] && kill "${AGENT_PID}" >/dev/null 2>&1 || true
  kill "${API_PID}" >/dev/null 2>&1 || true
  kill "${MEM_API_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

if ! wait_uvicorn_openapi "${API_PID}" "${API_PORT}" "Kanban API"; then
  exit 1
fi
if ! wait_uvicorn_openapi "${MEM_API_PID}" "${MEM_API_PORT}" "Memory API"; then
  exit 1
fi
if [ -n "${AGENT_PID}" ] \
  && ! wait_uvicorn_openapi "${AGENT_PID}" "${AGENT_PORT_VALUE}" "Agent service"; then
  exit 1
fi

rebuild_hub_yarn

if [ -n "${CLAWVIS_QUIET_START:-}" ]; then
  if [ -n "${CLAWVIS_NO_EXEC_VITE:-}" ]; then
    node "${ROOT_DIR}/hub/node_modules/vite/bin/vite.js" "${ROOT_DIR}/hub" \
      --port "${PORT}" --no-strictPort --logLevel silent &
    VITE_PID=$!
    wait "${VITE_PID}" || true
    exit 0
  fi
  exec node "${ROOT_DIR}/hub/node_modules/vite/bin/vite.js" "${ROOT_DIR}/hub" \
    --port "${PORT}" --no-strictPort --logLevel silent
fi
if [ -n "${CLAWVIS_NO_EXEC_VITE:-}" ]; then
  yarn --cwd "${ROOT_DIR}/hub" dev --port "${PORT}" --no-strictPort &
  VITE_PID=$!
  wait "${VITE_PID}" || true
  exit 0
fi
exec yarn --cwd "${ROOT_DIR}/hub" dev --port "${PORT}" --no-strictPort
