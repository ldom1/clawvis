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
  log "Quartz dependencies ensured."
else
  # ---- clone ---------------------------------------------------------------
  log "Cloning Quartz into quartz/..."
  git clone --depth 1 https://github.com/jackyzha0/quartz.git "${QUARTZ_DIR}"
  log "Installing Quartz dependencies..."
  npm install --prefix "${QUARTZ_DIR}" --silent
fi

# ---- configure Quartz content dir to instance memory ------------------------
# Quartz v4 uses a content directory (default: quartz/content). We symlink it to
# the instance memory so the explorer can see projects/, todo/, resources/, etc.
mkdir -p "${MEM_DIR}"
CONTENT_DIR="${QUARTZ_DIR}/content"
if [ -L "${CONTENT_DIR}" ] || [ -d "${CONTENT_DIR}" ]; then
  rm -rf "${CONTENT_DIR}"
fi
ln -s "${MEM_DIR}" "${CONTENT_DIR}"
log "Quartz content symlinked: quartz/content -> ${MEM_DIR}"

# ---- first build -----------------------------------------------------------
log "Running first Quartz build..."
(
  cd "${QUARTZ_DIR}"
  npx quartz build >/dev/null 2>&1
) && log "Quartz built successfully (output: quartz/public/)." || warn "Quartz build returned non-zero. Check quartz/ setup."

log ""
log "Quartz is ready."
log "  - Content source : ${MEM_DIR}"
log "  - Output         : ${QUARTZ_DIR}/public/"
log "  - Rebuild        : clawvis restart  (or: bash scripts/build-quartz.sh)"
log ""
log "The Brain display layer will now use Quartz on next restart."
