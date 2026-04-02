#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
EXAMPLE_FILE="${ROOT_DIR}/.env.example"
INSTANCES_DIR="${ROOT_DIR}/instances"
NON_INTERACTIVE=0
INSTANCE_NAME_FLAG=""
PROVIDER_FLAG=""
HUB_PORT_FLAG=""
MEMORY_PORT_FLAG=""
KANBAN_API_PORT_FLAG=""
PROJECTS_ROOT_FLAG=""
OPENCLAW_BASE_URL_FLAG=""
OPENCLAW_API_KEY_FLAG=""
CLAUDE_API_KEY_FLAG=""
MISTRAL_API_KEY_FLAG=""
MODE_FLAG=""
SKIP_PRIMARY=0
NO_START=0

info() { printf "\n==> %s\n" "$1"; }
warn() { printf "\n[warn] %s\n" "$1"; }
ask() {
  local prompt="$1" default="${2:-}"
  local value
  if [ -n "$default" ]; then
    read -r -p "$prompt [$default]: " value
    printf "%s" "${value:-$default}"
  else
    read -r -p "$prompt: " value
    printf "%s" "$value"
  fi
}
ensure_cli_shim() {
  local bin_dir="${HOME}/.local/bin"
  mkdir -p "${bin_dir}"
  ln -sf "${ROOT_DIR}/clawvis" "${bin_dir}/clawvis"
  case ":${PATH}:" in
    *":${bin_dir}:"*) ;;
    *)
      local export_line="export PATH=\"${bin_dir}:\$PATH\""
      local rc_file=""
      if [ -f "${HOME}/.zshrc" ] && [ "${SHELL:-}" = "/bin/zsh" -o "${SHELL:-}" = "/usr/bin/zsh" ]; then
        rc_file="${HOME}/.zshrc"
      elif [ -f "${HOME}/.bashrc" ]; then
        rc_file="${HOME}/.bashrc"
      elif [ -f "${HOME}/.zshrc" ]; then
        rc_file="${HOME}/.zshrc"
      fi
      if [ -n "${rc_file}" ]; then
        if ! grep -qF "${bin_dir}" "${rc_file}" 2>/dev/null; then
          printf "\n# Added by clawvis installer\n%s\n" "${export_line}" >> "${rc_file}"
          warn "Added ${bin_dir} to PATH in ${rc_file}. Run: source ${rc_file}"
        fi
      else
        warn "Add to your shell profile: ${export_line}"
      fi
      export PATH="${bin_dir}:${PATH}"
      ;;
  esac
}
usage() {
  cat <<'EOF'
Usage: ./install.sh [options]

Interactive mode (default): asks values step by step.
Non-interactive mode: pass --non-interactive and required flags.

Options:
  --non-interactive
  --instance <name>
  --provider <openclaw|claude|mistral>
  --hub-port <port>
  --memory-port <port>
  --kanban-api-port <port>
  --projects-root <path>
  --openclaw-base-url <url>
  --openclaw-api-key <key>
  --claude-api-key <key>
  --mistral-api-key <key>
  --mode <docker|dev>
  --skip-primary  Skip primary AI runtime setup (dev-only)
  --no-start      Create instance structure only, do not launch services
  -h, --help
EOF
}
upsert_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "${ENV_FILE}" 2>/dev/null; then
    python3 - "$ENV_FILE" "$key" "$value" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text(encoding="utf-8").splitlines()
