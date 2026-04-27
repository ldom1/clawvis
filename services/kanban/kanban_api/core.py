"""Kanban business logic: tasks.json load/save, CRUD, dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from hub_core.brain_memory import (
    active_brain_memory_root as resolve_active_brain_memory_root,
)
from hub_core.central_logger import trace_event

from kanban_api.models import (
    STATUSES,
    CommentCreate,
    DependenciesUpdate,
    HubSettingsUpdate,
    MetaUpdate,
    ProjectCreate,
    SplitTaskRequest,
    TaskCreate,
    TaskUpdate,
)

_CLAWVIS_ROOT = (
    Path(os.environ["CLAWVIS_ROOT"]).expanduser().resolve()
    if os.environ.get("CLAWVIS_ROOT")
    else Path(__file__).resolve().parents[3]
)
_memory_root_env = os.environ.get("MEMORY_ROOT")
if _memory_root_env:
    _memory_root_path = Path(_memory_root_env).expanduser()
    if not _memory_root_path.is_absolute():
        _memory_root_path = _CLAWVIS_ROOT / _memory_root_path
else:
    _memory_root_path = Path.home() / ".openclaw/workspace/memory"

TASKS_FILE = _memory_root_path / "kanban" / "tasks.json"

_ROADMAP_TITLE = "## Roadmap"
_ROADMAP_HEADER = "| Task | Priority | Start | End | Effort | Status | Deps |"
_ROADMAP_DIVIDER = "|------|----------|-------|-----|--------|--------|------|"


def _md_cell(value: object) -> str:
    if value is None:
        return "-"
    text = str(value).strip()
    return text if text else "-"


def _format_status(value: object) -> str:
    return _md_cell(value).lower()


def _format_effort(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


def _split_md_row(line: str) -> list[str]:
    if "|" not in line:
        return []
    parts = [p.strip() for p in line.strip().strip("|").split("|")]
    return parts if len(parts) >= 7 else []


def _roadmap_bounds(lines: list[str]) -> tuple[int, int] | None:
    start = -1
    for i, line in enumerate(lines):
        if line.strip().lower() == "## roadmap":
            start = i
            break
    if start < 0:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return (start, end)


def _ensure_roadmap_table(lines: list[str]) -> tuple[int, int]:
    """Guarantee a ## Roadmap section with a task table exists; return (header_idx, divider_idx)."""
    bounds = _roadmap_bounds(lines)
    if bounds is None:
        if lines and lines[-1].strip():
            lines.extend(["", ""])
        elif lines:
            lines.append("")
        lines.extend([_ROADMAP_TITLE, "", _ROADMAP_HEADER, _ROADMAP_DIVIDER])
        bounds = _roadmap_bounds(lines)
    assert bounds is not None
    start, end = bounds
    header_idx = -1
    for i in range(start + 1, end):
        if lines[i].strip() == _ROADMAP_HEADER:
            header_idx = i
            break
    if header_idx < 0:
        insert_at = start + 1
        lines[insert_at:insert_at] = ["", _ROADMAP_HEADER, _ROADMAP_DIVIDER]
        return (insert_at + 1, insert_at + 2)
    divider_idx = header_idx + 1
    if divider_idx >= len(lines) or lines[divider_idx].strip() != _ROADMAP_DIVIDER:
        lines.insert(divider_idx, _ROADMAP_DIVIDER)
    return (header_idx, divider_idx)


def create_task_in_md(project: str, task_data: dict) -> str:
    """Append a task row to the project memory page, creating the file and Roadmap table if absent."""
    slug = str(project or "").strip()
    if not slug:
        return ""
    path = _memory_file_for(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else f"# {slug}\n"
    lines = content.splitlines()
    _, divider_idx = _ensure_roadmap_table(lines)
    row = (
        f"| {_md_cell(task_data.get('title'))} | {_md_cell(task_data.get('priority'))} | "
        f"{_md_cell(task_data.get('start_date'))} | {_md_cell(task_data.get('end_date'))} | "
        f"{_format_effort(task_data.get('effort_hours'))} | {_format_status(task_data.get('status'))} | - |"
    )
    insert_at = divider_idx + 1
    while insert_at < len(lines) and lines[insert_at].strip().startswith("|"):
        insert_at += 1
    lines.insert(insert_at, row)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return str(path)


def write_task_to_md(source_file: str, title: str, updates: dict) -> None:
    path = Path(source_file).expanduser()
    if not path.exists():
        return
    lines = path.read_text(encoding="utf-8").splitlines()
    bounds = _roadmap_bounds(lines)
    if bounds is None:
        return
    start, end = bounds
    for i in range(start + 1, end):
        cols = _split_md_row(lines[i])
        if not cols:
            continue
        if cols[0] != title:
            continue
        priority = _md_cell(updates.get("priority", cols[1]))
        start_date = _md_cell(updates.get("start_date", cols[2]))
        end_date = _md_cell(updates.get("end_date", cols[3]))
        effort = _format_effort(updates.get("effort_hours", cols[4]))
        status = _format_status(updates.get("status", cols[5]))
        deps = _md_cell(cols[6])
        lines[i] = (
            f"| {cols[0]} | {priority} | {start_date} | {end_date} | {effort} | {status} | {deps} |"
        )
        path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        return

HUB_SETTINGS_FILE = _memory_root_path / "kanban" / "hub_settings.json"
HUB_METADATA_FILE = ".clawvis-project.json"
PROJECT_TEMPLATES_DIR = _CLAWVIS_ROOT / "skills" / "project-init" / "templates"


def _log(level: str, action: str, message: str, metadata: dict | None = None):
    trace_event(
        "kanban.api",
        action,
        level=level,
        message=message,
        **(metadata or {}),
    )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"


def _load_raw() -> dict:
    if not TASKS_FILE.exists():
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {
            "tasks": [],
            "generated": now_iso(),
            "meta": {},
            "stats": {},
            "kanban": {},
        }
    with open(TASKS_FILE, encoding="utf-8") as f:
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
    return {
        s: [t["id"] for t in tasks if t["status"] == s] for s in STATUSES + ["Archived"]
    }


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
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
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
        "title": body.title,
        "priority": body.priority,
        "effort_hours": body.effort_hours,
        "status": "To Start",
        "start_date": body.start_date,
        "end_date": body.end_date,
    }
    try:
        source_file = create_task_in_md(body.project, task_data)
    except Exception:
        pass
    if source_file:
        tid = (
            "task-"
            + hashlib.md5(f"{body.title}:{source_file}".encode()).hexdigest()[:8]
        )
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
    _log(
        "INFO",
        "task:create",
        f"Created '{body.title}'",
        {"id": tid, "project": body.project},
    )
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
    if task.get("source_file"):
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
    _log(
        "INFO",
        "task:update",
        f"Updated '{task['title']}'",
        {"id": task_id, "fields": list(updates.keys())},
    )
    return _fill(task)


