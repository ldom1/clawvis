#!/usr/bin/env bash
set -euo pipefail

# Playwright E2E gate (persona specs). Run from repo root: bash tests/ci-playwright.sh
# Starts Hub + APIs via Playwright webServer unless PW_NO_WEBSERVER=1.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v uv >/dev/null 2>&1; then
  echo "==> [ERROR] uv is required (install astral-sh/uv)"
  exit 1
fi
corepack enable >/dev/null 2>&1 || true

PW_DIR="${ROOT_DIR}/tests/playwright"
if [[ ! -f "${PW_DIR}/package-lock.json" ]]; then
  echo "==> [ERROR] missing ${PW_DIR}/package-lock.json"
  exit 1
fi

npm ci --prefix "${PW_DIR}"
(
  cd "${PW_DIR}"
  # --with-deps needs apt/sudo; use only on GitHub-hosted runners (not generic CI=true locally).
  if [[ "${GITHUB_ACTIONS:-}" == "true" ]]; then
    npx playwright install --with-deps chromium
  else
    npx playwright install chromium
  fi
  CI=true npx playwright test --project=chromium --reporter=list --reporter=html
)
