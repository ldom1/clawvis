#!/usr/bin/env bash
# dombot-mail — wrapper around the Python CLI in core/
# Usage: dombot-mail.sh <subcommand> [options...]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CORE_DIR="$SKILL_ROOT/core"

# shellcheck disable=SC1091
source "$(cd "$SKILL_ROOT/.." && pwd)/_clawvis_env.sh"
clawvis_env_load || true

for envf in "$SKILL_ROOT/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done
if [ -n "${CLAWVIS_ROOT:-}" ] && [ -f "${CLAWVIS_ROOT}/.env" ]; then
  set -a && . "${CLAWVIS_ROOT}/.env" && set +a
fi

export UV_PROJECT_ENVIRONMENT="${TMPDIR:-/tmp}/clawvis-venvs/dombot-mail-core"
exec uv run --directory "$CORE_DIR" dombot-mail "$@"
