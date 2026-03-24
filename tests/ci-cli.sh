#!/usr/bin/env bash
set -euo pipefail

# CLI gate:
# - syntax check
# - smoke help output

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

npm --prefix clawvis-cli ci
node --check clawvis-cli/cli.mjs
node clawvis-cli/cli.mjs --help >/dev/null