def delete_task(task_id: str) -> dict:
    data = _load_raw()
    tasks = data.get("tasks", [])
    task = next((t for t in tasks if t.get("id") == task_id), None)
    if not task:
        raise KeyError("Task not found")
    title = task.get("title", task_id)
    if task.get("source_file"):
        try:
            write_task_to_md(
                task["source_file"],
                task["title"],
                {"status": "Deleted", "deleted": True},
            )
        except Exception:
            pass
    kept = [t for t in tasks if t.get("id") != task_id]
    for t in kept:
        deps = t.get("dependencies") or []
        t["dependencies"] = [d for d in deps if d != task_id]
    data["tasks"] = kept
    save(data)
    _log("INFO", "task:delete", f"Deleted '{title}'", {"id": task_id})
    return {"ok": True, "id": task_id}


def delete_tasks_bulk(project: str | None = None) -> dict:
    """Remove all non-archived tasks, optionally scoped to one project slug."""
    data = _load_raw()
    tasks = data.get("tasks", [])
    to_remove: list[dict] = []
    for t in tasks:
        if t.get("status") == "Archived":
            continue
        if project is not None and (t.get("project") or "") != project:
            continue
        to_remove.append(t)
    removed_ids = {t.get("id") for t in to_remove}
    if not removed_ids:
        return {"ok": True, "deleted": 0}
    for task in to_remove:
        if task.get("source_file"):
            try:
                write_task_to_md(
                    task["source_file"],
                    task["title"],
                    {"status": "Deleted", "deleted": True},
                )
            except Exception:
                pass
    kept = [t for t in tasks if t.get("id") not in removed_ids]
    for t in kept:
        deps = t.get("dependencies") or []
        t["dependencies"] = [d for d in deps if d not in removed_ids]
    data["tasks"] = kept
    save(data)
    _log(
        "INFO",
        "task:bulk_delete",
        f"Bulk-deleted {len(removed_ids)} task(s)"
        + (f" for project '{project}'" if project else ""),
        {"count": len(removed_ids), "project": project or ""},
    )
    return {"ok": True, "deleted": len(removed_ids)}


