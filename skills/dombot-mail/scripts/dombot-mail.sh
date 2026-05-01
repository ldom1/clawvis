#!/usr/bin/env bash
# dombot-mail — wrapper around the Python CLI in core/
# Usage: dombot-mail.sh <subcommand> [options...]
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CORE_DIR="$SKILL_DIR/core"

# Load .env if present
for envf in "$SKILL_DIR/.env" "$CORE_DIR/.env"; do
  [ -f "$envf" ] && { set -a; . "$envf"; set +a; }
done

exec uv run --directory "$CORE_DIR" dombot-mail "$@"
