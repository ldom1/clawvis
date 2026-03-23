#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${ROOT_DIR}/scripts/lifecycle.sh"
load_env_file

PORT="${HUB_PORT:-8088}"
API_PORT="${KANBAN_API_PORT:-8090}"

echo "Starting Clawvis dev server on http://localhost:${PORT}"
echo "Starting Kanban API on http://localhost:${API_PORT}"
echo "Starting Vite Hub app on http://localhost:${PORT}"
echo "Ensuring Brain runtime on http://localhost:${MEMORY_PORT:-3099}"
echo "If port is busy, stop docker stack first: docker compose down"

init_instance_memory
docker compose up -d memory >/dev/null 2>&1 || true

uv run --directory "${ROOT_DIR}/kanban" python -m uvicorn \
  kanban_api.server:app \
  --host 0.0.0.0 \
  --port "${API_PORT}" \
  --reload \
  --reload-dir "${ROOT_DIR}/kanban/kanban_api" &
API_PID=$!

cleanup() {
  kill "${API_PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

rebuild_hub_yarn

exec yarn --cwd "${ROOT_DIR}/hub" dev --host 0.0.0.0 --port "${PORT}"
