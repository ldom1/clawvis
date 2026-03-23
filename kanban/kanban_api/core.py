"""Kanban business logic: tasks.json load/save, CRUD, dependencies."""
from __future__ import annotations

import hashlib
import os
import json
import re
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
    STATUSES,
    SplitTaskRequest,
    MetaUpdate,
    ProjectCreate,
    HubSettingsUpdate,
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
    from kanban_parser.markdown_writer import write_task_to_md, create_task_in_md
    _MD_SYNC = True
except ImportError:
    _MD_SYNC = False

_LOGGER_DIR = str(Path.home() / ".openclaw/skills/logger/core")
HUB_SETTINGS_FILE = _memory_root_path / "kanban" / "hub_settings.json"
HUB_METADATA_FILE = ".clawvis-project.json"


def _log(level: str, action: str, message: str, metadata: dict | None = None):
    cmd = ["uv", "run", "--directory", _LOGGER_DIR, "dombot-log", level, "project:kanban-api", "system", action, message]
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
        return {"tasks": [], "generated": now_iso(), "meta": {}, "stats": {}, "kanban": {}}
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


def _default_hub_settings() -> dict:
    return {
        "projects_root": str(Path.home() / "Lab/projects"),
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
    out = {
        "projects_root": str(current.get("projects_root") or defaults["projects_root"]),
    }
    HUB_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUB_SETTINGS_FILE.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def update_hub_settings(body: HubSettingsUpdate) -> dict:
    settings = {
        "projects_root": body.projects_root,
    }
    HUB_SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUB_SETTINGS_FILE.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
    return settings


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
    return _memory_root_path / "projects" / f"{slug}.md"


def _ensure_memory_structure() -> None:
    root = _memory_root_path
    for name in ("projects", "resources", "daily", "archive", "todo"):
        (root / name).mkdir(parents=True, exist_ok=True)


def _parse_markdown_major_info(content: str) -> dict:
    lines = content.splitlines()
    title = ""
    sections: dict[str, str] = {}
    current = None
    for raw in lines:
        line = raw.rstrip()
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections[current] = ""
            continue
        if current:
            sections[current] += f"{line}\n"
    def clean(name: str) -> str:
        return (sections.get(name, "") or "").strip()
    return {
        "title": title,
        "objective": clean("objective"),
        "context": clean("context"),
        "kanban": clean("kanban"),
        "links": clean("links"),
        "notes": clean("notes"),
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


def _maybe_init_git(repo_dir: Path, enabled: bool) -> None:
    if not enabled:
        return
    try:
        subprocess.run(["git", "init"], cwd=str(repo_dir), check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _seed_project_tasks(project_slug: str, project_name: str) -> None:
    data = _load_raw()
    existing = [t for t in data.get("tasks", []) if (t.get("project") or "") == project_slug]
    if existing:
        return
    ts = now_iso()
    templates = [
        ("Define scope", "Backlog", "High"),
        ("Setup technical baseline", "To Start", "Medium"),
        ("First user-facing milestone", "To Start", "High"),
    ]
    for title, status, priority in templates:
        tid = "task-" + hashlib.md5(f"{project_slug}:{title}:{ts}".encode()).hexdigest()[:8]
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
    repo_dir.mkdir(parents=True, exist_ok=True)
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
    }
    (repo_dir / HUB_METADATA_FILE).write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return metadata


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


def list_memory_project_files() -> dict:
    projects_dir = _memory_root_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(p.name for p in projects_dir.glob("*.md"))
    return {"files": files}


def read_memory_project_file(filename: str) -> dict:
    safe = Path(filename).name
    path = _memory_root_path / "projects" / safe
    if path.suffix.lower() != ".md":
        raise ValueError("Only .md files are allowed")
    if not path.exists():
        raise KeyError("Memory file not found")
    content = path.read_text(encoding="utf-8")
    return {"filename": safe, "content": content, "major": _parse_markdown_major_info(content)}


def save_memory_project_file(filename: str, content: str) -> dict:
    safe = Path(filename).name
    path = _memory_root_path / "projects" / safe
    if path.suffix.lower() != ".md":
        raise ValueError("Only .md files are allowed")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _log("INFO", "memory:save", f"Saved memory file '{safe}'", {"file": safe})
    return {"ok": True, "filename": safe}
