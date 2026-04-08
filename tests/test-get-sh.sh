#!/usr/bin/env bash
# tests/test-get-sh.sh — smoke install without touching ~/.clawvis
#
# Modes:
#   --workspace (default) — rsync repo copy, fake docker, install.sh --no-start (no network)
#   --clone — run get.sh with CLAWVIS_REPO_URL=workspace path (tests clone + install, no GitHub)
#   --from-github — curl raw main get.sh | bash (needs network + matches README one-liner)
#
# Usage:
#   bash tests/test-get-sh.sh
#   bash tests/test-get-sh.sh --clone
#   bash tests/test-get-sh.sh --from-github
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="workspace"
INSTANCE="gettest"
RUN_MODE="prod"
RAW_URL="https://raw.githubusercontent.com/ldom1/clawvis/main/get.sh"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --workspace) MODE="workspace" ;;
    --clone) MODE="clone" ;;
    --from-github) MODE="github" ;;
    --run-mode) RUN_MODE="${2:-}"; shift ;;
    -h|--help)
      grep '^#' "$0" | grep -v '#!/'; exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

INSTALL_ARGS=(
  --non-interactive
  --instance "${INSTANCE}"
  --mode "${RUN_MODE}"
  --no-start
  --hub-port 8088
  --memory-port 3099
  --kanban-api-port 8090
)

case "${RUN_MODE}" in
  dev) EXPECT_MODE="dev" ;;
  prod|minimal|docker) EXPECT_MODE="docker" ;;
  *)
    echo "Unsupported run mode for test: ${RUN_MODE}" >&2
    exit 1
    ;;
esac

TEST_HOME=""
TMP_WORK=""
FAKEBIN=""
CLAWVIS_DIR=""

cleanup() {
  [ -n "${TEST_HOME}" ] && rm -rf "${TEST_HOME}"
  [ -n "${TMP_WORK}" ] && rm -rf "${TMP_WORK}"
  [ -n "${FAKEBIN}" ] && rm -rf "${FAKEBIN}"
}
trap cleanup EXIT

TEST_HOME="$(mktemp -d)"
TMP_WORK="$(mktemp -d)"
FAKEBIN="$(mktemp -d)"
printf '#!/bin/sh\nexit 0\n' > "${FAKEBIN}/docker"
chmod +x "${FAKEBIN}/docker"

export HOME="${TEST_HOME}"
export PATH="${FAKEBIN}:${PATH}"
export CLAWVIS_NO_NODE_WRAPPER=1
export CLAWVIS_SKIP_QUARTZ=1

case "${MODE}" in
  workspace)
    CLAWVIS_DIR="${TMP_WORK}/clawvis"
    mkdir -p "${CLAWVIS_DIR}"
    rsync -a --delete \
      --exclude node_modules \
      --exclude .git \
      --exclude .venv \
      --exclude __pycache__ \
      --exclude '.yarn/cache' \
      --exclude hub/node_modules \
      "${ROOT}/" "${CLAWVIS_DIR}/"
    bash "${CLAWVIS_DIR}/install.sh" "${INSTALL_ARGS[@]}"
    ;;
  clone)
    export CLAWVIS_REPO_URL="${ROOT}"
    CLAWVIS_DIR="${TMP_WORK}/clawvis"
    export CLAWVIS_DIR
    bash "${ROOT}/get.sh" "${INSTALL_ARGS[@]}"
    ;;
  github)
    CLAWVIS_DIR="${TMP_WORK}/clawvis"
    export CLAWVIS_DIR
    curl -fsSL "${RAW_URL}" | bash -s -- "${INSTALL_ARGS[@]}"
    ;;
esac

BASE="${CLAWVIS_DIR}"
PASS=0
FAIL=0
check() {
  if eval "$2"; then
    printf "  [PASS] %s\n" "$1"
    PASS=$((PASS + 1))
  else
    printf "  [FAIL] %s\n" "$1"
    FAIL=$((FAIL + 1))
  fi
}

echo ""
echo "=== test-get-sh.sh (${MODE}, run-mode=${RUN_MODE}) ==="
echo ""
check ".env created" "[ -f ${BASE}/.env ]"
check ".env INSTANCE_NAME" "grep -q 'INSTANCE_NAME=${INSTANCE}' ${BASE}/.env"
check ".env HUB_PORT=8088" "grep -q 'HUB_PORT=8088' ${BASE}/.env"
check ".env MEMORY_ROOT" "grep -q 'MEMORY_ROOT=' ${BASE}/.env"
check ".env MODE=${EXPECT_MODE}" "grep -q 'MODE=${EXPECT_MODE}' ${BASE}/.env"
check "instance dir" "[ -d ${BASE}/instances/${INSTANCE} ]"
check "memory/projects" "[ -d ${BASE}/instances/${INSTANCE}/memory/projects ]"
check "example project" "[ -f ${BASE}/instances/${INSTANCE}/memory/projects/example-project.md ]"
check "~/.local/bin/clawvis symlink" "[ -L ${TEST_HOME}/.local/bin/clawvis ]"
check "clawvis executable" "[ -x ${BASE}/clawvis ]"

echo ""
printf "Results: %d passed, %d failed\n" "${PASS}" "${FAIL}"
[ "${FAIL}" -eq 0 ]
