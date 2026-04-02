#!/usr/bin/env bash
# Clawvis bootstrap — one-liner installer
# Usage: curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash
#
# CLAWVIS_DIR     install path (default: ~/.clawvis)
# CLAWVIS_REPO_URL clone source — https URL or local path to a git repo (default: GitHub)
# CLAWVIS_REF      optional branch or tag for fresh clone (--depth 1)
set -euo pipefail

REPO_URL="${CLAWVIS_REPO_URL:-https://github.com/ldom1/clawvis}"
REF="${CLAWVIS_REF:-}"
INSTALL_DIR="${CLAWVIS_DIR:-$HOME/.clawvis}"

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required. Install git and retry."
  exit 1
fi

echo "==> Clawvis bootstrap"
echo "    Destination: ${INSTALL_DIR}"

if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "==> Repo already present, pulling latest"
  git -C "${INSTALL_DIR}" pull --ff-only
else
  if [ -n "${REF}" ]; then
    git clone --depth 1 --branch "${REF}" "${REPO_URL}" "${INSTALL_DIR}"
  else
    git clone "${REPO_URL}" "${INSTALL_DIR}"
  fi
fi

exec bash "${INSTALL_DIR}/install.sh" "$@"
