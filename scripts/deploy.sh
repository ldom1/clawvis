#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Production deploy over SSH.
# Override with env vars when needed.
REMOTE_HOST="${DEPLOY_HOST:-localhost}"
REMOTE_USER="${DEPLOY_USER:-$USER}"
REMOTE_PATH="${DEPLOY_PATH:-/opt/clawvis}"
SSH_PORT="${DEPLOY_SSH_PORT:-22}"

if ! command -v rsync >/dev/null 2>&1; then
  echo "rsync is required"
  exit 1
fi

echo "Deploying to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

ssh -p "${SSH_PORT}" "${REMOTE_USER}@${REMOTE_HOST}" "mkdir -p '${REMOTE_PATH}'"

rsync -az --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude ".cursor" \
  -e "ssh -p ${SSH_PORT}" \
  "${ROOT_DIR}/" "${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/"

ssh -p "${SSH_PORT}" "${REMOTE_USER}@${REMOTE_HOST}" \
  "cd '${REMOTE_PATH}' && chmod +x scripts/lifecycle.sh scripts/init-memory.sh && bash -lc 'source scripts/lifecycle.sh; load_env_file; init_instance_memory; rebuild_hub_yarn' && docker compose up -d --build"

echo "Deploy complete."
