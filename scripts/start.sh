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

PORT="${HUB_PORT:-8088}"
API_PORT="${KANBAN_API_PORT:-8090}"

if [ -z "${CLAWVIS_SKIP_START_ECHO:-}" ]; then
  echo "Starting Clawvis dev server on http://localhost:${PORT}"
  echo "Starting Kanban API on http://localhost:${API_PORT}"
  echo "Starting Vite Hub app (port ${PORT}, or next free if busy; URL in Vite output)"
  echo "Ensuring Brain runtime on http://localhost:${MEMORY_PORT:-3099}"
  echo "If port is busy, run: clawvis shutdown   (or: docker compose down)"
fi

init_instance_memory
if ! docker compose up -d memory >/dev/null 2>&1; then
  echo "[clawvis] Échec: docker compose up memory (Docker démarré ? lance depuis la racine Clawvis ?)." >&2
  exit 1
fi

uvicorn_extra=()
if [ -n "${CLAWVIS_QUIET_START:-}" ]; then
  uvicorn_extra+=(--log-level warning --no-access-log)
fi

wait_kanban_api() {
  local pid="$1"
  local i=0
  local max=80
  while [ "${i}" -lt "${max}" ]; do
    if ! kill -0 "${pid}" 2>/dev/null; then
      echo "[clawvis] L'API Kanban (uvicorn) s'est arrêtée — port ${API_PORT} déjà pris ou erreur uv/Python ?" >&2
      return 1
    fi
    if command -v curl >/dev/null 2>&1 \
      && curl -fsS -m 1 "http://127.0.0.1:${API_PORT}/openapi.json" >/dev/null 2>&1; then
      return 0
    fi
    if (echo >/dev/tcp/127.0.0.1/"${API_PORT}") 2>/dev/null; then
      return 0
    fi
    sleep 0.25
    i=$((i + 1))
  done
  echo "[clawvis] Timeout: pas de réponse Kanban API sur http://127.0.0.1:${API_PORT}/ (openapi.json)." >&2
  return 1
}

uv run --directory "${ROOT_DIR}/kanban" python -m uvicorn \
  kanban_api.server:app \
  --host 0.0.0.0 \
  --port "${API_PORT}" \
  --reload \
  --reload-dir "${ROOT_DIR}/kanban/kanban_api" \
  --reload-dir "${ROOT_DIR}/hub-core/hub_core" \
  "${uvicorn_extra[@]}" &
API_PID=$!

cleanup() {
  kill "${API_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

if ! wait_kanban_api "${API_PID}"; then
  exit 1
fi

rebuild_hub_yarn

if [ -n "${CLAWVIS_QUIET_START:-}" ]; then
  exec node "${ROOT_DIR}/hub/node_modules/vite/bin/vite.js" "${ROOT_DIR}/hub" \
    --port "${PORT}" --no-strictPort --logLevel silent
fi
exec yarn --cwd "${ROOT_DIR}/hub" dev --port "${PORT}" --no-strictPort
