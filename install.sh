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
TTY_FD=""        # file descriptor for /dev/tty when stdin is piped
STEP_CURRENT=0   # incremented by run_quiet
STEP_TOTAL=5     # rough estimate; keeps percentage meaningful

# Ensure all relative paths and docker compose commands run from repo root.
cd "${ROOT_DIR}"

# ---------------------------------------------------------------------------
# Display helpers — degrade gracefully on non-TTY
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
  _R=$'\033[0m' _B=$'\033[1m' _D=$'\033[2m'
  _C=$'\033[36m' _G=$'\033[32m' _Y=$'\033[33m' _RE=$'\033[31m'
else
  _R='' _B='' _D='' _C='' _G='' _Y='' _RE=''
fi

info()      { printf "\n${_B}${_C}==> %s${_R}\n" "$1"; }
warn()      { printf "  ${_Y}⚠${_R}  %s\n" "$1"; }
error_msg() { printf "  ${_RE}✗${_R}  %s\n" "$1" >&2; }
step()      { printf "  ${_D}→${_R}  %s\n" "$1"; }

_braille=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
spinner() {
  local pid="$1" msg="$2" pct="${3:-}"
  local i=0 nf="${#_braille[@]}"
  [ -t 1 ] || { wait "${pid}"; return; }  # degrade if no ANSI
  tput civis 2>/dev/null || true
  while kill -0 "${pid}" 2>/dev/null; do
    if [ -n "${pct}" ]; then
      printf "\r  %s  %s  %d%%" "${_braille[$((i % nf))]}" "${msg}" "${pct}"
    else
      printf "\r  %s  %s" "${_braille[$((i % nf))]}" "${msg}"
    fi
    sleep 0.08
    i=$((i + 1))
  done
  tput cnorm 2>/dev/null || true
}

run_quiet() {
  local msg="$1"
  shift
  STEP_CURRENT=$((STEP_CURRENT + 1))
  local pct=0
  [ "${STEP_TOTAL}" -gt 0 ] && pct=$(( (STEP_CURRENT * 100) / STEP_TOTAL ))
  "$@" >"${LAST_LOG}" 2>&1 &
  local pid=$!
  spinner "${pid}" "${msg}" "${pct}"
  wait "${pid}"
  local code=$?
  if [ "${code}" -ne 0 ]; then
    printf "\r  ${_RE}✗${_R}  %s (failed)\n" "${msg}"
    cat "${LAST_LOG}" >&2
    exit "${code}"
  fi
  printf "\r  ${_G}✓${_R}  %s\n" "${msg}"
}

print_banner() {
  local version
  version="$(python3 -c "import json; print(json.load(open('${ROOT_DIR}/hub/package.json')).get('version','dev'))" 2>/dev/null || echo "dev")"
  local R="" B="" D="" Y="" C=""
  if [ -t 1 ]; then
    R=$'\033[0m'; B=$'\033[1m'; D=$'\033[2m'; Y=$'\033[33m'; C=$'\033[36m'
  fi
  printf "\n"
  printf "%s┌──────────────────────────────────────┐%s\n" "${C}" "${R}"
  printf "%s│%s  %s♛ Clawvis%s  %sv%-24s%s%s│%s\n" \
    "${C}" "${R}" "${Y}${B}" "${R}" "${D}" "${version}" "${R}" "${C}" "${R}"
  printf "%s└──────────────────────────────────────┘%s\n" "${C}" "${R}"
  printf "\n"
}

ask() {
  local prompt="$1" default="${2:-}"
  local value
  if [ -n "$default" ]; then
    if [ -n "${TTY_FD}" ]; then
      printf "%s [%s]: " "$prompt" "$default" >&"${TTY_FD}"
      read -r value <&"${TTY_FD}"
    else
      read -r -p "$prompt [$default]: " value
    fi
    printf "%s" "${value:-$default}"
  else
    if [ -n "${TTY_FD}" ]; then
      printf "%s: " "$prompt" >&"${TTY_FD}"
      read -r value <&"${TTY_FD}"
    else
      read -r -p "$prompt: " value
    fi
    printf "%s" "$value"
  fi
}

