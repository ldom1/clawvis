"""Kanban API helpers for project-init."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from project_init.config import KANBAN_API_URL


@dataclass
class ProjectPayload:
    slug: str
    name: str
    description: str
    status: str = "active"
    stage: str = "discovery"
    type: str = "project"


@dataclass
class TaskPayload:
    title: str
    project: str
    status: str = "To Start"
    priority: str = "Medium"
    effort_hours: float = 1.0
    assignee: str = "DomBot"
    description: str = ""


def _post(path: str, payload: dict) -> dict:
    url = f"{KANBAN_API_URL.rstrip('/')}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"POST {path} → {e.code}: {body}") from e


def create_project(p: ProjectPayload) -> dict:
    return _post("/projects", {
        "slug": p.slug,
        "name": p.name,
        "description": p.description,
        "status": p.status,
        "stage": p.stage,
        "type": p.type,
    })


def create_task(t: TaskPayload) -> dict:
    return _post("/tasks", {
        "title": t.title,
        "project": t.project,
        "status": t.status,
        "priority": t.priority,
        "effort_hours": t.effort_hours,
        "assignee": t.assignee,
        "description": t.description,
    })
