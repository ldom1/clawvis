#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_REF="${1:-}"
# shellcheck disable=SC1091
. "${ROOT_DIR}/scripts/lifecycle.sh"
load_env_file

if [ -z "${TARGET_REF}" ]; then
  echo "Usage: clawvis update --tag <target_ref>"
  exit 1
fi

if [ ! -d "${ROOT_DIR}/.git" ]; then
  echo "This script must run in a git checkout."
  exit 1
fi

cd "${ROOT_DIR}"

echo "==> Fetch tags and refs"
git fetch --tags origin >/dev/null 2>&1 || git fetch --tags

CURRENT_REF="$(git describe --tags --always 2>/dev/null || git rev-parse --short HEAD)"
echo "==> Current: ${CURRENT_REF}"
echo "==> Target:  ${TARGET_REF}"

if [ -n "$(git status --porcelain --ignore-submodules=dirty)" ]; then
  echo "Working tree is dirty. Commit/stash first."
  exit 1
fi

echo "==> Checkout target tag"
if git rev-parse -q --verify "refs/tags/${TARGET_REF}" >/dev/null; then
  git checkout "${TARGET_REF}"
elif git rev-parse -q --verify "${TARGET_REF}" >/dev/null; then
  git checkout "${TARGET_REF}"
elif git ls-remote --heads origin "${TARGET_REF}" | rg "${TARGET_REF}" >/dev/null 2>&1; then
  git checkout -B "${TARGET_REF}" "origin/${TARGET_REF}"
else
  echo "Target ref not found: ${TARGET_REF}"
  exit 1
fi

echo "==> Initialize memory"
init_instance_memory

echo "==> Rebuild hub"
rebuild_hub_yarn

echo "==> Restart stack"
docker compose up -d --build

HUB_PORT="${HUB_PORT:-8088}"
MEMORY_PORT="${MEMORY_PORT:-3099}"

echo "==> Smoke checks"
if command -v curl >/dev/null 2>&1; then
  curl -fsS "http://localhost:${HUB_PORT}/" >/dev/null
  curl -fsS "http://localhost:${HUB_PORT}/logs/" >/dev/null
  curl -fsS "http://localhost:${HUB_PORT}/kanban/" >/dev/null
  curl -fsS "http://localhost:${HUB_PORT}/memory/" >/dev/null
  curl -fsS "http://localhost:${MEMORY_PORT}/" >/dev/null || echo "[warn] Brain runtime not reachable"
else
  echo "[warn] curl missing, smoke checks skipped."
fi

echo "Upgrade completed to ${TARGET_REF}"
