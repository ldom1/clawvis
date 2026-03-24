#!/usr/bin/env bash
# setup-runtime.sh — Configure the primary AI provider in .env
# Run via: clawvis setup provider --provider claude --key sk-ant-...
#         clawvis setup provider --provider mistral --key <key>
#         clawvis setup provider --provider openclaw --url http://host:3333 [--key <key>]
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

log()  { printf "==> %s\n" "$1"; }
warn() { printf "[warn] %s\n" "$1"; }
die()  { printf "[error] %s\n" "$1" >&2; exit 1; }

# ---- parse args ------------------------------------------------------------
provider=""
claude_key=""
mistral_key=""
openclaw_url=""
openclaw_key=""
non_interactive=0

while [ $# -gt 0 ]; do
  case "$1" in
    --non-interactive) non_interactive=1 ;;
    --provider) provider="${2:-}"; shift ;;
    --claude-api-key) claude_key="${2:-}"; shift ;;
    --mistral-api-key) mistral_key="${2:-}"; shift ;;
    --openclaw-base-url) openclaw_url="${2:-}"; shift ;;
    --openclaw-api-key) openclaw_key="${2:-}"; shift ;;
    *) die "Unknown flag: $1. Use --provider, --claude-api-key, --mistral-api-key, --openclaw-base-url, --openclaw-api-key" ;;
  esac
  shift
done

# ---- ensure .env exists ----------------------------------------------------
if [ ! -f "${ENV_FILE}" ]; then
  if [ -f "${ROOT_DIR}/.env.example" ]; then
    cp "${ROOT_DIR}/.env.example" "${ENV_FILE}"
    log "Created .env from .env.example"
  else
    touch "${ENV_FILE}"
    log "Created empty .env"
  fi
fi

# ---- helper: set or update a key=value in .env ----------------------------
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

# ---- apply changes ---------------------------------------------------------
changed=0

if [ -n "${claude_key}" ]; then
  set_env_var "CLAUDE_API_KEY" "${claude_key}"
  log "CLAUDE_API_KEY updated."
  changed=1
fi

if [ -n "${mistral_key}" ]; then
  set_env_var "MISTRAL_API_KEY" "${mistral_key}"
  log "MISTRAL_API_KEY updated."
  changed=1
fi

if [ -n "${openclaw_url}" ]; then
  set_env_var "OPENCLAW_BASE_URL" "${openclaw_url}"
  log "OPENCLAW_BASE_URL updated."
  changed=1
fi

if [ -n "${openclaw_key}" ]; then
  set_env_var "OPENCLAW_API_KEY" "${openclaw_key}"
  log "OPENCLAW_API_KEY updated."
  changed=1
fi

if [ -n "${provider}" ]; then
  set_env_var "PRIMARY_AI_PROVIDER" "${provider}"
  log "PRIMARY_AI_PROVIDER set to: ${provider}"
  changed=1
fi

if [ "${changed}" -eq 0 ]; then
  # Show current state when called with no args
  log "Current provider configuration in .env:"
  local_grep() { grep -E "^(CLAUDE_API_KEY|MISTRAL_API_KEY|OPENCLAW_BASE_URL|PRIMARY_AI_PROVIDER)=" "${ENV_FILE}" 2>/dev/null || true; }
  local_grep | while IFS='=' read -r k v; do
    # Mask key values
    if [ ${#v} -gt 8 ]; then
      printf "  %-28s %s\n" "${k}=" "${v:0:6}...${v: -2}"
    else
      printf "  %-28s %s\n" "${k}=" "${v}"
    fi
  done
  echo ""
  log "Usage:"
  echo "  clawvis setup provider --provider claude --key <sk-ant-...>"
  echo "  clawvis setup provider --provider mistral --key <key>"
  echo "  clawvis setup provider --provider openclaw --url http://host:3333"
  echo ""
  log "Or configure via Hub UI: http://localhost:\${HUB_PORT:-8088}/settings/"
  exit 0
fi

log "Configuration saved to .env"
log "Restart Clawvis for changes to take effect: clawvis restart"
