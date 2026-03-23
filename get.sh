#!/usr/bin/env bash
# Clawvis bootstrap — one-liner installer
# Usage: curl -fsSL https://raw.githubusercontent.com/lgiron/clawvis/main/get.sh | bash
set -euo pipefail

REPO_URL="https://github.com/lgiron/clawvis"
INSTALL_DIR="${CLAWVIS_DIR:-$HOME/.clawvis}"

echo "==> Clawvis bootstrap"
echo "    Destination: ${INSTALL_DIR}"

if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "==> Repo already present, pulling latest"
  git -C "${INSTALL_DIR}" pull --ff-only
else
  git clone "${REPO_URL}" "${INSTALL_DIR}"
fi

exec bash "${INSTALL_DIR}/install.sh" "$@"
