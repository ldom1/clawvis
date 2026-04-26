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
_K=$'\033[K' # erase to end of line (clears spinner % / trailing chars)
if [ -t 1 ]; then
  _R=$'\033[0m' _B=$'\033[1m' _D=$'\033[2m'
  _M=$'\033[35m' _C=$'\033[36m' _G=$'\033[32m' _Y=$'\033[33m' _RE=$'\033[31m'
else
  _R='' _B='' _D='' _M='' _C='' _G='' _Y='' _RE=''
fi

# Magenta section titles — parity with clawvis-cli printSection / box border
info()      { printf "\n${_B}${_M}==> %s${_R}\n" "$1"; }
warn()      { printf "  ${_Y}⚠${_R}  %s\n" "$1"; }
error_msg() { printf "  ${_RE}✗${_R}  %s\n" "$1" >&2; }
# Informative status only (no subprocess). Long tasks use run_quiet → green ✓ when done.
step()      { printf "  ${_D}→${_R}  %s\n" "$1"; }

_braille=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
spinner() {
  local pid="$1" msg="$2" pct="${3:-}"
  local i=0 nf="${#_braille[@]}"
  [ -t 1 ] || { wait "${pid}"; return; }  # degrade if no ANSI
  tput civis 2>/dev/null || true
  while kill -0 "${pid}" 2>/dev/null; do
    if [ -n "${pct}" ]; then
      printf "\r  %s  %s  %d%%%s" "${_braille[$((i % nf))]}" "${msg}" "${pct}" "${_K}"
    else
      printf "\r  %s  %s%s" "${_braille[$((i % nf))]}" "${msg}" "${_K}"
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
    printf "\r  ${_RE}✗${_R}  %s (failed)%s\n" "${msg}" "${_K}"
    cat "${LAST_LOG}" >&2
    exit "${code}"
  fi
  printf "\r  ${_G}✓${_R}  %s%s\n" "${msg}" "${_K}"
}

