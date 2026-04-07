#!/usr/bin/env bash
# setup-runtime.sh — Configure PRIMARY_AI_PROVIDER in .env
# Run via: clawvis setup provider --provider openclaw|claude
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

log()  { printf "==> %s\n" "$1"; }
warn() { printf "[warn] %s\n" "$1"; }
die()  { printf "[error] %s\n" "$1" >&2; exit 1; }

provider=""

while [ $# -gt 0 ]; do
  case "$1" in
    --provider) provider="${2:-}"; shift ;;
    --non-interactive) ;;
    *) die "Unknown flag: $1. Use --provider openclaw|claude" ;;
  esac
  shift
done

if [ ! -f "${ENV_FILE}" ]; then
  if [ -f "${ROOT_DIR}/.env.example" ]; then
    cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
    log "Created .env from .env.example"
  else
    touch "${ENV_FILE}"
    log "Created empty .env"
  fi
fi

set_env_var() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null; then
    # Replace existing line (portable sed)
    sed -i "s|^${key}=.*|${key}=${value}|" "${ENV_FILE}"
  elif grep -q "^#\s*${key}=" "${ENV_FILE}" 2>/dev/null; then
    # Uncomment and set
    sed -i "s|^#\s*${key}=.*|${key}=${value}|" "${ENV_FILE}"
  else
    echo "${key}=${value}" >> "${ENV_FILE}"
  fi
}

if [ -n "${provider}" ]; then
  case "${provider}" in
    openclaw|claude) ;;
    *) die "Invalid provider: ${provider}. Use openclaw or claude." ;;
  esac
  set_env_var "PRIMARY_AI_PROVIDER" "${provider}"
  log "PRIMARY_AI_PROVIDER set to: ${provider}"
  log "Configuration saved to .env"
  log "Restart Clawvis for changes to take effect: clawvis restart"
  exit 0
fi

log "Current provider configuration in .env:"
grep -E "^PRIMARY_AI_PROVIDER=" "${ENV_FILE}" 2>/dev/null || echo "  PRIMARY_AI_PROVIDER=(not set)"
echo ""
log "Usage:"
echo "  clawvis setup provider --provider openclaw"
echo "  clawvis setup provider --provider claude"
