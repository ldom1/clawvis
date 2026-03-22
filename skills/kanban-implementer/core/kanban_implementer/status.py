"""Update task status in tasks.json."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from kanban_implementer.config import TASKS_JSON

VALID_STATUSES = {"Backlog", "To Start", "In Progress", "Blocked", "Review", "Done"}


def update_task_status(task_id: str, new_status: str) -> bool:
    """
    Update a task's status in tasks.json.
    Returns True if found and updated, False otherwise.
    """
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