out = []
for line in lines:
    if line.startswith(f"{key}="):
        out.append(f"{key}={value}")
    else:
        out.append(line)
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
  else
    printf "%s=%s\n" "$key" "$value" >> "${ENV_FILE}"
  fi
}
parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --non-interactive) NON_INTERACTIVE=1 ;;
      --instance) INSTANCE_NAME_FLAG="${2:-}"; shift ;;
      --provider) PROVIDER_FLAG="${2:-}"; shift ;;
      --skip-primary) SKIP_PRIMARY=1 ;;
      --no-start) NO_START=1 ;;
      --hub-port) HUB_PORT_FLAG="${2:-}"; shift ;;
      --memory-port) MEMORY_PORT_FLAG="${2:-}"; shift ;;
      --kanban-api-port) KANBAN_API_PORT_FLAG="${2:-}"; shift ;;
      --projects-root) PROJECTS_ROOT_FLAG="${2:-}"; shift ;;
      --openclaw-base-url) OPENCLAW_BASE_URL_FLAG="${2:-}"; shift ;;
      --openclaw-api-key) OPENCLAW_API_KEY_FLAG="${2:-}"; shift ;;
      --claude-api-key) CLAUDE_API_KEY_FLAG="${2:-}"; shift ;;
      --mistral-api-key) MISTRAL_API_KEY_FLAG="${2:-}"; shift ;;
      --mode) MODE_FLAG="${2:-}"; shift ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
    shift
  done
}
migrate_memory_if_needed() {
  local target_rel="$1"
  local target_abs="${ROOT_DIR}/${target_rel}"
  local legacy_abs="${ROOT_DIR}/memory"
  if [ "${target_abs}" = "${legacy_abs}" ]; then
    return
  fi
  if [ -d "${legacy_abs}" ] && [ -n "$(find "${legacy_abs}" -mindepth 1 -not -name 'README.md' -print -quit 2>/dev/null)" ]; then
    info "Migrating legacy memory -> ${target_rel}"
    mkdir -p "${target_abs}"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a "${legacy_abs}/" "${target_abs}/"
    else
      cp -a "${legacy_abs}/." "${target_abs}/"
    fi
    warn "Legacy memory kept at ${legacy_abs} (not deleted)."
  fi
}

parse_args "$@"

# When called directly (not from CLI), redirect to pretty CLI wizard if node is available
if [ "${NON_INTERACTIVE}" -eq 0 ] && [ -z "${CLAWVIS_NO_NODE_WRAPPER:-}" ]; then
  CLI_MJS="${ROOT_DIR}/clawvis-cli/cli.mjs"
  CLI_PKG="${ROOT_DIR}/clawvis-cli"
  if command -v node >/dev/null 2>&1 && [ -f "${CLI_MJS}" ]; then
    # Require Node >= 18
    NODE_MAJOR="$(node -e 'process.stdout.write(String(process.versions.node.split(".")[0]))' 2>/dev/null || echo "0")"
    if [ "${NODE_MAJOR}" -ge 18 ] 2>/dev/null; then
      if [ ! -d "${CLI_PKG}/node_modules/commander" ]; then
        if command -v npm >/dev/null 2>&1; then
          info "Installing CLI dependencies"
          (cd "${CLI_PKG}" && npm ci --no-audit --no-fund 2>/dev/null) || (cd "${CLI_PKG}" && npm install --no-audit --no-fund)
        else
          warn "npm not found; skipping Node install wizard (set CLAWVIS_NO_NODE_WRAPPER=1 to silence)"
        fi
      fi
      if [ -d "${CLI_PKG}/node_modules/commander" ]; then
        exec node "${CLI_MJS}" install "$@"
      fi
    else
      warn "Node.js >= 18 required for interactive wizard (found: $(node --version 2>/dev/null || echo 'unknown')); continuing with shell mode"
    fi
  fi
fi

chmod +x "${ROOT_DIR}/clawvis"
ensure_cli_shim

for cmd in docker; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: Docker is required but not found."
    echo "  Install Docker: https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is installed but not running."
    echo "  Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
  fi
done

if [ ! -f "${ENV_FILE}" ]; then
  info "Creating .env from .env.example"
  cp "${EXAMPLE_FILE}" "${ENV_FILE}"
else
  info ".env already exists, keeping current values"
fi

info "Instance setup"
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  INSTANCE_NAME="${INSTANCE_NAME_FLAG:-${USER}}"
else
  INSTANCE_NAME="$(ask "Instance name" "${USER}")"
fi
EXAMPLE_PATH="${INSTANCES_DIR}/example"
INSTANCE_PATH="${INSTANCES_DIR}/${INSTANCE_NAME}"
if [ "${INSTANCE_NAME}" = "example" ]; then
  warn "Instance name 'example' keeps template semantics; choose a custom name for production."
fi
if [ -d "${INSTANCE_PATH}" ] && [ "${INSTANCE_NAME}" != "example" ]; then
  info "Instance folder already exists: ${INSTANCE_PATH}"
