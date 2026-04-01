#!/usr/bin/env bash
set -euo pipefail

# ROOT_DIR may be preset by install.sh / clawvis / ssh+zsh callers before sourcing.
if [ -z "${ROOT_DIR:-}" ]; then
  if [ -n "${BASH_SOURCE[0]:-}" ]; then
    ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  else
    echo "lifecycle.sh: export ROOT_DIR=<Clawvis repo> before sourcing, or run under bash." >&2
    exit 1
  fi
fi
ENV_FILE="${ROOT_DIR}/.env"

load_env_file() {
  if [ -f "${ENV_FILE}" ]; then
    set -a
    # shellcheck disable=SC1090
    . "${ENV_FILE}"
    set +a
  fi
}

# Pin must match hub/package.json "packageManager": "yarn@x.y.z"
_hub_yarn_pin() {
  local ver="4.12.0"
  local pj="${ROOT_DIR}/hub/package.json"
  if [ -f "${pj}" ]; then
    ver="$(
      grep -o '"packageManager"[[:space:]]*:[[:space:]]*"yarn@[0-9][0-9.]*"' "${pj}" 2>/dev/null |
        head -1 |
        sed 's/.*yarn@//;s/".*//'
    )"
    [ -n "${ver}" ] || ver="4.12.0"
  fi
  printf '%s' "${ver}"
}

# Make `yarn` available via Corepack (Yarn 4 Berry) — no global npm install.
ensure_yarn() {
  if command -v yarn >/dev/null 2>&1; then
    return 0
  fi
  if ! command -v corepack >/dev/null 2>&1; then
    echo "Missing yarn and corepack. Install Node.js 18+ (includes corepack) or: npm i -g corepack" >&2
    exit 1
  fi
  corepack enable >/dev/null 2>&1 || true
  corepack prepare "yarn@$(_hub_yarn_pin)" --activate >/dev/null 2>&1 || true
  hash -r 2>/dev/null || true
  if command -v yarn >/dev/null 2>&1; then
    return 0
  fi
  # Last resort: some distros need a second prepare after enable
  corepack prepare "yarn@$(_hub_yarn_pin)" --activate 2>/dev/null || true
  hash -r 2>/dev/null || true
  if command -v yarn >/dev/null 2>&1; then
    return 0
  fi
  # Yarn shim not always on PATH; corepack yarn still works.
  if corepack yarn --version >/dev/null 2>&1; then
    return 0
  fi
  echo "Missing yarn after corepack bootstrap. Try: corepack enable && corepack prepare yarn@$(_hub_yarn_pin) --activate" >&2
  exit 1
}

# Prefer real yarn when on PATH; else delegate to corepack (after ensure_yarn).
_clawvis_yarn() {
  if command -v yarn >/dev/null 2>&1; then
    command yarn "$@"
  else
    corepack yarn "$@"
  fi
}

init_instance_memory() {
  chmod +x "${ROOT_DIR}/scripts/init-memory.sh"
  bash "${ROOT_DIR}/scripts/init-memory.sh"
}

rebuild_hub_yarn() {
  ensure_yarn
  if [ -n "${CLAWVIS_QUIET_START:-}" ]; then
    if ! _clawvis_yarn --cwd "${ROOT_DIR}/hub" install --immutable --silent >/dev/null 2>&1; then
      echo "[clawvis] hub: yarn install a échoué (lance cd hub && yarn install)" >&2
      exit 1
    fi
    if ! _clawvis_yarn --cwd "${ROOT_DIR}/hub" build >/dev/null 2>&1; then
      echo "[clawvis] hub: vite build a échoué (lance cd hub && yarn build)" >&2
      exit 1
    fi
  else
    echo "Rebuilding hub dependencies and bundle with yarn..."
    _clawvis_yarn --cwd "${ROOT_DIR}/hub" install --immutable
    _clawvis_yarn --cwd "${ROOT_DIR}/hub" build
  fi
}
