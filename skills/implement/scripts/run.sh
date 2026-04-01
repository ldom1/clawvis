#!/usr/bin/env bash
# Load task JSON from Kanban API for agent implementation loop.
set -euo pipefail
TASK_ID="${1:?usage: run.sh <task_id>}"
API="${KANBAN_API_URL:-http://127.0.0.1:8090}"
KEY="${KANBAN_API_KEY:-}"
ARGS=(-fsS "$API/tasks")
[[ -n "$KEY" ]] && ARGS+=(-H "X-API-Key: $KEY")
TASK_JSON=$(curl "${ARGS[@]}")
TASK=$(echo "$TASK_JSON" | python3 -c "import json,sys; data=json.load(sys.stdin); tid=sys.argv[1]; \
print(json.dumps(next((t for t in data.get('tasks',[]) if t.get('id')==tid), {})))" "$TASK_ID")
if [[ "$TASK" == "{}" ]]; then
  echo "implement: task not found: $TASK_ID" >&2
  exit 1
fi
echo "--- Task (JSON) ---"
echo "$TASK" | python3 -m json.tool
echo ""
echo "--- Next steps (agent) ---"
echo "1. kanban-implementer update $TASK_ID \"In Progress\""
echo "2. Edit repo per PROTOCOL.md and task source_file / project."
echo "3. Branch, commit, gh pr create, then kanban-implementer update $TASK_ID \"Review\""
