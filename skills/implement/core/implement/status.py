"""Update task status directly in tasks.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from implement.config import TASKS_JSON

VALID_STATUSES = {"Backlog", "To Start", "In Progress", "Blocked", "Review", "Done"}


def update_task_status(task_id: str, new_status: str) -> bool:
    if new_status not in VALID_STATUSES:
        print(f"❌ Invalid status: {new_status}. Valid: {', '.join(sorted(VALID_STATUSES))}")
        return False

    if not TASKS_JSON.exists():
        print(f"❌ tasks.json not found: {TASKS_JSON}")
        return False

    with open(TASKS_JSON, encoding="utf-8") as f:
        data = json.load(f)

    updated = False
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            old_status = task.get("status", "?")
            task["status"] = new_status
            task["updated"] = datetime.now(timezone.utc).isoformat()
            updated = True
            print(f"✅ Task {task_id}: {old_status} → {new_status}")
            break

    if not updated:
        print(f"❌ Task not found: {task_id}")
        return False

    with open(TASKS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


def _cli_update() -> None:
    import sys
    args = sys.argv[1:]
    if len(args) < 2:
        print("Usage: kanban-update <task-id> <status>")
        print("Status: " + " | ".join(sorted(VALID_STATUSES)))
        sys.exit(1)
    sys.exit(0 if update_task_status(args[0], args[1]) else 1)
