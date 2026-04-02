"""Kanban API helpers for implement."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from implement.config import KANBAN_API_URL, MEMORY_ROOT


@dataclass
class TaskContext:
    id: str
    title: str
    description: str
    project: str
    status: str
    priority: str
    effort_hours: float
    brain_note: str  # path to Brain note (may not exist yet)
    brain_content: str  # content of Brain note (empty if not found)


def get_task(task_id: str) -> TaskContext:
    url = f"{KANBAN_API_URL.rstrip('/')}/tasks/{task_id}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GET /tasks/{task_id} → {e.code}") from e

    project = data.get("project", "")
    brain_note_path = MEMORY_ROOT / "projects" / f"{project}.md"
    brain_content = brain_note_path.read_text(encoding="utf-8") if brain_note_path.exists() else ""

    return TaskContext(
        id=task_id,
        title=data.get("title", ""),
        description=data.get("description", ""),
        project=project,
        status=data.get("status", ""),
        priority=data.get("priority", ""),
        effort_hours=float(data.get("effort_hours", 1.0)),
        brain_note=str(brain_note_path),
        brain_content=brain_content,
    )


def update_status(task_id: str, status: str) -> None:
    url = f"{KANBAN_API_URL.rstrip('/')}/tasks/{task_id}"
    data = json.dumps({"status": status}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="PATCH")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"PATCH /tasks/{task_id} → {e.code}") from e
