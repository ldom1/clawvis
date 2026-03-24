#!/usr/bin/env bash
set -euo pipefail

# Hub quality gate:
# - format check
# - test suite

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if command -v corepack >/dev/null 2>&1; then
  corepack enable
fi
yarn --cwd hub install --frozen-lockfile
yarn --cwd hub format:check
yarn --cwd hub test
yarn --cwd hub build
