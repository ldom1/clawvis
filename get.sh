#!/usr/bin/env bash
# Clawvis bootstrap — one-liner installer
# Usage: curl -fsSL https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh | bash
#
# CLAWVIS_DIR     install path (default: ~/.clawvis)
# CLAWVIS_REPO_URL clone source — https URL or local path to a git repo (default: GitHub)
# CLAWVIS_REF      optional branch or tag for fresh clone (--depth 1)
set -euo pipefail

REPO_URL="${CLAWVIS_REPO_URL:-https://github.com/ldom1/clawvis}"
REF="${CLAWVIS_REF:-}"
INSTALL_DIR="${CLAWVIS_DIR:-$HOME/.clawvis}"
LAST_LOG="${CLAWVIS_LAST_LOG:-/tmp/clawvis_last.log}"

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

if ! command -v git >/dev/null 2>&1; then
  echo "Error: git is required. Install git and retry."
  exit 1
fi

echo "==> Clawvis bootstrap"
echo "    Destination: ${INSTALL_DIR}"

if [ -d "${INSTALL_DIR}/.git" ]; then
  echo "==> Repo already present, pulling latest"
  run_quiet "Updating existing repository" git -C "${INSTALL_DIR}" pull --ff-only
else
  if [ -n "${REF}" ]; then
    run_quiet "Cloning Clawvis repository" git clone --depth 1 --branch "${REF}" "${REPO_URL}" "${INSTALL_DIR}"
  else
    run_quiet "Cloning Clawvis repository" git clone "${REPO_URL}" "${INSTALL_DIR}"
  fi
fi

INSTALL_ARGS=("$@")
if [ ! -t 0 ]; then
  has_non_interactive=0
  for arg in "${INSTALL_ARGS[@]}"; do
    if [ "${arg}" = "--non-interactive" ]; then
      has_non_interactive=1
      break
    fi
  done
  if [ "${has_non_interactive}" -eq 0 ]; then
    if [ -r /dev/tty ] && [ -w /dev/tty ]; then
      echo "==> Piped stdin detected; interactive wizard will use /dev/tty"
    else
      echo "==> Non-interactive stdin detected; using default non-interactive install flags"
      INSTALL_ARGS+=(--non-interactive)
    fi
  fi
fi

exec bash "${INSTALL_DIR}/install.sh" "${INSTALL_ARGS[@]}"
