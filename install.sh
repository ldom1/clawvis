#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env"
EXAMPLE_FILE="${ROOT_DIR}/.env.example"
INSTANCES_DIR="${ROOT_DIR}/instances"
NON_INTERACTIVE=0
INSTANCE_NAME_FLAG=""
HUB_PORT_FLAG=""
MEMORY_PORT_FLAG=""
KANBAN_API_PORT_FLAG=""
PROJECTS_ROOT_FLAG=""
MODE_FLAG=""
BRAIN_PATH_FLAG=""
MEMORY_TYPE_FLAG=""
NO_START=0
LAST_LOG="${CLAWVIS_LAST_LOG:-/tmp/clawvis_last.log}"

info() { printf "\n==> %s\n" "$1"; }
warn() { printf "\n[warn] %s\n" "$1"; }
spinner() {
  local pid="$1" msg="$2"
  local spin='|/-\'
  local i=0
  tput civis 2>/dev/null || true
  while kill -0 "${pid}" 2>/dev/null; do
    printf "\r  %s  %s" "${spin:$((i % ${#spin})):1}" "${msg}"
    sleep 0.08
    i=$((i + 1))
  done
  tput cnorm 2>/dev/null || true
}
run_quiet() {
  local msg="$1"
  shift
  "$@" >"${LAST_LOG}" 2>&1 &
  local pid=$!
  spinner "${pid}" "${msg}"
  wait "${pid}"
  local code=$?
  if [ "${code}" -ne 0 ]; then
    printf "\r  ✗  %s (failed — see %s)\n" "${msg}" "${LAST_LOG}"
    exit "${code}"
  fi
  printf "\r  ✓  %s\n" "${msg}"
}
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
ask_choice() {
  local prompt="$1" default="$2"
  shift 2
  local options=("$@")
  local value=""
  while :; do
    printf "%s\n" "${prompt}"
    local idx=1
    for option in "${options[@]}"; do
      printf "  %d) %s\n" "${idx}" "${option}"
      idx=$((idx + 1))
    done
    read -r -p "Choice [${default}]: " value
    value="${value:-$default}"
    if [[ "${value}" =~ ^[0-9]+$ ]] && [ "${value}" -ge 1 ] && [ "${value}" -le "${#options[@]}" ]; then
      printf "%s" "${options[$((value - 1))]}"
      return
    fi
    warn "Invalid choice: ${value}"
  done
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
  --hub-port <port>
  --memory-port <port>
  --kanban-api-port <port>
  --projects-root <path>
  --mode <dev|prod|minimal|docker>
  --brain-path <path>
  --memory-type <local|symlink>
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
      --no-start) NO_START=1 ;;
      --hub-port) HUB_PORT_FLAG="${2:-}"; shift ;;
      --memory-port) MEMORY_PORT_FLAG="${2:-}"; shift ;;
      --kanban-api-port) KANBAN_API_PORT_FLAG="${2:-}"; shift ;;
      --projects-root) PROJECTS_ROOT_FLAG="${2:-}"; shift ;;
      --mode) MODE_FLAG="${2:-}"; shift ;;
      --brain-path) BRAIN_PATH_FLAG="${2:-}"; shift ;;
      --memory-type) MEMORY_TYPE_FLAG="${2:-}"; shift ;;
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
      run_quiet "Migrating legacy memory files" rsync -a "${legacy_abs}/" "${target_abs}/"
    else
      run_quiet "Migrating legacy memory files" cp -a "${legacy_abs}/." "${target_abs}/"
    fi
    warn "Legacy memory kept at ${legacy_abs} (not deleted)."
  fi
}

parse_args "$@"

if [ "${NON_INTERACTIVE}" -eq 0 ] && [ ! -t 0 ]; then
  echo "Error: interactive setup requires a TTY."
  echo "Run with --non-interactive for CI/piped mode."
  exit 1
fi

chmod +x "${ROOT_DIR}/clawvis"
ensure_cli_shim

info "Clawvis bootstrap"
if [ ! -f "${ENV_FILE}" ]; then
  run_quiet "Creating .env from template" cp "${EXAMPLE_FILE}" "${ENV_FILE}"
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

if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  case "${MODE_FLAG:-prod}" in
    docker|prod) WIZARD_MODE="prod"; RUN_MODE="docker" ;;
    dev) WIZARD_MODE="dev"; RUN_MODE="dev" ;;
    minimal) WIZARD_MODE="minimal"; RUN_MODE="docker"; NO_START=1 ;;
    *) echo "Invalid --mode value: ${MODE_FLAG}"; exit 1 ;;
  esac
else
  info "Choose run mode"
  MODE_PICK="$(ask_choice "? Choose run mode:" "1" "dev" "prod" "minimal")"
  case "${MODE_PICK}" in
    dev) WIZARD_MODE="dev"; RUN_MODE="dev" ;;
    prod) WIZARD_MODE="prod"; RUN_MODE="docker" ;;
    minimal) WIZARD_MODE="minimal"; RUN_MODE="docker"; NO_START=1 ;;
  esac
fi
upsert_env "MODE" "${RUN_MODE}"

info "Memory configuration"
MEMORY_ROOT="instances/${INSTANCE_NAME}/memory"
INSTANCE_MEMORY_PATH="${ROOT_DIR}/${MEMORY_ROOT}"
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  BRAIN_PATH_INPUT="${BRAIN_PATH_FLAG:-}"
  if [ -n "${BRAIN_PATH_INPUT}" ] || [ "${MEMORY_TYPE_FLAG:-}" = "symlink" ]; then
    MEMORY_TYPE="symlink"
  else
    MEMORY_TYPE="local"
  fi