def archive_task(task_id: str) -> dict:
    data = _load_raw()
    task = _find_task(data, task_id)
    if task.get("source_file"):
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
    if task.get("source_file"):
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
        "id": hashlib.md5(f"{task_id}:{now_iso()}:{body.text}".encode()).hexdigest()[
            :8
        ],
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
    proj = (parent.get("project") or "").strip()
    children: list[dict] = []
    base = body.base_title or parent.get("title") or "Subtask"
    for idx in range(1, body.count + 1):
        cid = (
            "task-" + hashlib.md5(f"{parent['id']}:{idx}:{ts}".encode()).hexdigest()[:8]
        )
        title = f"{base} #{idx}" if body.count > 1 else base
        source_file = ""
        if proj:
            task_md = {
                "title": title,
                "priority": parent.get("priority", "Medium"),
                "effort_hours": parent.get("effort_hours"),
                "status": "To Start",
                "start_date": parent.get("start_date"),
                "end_date": parent.get("end_date"),
            }
            try:
                source_file = create_task_in_md(proj, task_md) or ""
            except Exception:
                source_file = ""
        child = {
            "id": cid,
            "title": title,
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
            "source_file": source_file,
            "notes": "",
            "confidence": parent.get("confidence"),
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


def _default_hub_settings() -> dict:
    return {
        "projects_root": str(_memory_root_path.parent / "projects"),
        "instances_external_root": "",
        "linked_instances": [],
    }


def get_hub_settings() -> dict:
    defaults = _default_hub_settings()
    # Saved workspace settings should win so the Hub UI can effectively change
    # the active projects root. Environment values are a bootstrap fallback.
    env_projects_root = os.environ.get("PROJECTS_ROOT", "").strip()
    if HUB_SETTINGS_FILE.exists():
        try:
            current = json.loads(HUB_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            current = {}
    else:
        current = {}
    # Empty LINKED_INSTANCES must clear links (``[] or file`` would wrongly keep file).
    if "LINKED_INSTANCES" in os.environ:
        linked = [
            p.strip()
            for p in (os.environ.get("LINKED_INSTANCES") or "").split(":")
            if p.strip()
        ]
    else:
        linked_raw = current.get("linked_instances") or []
        linked = linked_raw if isinstance(linked_raw, list) else []
    linked = [str(p) for p in linked if str(p).strip()]
    out = {
        "projects_root": str(
            current.get("projects_root") or env_projects_root or defaults["projects_root"]
        ),
        "instances_external_root": str(
            current.get("instances_external_root")
            or defaults["instances_external_root"]
        ),
        "linked_instances": linked,
    }
    HUB_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUB_SETTINGS_FILE.write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return out


def update_hub_settings(body: HubSettingsUpdate) -> dict:
    current = get_hub_settings()
    settings = {
        "projects_root": body.projects_root or current["projects_root"],
        "instances_external_root": (
            body.instances_external_root
            if body.instances_external_root is not None
            else current.get("instances_external_root", "")
        ),
        "linked_instances": current.get("linked_instances", []),
    }
    HUB_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUB_SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return settings


def _is_instance_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    return any(
        candidate.exists()
        for candidate in (
            path / "docker-compose.override.yml",
            path / "memory",
            path / ".env.local",
        )
    )


def _scan_instances(root: Path, source: str) -> list[dict]:
    if not root.exists() or not root.is_dir():
        return []
    out = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if not _is_instance_dir(entry):
            continue
        out.append(
            {
                "name": entry.name,
                "path": str(entry.resolve()),
                "source": source,
                "has_memory": (entry / "memory").exists(),
                "has_compose_override": (
                    entry / "docker-compose.override.yml"
                ).exists(),
            }
        )
    return out


def list_instances() -> dict:
    settings = get_hub_settings()
    local_root = (_CLAWVIS_ROOT / "instances").resolve()
    external_raw = (settings.get("instances_external_root") or "").strip()
    external_root = Path(external_raw).expanduser().resolve() if external_raw else None

    discovered = _scan_instances(local_root, "local")
    if external_root and external_root != local_root:
        discovered.extend(_scan_instances(external_root, "external"))

    linked = {str(Path(p).expanduser().resolve()) for p in settings["linked_instances"]}
    for item in discovered:
        item["linked"] = item["path"] in linked

    linked_only = [
        {
            "name": Path(path).name,
            "path": path,
            "source": "linked",
            "has_memory": (Path(path) / "memory").exists(),
            "has_compose_override": (
                Path(path) / "docker-compose.override.yml"
            ).exists(),
            "linked": True,
            "missing": not Path(path).exists(),
        }
        for path in sorted(linked)
        if path not in {d["path"] for d in discovered}
    ]
    return {
        "instances": discovered + linked_only,
        "local_root": str(local_root),
        "external_root": str(external_root) if external_root else "",
    }


def link_instance(path: str) -> dict:
    target = str(Path(path).expanduser().resolve())
    if not Path(target).exists():
        raise ValueError("Instance path not found")
    settings = get_hub_settings()
    linked = {str(Path(p).expanduser().resolve()) for p in settings["linked_instances"]}
    linked.add(target)
    settings["linked_instances"] = sorted(linked)
    HUB_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUB_SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {"ok": True, "linked_instances": settings["linked_instances"]}


def unlink_instance(path: str) -> dict:
    target = str(Path(path).expanduser().resolve())
    settings = get_hub_settings()
    linked = {str(Path(p).expanduser().resolve()) for p in settings["linked_instances"]}
    if target in linked:
        linked.remove(target)
    settings["linked_instances"] = sorted(linked)
    HUB_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUB_SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return {"ok": True, "linked_instances": settings["linked_instances"]}


def active_brain_memory_root(settings: dict | None = None) -> Path:
    """Delegates to :func:`hub_core.brain_memory.active_brain_memory_root`."""
    if settings is None:
        settings = get_hub_settings()
    return resolve_active_brain_memory_root(
        memory_root=_memory_root_path,
        linked_instances=settings.get("linked_instances"),
    )


def _slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:48] or "project"


def _derive_name(description: str, explicit_name: str | None) -> str:
    if explicit_name:
        return explicit_name.strip()[:80]
    first = description.strip().splitlines()[0][:80]
    return first


def _normalize_tags(tags: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = raw.strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag[:24])
    return out[:8]


def _memory_file_for(slug: str) -> Path:
    return active_brain_memory_root() / "projects" / f"{slug}.md"


def _parse_brain_md_frontmatter(content: str) -> dict:
    """Minimal YAML frontmatter (--- … ---) for memory/projects/*.md."""
    out: dict[str, object] = {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return out
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i]
        if ":" in line and not line.lstrip().startswith("#"):
            key, _, rest = line.partition(":")
            k = key.strip()
            v = rest.strip()
            if k == "tags":
                m = re.search(r"\[([^\]]*)\]", v)
                if m:
                    raw = m.group(1)
                    out["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
                else:
                    out["tags"] = []
            elif k in (
                "title",
                "status",
                "path",
                "repo",
                "caps",
                "start",
                "end",
                "description",
            ):
                out[k] = v.strip().strip("\"'")
        i += 1
    return out


def _upsert_brain_frontmatter_status(content: str, status: str) -> str:
    """Insert or replace ``status:`` in the first YAML frontmatter block."""
    st = status.strip()
    if not st or "\n" in st or "\r" in st:
        raise ValueError("Invalid status")
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        rest = content.lstrip("\n") if content else ""
        return (
            f"---\nstatus: {st}\n---\n\n{rest}"
            if rest
            else f"---\nstatus: {st}\n---\n\n"
        )

    fm_lines: list[str] = []
    i = 1
    found = False
    while i < len(lines):
        if lines[i].strip() == "---":
            break
        line = lines[i]
        if re.match(r"^\s*status\s*:", line):
            fm_lines.append(f"status: {st}")
            found = True
        else:
            fm_lines.append(line)
        i += 1

    if i >= len(lines) or lines[i].strip() != "---":
        return f"---\nstatus: {st}\n---\n\n{content}"

    if not found:
        fm_lines.append(f"status: {st}")

    body_lines = lines[i + 1 :]
    body = "\n".join(body_lines)
    prefix = "---\n" + "\n".join(fm_lines) + "\n---"
    if not body:
        return prefix + "\n"
    return prefix + "\n" + body


def _memory_md_path_for_project(project: dict) -> Path:
    mp = str(project.get("memory_path") or "").strip()
    if mp:
        return Path(mp).expanduser().resolve()
    slug = str(project.get("slug") or "").strip()
    return _memory_file_for(slug)


def set_project_brain_status(project_slug: str, status: str) -> dict:
    """Set ``status`` in project memory YAML frontmatter (drives Hub ``brain_status``)."""
    project = _find_project_or_raise(project_slug)
    path = _memory_md_path_for_project(project)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    new_content = _upsert_brain_frontmatter_status(content, status)
    path.write_text(new_content, encoding="utf-8")
    _log(
        "INFO",
        "project:brain-status",
        f"Set brain status for '{project_slug}'",
        {"slug": project_slug, "status": status.strip()},
    )
    return {"ok": True, "slug": project_slug, "brain_status": status.strip()}


def _metadata_from_brain_only(slug: str, md_path: Path) -> dict:
    content = md_path.read_text(encoding="utf-8", errors="ignore")
    fm = _parse_brain_md_frontmatter(content)
    name = str(fm.get("title") or slug).strip() or slug
    tags = _normalize_tags(list(fm.get("tags") or []))
    status = str(fm.get("status") or "").strip()
    major = _parse_markdown_major_info(content)
    description = (
        (major.get("description") or "").strip()
        or (major.get("objective") or "").strip()
        or (major.get("context") or "").strip()
    )
    if not description:
        tail = content.split("---", 2)[-1].strip()
        one_line = " ".join(tail.split())[:280]
        description = one_line + ("…" if len(tail) > 280 else "")
    stage = "PoC" if not status else status[:24]
    return {
        "name": name,
        "slug": slug,
        "stage": stage,
        "tags": tags,
        "template": "empty",
        "description": description[:2000],
        "repo_path": "",
        "memory_path": str(md_path),
        "has_logo": False,
        "brain_only": True,
        "brain_status": status,
    }


def _ensure_memory_structure() -> None:
    root = active_brain_memory_root()
    for name in ("projects", "resources", "daily", "archive", "todo"):
        (root / name).mkdir(parents=True, exist_ok=True)


_MAJOR_SECTION_LABELS: dict[str, str] = {
    "description": "Description",
    "macro_objectives": "Objectifs macro",
    "strategy": "Stratégie",
    "objective": "Objectif",
    "context": "Contexte",
    "kanban": "Kanban",
    "links": "Liens",
    "notes": "Notes",
}


def _memory_major_field_order() -> list[str]:
    return list(_MAJOR_SECTION_LABELS.keys())


def _section_key_from_heading(heading: str) -> str | None:
    n = heading.strip().lower()
    aliases = {
        "description": "description",
        "objectifs macro": "macro_objectives",
        "macro objectives": "macro_objectives",
        "macro objectifs": "macro_objectives",
        "stratégie": "strategy",
        "strategy": "strategy",
        "objective": "objective",
        "objectif": "objective",
        "objectif principal": "objective",
        "context": "context",
        "contexte": "context",
        "kanban": "kanban",
        "links": "links",
        "liens": "links",
        "notes": "notes",
        "hub": "hub",
    }
    return aliases.get(n)


def _parse_memory_md_structure(content: str) -> tuple[str, str, list[tuple[str, str]]]:
    lines = content.splitlines()
    idx = 0
    title = ""
    if (
        idx < len(lines)
        and lines[idx].startswith("# ")
        and not lines[idx].startswith("##")
    ):
        title = lines[idx][2:].strip()
        idx += 1
    preamble_lines: list[str] = []
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("## ") and not line.startswith("###"):
            break
        preamble_lines.append(line)
        idx += 1
    preamble = "\n".join(preamble_lines).rstrip("\n")
    blocks: list[tuple[str, str]] = []
    cur_h: str | None = None
    cur_b: list[str] = []
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("## ") and not line.startswith("###"):
            if cur_h is not None:
                blocks.append((cur_h, "\n".join(cur_b).rstrip("\n")))
            cur_h = line[3:].strip()
            cur_b = []
        else:
            cur_b.append(line)
        idx += 1
    if cur_h is not None:
        blocks.append((cur_h, "\n".join(cur_b).rstrip("\n")))
    return title, preamble, blocks


def _serialize_memory_md(
    title: str, preamble: str, blocks: list[tuple[str, str]]
) -> str:
    parts: list[str] = [f"# {title}"]
    if preamble:
        parts.append("")
        parts.append(preamble)
    for heading, body in blocks:
        parts.append("")
        parts.append(f"## {heading}")
        parts.append(body)
    return "\n".join(parts).rstrip() + "\n"


def _parse_markdown_major_info(content: str) -> dict:
    title, _preamble, blocks = _parse_memory_md_structure(content)
    sections: dict[str, str] = {}
    for heading, body in blocks:
        key = _section_key_from_heading(heading)
        if key and key != "hub":
            sections[key] = body.strip()
    return {
        "title": title,
        "description": sections.get("description", ""),
        "macro_objectives": sections.get("macro_objectives", ""),
        "strategy": sections.get("strategy", ""),
        "objective": sections.get("objective", ""),
        "context": sections.get("context", ""),
        "kanban": sections.get("kanban", ""),
        "links": sections.get("links", ""),
        "notes": sections.get("notes", ""),
    }


def update_project_memory_major(project_slug: str, updates: dict) -> dict:
    _find_project_or_raise(project_slug)
    path = _memory_file_for(project_slug)
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    title, preamble, blocks = _parse_memory_md_structure(content)
    by_canon: dict[str, dict[str, str]] = {}
    custom_blocks: list[tuple[str, str]] = []
    for h, body in blocks:
        ck = _section_key_from_heading(h)
        if ck:
            by_canon[ck] = {"heading": h, "body": body}
        else:
            custom_blocks.append((h, body))
    if "title" in updates:
        t = updates["title"]
        if t is not None:
            title = str(t).strip()
    for k in _memory_major_field_order():
        if k not in updates:
            continue
        v = updates[k]
        if v is None:
            continue
        body = str(v).strip("\n")
        prev = by_canon.get(k)
        heading = prev["heading"] if prev else _MAJOR_SECTION_LABELS[k]
        by_canon[k] = {"heading": heading, "body": body}
    order = _memory_major_field_order() + ["hub"]
    out_blocks: list[tuple[str, str]] = []
    for k in order:
        if k not in by_canon:
            continue
        d = by_canon[k]
        out_blocks.append((d["heading"], d["body"]))
    out_blocks.extend(custom_blocks)
    new_content = _serialize_memory_md(title, preamble, out_blocks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_content, encoding="utf-8")
    _log(
        "INFO",
        "project:memory-major",
        f"Updated memory major sections for '{project_slug}'",
        {"slug": project_slug},
    )
    return get_project(project_slug)


def rebuild_brain_static() -> dict:
    script = _CLAWVIS_ROOT / "scripts" / "build-quartz.sh"
    if not script.is_file():
        return {"ok": False, "error": "build-quartz.sh not found"}
    try:
        proc = subprocess.run(
            ["bash", str(script)],
            cwd=str(_CLAWVIS_ROOT),
            capture_output=True,
            text=True,
            timeout=180,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    ok = proc.returncode == 0
    return {
        "ok": ok,
        "returncode": proc.returncode,
        "stderr": (proc.stderr or "")[-4000:],
        "stdout": (proc.stdout or "")[-4000:],
    }


def _template_files(template: str, project_name: str) -> dict[str, str]:
    if template == "nextjs":
        return {
            "README.md": f"# {project_name}\n\nNext.js starter for Clawvis project hub.\n",
            "package.json": (
                "{\n"
                f'  "name": "{_slugify(project_name)}",\n'
                '  "private": true,\n'
                '  "version": "0.1.0",\n'
                '  "scripts": {\n'
                '    "dev": "next dev",\n'
                '    "build": "next build",\n'
                '    "start": "next start"\n'
                "  },\n"
                '  "dependencies": {\n'
                '    "next": "^15.0.0",\n'
                '    "react": "^19.0.0",\n'
                '    "react-dom": "^19.0.0"\n'
                "  }\n"
                "}\n"
            ),
            "app/page.js": "export default function Page(){return <main>Clawvis Next.js project ready</main>}\n",
        }
    if template == "vite":
        return {
            "README.md": f"# {project_name}\n\nVite starter for Clawvis project hub.\n",
            "package.json": (
                "{\n"
                f'  "name": "{_slugify(project_name)}",\n'
                '  "private": true,\n'
                '  "version": "0.1.0",\n'
                '  "scripts": {\n'
                '    "dev": "vite",\n'
                '    "build": "vite build",\n'
                '    "preview": "vite preview"\n'
                "  },\n"
                '  "dependencies": {\n'
                '    "react": "^19.0.0",\n'
                '    "react-dom": "^19.0.0"\n'
                "  },\n"
                '  "devDependencies": {\n'
                '    "vite": "^7.0.0"\n'
                "  }\n"
                "}\n"
            ),
            "src/main.js": "console.log('Clawvis Vite project ready');\n",
        }
    if template == "python":
        return {
            "README.md": f"# {project_name}\n\nPython starter for Clawvis project hub.\n",
            "pyproject.toml": (
                "[project]\n"
                f'name = "{_slugify(project_name)}"\n'
                'version = "0.1.0"\n'
                'requires-python = ">=3.11"\n'
                "dependencies = []\n"
            ),
            "main.py": "def main():\n    print('Clawvis Python project ready')\n\n\nif __name__ == '__main__':\n    main()\n",
        }
    return {"README.md": f"# {project_name}\n\nEmpty starter.\n"}


def _render_template_content(raw: str, project_name: str, project_slug: str) -> str:
    return raw.replace("{{PROJECT_NAME}}", project_name).replace(
        "{{PROJECT_SLUG}}", project_slug
    )


def _copy_cookiecutter_template(
    template: str, project_name: str, project_slug: str, repo_dir: Path
) -> bool:
    template_dir = PROJECT_TEMPLATES_DIR / template
    if not template_dir.exists() or not template_dir.is_dir():
        return False
    for src in template_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(template_dir)
        if src.name == ".gitkeep":
            continue
        dest = repo_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.suffix.lower() in {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".ico",
            ".pdf",
        }:
            shutil.copy2(src, dest)
        else:
            content = src.read_text(encoding="utf-8")
            dest.write_text(
                _render_template_content(content, project_name, project_slug),
                encoding="utf-8",
            )
    return True


def _run_cookiecutter_template(
    template: str, projects_root: Path, project_name: str, project_slug: str
) -> bool:
    template_dir = PROJECT_TEMPLATES_DIR / template
    if not (template_dir / "cookiecutter.json").exists():
        return False
    cmd = [
        "uv",
        "run",
        "--with",
        "cookiecutter",
        "cookiecutter",
        str(template_dir),
        "--no-input",
        "-o",
        str(projects_root),
        f"project_name={project_name}",
        f"project_slug={project_slug}",
    ]
    try:
        subprocess.run(
            cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return True
    except Exception:
        return False


def _maybe_init_git(repo_dir: Path, enabled: bool) -> None:
    if not enabled:
        return
    try:
        subprocess.run(
            ["git", "init"],
            cwd=str(repo_dir),
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _seed_project_tasks(project_slug: str, project_name: str) -> None:
    data = _load_raw()
    existing = [
        t for t in data.get("tasks", []) if (t.get("project") or "") == project_slug
    ]
    if existing:
        return
    ts = now_iso()
    templates = [
        ("Define scope", "Backlog", "High"),
        ("Setup technical baseline", "To Start", "Medium"),
        ("First user-facing milestone", "To Start", "High"),
    ]
    for title, status, priority in templates:
        tid = (
            "task-"
            + hashlib.md5(f"{project_slug}:{title}:{ts}".encode()).hexdigest()[:8]
        )
        data.setdefault("tasks", []).append(
            {
                "id": tid,
                "title": f"{project_name}: {title}",
                "description": "",
                "project": project_slug,
                "status": status,
                "priority": priority,
                "effort_hours": None,
                "timeline": None,
                "start_date": None,
                "end_date": None,
                "assignee": "user",
                "dependencies": [],
                "tags": [],
                "comments": [],
                "progress": 0.0,
                "source_file": "",
                "notes": "",
                "confidence": None,
                "created_by": "user",
                "created": ts,
                "updated": ts,
                "archived_at": None,
            }
        )
    save(data)


def create_project(body: ProjectCreate) -> dict:
    _ensure_memory_structure()
    settings = get_hub_settings()
    root = Path(settings["projects_root"]).expanduser()
    root.mkdir(parents=True, exist_ok=True)
    name = _derive_name(body.description, body.name)
    slug = _slugify(name)
    tags = _normalize_tags(body.tags)
    repo_dir = root / slug
    if repo_dir.exists() and any(repo_dir.iterdir()):
        raise ValueError(f"Project already exists: {slug}")
    used_cookiecutter_cli = _run_cookiecutter_template(body.template, root, name, slug)
    if not used_cookiecutter_cli:
        repo_dir.mkdir(parents=True, exist_ok=True)
    if not used_cookiecutter_cli:
        used_cookiecutter_copy = _copy_cookiecutter_template(
            body.template, name, slug, repo_dir
        )
    else:
        used_cookiecutter_copy = False
    if not used_cookiecutter_cli and not used_cookiecutter_copy:
        for rel_path, content in _template_files(body.template, name).items():
            file_path = repo_dir / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
    _maybe_init_git(repo_dir, body.init_git)
    memory_file = _memory_file_for(slug)
    memory_file.parent.mkdir(parents=True, exist_ok=True)
    if not memory_file.exists() or not memory_file.read_text(encoding="utf-8").strip():
        memory_file.write_text(
            (
                f"# {name}\n\n> Reference projet: cette page memoire est la source principale.\n\n"
                f"## Description\n{body.description.strip()}\n\n"
                f"## Hub\n- Stage: {body.stage}\n- Template: {body.template}\n- Repo: `{repo_dir}`\n"
                + (f"- Tags: {', '.join(tags)}\n" if tags else "")
            ),
            encoding="utf-8",
        )
    _seed_project_tasks(slug, name)
    metadata = {
        "name": name,
        "slug": slug,
        "stage": body.stage,
        "tags": tags,
        "template": body.template,
        "description": body.description.strip(),
        "repo_path": str(repo_dir),
        "memory_path": str(memory_file),
        "has_logo": False,
    }
    (repo_dir / HUB_METADATA_FILE).write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return metadata


_LOGO_ALLOWED_EXT = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"})
_MAX_PROJECT_LOGO_BYTES = 2 * 1024 * 1024


def _project_clawvis_dir(repo_dir: Path) -> Path:
    return repo_dir / ".clawvis"


def project_logo_file(repo_dir: Path) -> Path | None:
    d = _project_clawvis_dir(repo_dir)
    if not d.is_dir():
        return None
    for p in sorted(d.glob("logo.*")):
        if p.suffix.lower() in _LOGO_ALLOWED_EXT and p.is_file():
            return p
    return None


def _load_project_metadata(project_dir: Path) -> dict:
    meta_path = project_dir / HUB_METADATA_FILE
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}
    slug = project_dir.name
    memory_file = _memory_file_for(slug)
    description = (meta.get("description") or "").strip()
    brain_content = ""
    brain_fm: dict[str, object] = {}
    if memory_file.exists():
        try:
            brain_content = memory_file.read_text(encoding="utf-8", errors="ignore")
            brain_fm = _parse_brain_md_frontmatter(brain_content)
        except OSError:
            pass
    if not description and brain_content:
        major = _parse_markdown_major_info(brain_content)
        description = (
            (major.get("description") or "").strip()
            or (major.get("objective") or "").strip()
            or (major.get("context") or "").strip()
        )
        if not description:
            description = str(brain_fm.get("description") or "").strip()
        if not description:
            tail = brain_content.split("---", 2)[-1].strip()
            one_line = " ".join(tail.split())[:280]
            description = (one_line + ("…" if len(tail) > 280 else "")).strip()
    fm_status = str(brain_fm.get("status") or "").strip()
    return {
        "name": meta.get("name") or project_dir.name,
        "slug": meta.get("slug") or slug,
        "stage": meta.get("stage") or "PoC",
        "tags": _normalize_tags(meta.get("tags") or []),
        "template": meta.get("template") or "empty",
        "description": (description or "")[:2000],
        "repo_path": str(project_dir),
        "memory_path": str(meta.get("memory_path") or memory_file),
        "has_logo": project_logo_file(project_dir) is not None,
        "brain_status": fm_status,
    }


def _brain_projects_scan_dirs(settings: dict) -> list[Path]:
    """`memory/projects` dirs that may contain `*.md` hub projects.

    Order: resolved active memory first, then ``BRAIN_PATH``/projects from the
    environment. External brains symlinked under ``instances/<name>/memory`` often
    fail inside Docker unless the target is bind-mounted; ``BRAIN_PATH`` is that
    host target and may be the only readable location for ``projects/*.md``.
    """
    seen_keys: set[str] = set()
    dirs: list[Path] = []

    def add(p: Path) -> None:
        if not p.is_dir():
            return
        try:
            key = str(p.resolve(strict=False))
        except OSError:
            key = str(p)
        if key in seen_keys:
            return
        seen_keys.add(key)
        dirs.append(p)

    add(active_brain_memory_root(settings) / "projects")
    bp = os.environ.get("BRAIN_PATH", "").strip()
    if bp:
        add(Path(bp).expanduser() / "projects")
    return dirs


def list_projects() -> dict:
    settings = get_hub_settings()
    items = []
    seen_slugs: set[str] = set()
    root = Path(settings["projects_root"]).expanduser()
    if root.exists():
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name == "archived":
                continue
            slug = entry.name
            has_metadata = (entry / HUB_METADATA_FILE).is_file()
            has_memory = _memory_file_for(slug).is_file()
            has_clawvis_marker = (entry / ".clawvis").is_dir()
            if not (has_metadata or has_memory or has_clawvis_marker):
                continue
            meta = _load_project_metadata(entry)
            items.append(meta)
            seen_slugs.add(meta.get("slug") or slug)
    for projects_dir in _brain_projects_scan_dirs(settings):
        for md in sorted(projects_dir.glob("*.md")):
            if md.name.startswith("_") or md.name.lower() == "index.md":
                continue
            slug = md.stem
            if slug in seen_slugs:
                continue
            try:
                items.append(_metadata_from_brain_only(slug, md))
                seen_slugs.add(slug)
            except OSError:
                pass
    return {"projects": items}


def get_project(project_slug: str) -> dict:
    data = list_projects()
    project = next((p for p in data["projects"] if p["slug"] == project_slug), None)
    if not project:
        raise KeyError("Project not found")
    memory_path = Path(project["memory_path"]).expanduser()
    memory_content = ""
    if memory_path.exists():
        memory_content = memory_path.read_text(encoding="utf-8")
    return {
        "project": project,
        "memory": memory_content,
        "major": _parse_markdown_major_info(memory_content),
    }


def _find_project_or_raise(project_slug: str) -> dict:
    projects = list_projects().get("projects", [])
    project = next((p for p in projects if p.get("slug") == project_slug), None)
    if not project:
        raise KeyError("Project not found")
    return project


def _project_repo_dir(project: dict) -> Path | None:
    repo_path = str(project.get("repo_path") or "").strip()
    if not repo_path:
        return None
    return Path(repo_path).expanduser()


def _path_is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (OSError, ValueError):
        return False


def _load_package_json(repo_dir: Path) -> dict:
    package_json = repo_dir / "package.json"
    if not package_json.is_file():
        return {}
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _node_build_plan(project: dict, repo_dir: Path, app_slug: str) -> dict | None:
    package_data = _load_package_json(repo_dir)
    scripts = package_data.get("scripts")
    if not isinstance(scripts, dict):
        return None
    build_script = scripts.get("build")
    if not isinstance(build_script, str) or not build_script.strip():
        return None
    template = str(project.get("template") or "").strip().lower()
    script_lower = build_script.lower()
    is_vite = template in {"frontend-vite", "vite"} or "vite" in script_lower
    if not is_vite:
        return None
    build_cmd = ["npm", "run", "build", "--", f"--base=/apps/{app_slug}/"]
    return {
        "install_cmd": ["npm", "install"],
        "build_cmd": build_cmd,
        "display": "npm install && " + " ".join(build_cmd),
    }


def get_project_launch_status(project_slug: str) -> dict:
    project = _find_project_or_raise(project_slug)
    settings = get_hub_settings()
    projects_root = Path(settings["projects_root"]).expanduser()
    repo_dir = _project_repo_dir(project)
    app_slug = repo_dir.name if repo_dir else str(project.get("slug") or "").strip()
    launch_url = f"/apps/{app_slug}/" if app_slug else ""
    repo_exists = bool(repo_dir and repo_dir.is_dir())
    repo_in_projects_root = bool(
        repo_exists and repo_dir and projects_root and _path_is_within_root(repo_dir, projects_root)
    )
    build_plan = (
        _node_build_plan(project, repo_dir, app_slug)
        if repo_exists and repo_dir
        else None
    )
    dist_index = repo_dir / "dist" / "index.html" if repo_exists and repo_dir else None
    root_index = repo_dir / "index.html" if repo_exists and repo_dir else None
    has_dist = bool(dist_index and dist_index.is_file())
    has_root_index = bool(root_index and root_index.is_file())
    deployed_entry = ""
    state = "missing"
    reason = "not_deployed"
    if not repo_dir:
        reason = "brain_only"
    elif not repo_exists:
        reason = "repo_missing"
    elif not repo_in_projects_root:
        reason = "outside_projects_root"
    elif has_dist:
        state = "launchable"
        reason = "dist_ready"
        deployed_entry = "dist/index.html"
    elif has_root_index and not build_plan:
        state = "launchable"
        reason = "index_ready"
        deployed_entry = "index.html"
    elif build_plan:
        state = "buildable"
        reason = "build_required"
    elif has_root_index:
        state = "launchable"
        reason = "index_ready"
        deployed_entry = "index.html"
    return {
        "ok": True,
        "project_slug": str(project.get("slug") or project_slug),
        "app_slug": app_slug,
        "launch_url": launch_url,
        "state": state,
        "reason": reason,
        "repo_path": str(repo_dir) if repo_dir else "",
        "repo_exists": repo_exists,
        "repo_in_projects_root": repo_in_projects_root,
        "projects_root": str(projects_root),
        "deployed_entry": deployed_entry,
        "build_command": build_plan["display"] if build_plan else "",
        "buildable": bool(build_plan),
    }


def build_project_and_launch(project_slug: str) -> dict:
    status = get_project_launch_status(project_slug)
    if status["state"] == "launchable":
        return {"ok": True, "built": False, "launch_status": status}
    if status["state"] != "buildable":
        raise ValueError("Project is not buildable from the current workspace.")
    repo_dir = Path(status["repo_path"]).expanduser()
    app_slug = str(status["app_slug"] or "").strip()
    project = _find_project_or_raise(project_slug)
    build_plan = _node_build_plan(project, repo_dir, app_slug)
    if not build_plan:
        raise ValueError("Missing supported build command for this project.")
    if not (repo_dir / "node_modules").exists():
        try:
            subprocess.run(
                build_plan["install_cmd"],
                cwd=repo_dir,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Dependency install timed out.") from exc
        except subprocess.CalledProcessError as exc:
            tail = (exc.stderr or exc.stdout or "").strip()[-4000:]
            raise RuntimeError(f"Dependency install failed.\n{tail}".strip()) from exc
    try:
        subprocess.run(
            build_plan["build_cmd"],
            cwd=repo_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Build timed out.") from exc
    except subprocess.CalledProcessError as exc:
        tail = (exc.stderr or exc.stdout or "").strip()[-4000:]
        raise RuntimeError(f"Build failed.\n{tail}".strip()) from exc
    refreshed = get_project_launch_status(project_slug)
    if refreshed["state"] != "launchable":
        raise RuntimeError("Build completed but the app is still not launchable.")
    return {"ok": True, "built": True, "launch_status": refreshed}


def get_project_logo_path(project_slug: str) -> Path:
    project = _find_project_or_raise(project_slug)
    rp = project.get("repo_path") or ""
    if not rp:
        raise KeyError("Logo not found")
    repo = Path(rp).expanduser()
    path = project_logo_file(repo)
    if not path:
        raise KeyError("Logo not found")
    return path


def save_project_logo(project_slug: str, data: bytes, upload_name: str) -> dict:
    if len(data) > _MAX_PROJECT_LOGO_BYTES:
        raise ValueError("Logo too large (max 2MB)")
    ext = Path(upload_name).suffix.lower()
    if ext not in _LOGO_ALLOWED_EXT:
        raise ValueError("Use PNG, JPEG, GIF, WebP, or SVG")
    project = _find_project_or_raise(project_slug)
    rp = project.get("repo_path") or ""
    if not rp:
        raise KeyError("Project not found")
    repo = Path(rp).expanduser()
    if not repo.is_dir():
        raise KeyError("Project not found")
    d = _project_clawvis_dir(repo)
    d.mkdir(parents=True, exist_ok=True)
    for old in d.glob("logo.*"):
        try:
            old.unlink()
        except OSError:
            pass
    dest = d / f"logo{ext}"
    dest.write_bytes(data)
    _log(
        "INFO",
        "project:logo",
        f"Saved logo for '{project_slug}'",
        {"slug": project_slug, "file": dest.name},
    )
    return {"ok": True, "filename": dest.name}


def delete_project_logo(project_slug: str) -> dict:
    project = _find_project_or_raise(project_slug)
    rp = project.get("repo_path") or ""
    if not rp:
        raise KeyError("Logo not found")
    repo = Path(rp).expanduser()
    d = _project_clawvis_dir(repo)
    removed = False
    if d.is_dir():
        for old in list(d.glob("logo.*")):
            try:
                old.unlink()
                removed = True
            except OSError:
                pass
    return {"ok": True, "removed": removed}


def _archive_project_tasks(project_slug: str) -> int:
    data = _load_raw()
    ts = now_iso()
    changed = 0
    for task in data.get("tasks", []):
        if (task.get("project") or "") == project_slug:
            task["status"] = "Archived"
            task["archived_at"] = ts
            task["updated"] = ts
            changed += 1
    if changed:
        save(data)
    return changed


def _delete_project_tasks(project_slug: str) -> int:
    data = _load_raw()
    tasks = data.get("tasks", [])
    removed_ids = {
        t.get("id") for t in tasks if (t.get("project") or "") == project_slug
    }
    kept = [t for t in tasks if (t.get("project") or "") != project_slug]
    if removed_ids:
        for task in kept:
            deps = task.get("dependencies") or []
            task["dependencies"] = [d for d in deps if d not in removed_ids]
    removed_count = len(tasks) - len(kept)
    if removed_count:
        data["tasks"] = kept
        save(data)
    return removed_count


def archive_project(project_slug: str) -> dict:
    project = _find_project_or_raise(project_slug)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    rp = project.get("repo_path") or ""
    repo_dir = Path(rp).expanduser() if rp else Path()
    target: Path | None = None
    if rp and repo_dir.exists():
        settings = get_hub_settings()
        projects_root = Path(settings["projects_root"]).expanduser()
        archived_root = projects_root / "archived"
        archived_root.mkdir(parents=True, exist_ok=True)
        target = archived_root / f"{project_slug}-{suffix}"
        shutil.move(str(repo_dir), str(target))

    memory_file = _memory_file_for(project_slug)
    archived_memory_dir = active_brain_memory_root() / "archive" / "projects"
    archived_memory_dir.mkdir(parents=True, exist_ok=True)
    archived_memory_file = archived_memory_dir / f"{project_slug}-{suffix}.md"
    if memory_file.exists():
        shutil.move(str(memory_file), str(archived_memory_file))

    archived_tasks = _archive_project_tasks(project_slug)
    _log(
        "INFO",
        "project:archive",
        f"Archived project '{project_slug}'",
        {"slug": project_slug, "tasks_archived": archived_tasks},
    )
    return {
        "ok": True,
        "slug": project_slug,
        "repo_archived_to": str(target) if target else "",
        "memory_archived_to": str(archived_memory_file)
        if archived_memory_file.exists()
        else "",
        "tasks_archived": archived_tasks,
    }


def _cleanup_nginx_route(slug: str) -> bool:
    """Remove projects.d/<slug>.conf and reload nginx if NGINX_PROJECTS_D is set."""
    projects_d = os.environ.get("NGINX_PROJECTS_D", "")
    nginx_pid = os.environ.get("NGINX_PID", "")
    if not projects_d:
        return False
    conf = Path(projects_d) / f"{slug}.conf"
    if conf.exists():
        conf.unlink()
    else:
        return False
    if nginx_pid and Path(nginx_pid).exists():
        try:
            pid = Path(nginx_pid).read_text().strip()
            subprocess.run(["kill", "-HUP", pid], check=False, timeout=5)
        except Exception:
            pass
    return True


def delete_project(project_slug: str) -> dict:
    project = _find_project_or_raise(project_slug)
    rp = project.get("repo_path") or ""
    if rp:
        repo_dir = Path(rp).expanduser()
        if repo_dir.exists():
            shutil.rmtree(repo_dir)
    memory_file = _memory_file_for(project_slug)
    if memory_file.exists():
        memory_file.unlink()
    deleted_tasks = _delete_project_tasks(project_slug)
    nginx_cleaned = _cleanup_nginx_route(project_slug)
    _log(
        "INFO",
        "project:delete",
        f"Deleted project '{project_slug}'",
        {
            "slug": project_slug,
            "tasks_deleted": deleted_tasks,
            "nginx_route_removed": nginx_cleaned,
        },
    )
    return {
        "ok": True,
        "slug": project_slug,
        "tasks_deleted": deleted_tasks,
        "nginx_route_removed": nginx_cleaned,
    }


def list_memory_project_files() -> dict:
    projects_dir = active_brain_memory_root() / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in projects_dir.glob("*.md"))
    return {"files": files}


def _quartz_public_dir() -> Path | None:
    """Return quartz/public/ if a real Quartz build is present, else None.

    A real build has at least one content HTML page (not 404.html or _*.html).
    """
    quartz_public = _CLAWVIS_ROOT / "quartz" / "public"
    if quartz_public.is_dir() and any(
        p
        for p in quartz_public.glob("*.html")
        if p.name != "404.html" and not p.name.startswith("_")
    ):
        return quartz_public
    return None


def list_memory_quartz_pages() -> dict:
    quartz_dir = _quartz_public_dir()
    if quartz_dir is not None:
        # Serve real Quartz output — list top-level HTML pages
        files = sorted(
            p.name
            for p in quartz_dir.glob("*.html")
            if p.name != "404.html" and not p.name.startswith("_")
        )
        return {"files": files, "source": "quartz"}
    # Fallback: Python-generated HTML alongside .md files
    projects_dir = active_brain_memory_root() / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in projects_dir.glob("*.html"))
    return {"files": files, "source": "fallback"}


def read_memory_quartz_page(filename: str) -> dict:
    safe = Path(filename).name
    if Path(safe).suffix.lower() != ".html":
        raise ValueError("Only .html files are allowed")
    quartz_dir = _quartz_public_dir()
    if quartz_dir is not None:
        path = quartz_dir / safe
    else:
        path = active_brain_memory_root() / "projects" / safe
    if not path.exists():
        raise KeyError("Quartz page not found")
    return {
        "filename": safe,
        "content": path.read_text(encoding="utf-8"),
        "source": "quartz" if quartz_dir else "fallback",
    }


def read_memory_project_file(filename: str) -> dict:
    safe = Path(filename).name
    path = active_brain_memory_root() / "projects" / safe
    if path.suffix.lower() != ".md":
        raise ValueError("Only .md files are allowed")
    if not path.exists():
        raise KeyError("Memory file not found")
    content = path.read_text(encoding="utf-8")
    return {
        "filename": safe,
        "content": content,
        "major": _parse_markdown_major_info(content),
    }


def save_memory_project_file(filename: str, content: str) -> dict:
    safe = Path(filename).name
    path = active_brain_memory_root() / "projects" / safe
    if path.suffix.lower() != ".md":
        raise ValueError("Only .md files are allowed")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _log("INFO", "memory:save", f"Saved memory file '{safe}'", {"file": safe})
    return {"ok": True, "filename": safe}
