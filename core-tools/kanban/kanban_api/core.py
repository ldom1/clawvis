"""Kanban business logic: tasks.json load/save, CRUD, dependencies."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from .models import (
    DependenciesUpdate,
    CommentCreate,
    TaskCreate,
    TaskUpdate,
    Status,
    SplitTaskRequest,
    MetaUpdate,
)

TASKS_FILE = Path.home() / ".openclaw/workspace/memory/kanban/tasks.json"
STATUSES: list[Status] = ["Backlog", "To Start", "In Progress", "Review", "Done"]
_kanban_dir = str(TASKS_FILE.parent)
if _kanban_dir not in sys.path:
    sys.path.insert(0, _kanban_dir)
try:
    from kanban_parser.markdown_writer import write_task_to_md, create_task_in_md
    _MD_SYNC = True
except ImportError:
    _MD_SYNC = False

_LOGGER_DIR = str(Path.home() / ".openclaw/skills/logger/core")


def _log(level: str, action: str, message: str, metadata: dict | None = None):
    cmd = ["uv", "run", "--directory", _LOGGER_DIR, "dombot-log", level, "kanban-api", "system", action, message]
    if metadata:
        cmd.append(json.dumps(metadata))
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _load_raw() -> dict:
    with open(TASKS_FILE) as f:
        return json.load(f)


def _fill(task: dict) -> dict:
    task.setdefault("archived_at", None)
    task.setdefault("created_by", "parser")
    task.setdefault("notes", "")
    task.setdefault("dependencies", [])
    task.setdefault("comments", [])
    task.setdefault("tags", [])
    task.setdefault("start_date", None)
    task.setdefault("end_date", None)
    return task


def _ensure_meta(data: dict) -> dict:
    meta = data.setdefault("meta", {})
    meta.setdefault("vision", "")
    meta.setdefault("description", "")
    meta.setdefault("pr_links", [])
    meta.setdefault("counters", {})
    return meta


def _bump_counter(data: dict, key: str) -> None:
    meta = _ensure_meta(data)
    counters = meta.setdefault("counters", {})
    counters[key] = int(counters.get(key, 0)) + 1


def _compute_stats(tasks: list[dict]) -> dict:
    active = [t for t in tasks if t.get("status") != "Archived"]
    done = sum(1 for t in active if t["status"] == "Done")
    return {
        "total_tasks": len(active),
        "by_status": {s: sum(1 for t in active if t["status"] == s) for s in STATUSES},
        "by_priority": {
            p: sum(1 for t in active if t.get("priority") == p)
            for p in ["Critical", "High", "Medium", "Low"]
        },
        "effort_remaining_hours": sum(
            t.get("effort_hours") or 0
            for t in active
            if t["status"] not in ("Done", "Archived")
        ),
        "completion_rate": done / max(len(active), 1),
    }


def _compute_kanban(tasks: list[dict]) -> dict:
    return {s: [t["id"] for t in tasks if t["status"] == s] for s in STATUSES + ["Archived"]}


def _normalize_tasks(tasks: list[dict]) -> list[dict]:
    for t in tasks:
        _fill(t)
    ids = {t["id"] for t in tasks}
    for t in tasks:
        deps = t.get("dependencies") or []
        t["dependencies"] = [d for d in deps if d in ids and d != t["id"]]
    order = {s: i for i, s in enumerate(STATUSES + ["Archived"])}

    def key(t: dict):
        return (
            t.get("project") or "",
            order.get(t.get("status"), 0),
            t.get("start_date") or t.get("timeline") or "",
            t.get("created") or "",
        )

    tasks.sort(key=key)
    return tasks


def save(data: dict) -> None:
    tasks = _normalize_tasks(data["tasks"])
    data["tasks"] = tasks
    data["generated"] = now_iso()
    data["kanban"] = _compute_kanban(tasks)
    data["stats"] = _compute_stats(tasks)
    with open(TASKS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def list_active_tasks(project: str | None = None, status: str | None = None) -> dict:
    data = _load_raw()
    tasks = [_fill(t) for t in data["tasks"] if t.get("status") != "Archived"]
    if project:
        tasks = [t for t in tasks if t.get("project") == project]
    if status:
        tasks = [t for t in tasks if t.get("status") == status]
    for t in tasks:
        t["has_comments"] = bool(t.get("comments"))
    projects = sorted(set(t["project"] for t in tasks if t.get("project")))
    return {
        "tasks": tasks,
        "stats": data.get("stats", {}),
        "projects": projects,
        "meta": data.get("meta", {}),
    }


def list_archive_tasks() -> list[dict]:
    data = _load_raw()
    return [_fill(t) for t in data["tasks"] if t.get("status") == "Archived"]


def get_stats() -> dict:
    return _load_raw().get("stats", {})


def create_task(body: TaskCreate) -> dict:
    data = _load_raw()
    ts = now_iso()
    source_file = ""
    task_data = {
        "title": body.title, "priority": body.priority,
        "effort_hours": body.effort_hours, "status": "To Start",
        "start_date": body.start_date, "end_date": body.end_date,
    }
    if _MD_SYNC:
        try:
            source_file = create_task_in_md(body.project, task_data)
        except Exception:
            pass
    if source_file:
        tid = "task-" + hashlib.md5(f"{body.title}:{source_file}".encode()).hexdigest()[:8]
    else:
        tid = "task-" + hashlib.md5(f"{body.title}:{ts}".encode()).hexdigest()[:8]
    task = {
        "id": tid,
        "title": body.title,
        "description": body.description,
        "project": body.project,
        "status": "To Start",
        "priority": body.priority,
        "effort_hours": body.effort_hours,
        "timeline": body.timeline,
        "start_date": body.start_date,
        "end_date": body.end_date,
        "assignee": body.assignee,
        "dependencies": [],
        "tags": [],
        "comments": [],
        "progress": 0.0,
        "source_file": source_file,
        "notes": body.notes,
        "confidence": body.confidence,
        "created_by": "user",
        "created": ts,
        "updated": ts,
        "archived_at": None,
    }
    data.setdefault("tasks", []).insert(0, task)
    _bump_counter(data, "created_total")
    save(data)
    _log("INFO", "task:create", f"Created '{body.title}'", {"id": tid, "project": body.project})
    return _fill(task)


def _find_task(data: dict, task_id: str) -> dict:
    task = next((t for t in data["tasks"] if t["id"] == task_id), None)
    if not task:
        raise KeyError("Task not found")
    return task


class DependencyBlockedError(Exception):
    def __init__(self, blocker_title: str):
        self.blocker_title = blocker_title
        super().__init__(f"Blocked by dependency: {blocker_title}")


def _check_dependencies(data: dict, task: dict, target_status: str) -> None:
    if target_status != "In Progress":
        return
    for dep_id in task.get("dependencies") or []:
        dep = next((t for t in data["tasks"] if t["id"] == dep_id), None)
        if dep and dep.get("status") != "Done":
            raise DependencyBlockedError(dep.get("title", dep_id))


def update_task(task_id: str, body: TaskUpdate) -> dict:
    data = _load_raw()
    task = _find_task(data, task_id)
    before_status = task.get("status")
    updates = body.model_dump(exclude_unset=True)
    if "status" in updates:
        _check_dependencies(data, task, updates["status"])
    if _MD_SYNC and task.get("source_file"):
        try:
            write_task_to_md(task["source_file"], task["title"], updates)
        except Exception:
            pass
    for k, v in updates.items():
        task[k] = v
    task["updated"] = now_iso()
    if before_status == "To Start" and task.get("status") == "In Progress":
        _bump_counter(data, "to_start_to_in_progress")
    if task.get("status") == "Done":
        task["progress"] = 1.0
    elif task.get("status") == "In Progress":
        task.setdefault("progress", 0.5)
    save(data)
    _log("INFO", "task:update", f"Updated '{task['title']}'", {"id": task_id, "fields": list(updates.keys())})
    return _fill(task)


def archive_task(task_id: str) -> dict:
    data = _load_raw()
    task = _find_task(data, task_id)
    if _MD_SYNC and task.get("source_file"):
        try:
            write_task_to_md(task["source_file"], task["title"], {"status": "Archived"})
        except Exception:
            pass
    task["status"] = "Archived"
    task["archived_at"] = task["updated"] = now_iso()
    save(data)
    _log("INFO", "task:archive", f"Archived '{task['title']}'", {"id": task_id})
    return _fill(task)


def restore_task(task_id: str) -> dict:
    data = _load_raw()
    task = _find_task(data, task_id)
    if _MD_SYNC and task.get("source_file"):
        try:
            write_task_to_md(task["source_file"], task["title"], {"status": "Backlog"})
        except Exception:
            pass
    task["status"] = "Backlog"
    task["archived_at"] = None
    task["updated"] = now_iso()
    save(data)
    _log("INFO", "task:restore", f"Restored '{task['title']}'", {"id": task_id})
    return _fill(task)


def add_comment(task_id: str, body: CommentCreate) -> dict:
    data = _load_raw()
    task = _find_task(data, task_id)
    comment = {
        "id": hashlib.md5(f"{task_id}:{now_iso()}:{body.text}".encode()).hexdigest()[:8],
        "text": body.text,
        "author": body.author,
        "created_at": now_iso(),
    }
    task.setdefault("comments", []).append(comment)
    task["updated"] = now_iso()
    save(data)
    return comment


def delete_comment(task_id: str, comment_id: str) -> None:
    data = _load_raw()
    task = _find_task(data, task_id)
    comments = task.get("comments") or []
    new_comments = [c for c in comments if c.get("id") != comment_id]
    if len(new_comments) == len(comments):
        raise KeyError("Comment not found")
    task["comments"] = new_comments
    task["updated"] = now_iso()
    save(data)


def add_dependencies(task_id: str, body: DependenciesUpdate) -> list[str]:
    data = _load_raw()
    tasks = data["tasks"]
    task = _find_task(data, task_id)
    valid_ids = {t["id"] for t in tasks}
    deps = task.setdefault("dependencies", [])
    for dep_id in body.ids:
        if dep_id == task_id or dep_id not in valid_ids:
            continue
        if dep_id not in deps:
            deps.append(dep_id)
    task["updated"] = now_iso()
    save(data)
    return deps


def delete_dependency(task_id: str, dependency_id: str) -> list[str]:
    data = _load_raw()
    task = _find_task(data, task_id)
    deps = task.get("dependencies") or []
    if dependency_id not in deps:
        raise KeyError("Dependency not found")
    task["dependencies"] = [d for d in deps if d != dependency_id]
    task["updated"] = now_iso()
    save(data)
    return task["dependencies"]


def split_task(task_id: str, body: SplitTaskRequest) -> dict:
    data = _load_raw()
    parent = _find_task(data, task_id)
    ts = now_iso()
    children: list[dict] = []
    base = body.base_title or parent.get("title") or "Subtask"
    for idx in range(1, body.count + 1):
        cid = "task-" + hashlib.md5(f"{parent['id']}:{idx}:{ts}".encode()).hexdigest()[:8]
        child = {
            "id": cid,
            "title": f"{base} #{idx}" if body.count > 1 else base,
            "description": parent.get("description", ""),
            "project": parent.get("project", ""),
            "status": "To Start",
            "priority": parent.get("priority", "Medium"),
            "effort_hours": parent.get("effort_hours"),
            "timeline": parent.get("timeline"),
            "start_date": parent.get("start_date"),
            "end_date": parent.get("end_date"),
            "assignee": parent.get("assignee", "DomBot"),
            "dependencies": list(parent.get("dependencies") or []),
            "tags": list(parent.get("tags") or []),
            "comments": [],
            "progress": 0.0,
            "source_file": "",
            "notes": "",
            "created_by": "user",
            "created": ts,
            "updated": ts,
            "archived_at": None,
        }
        data.setdefault("tasks", []).append(child)
        children.append(child)
    parent["dependencies"] = [c["id"] for c in children]
    parent["updated"] = now_iso()
    save(data)
    _log(
        "INFO",
        "task:split",
        f"Split '{parent['title']}' into {len(children)}",
        {"id": task_id, "children": [c["id"] for c in children]},
    )
    return {"parent": _fill(parent), "children": [_fill(c) for c in children]}


def get_meta() -> dict:
    data = _load_raw()
    return {
        "meta": data.get("meta", {}),
        "stats": data.get("stats", {}),
    }


def update_meta(body: MetaUpdate) -> dict:
    data = _load_raw()
    meta = _ensure_meta(data)
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "pr_links" and value is not None:
            meta["pr_links"] = value
        elif value is not None:
            meta[key] = value
    meta["last_update"] = now_iso()
    save(data)
    return meta