# Same wordmark as clawvis-cli/cli.mjs (keep get.sh + clawvis copies in sync).
clawvis_cli_print_header() {
  local root="${1:-.}"
  local v
  v="$(git -C "${root}" describe --tags --always 2>/dev/null || echo "dev")"
  [ "${v#v}" = "${v}" ] && v="v${v}"
  if [ ! -t 1 ]; then
    printf '\n♛ CLAWVIS %s\n\n' "${v}"
    return 0
  fi
  local M=$'\033[35m' B=$'\033[1;35m' D=$'\033[2m' R=$'\033[0m'
  local inner=36
  local row1_pad=$((inner - 12))
  [ "${row1_pad}" -lt 0 ] && row1_pad=0
  local row2_pad=$((inner - 5 - ${#v}))
  [ "${row2_pad}" -lt 0 ] && row2_pad=0
  printf '\n'
  printf '%b╭────────────────────────────────────╮%b\n' "${M}" "${R}"
  printf '%b│%b  %s♛%s  %sCLAWVIS%s%*s%b│%b\n' \
    "${M}" "${R}" "${M}" "${R}" "${B}" "${R}" "${row1_pad}" "" "${M}" "${R}"
  printf '%b│%b     %s%s%*s%b│%b\n' \
    "${M}" "${R}" "${D}" "${v}" "${row2_pad}" "" "${M}" "${R}"
  printf '%b╰────────────────────────────────────╯%b\n\n' "${M}" "${R}"
}

print_banner() {
  clawvis_cli_print_header "${ROOT_DIR}"
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
  --mode <Franc|Soissons|Merovingien>  (legacy: docker|prod|dev|minimal accepted)
  --brain-path <path>
  --memory-type <local|symlink>
  --no-start      Create instance structure only, do not launch services
  -h, --help
EOF
}

upsert_env() {
  local key="$1" value="$2"
  python3 - "$ENV_FILE" "$key" "$value" <<'PY'
import re
import shlex
import sys
from pathlib import Path

# Values with spaces (e.g. BRAIN_PATH=.../Local Brain) must be quoted or `source .env`
# treats the next token as a command (Quartz: lifecycle.sh load_env_file).
_SAFE_UNQUOTED = re.compile(r"^[A-Za-z0-9_./:@+-]+$")


def format_env_value(v: str) -> str:
    if v == "":
        return "''"
    if _SAFE_UNQUOTED.fullmatch(v):
        return v
    return shlex.quote(v)


path = Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
line = f"{key}={format_env_value(value)}"
if not path.exists():
    path.write_text(line + "\n", encoding="utf-8")
    raise SystemExit(0)
lines = path.read_text(encoding="utf-8").splitlines()
out = []
replaced = False
for ln in lines:
    if ln.startswith(f"{key}="):
        out.append(line)
        replaced = True
    else:
        out.append(ln)
if not replaced:
    out.append(line)
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
}

delete_env_key() {
  local key="$1"
  [ -f "${ENV_FILE}" ] || return 0
  python3 - "$ENV_FILE" "$key" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
key = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()
out = [ln for ln in lines if not ln.startswith(f"{key}=")]
path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY
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

# Normalize pasted brain paths: BOM/CR, outer quotes, ~, Windows drive letters (wslpath),
# and MSYS /c/... vs WSL /mnt/c/... (same folder, different mount prefixes).
normalize_brain_path_input() {
  CLAWVIS_BRAIN_PATH_RAW="$1" python3 <<'PY'
import os, shutil, subprocess
from pathlib import Path

raw = os.environ.get("CLAWVIS_BRAIN_PATH_RAW", "")

s = raw.strip().strip("\ufeff").replace("\r", "").strip()
while len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
    s = s[1:-1].strip()

candidates = []
p0 = Path(s).expanduser()
candidates.append(p0)
wslpath_bin = shutil.which("wslpath")
if wslpath_bin and len(s) >= 2 and s[1] == ":":
    try:
        out = subprocess.check_output([wslpath_bin, "-u", s], text=True).strip()
        candidates.append(Path(out))
    except (subprocess.CalledProcessError, OSError):
        pass
if s.startswith("/mnt/c/"):
    candidates.append(Path("/c") / s[len("/mnt/c/") :])
if s.startswith("/c/"):
    candidates.append(Path("/mnt/c") / s[len("/c/") :])

for p in candidates:
    if p.exists():
        print(str(p.resolve()), end="")
        raise SystemExit(0)
print(str(p0), end="")
PY
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
# Run mode — Franc (Docker), Soissons (local dev), Merovingien (VPS/no-start)
# Legacy values (docker, prod, dev, minimal) accepted for backward compatibility.
# ---------------------------------------------------------------------------
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  case "${MODE_FLAG:-Franc}" in
    Franc|franc|docker|prod)         WIZARD_MODE="Franc";       RUN_MODE="docker" ;;
    Soissons|soissons|Soisson|soisson|dev) WIZARD_MODE="Soissons"; RUN_MODE="dev" ;;
    Merovingien|merovingien|minimal) WIZARD_MODE="Merovingien"; RUN_MODE="docker"; NO_START=1 ;;
    *) error_msg "Invalid --mode value: ${MODE_FLAG}"; exit 1 ;;
  esac
else
  info "Choose run mode"
  MODE_PICK="$(ask_choice "? Choose run mode (1=Franc, 2=Soissons, 3=Merovingien):" "1" \
    "Franc       — Docker, quick start (recommended)" \
    "Soissons    — Local dev / contribution (Vite + uvicorn)" \
    "Merovingien — VPS / server deploy (configure only, no local start)")"
  case "${MODE_PICK}" in
    Franc*)       WIZARD_MODE="Franc";       RUN_MODE="docker" ;;
    Soissons*)    WIZARD_MODE="Soissons";    RUN_MODE="dev" ;;
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
  BRAIN_PATH_INPUT="$(normalize_brain_path_input "${BRAIN_PATH_INPUT}")"
  if [ ! -e "${BRAIN_PATH_INPUT}" ]; then
    error_msg "Memory path does not exist: ${BRAIN_PATH_INPUT}"
    warn "From this shell, run: ls -la \"${BRAIN_PATH_INPUT}\" — if that fails under WSL, the folder may be OneDrive online-only (sync locally) or use the path form this environment understands (e.g. /c/Users/... in Git Bash vs /mnt/c/... in WSL)."
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

