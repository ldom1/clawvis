#!/usr/bin/env bash
# POST /hub/projects — create project + memory + seed tasks (Kanban API).
set -euo pipefail
DESC="${1:?usage: init.sh <description> [display_name]}"
NAME="${2:-}"
API="${KANBAN_API_URL:-http://127.0.0.1:8090}"
KEY="${KANBAN_API_KEY:-}"

BODY=$(python3 -c "
import json, sys
d = {'description': sys.argv[1]}
if len(sys.argv) > 2 and sys.argv[2].strip():
    d['name'] = sys.argv[2].strip()
print(json.dumps(d))
" "$DESC" "$NAME")

ARGS=(-fsS -X POST "$API/hub/projects" -H "Content-Type: application/json" -d "$BODY")
[[ -n "$KEY" ]] && ARGS+=(-H "X-API-Key: $KEY")
exec curl "${ARGS[@]}"