else
  if [ -d "${EXAMPLE_PATH}" ] && [ "${INSTANCE_NAME}" != "example" ]; then
    info "Renaming instances/example -> instances/${INSTANCE_NAME}"
    mv "${EXAMPLE_PATH}" "${INSTANCE_PATH}"
  elif [ -d "${EXAMPLE_PATH}" ] && [ "${INSTANCE_NAME}" = "example" ]; then
    info "Using existing instances/example"
  else
    warn "instances/example not found; creating empty instance directory."
    mkdir -p "${INSTANCE_PATH}"
  fi
fi

info "Provider configuration"
if [ "${SKIP_PRIMARY}" -eq 1 ]; then
  info "Skipping primary AI runtime setup (dev)."
else
  if [ "${NON_INTERACTIVE}" -eq 1 ]; then
    case "${PROVIDER_FLAG:-claude}" in
      openclaw) PRIMARY="1" ;;
      claude) PRIMARY="2" ;;
      mistral) PRIMARY="3" ;;
      *) echo "Invalid --provider value: ${PROVIDER_FLAG}"; exit 1 ;;
    esac
  else
    echo "Choose your primary AI runtime:"
    echo "  1) OpenClaw (self-hosted)"
    echo "  2) Claude Code (Anthropic API key)"
    echo "  3) Mistral vibe (Mistral API key)"
    PRIMARY="$(ask "Select 1/2/3" "2")"
  fi

  case "${PRIMARY}" in
    1)
      if [ "${NON_INTERACTIVE}" -eq 1 ]; then
        OPENCLAW_BASE_URL="${OPENCLAW_BASE_URL_FLAG:-http://localhost:3333}"
        OPENCLAW_API_KEY="${OPENCLAW_API_KEY_FLAG:-}"
      else
        OPENCLAW_BASE_URL="$(ask "OpenClaw base URL" "http://localhost:3333")"
        OPENCLAW_API_KEY="$(ask "OpenClaw API key (optional)")"
      fi
      upsert_env "OPENCLAW_BASE_URL" "${OPENCLAW_BASE_URL}"
      upsert_env "OPENCLAW_API_KEY" "${OPENCLAW_API_KEY}"
      ;;
    2)
      if [ "${NON_INTERACTIVE}" -eq 1 ]; then
        CLAUDE_API_KEY="${CLAUDE_API_KEY_FLAG:-}"
      else
        CLAUDE_API_KEY="$(ask "Claude API key (sk-ant-...)" "")"
      fi
      upsert_env "CLAUDE_API_KEY" "${CLAUDE_API_KEY}"
      ;;
    3)
      if [ "${NON_INTERACTIVE}" -eq 1 ]; then
        MISTRAL_API_KEY="${MISTRAL_API_KEY_FLAG:-}"
      else
        MISTRAL_API_KEY="$(ask "Mistral API key" "")"
      fi
      upsert_env "MISTRAL_API_KEY" "${MISTRAL_API_KEY}"
      ;;
    *)
      warn "Unknown selection, skipping provider setup."
      ;;
  esac
fi

if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  PROJECTS_ROOT="${PROJECTS_ROOT_FLAG:-/home/${USER}/lab_perso/projects}"
  HUB_PORT="${HUB_PORT_FLAG:-8088}"
  MEMORY_PORT="${MEMORY_PORT_FLAG:-3099}"
  KANBAN_API_PORT="${KANBAN_API_PORT_FLAG:-8090}"
else
  PROJECTS_ROOT="$(ask "Projects root path" "/home/${USER}/lab_perso/projects")"
  HUB_PORT="$(ask "Hub port" "8088")"
  MEMORY_PORT="$(ask "Brain port" "3099")"
  KANBAN_API_PORT="$(ask "Kanban API port (dev mode)" "8090")"
fi
MEMORY_ROOT="instances/${INSTANCE_NAME}/memory"
upsert_env "PROJECTS_ROOT" "${PROJECTS_ROOT}"
upsert_env "HUB_PORT" "${HUB_PORT}"
upsert_env "MEMORY_PORT" "${MEMORY_PORT}"
upsert_env "KANBAN_API_PORT" "${KANBAN_API_PORT}"
upsert_env "INSTANCE_NAME" "${INSTANCE_NAME}"
upsert_env "MEMORY_ROOT" "${MEMORY_ROOT}"
upsert_env "HOST_UID" "$(id -u)"
upsert_env "HOST_GID" "$(id -g)"

