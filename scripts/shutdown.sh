#!/usr/bin/env bash
# Arrêt propre : conteneurs compose du dépôt, puis libération des ports dev (Vite / Kanban API).
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${ROOT_DIR}/scripts/lifecycle.sh"
load_env_file

HUB_PORT="${HUB_PORT:-8088}"
KANBAN_API_PORT="${KANBAN_API_PORT:-8090}"
HUB_VITE_PORT="${HUB_VITE_PORT:-5173}"

say() {
  if [ -z "${CLAWVIS_SHUTDOWN_QUIET:-}" ]; then
    printf "%s\n" "$1"
  fi
}

free_listen_port() {
  local port="$1"
  [ -n "${port}" ] || return 0
  if ! command -v lsof >/dev/null 2>&1; then
    return 0
  fi
  local pids
  pids="$(lsof -t -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -z "${pids}" ]; then
    return 0
  fi
  # shellcheck disable=SC2086
  kill ${pids} 2>/dev/null || true
  sleep 0.25
  pids="$(lsof -t -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null || true)"
  if [ -n "${pids}" ]; then
    # shellcheck disable=SC2086
    kill -9 ${pids} 2>/dev/null || true
  fi
}

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  say "[clawvis] Docker compose down (hub, memory, …)"
  (cd "${ROOT_DIR}" && docker compose -f docker-compose.yml down >/dev/null 2>&1) || true
else
  say "[clawvis] Docker absent — compose ignoré"
fi

say "[clawvis] Libération ports ${HUB_PORT}, ${KANBAN_API_PORT}, ${HUB_VITE_PORT} (dev local)"
free_listen_port "${HUB_PORT}"
free_listen_port "${KANBAN_API_PORT}"
free_listen_port "${HUB_VITE_PORT}"

say "[clawvis] Shutdown terminé."
