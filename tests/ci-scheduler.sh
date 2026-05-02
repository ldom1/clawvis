#!/usr/bin/env bash
set -euo pipefail

# Scheduler quality gate (services/scheduler — workflow/job runner, shell vs agent paths).

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

uv run --directory services/scheduler --with pytest pytest -q tests