info "Initialize memory structure"
chmod +x "${ROOT_DIR}/scripts/init-memory.sh"
export INSTANCE_NAME MEMORY_ROOT
migrate_memory_if_needed "${MEMORY_ROOT}"
bash "${ROOT_DIR}/scripts/init-memory.sh"
if [ -f "${ROOT_DIR}/${MEMORY_ROOT}/projects/example-project.md" ]; then
  info "Validation log: example project seeded at ${MEMORY_ROOT}/projects/example-project.md"
fi

info "Quartz (Brain display)"
if [ "${CLAWVIS_SKIP_QUARTZ:-0}" = "1" ]; then
  warn "Quartz setup skipped (CLAWVIS_SKIP_QUARTZ=1)."
else
  if command -v git >/dev/null 2>&1 && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    chmod +x "${ROOT_DIR}/scripts/setup-quartz.sh"
    export INSTANCE_NAME MEMORY_ROOT
    bash "${ROOT_DIR}/scripts/setup-quartz.sh" || warn "Quartz setup failed — continuing without Quartz."
  else
    warn "Quartz setup skipped (requires: git + node>=18 + npm)."
  fi
fi

info "Choose run mode"
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  case "${MODE_FLAG:-docker}" in
    docker) MODE="1"; RUN_MODE="docker" ;;
    dev) MODE="2"; RUN_MODE="dev" ;;
    *) echo "Invalid --mode value: ${MODE_FLAG}"; exit 1 ;;
  esac
else
  echo "  1) Docker (hub + kanban + brain)"
  echo "  2) Local dev (hub Vite + kanban API + brain)"
  MODE="$(ask "Select 1/2" "1")"
  if [ "${MODE}" = "1" ]; then RUN_MODE="docker"; else RUN_MODE="dev"; fi
fi
upsert_env "MODE" "${RUN_MODE}"

if [ "${NO_START}" -eq 1 ]; then
  info "Instance ready (--no-start: services not launched)"
  echo "- Instance: ${INSTANCE_PATH}"
  echo "- .env:     ${ENV_FILE}"
  echo ""
  echo "To start manually:"
  echo "  docker compose up -d hub kanban-api hub-memory-api"
  echo "  # or: clawvis start"
elif [ "${MODE}" = "1" ]; then
  # hub depends_on kanban-api + hub-memory-api; list them explicitly so all modes match.
  docker compose up -d hub kanban-api hub-memory-api
  info "Instance started"
  echo "- Hub:    http://localhost:${HUB_PORT}"
  echo "- Brain:  http://localhost:${MEMORY_PORT}"
  echo "- Memory API (Quartz/settings): http://localhost:${HUB_MEMORY_API_PORT:-8091}"
  echo "- Logs:   http://localhost:${HUB_PORT}/logs/"
  echo "- Kanban: http://localhost:${HUB_PORT}/kanban/"
else
  if ! command -v npm >/dev/null 2>&1; then
    echo "Error: npm is required for dev mode."
    echo "  Install Node.js (>= 18): https://nodejs.org/"
    exit 1
  fi
  # shellcheck disable=SC1090
  . "${ROOT_DIR}/scripts/lifecycle.sh"
  ensure_yarn
  if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is required for local Kanban API."
    echo "  Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
  fi
  info "Starting dev stack (foreground)"
  chmod +x "${ROOT_DIR}/scripts/start.sh"
  exec "${ROOT_DIR}/scripts/start.sh"
fi

info "Next step: connect your runtime"
echo "- OpenClaw: set OPENCLAW_BASE_URL / OPENCLAW_API_KEY in .env"
echo "- Claude Code: set CLAUDE_API_KEY in .env"
echo "- Mistral vibe: set MISTRAL_API_KEY in .env"
echo "- Re-run: docker compose up -d --build"
echo "- Upgrade lifecycle: clawvis update --tag <tag>"
echo "- New CLI: clawvis --help"
