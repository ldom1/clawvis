#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

load_env_file() {
  if [ -f "${ENV_FILE}" ]; then
    set -a
    # shellcheck disable=SC1090
    . "${ENV_FILE}"
    set +a
  fi
}

ensure_yarn() {
  if ! command -v yarn >/dev/null 2>&1; then
    echo "Missing yarn. Install it first."
    exit 1
  fi
}

init_instance_memory() {
  chmod +x "${ROOT_DIR}/scripts/init-memory.sh"
  bash "${ROOT_DIR}/scripts/init-memory.sh"
}

rebuild_hub_yarn() {
  ensure_yarn
  echo "Rebuilding hub dependencies and bundle with yarn..."
  yarn --cwd "${ROOT_DIR}/hub" install --frozen-lockfile
  yarn --cwd "${ROOT_DIR}/hub" build
}