ask_choice() {
  local prompt="$1" default="$2"
  shift 2
  local options=("$@")
  local value=""
  while :; do
    if [ -n "${TTY_FD}" ]; then
      printf "%s\n" "${prompt}" >&"${TTY_FD}"
    else
      printf "%s\n" "${prompt}"
    fi
    local idx=1
    for option in "${options[@]}"; do
      if [ -n "${TTY_FD}" ]; then
        printf "  %d) %s\n" "${idx}" "${option}" >&"${TTY_FD}"
      else
        printf "  %d) %s\n" "${idx}" "${option}"
      fi
      idx=$((idx + 1))
    done
    if [ -n "${TTY_FD}" ]; then
      printf "Choice [%s]: " "${default}" >&"${TTY_FD}"
      read -r value <&"${TTY_FD}"
    else
      read -r -p "Choice [${default}]: " value
    fi
    value="${value:-$default}"
    if [[ "${value}" =~ ^[0-9]+$ ]] && [ "${value}" -ge 1 ] && [ "${value}" -le "${#options[@]}" ]; then
      printf "%s" "${options[$((value - 1))]}"
      return
    fi
    if [ -n "${TTY_FD}" ]; then
      printf "\n  ${_Y}⚠${_R}  Invalid choice: %s\n" "${value}" >&"${TTY_FD}"
    else
      warn "Invalid choice: ${value}"
    fi
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
  --hub-port <port>          (default: 8088; documented in .env.example)
  --memory-port <port>       (default: 3099)
  --kanban-api-port <port>   (default: 8090)
  --projects-root <path>
  --mode <Franc|Soisson|Merovingien>   (legacy: docker|prod|dev|minimal accepted)
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
      *) error_msg "Unknown option: $1"; usage; exit 1 ;;
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

# ---------------------------------------------------------------------------
# Open URL in default browser — cross-platform (Linux / macOS / WSL)
# ---------------------------------------------------------------------------
open_browser() {
  local url="$1"
  if command -v wslview >/dev/null 2>&1; then
    wslview "${url}" >/dev/null 2>&1 &
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${url}" >/dev/null 2>&1 &
  elif command -v open >/dev/null 2>&1; then
    open "${url}" >/dev/null 2>&1 &
  fi
}

# ---------------------------------------------------------------------------
parse_args "$@"

USE_TTY_INPUT=0
if [ "${NON_INTERACTIVE}" -eq 0 ] && [ ! -t 0 ]; then
  if [ -r /dev/tty ] && [ -w /dev/tty ]; then
    exec 3<>/dev/tty   # open /dev/tty once as FD 3; reused by ask/ask_choice
    TTY_FD=3
    USE_TTY_INPUT=1
  else
    error_msg "Interactive setup requires a TTY."
    step "Run with --non-interactive for CI/piped mode."
    exit 1
  fi
fi

chmod +x "${ROOT_DIR}/clawvis"
ensure_cli_shim

print_banner
if [ ! -f "${ENV_FILE}" ]; then
  run_quiet "Creating .env from template" cp "${EXAMPLE_FILE}" "${ENV_FILE}"
else
  info ".env already exists, keeping current values"
fi

# ---------------------------------------------------------------------------
# Instance name
# ---------------------------------------------------------------------------
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
  step "Instance folder already exists: ${INSTANCE_PATH}"
else
  if [ -d "${EXAMPLE_PATH}" ] && [ "${INSTANCE_NAME}" != "example" ]; then
    step "Renaming instances/example -> instances/${INSTANCE_NAME}"
    mv "${EXAMPLE_PATH}" "${INSTANCE_PATH}"
  elif [ -d "${EXAMPLE_PATH}" ] && [ "${INSTANCE_NAME}" = "example" ]; then
    step "Using existing instances/example"
  else
    warn "instances/example not found; creating empty instance directory."
    mkdir -p "${INSTANCE_PATH}"
  fi
fi

# ---------------------------------------------------------------------------
# Run mode — Franc (Docker), Soisson (local dev), Merovingien (VPS/no-start)
# Legacy values (docker, prod, dev, minimal) accepted for backward compatibility.
# ---------------------------------------------------------------------------
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  case "${MODE_FLAG:-Franc}" in
    Franc|franc|docker|prod)         WIZARD_MODE="Franc";       RUN_MODE="docker" ;;
    Soisson|soisson|dev)             WIZARD_MODE="Soisson";     RUN_MODE="dev" ;;
    Merovingien|merovingien|minimal) WIZARD_MODE="Merovingien"; RUN_MODE="docker"; NO_START=1 ;;
    *) error_msg "Invalid --mode value: ${MODE_FLAG}"; exit 1 ;;
  esac
