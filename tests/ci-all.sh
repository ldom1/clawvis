#!/usr/bin/env bash
set -euo pipefail

# Global Clawvis test orchestrator for CI.
# Runs component gates in a deterministic order so failures are easy to locate.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

FAILURES=0

run_step() {
  local name="$1"
  local cmd="$2"
  echo "==> [RUN] ${name}"
  if ! eval "${cmd}"; then
    echo "==> [ERROR] ${name} failed"
    FAILURES=$((FAILURES + 1))
  else
    echo "==> [OK] ${name}"
  fi
}

run_step "get-sh" "bash tests/test-get-sh.sh --workspace --run-mode prod && bash tests/test-get-sh.sh --workspace --run-mode dev && bash tests/test-get-sh.sh --workspace --run-mode minimal && bash tests/test-get-sh.sh --clone --run-mode prod"
run_step "kanban" "bash tests/ci-kanban.sh"
run_step "hub-core" "bash tests/ci-hub-core.sh"
run_step "hub" "bash tests/ci-hub.sh"
run_step "playwright" "bash tests/ci-playwright.sh"
run_step "skills" "bash tests/ci-skills.sh"
run_step "cli" "bash tests/ci-cli.sh"

if [ "${FAILURES}" -gt 0 ]; then
  echo "==> CI failed with ${FAILURES} failing step(s)"
  exit 1
fi

echo "==> CI passed: all steps successful"
