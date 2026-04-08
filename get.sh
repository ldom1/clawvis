#!/usr/bin/env bash
# Clawvis bootstrap — one-liner installer
# Usage: curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash
#
# CLAWVIS_DIR     install path (default: ~/.clawvis)
# CLAWVIS_REPO_URL clone source — https URL or local path to a git repo (default: GitHub)
# CLAWVIS_REF      optional branch or tag for fresh clone (--depth 1)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_REPO_URL="https://github.com/ldom1/clawvis"
DEFAULT_REF=""

# Local dev convenience:
# when running get.sh from a checked-out repo, reuse that repo + current branch.
if [ -d "${SCRIPT_DIR}/.git" ]; then
  DEFAULT_REPO_URL="${SCRIPT_DIR}"
  DEFAULT_REF="$(git -C "${SCRIPT_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
fi

REPO_URL="${CLAWVIS_REPO_URL:-${DEFAULT_REPO_URL}}"
REF="${CLAWVIS_REF:-${DEFAULT_REF}}"
INSTALL_DIR="${CLAWVIS_DIR:-$HOME/.clawvis}"
LAST_LOG="${CLAWVIS_LAST_LOG:-/tmp/clawvis_last.log}"
LOCAL_DEV_SOURCE=0
[ "${REPO_URL}" = "${SCRIPT_DIR}" ] && LOCAL_DEV_SOURCE=1

_braille=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
spinner() {
  local pid="$1" msg="$2"
  local i=0 nf="${#_braille[@]}"
  [ -t 1 ] || { wait "${pid}"; return; }
  tput civis 2>/dev/null || true
  while kill -0 "${pid}" 2>/dev/null; do
    printf "\r  %s  %s" "${_braille[$((i % nf))]}" "${msg}"
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

ensure_cli_deps() {
  local cli_dir="${INSTALL_DIR}/clawvis-cli"
  local marker="${cli_dir}/node_modules/commander/package.json"
  if [ ! -d "${cli_dir}" ] || [ ! -f "${cli_dir}/package.json" ]; then
    return 1
  fi
  if [ -f "${marker}" ]; then
    return 0
  fi
  if ! command -v npm >/dev/null 2>&1; then
    return 1
  fi
  run_quiet "Installing CLI dependencies" npm --prefix "${cli_dir}" ci
}

sync_local_worktree() {
  if [ "${LOCAL_DEV_SOURCE}" -ne 1 ]; then
    return 0
  fi
  if command -v rsync >/dev/null 2>&1; then
    run_quiet "Syncing local working tree" rsync -a \
      --exclude ".git/" \
      --exclude "node_modules/" \
      --exclude ".venv/" \
      --exclude ".pytest_cache/" \
      --exclude ".mypy_cache/" \
      --exclude "quartz/" \
      --exclude "hub/node_modules/" \
      --exclude "clawvis-cli/node_modules/" \
      --exclude "quartz/.git/" \
      "${SCRIPT_DIR}/" "${INSTALL_DIR}/"
  else
    echo "==> Local source detected but rsync is missing; using committed state only"
  fi
}

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required. Install git and retry."
  exit 1
fi

echo "==> Clawvis bootstrap"
echo "    Destination: ${INSTALL_DIR}"

if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "==> Repo already present, updating"
  if [ -n "${REF}" ]; then
    current="$(git -C "${INSTALL_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
    if [ "${current}" != "${REF}" ]; then
      run_quiet "Switching to ${REF}" bash -c \
        "git -C \"${INSTALL_DIR}\" fetch origin \"${REF}\" && git -C \"${INSTALL_DIR}\" checkout \"${REF}\""
    fi
    run_quiet "Updating to latest ${REF}" git -C "${INSTALL_DIR}" pull --ff-only
  else
    run_quiet "Updating existing repository" git -C "${INSTALL_DIR}" pull --ff-only
  fi
  sync_local_worktree
else
  if [ -n "${REF}" ]; then
    run_quiet "Cloning Clawvis repository" git clone --depth 1 --branch "${REF}" "${REPO_URL}" "${INSTALL_DIR}"
  else
    run_quiet "Cloning Clawvis repository" git clone "${REPO_URL}" "${INSTALL_DIR}"
  fi
  sync_local_worktree
fi

INSTALL_ARGS=("$@")
has_non_interactive=0
for arg in "${INSTALL_ARGS[@]}"; do
  if [ "${arg}" = "--non-interactive" ]; then
    has_non_interactive=1
    break
  fi
done

if [ ! -t 0 ]; then
  if [ "${has_non_interactive}" -eq 0 ]; then
    if [ -r /dev/tty ] && [ -w /dev/tty ]; then
      echo "==> Piped stdin detected; interactive wizard will use /dev/tty"
    else
      echo "==> Non-interactive stdin detected; using default non-interactive install flags"
      INSTALL_ARGS+=(--non-interactive)
    fi
  fi
fi

# Prefer compact Node wizard in interactive sessions (terminal or piped+tty),
# while keeping install.sh as the execution engine.
if [ "${has_non_interactive}" -eq 0 ] && command -v node >/dev/null 2>&1 && [ -f "${INSTALL_DIR}/clawvis-cli/cli.mjs" ]; then
  if [ -t 0 ] || { [ -r /dev/tty ] && [ -w /dev/tty ]; }; then
    if ensure_cli_deps; then
      echo "==> Launching setup wizard"
      exec env CLAWVIS_COMPACT_INSTALL_HEADER=1 \
        node "${INSTALL_DIR}/clawvis-cli/cli.mjs" install
    else
      echo "==> Compact wizard unavailable (CLI deps missing); falling back to bash installer"
    fi
  fi
fi

exec bash "${INSTALL_DIR}/install.sh" "${INSTALL_ARGS[@]}"
