#!/usr/bin/env bash
set -euo pipefail

# Kanban quality gate:
# - style/lint with ruff
# - static quality with pylint
# - unit tests with pytest

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYLINTHOME="${ROOT_DIR}/.tmp/pylint-kanban"
mkdir -p "${PYLINTHOME}"

uv run --directory kanban --with ruff ruff check kanban_api tests
# Keep pylint signal high in CI without blocking on legacy style debt.
uv run --directory kanban --with pylint pylint --disable=all --enable=E,F --ignored-modules=kanban_parser,kanban_parser.parser kanban_api
uv run --directory kanban --with pytest pytest -q tests