else
  MEMORY_CHOICE="$(ask_choice "? Do you already have a brain/memory directory you want to point to?" "2" "Yes, I have an existing memory path" "No, create a fresh memory for this instance")"
  if [ "${MEMORY_CHOICE}" = "Yes, I have an existing memory path" ]; then
    MEMORY_TYPE="symlink"
    BRAIN_PATH_INPUT="$(ask "? Enter the path to your existing brain/memory directory")"
  else
    MEMORY_TYPE="local"
    BRAIN_PATH_INPUT=""
  fi
fi

if [ "${MEMORY_TYPE}" = "symlink" ]; then
  if [ -z "${BRAIN_PATH_INPUT}" ]; then
    echo "Error: --brain-path is required when using symlink memory type."
    exit 1
  fi
  if [ ! -e "${BRAIN_PATH_INPUT}" ]; then
    echo "Error: memory path does not exist: ${BRAIN_PATH_INPUT}"
    exit 1
  fi
  BRAIN_PATH="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "${BRAIN_PATH_INPUT}")"
  mkdir -p "$(dirname "${INSTANCE_MEMORY_PATH}")"
  if [ -d "${INSTANCE_MEMORY_PATH}" ] && [ ! -L "${INSTANCE_MEMORY_PATH}" ]; then
    run_quiet "Removing default local memory directory" rm -rf "${INSTANCE_MEMORY_PATH}"
  elif [ -L "${INSTANCE_MEMORY_PATH}" ]; then
    rm -f "${INSTANCE_MEMORY_PATH}"
  fi
  ln -s "${BRAIN_PATH}" "${INSTANCE_MEMORY_PATH}"
  if [ ! -L "${INSTANCE_MEMORY_PATH}" ]; then
    echo "Error: Failed to create memory symlink"
    exit 1
  fi
else
  BRAIN_PATH="${INSTANCE_MEMORY_PATH}"
  chmod +x "${ROOT_DIR}/scripts/init-memory.sh"
  export INSTANCE_NAME MEMORY_ROOT
  migrate_memory_if_needed "${MEMORY_ROOT}"
  run_quiet "Initializing fresh memory structure" bash "${ROOT_DIR}/scripts/init-memory.sh"
  if [ -f "${ROOT_DIR}/${MEMORY_ROOT}/projects/example-project.md" ]; then
    info "Validation log: example project seeded at ${MEMORY_ROOT}/projects/example-project.md"
  fi
fi

upsert_env "INSTANCE_NAME" "${INSTANCE_NAME}"
upsert_env "MEMORY_ROOT" "${MEMORY_ROOT}"
upsert_env "BRAIN_PATH" "${BRAIN_PATH}"
upsert_env "MEMORY_TYPE" "${MEMORY_TYPE}"

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
upsert_env "PROJECTS_ROOT" "${PROJECTS_ROOT}"
upsert_env "HUB_PORT" "${HUB_PORT}"
upsert_env "MEMORY_PORT" "${MEMORY_PORT}"
upsert_env "KANBAN_API_PORT" "${KANBAN_API_PORT}"
upsert_env "HOST_UID" "$(id -u)"
upsert_env "HOST_GID" "$(id -g)"

info "Brain display (Quartz)"
if [ "${CLAWVIS_SKIP_QUARTZ:-0}" = "1" ]; then
  warn "Quartz setup skipped (CLAWVIS_SKIP_QUARTZ=1)."
else
  if command -v git >/dev/null 2>&1 && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    chmod +x "${ROOT_DIR}/scripts/setup-quartz.sh"
    export INSTANCE_NAME MEMORY_ROOT
    run_quiet "Rebuilding Quartz" bash "${ROOT_DIR}/scripts/setup-quartz.sh" || warn "Quartz setup failed — continuing without Quartz."
  else
    warn "Quartz setup skipped (requires: git + node>=18 + npm)."
  fi
fi

if [ "${NO_START}" -eq 1 ]; then
  info "Instance ready (--no-start: services not launched)"
  echo "- Instance: ${INSTANCE_PATH}"
  echo "- .env:     ${ENV_FILE}"
  echo ""
  echo "To start manually:"
  echo "  docker compose up -d hub kanban-api hub-memory-api"
  echo "  # or: clawvis start"
elif [ "${RUN_MODE}" = "docker" ]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker is required for prod mode."
    echo "  Install Docker: https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is installed but not running."
    echo "  Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
  fi
  # hub depends_on kanban-api + hub-memory-api; list them explicitly so all modes match.
  run_quiet "Starting Docker services" docker compose up -d hub kanban-api hub-memory-api
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

info "Done"
echo "╔══════════════════════════════════════════════════════╗"
echo "║              Clawvis — Setup complete                ║"
echo "╠══════════════════════════════════════════════════════╣"
printf "║  Instance   : %-38s║\n" "${INSTANCE_NAME}"
printf "║  Mode       : %-38s║\n" "${WIZARD_MODE}"
printf "║  Memory     : %-38s║\n" "${BRAIN_PATH}"
printf "║  Type       : %-38s║\n" "${MEMORY_TYPE}"
printf "║  Brain UI   : %-38s║\n" "${ROOT_DIR}/quartz/public/"
echo "╚══════════════════════════════════════════════════════╝"