AUTO_PROJECTS_ROOT=""
if [ "${MEMORY_TYPE}" = "symlink" ]; then
  CANDIDATE_PROJECTS_ROOT="$(python3 -c 'import os,sys; p=os.path.realpath(sys.argv[1]); inside=os.path.join(p,"projects"); sibling=os.path.join(os.path.dirname(p),"projects"); print(inside if os.path.isdir(inside) else sibling)' "${BRAIN_PATH}")"
  if [ -d "${CANDIDATE_PROJECTS_ROOT}" ]; then
    AUTO_PROJECTS_ROOT="${CANDIDATE_PROJECTS_ROOT}"
  fi
fi

# ---------------------------------------------------------------------------
# Configuration — ports are never prompted interactively.
# Override via --hub-port / --memory-port / --kanban-api-port flags (CI),
# or edit .env directly after first run. Defaults documented in .env.example.
# ---------------------------------------------------------------------------
if [ "${NON_INTERACTIVE}" -eq 1 ]; then
  if [ -n "${PROJECTS_ROOT_FLAG:-}" ]; then
    PROJECTS_ROOT="${PROJECTS_ROOT_FLAG}"
  elif [ -n "${AUTO_PROJECTS_ROOT}" ]; then
    PROJECTS_ROOT="${AUTO_PROJECTS_ROOT}"
  else
    PROJECTS_ROOT="/home/${USER}/lab_perso/projects"
  fi
else
  PROJECTS_ROOT_DEFAULT="${AUTO_PROJECTS_ROOT:-/home/${USER}/lab_perso/projects}"
  PROJECTS_ROOT="$(ask "Projects root path" "${PROJECTS_ROOT_DEFAULT}")"
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
# Local/dev and non-compose launches: default Claude CLI path for provider=cli.
if [ -x "${HOME}/.local/bin/claude" ]; then
  upsert_env "CLI_BIN" "${HOME}/.local/bin/claude"
fi

# Docker project name controls the container name prefix: clawvis-{instance}-{service}
# (Fix 4: container_name in docker-compose.yml uses INSTANCE_NAME; COMPOSE_PROJECT_NAME
# is a belt-and-suspenders fallback for any service without an explicit container_name.)
COMPOSE_PROJECT_NAME="clawvis-${INSTANCE_NAME}"
upsert_env "COMPOSE_PROJECT_NAME" "${COMPOSE_PROJECT_NAME}"
export COMPOSE_PROJECT_NAME INSTANCE_NAME

# Docker: bind-mount symlink target so Kanban/Memory APIs can read memory/projects/*.md.
if [ "${MEMORY_TYPE}" = "symlink" ]; then
  upsert_env "COMPOSE_FILE" "docker-compose.yml:docker-compose.clawvis-brain.yml"
else
  delete_env_key "COMPOSE_FILE"
fi

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
# MCP server dependencies
# ---------------------------------------------------------------------------
if command -v npm >/dev/null 2>&1 && [ -f "${ROOT_DIR}/mcp/package.json" ]; then
  if [ ! -d "${ROOT_DIR}/mcp/node_modules" ]; then
    run_quiet "Installing MCP server dependencies" npm --prefix "${ROOT_DIR}/mcp" install --silent
  fi
else
  warn "MCP server deps skipped (npm not found or mcp/package.json missing)."
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
  step "To start : docker compose up -d hub kanban-api hub-memory-api agent-service telegram scheduler"
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
  # hub depends_on kanban-api + hub-memory-api + agent-service; list all explicitly.
  run_quiet "Starting Docker services" docker compose up -d hub kanban-api hub-memory-api agent-service telegram scheduler

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
  # Soissons — local dev stack (foreground, replaces this process)
  if ! command -v npm >/dev/null 2>&1; then
    error_msg "npm is required for Soissons (dev) mode."
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
