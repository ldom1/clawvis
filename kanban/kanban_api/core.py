"""Kanban business logic: tasks.json load/save, CRUD, dependencies."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from hub_core.brain_memory import active_brain_memory_root as resolve_active_brain_memory_root

from .models import (
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

_CLAWVIS_ROOT = Path(__file__).resolve().parents[2]
_memory_root_env = os.environ.get("MEMORY_ROOT")
if _memory_root_env:
    _memory_root_path = Path(_memory_root_env).expanduser()
    if not _memory_root_path.is_absolute():
        _memory_root_path = _CLAWVIS_ROOT / _memory_root_path
else:
    _memory_root_path = Path.home() / ".openclaw/workspace/memory"

TASKS_FILE = _memory_root_path / "kanban" / "tasks.json"
_kanban_dir = str(TASKS_FILE.parent)
if _kanban_dir not in sys.path:
    sys.path.insert(0, _kanban_dir)
try:
    from kanban_parser.markdown_writer import create_task_in_md, write_task_to_md

    _MD_SYNC = True
except ImportError:
    _MD_SYNC = False

_LOGGER_DIR = str(Path.home() / ".openclaw/skills/logger/core")
HUB_SETTINGS_FILE = _memory_root_path / "kanban" / "hub_settings.json"
HUB_METADATA_FILE = ".clawvis-project.json"
PROJECT_TEMPLATES_DIR = _CLAWVIS_ROOT / "project-templates"


def _log(level: str, action: str, message: str, metadata: dict | None = None):
    cmd = [
        "uv",
        "run",
        "--directory",
        _LOGGER_DIR,
        "dombot-log",
        level,
        "project:kanban-api",
        "system",
        action,
        message,
    ]
    if metadata:
        cmd.append(json.dumps(metadata))
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


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
    if _MD_SYNC:
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
    if _MD_SYNC and task.get("source_file"):
        try:
            write_task_to_md(
                task["source_file"],
                task["title"],
                {"status": "Deleted", "deleted": True},
            )
        except Exception:
            try:
                write_task_to_md(
                    task["source_file"], task["title"], {"status": "Archived"}
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
        if _MD_SYNC and proj:
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
    if HUB_SETTINGS_FILE.exists():
        try:
            current = json.loads(HUB_SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            current = {}
    else:
        current = {}
    linked = current.get("linked_instances") or []
    if not isinstance(linked, list):
        linked = []
    linked = [str(p) for p in linked if str(p).strip()]
    out = {
        "projects_root": str(current.get("projects_root") or defaults["projects_root"]),
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
                "has_compose_override": (entry / "docker-compose.override.yml").exists(),
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
            "has_compose_override": (Path(path) / "docker-compose.override.yml").exists(),
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
    if idx < len(lines) and lines[idx].startswith("# ") and not lines[idx].startswith(
        "##"
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
    return {
        "name": meta.get("name") or project_dir.name,
        "slug": meta.get("slug") or slug,
        "stage": meta.get("stage") or "PoC",
        "tags": _normalize_tags(meta.get("tags") or []),
        "template": meta.get("template") or "empty",
        "description": meta.get("description") or "",
        "repo_path": str(project_dir),
        "memory_path": str(meta.get("memory_path") or memory_file),
        "has_logo": project_logo_file(project_dir) is not None,
    }


def list_projects() -> dict:
    settings = get_hub_settings()
    items = []
    root = Path(settings["projects_root"]).expanduser()
    if root.exists():
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                items.append(_load_project_metadata(entry))
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


def get_project_logo_path(project_slug: str) -> Path:
    project = _find_project_or_raise(project_slug)
    repo = Path(project["repo_path"]).expanduser()
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
    repo = Path(project["repo_path"]).expanduser()
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
    repo = Path(project["repo_path"]).expanduser()
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
    repo_dir = Path(project["repo_path"]).expanduser()
    if not repo_dir.exists():
        raise KeyError("Project not found")
    settings = get_hub_settings()
    projects_root = Path(settings["projects_root"]).expanduser()
    archived_root = projects_root / "archived"
    archived_root.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
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
        "repo_archived_to": str(target),
        "memory_archived_to": str(archived_memory_file)
        if archived_memory_file.exists()
        else "",
        "tasks_archived": archived_tasks,
    }


def delete_project(project_slug: str) -> dict:
    project = _find_project_or_raise(project_slug)
    repo_dir = Path(project["repo_path"]).expanduser()
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    memory_file = _memory_file_for(project_slug)
    if memory_file.exists():
        memory_file.unlink()
    deleted_tasks = _delete_project_tasks(project_slug)
    _log(
        "INFO",
        "project:delete",
        f"Deleted project '{project_slug}'",
        {"slug": project_slug, "tasks_deleted": deleted_tasks},
    )
    return {"ok": True, "slug": project_slug, "tasks_deleted": deleted_tasks}


def list_memory_project_files() -> dict:
    projects_dir = active_brain_memory_root() / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in projects_dir.glob("*.md"))
    return {"files": files}


def _quartz_public_dir() -> Path | None:
    """Return quartz/public/ if a real Quartz build is present, else None."""
    quartz_public = _CLAWVIS_ROOT / "quartz" / "public"
    if quartz_public.is_dir() and any(quartz_public.glob("*.html")):
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
    return {"filename": safe, "content": path.read_text(encoding="utf-8"), "source": "quartz" if quartz_dir else "fallback"}


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
