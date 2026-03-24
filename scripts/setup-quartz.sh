#!/usr/bin/env bash
# setup-quartz.sh — Clone and configure Quartz as the Brain display layer.
# Run via: clawvis setup quartz
# Quartz docs: https://quartz.jzhao.xyz/
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
. "${ROOT_DIR}/scripts/lifecycle.sh"
load_env_file

QUARTZ_DIR="${ROOT_DIR}/quartz"
MEM_DIR="${ROOT_DIR}/${MEMORY_ROOT:-instances/${INSTANCE_NAME:-example}/memory}"

log()  { printf "==> %s\n" "$1"; }
warn() { printf "[warn] %s\n" "$1"; }
die()  { printf "[error] %s\n" "$1" >&2; exit 1; }

# ---- checks ----------------------------------------------------------------
command -v git  >/dev/null 2>&1 || die "git is required."
command -v node >/dev/null 2>&1 || die "node is required (>= 18)."
command -v npm  >/dev/null 2>&1 || die "npm is required."

NODE_MAJOR="$(node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))' 2>/dev/null || echo "0")"
if [ "${NODE_MAJOR}" -lt 18 ] 2>/dev/null; then
  die "Node >= 18 is required (found: $(node --version))."
fi

# ---- already installed? ----------------------------------------------------
if [ -d "${QUARTZ_DIR}" ] && [ -f "${QUARTZ_DIR}/package.json" ]; then
  log "Quartz already present at quartz/. Pulling latest changes..."
  git -C "${QUARTZ_DIR}" pull --ff-only 2>/dev/null || warn "Pull failed — working tree may have local changes."
  log "Installing dependencies..."
  npm install --prefix "${QUARTZ_DIR}" --silent
  log "Quartz updated."
  exit 0
fi

# ---- clone -----------------------------------------------------------------
log "Cloning Quartz into quartz/..."
git clone --depth 1 https://github.com/jackyzha0/quartz.git "${QUARTZ_DIR}"
log "Installing Quartz dependencies..."
npm install --prefix "${QUARTZ_DIR}" --silent

# ---- configure Quartz content path to point to memory/projects -------------
QUARTZ_CFG="${QUARTZ_DIR}/quartz.config.ts"
if [ -f "${QUARTZ_CFG}" ]; then
  # Set content folder to our memory/projects directory (relative path from quartz/)
  PROJECTS_REL="$(python3 -c "
import os, sys
q = '${QUARTZ_DIR}'
m = '${MEM_DIR}/projects'
print(os.path.relpath(m, q))
" 2>/dev/null || echo "../${MEMORY_ROOT:-instances/${INSTANCE_NAME:-example}/memory}/projects")"
  # Patch contentFolder in quartz.config.ts if it differs
  if grep -q 'contentFolder:' "${QUARTZ_CFG}"; then
    sed -i "s|contentFolder: \"[^\"]*\"|contentFolder: \"${PROJECTS_REL}\"|g" "${QUARTZ_CFG}"
    log "Quartz contentFolder set to: ${PROJECTS_REL}"
  else
    warn "Could not auto-patch quartz.config.ts — set contentFolder manually to: ${PROJECTS_REL}"
  fi
fi

# ---- first build -----------------------------------------------------------
log "Running first Quartz build..."
(
  cd "${QUARTZ_DIR}"
  npx quartz build >/dev/null 2>&1
) && log "Quartz built successfully (output: quartz/public/)." || warn "Quartz build returned non-zero. Check quartz/ setup."

log ""
log "Quartz is ready."
log "  - Content source : ${MEM_DIR}/projects/*.md"
log "  - Output         : ${QUARTZ_DIR}/public/"
log "  - Rebuild        : clawvis restart  (or: bash scripts/build-quartz.sh)"
log ""
log "The Brain display layer will now use Quartz on next restart."