else
  info "Choose run mode"
  MODE_PICK="$(ask_choice "? Choose run mode:" "1" \
    "Franc       — Docker, quick start (recommended)" \
    "Soisson     — Local dev (Vite + uvicorn)" \
    "Merovingien — VPS / server deploy (configure only, no local start)")"
  case "${MODE_PICK}" in
    Franc*)       WIZARD_MODE="Franc";       RUN_MODE="docker" ;;
    Soisson*)     WIZARD_MODE="Soisson";     RUN_MODE="dev" ;;
    Merovingien*) WIZARD_MODE="Merovingien"; RUN_MODE="docker"; NO_START=1 ;;
  esac
fi
upsert_env "MODE" "${RUN_MODE}"
step "Mode: ${WIZARD_MODE}"

# ---------------------------------------------------------------------------
# Memory configuration
# ---------------------------------------------------------------------------
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
    error_msg "--brain-path is required when using symlink memory type."
    exit 1
  fi
  if [ ! -e "${BRAIN_PATH_INPUT}" ]; then
    error_msg "Memory path does not exist: ${BRAIN_PATH_INPUT}"
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
    error_msg "Failed to create memory symlink"
    exit 1
  fi
else
  BRAIN_PATH="${INSTANCE_MEMORY_PATH}"
  chmod +x "${ROOT_DIR}/scripts/init-memory.sh"
  export INSTANCE_NAME MEMORY_ROOT
  migrate_memory_if_needed "${MEMORY_ROOT}"
  run_quiet "Initializing fresh memory structure" bash "${ROOT_DIR}/scripts/init-memory.sh"
  if [ -f "${ROOT_DIR}/${MEMORY_ROOT}/projects/example-project.md" ]; then
    step "Example project seeded at ${MEMORY_ROOT}/projects/example-project.md"
  fi
fi

upsert_env "INSTANCE_NAME" "${INSTANCE_NAME}"
upsert_env "MEMORY_ROOT" "${MEMORY_ROOT}"
upsert_env "BRAIN_PATH" "${BRAIN_PATH}"
upsert_env "MEMORY_TYPE" "${MEMORY_TYPE}"

# ---------------------------------------------------------------------------
# Configuration — ports are never prompted interactively.
# Override via --hub-port / --memory-port / --kanban-api-port flags (CI),
# or edit .env directly after first run. Defaults documented in .env.example.
# ---------------------------------------------------------------------------
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  PROJECTS_ROOT="${PROJECTS_ROOT_FLAG:-/home/${USER}/lab_perso/projects}"
else
  PROJECTS_ROOT="$(ask "Projects root path" "/home/${USER}/lab_perso/projects")"
fi
HUB_PORT="${HUB_PORT_FLAG:-8088}"
MEMORY_PORT="${MEMORY_PORT_FLAG:-3099}"
KANBAN_API_PORT="${KANBAN_API_PORT_FLAG:-8090}"
HUB_MEMORY_API_PORT="${HUB_MEMORY_API_PORT:-8091}"

upsert_env "PROJECTS_ROOT" "${PROJECTS_ROOT}"
upsert_env "HUB_PORT" "${HUB_PORT}"
upsert_env "MEMORY_PORT" "${MEMORY_PORT}"
upsert_env "KANBAN_API_PORT" "${KANBAN_API_PORT}"
upsert_env "HUB_MEMORY_API_PORT" "${HUB_MEMORY_API_PORT}"
upsert_env "HOST_UID" "$(id -u)"
upsert_env "HOST_GID" "$(id -g)"

# Docker project name controls the container name prefix: clawvis-{instance}-{service}
# (Fix 4: container_name in docker-compose.yml uses INSTANCE_NAME; COMPOSE_PROJECT_NAME
# is a belt-and-suspenders fallback for any service without an explicit container_name.)
COMPOSE_PROJECT_NAME="clawvis-${INSTANCE_NAME}"
upsert_env "COMPOSE_PROJECT_NAME" "${COMPOSE_PROJECT_NAME}"
export COMPOSE_PROJECT_NAME INSTANCE_NAME

