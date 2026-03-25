#!/usr/bin/env bash
set -euo pipefail

# hub-core quality gate:
# - ruff
# - pylint (quality score)
# - pytest

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYLINTHOME="${ROOT_DIR}/.tmp/pylint-hub-core"
mkdir -p "${PYLINTHOME}"

uv run --directory hub-core --with ruff ruff check hub_core tests
uv run --directory hub-core --with pylint pylint --disable=all --enable=E,F --disable=E1101,E0401 hub_core tests
# Skip network/external dependency integration tests in CI gate.
uv run --directory hub-core --with pytest pytest -q tests -k "not real_providers and not transcriber_real_audio"