# ---------------------------------------------------------------------------
# Brain display (Quartz)
# ---------------------------------------------------------------------------
info "Brain display (Quartz)"
if [ "${CLAWVIS_SKIP_QUARTZ:-0}" = "1" ]; then
  warn "Quartz setup skipped (CLAWVIS_SKIP_QUARTZ=1)."
else
  if command -v git >/dev/null 2>&1 && command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    chmod +x "${ROOT_DIR}/scripts/setup-quartz.sh"
    export MEMORY_ROOT
    run_quiet "Rebuilding Quartz" bash "${ROOT_DIR}/scripts/setup-quartz.sh" || warn "Quartz setup failed — continuing without Quartz."
  else
    warn "Quartz setup skipped (requires: git + node>=18 + npm)."
  fi
fi

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
if [ "${NO_START}" -eq 1 ]; then
  # Merovingien — instance configured, services not started locally
  print_banner
  info "Instance ready — ${WIZARD_MODE} mode"
  step "Instance : ${INSTANCE_PATH}"
  step ".env     : ${ENV_FILE}"
  printf "\n"
  step "To start : docker compose up -d hub kanban-api hub-memory-api"
  step "       or : clawvis start"
  printf "\n"
  exit 0
elif [ "${RUN_MODE}" = "docker" ]; then
  # Franc — Docker launch
  if ! command -v docker >/dev/null 2>&1; then
    error_msg "Docker is required for Franc mode."
    step "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    error_msg "Docker is installed but not running."
    step "Start Docker Desktop or run: sudo systemctl start docker"
    exit 1
  fi
  # hub depends_on kanban-api + hub-memory-api; list them explicitly so all modes match.
  run_quiet "Starting Docker services" docker compose up -d hub kanban-api hub-memory-api

  # Wait for hub container to become healthy (up to 60s)
  info "Waiting for services"
  _wait_healthy() {
    local container="$1" max=60 i=0
    while [ "${i}" -lt "${max}" ]; do
      local status
      status="$(docker inspect --format='{{.State.Health.Status}}' "${container}" 2>/dev/null || echo "unknown")"
      [ "${status}" = "healthy" ] && return 0
      sleep 2
      i=$((i + 2))
    done
    return 1
  }
  if _wait_healthy "clawvis-${INSTANCE_NAME}-hub"; then
    printf "  ${_G}✓${_R}  Hub healthy\n"
  else
    warn "Hub health check timed out — services may still be starting."
  fi
else
  # Soisson — local dev stack (foreground, replaces this process)
  if ! command -v npm >/dev/null 2>&1; then
    error_msg "npm is required for Soisson (dev) mode."
    step "Install Node.js (>= 18): https://nodejs.org/"
    exit 1
  fi
  # shellcheck disable=SC1090
  . "${ROOT_DIR}/scripts/lifecycle.sh"
  ensure_yarn
  if ! command -v uv >/dev/null 2>&1; then
    error_msg "uv is required for local Kanban API."
    step "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
  fi
  info "Starting dev stack (foreground)"
  chmod +x "${ROOT_DIR}/scripts/start.sh"
  exec "${ROOT_DIR}/scripts/start.sh"
fi

# ---------------------------------------------------------------------------
# Setup complete (reached only for Franc/docker mode)
# ---------------------------------------------------------------------------
print_banner
printf "\n"
info "Setup complete"
printf "  ${_G}✓${_R}  All services running\n"
printf "  ${_D}→${_R}  Hub:        ${_C}http://localhost:${HUB_PORT}${_R}\n"
printf "  ${_D}→${_R}  Brain:      ${_C}http://localhost:${HUB_PORT}/memory/${_R}\n"
printf "  ${_D}→${_R}  Kanban API: ${_C}http://localhost:${KANBAN_API_PORT}${_R}\n"
printf "  ${_D}→${_R}  Instance:   %s\n" "${INSTANCE_NAME}"
printf "  ${_D}→${_R}  Mode:       %s\n" "${WIZARD_MODE}"
printf "\n"

# Open the Hub in the default browser (skip in CI / non-interactive runs)
if [ "${NON_INTERACTIVE}" -eq 0 ]; then
  open_browser "http://localhost:${HUB_PORT}"
fi
