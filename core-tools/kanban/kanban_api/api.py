"""Kanban REST routes."""
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from .core import (
    DependencyBlockedError,
    list_active_tasks,
    list_archive_tasks,
    get_stats,
    create_task,
    update_task,
    archive_task,
    restore_task,
    add_comment,
    delete_comment,
    add_dependencies,
    delete_dependency,
    split_task,
    get_meta,
    update_meta,
)
from .models import TaskCreate, TaskUpdate, CommentCreate, DependenciesUpdate, SplitTaskRequest, MetaUpdate
from .weekly_stats import get_weekly_stats_data

CODIR_FILE = Path.home() / ".openclaw/workspace/memory/kanban/CODIR.md"
router = APIRouter()


@router.get("/tasks")
def get_tasks(project: str | None = None, status: str | None = None):
    return list_active_tasks(project=project, status=status)


@router.get("/tasks/archive")
def get_archive():
    return {"tasks": list_archive_tasks()}


@router.get("/stats")
def stats():
    return get_stats()


@router.get("/stats/weekly")
async def get_weekly_stats():
    data = list_active_tasks()
    tasks = data["tasks"]
    lab_repos = os.environ.get("LAB_REPOS", "")
    return await get_weekly_stats_data(tasks, lab_repos)


@router.get("/meta")
def get_meta_endpoint():
    return get_meta()


@router.post("/tasks")
def create_task_endpoint(body: TaskCreate):
    return create_task(body)


@router.get("/codir")
def get_codir():
    if CODIR_FILE.exists():
        return PlainTextResponse(CODIR_FILE.read_text(encoding="utf-8"), media_type="text/markdown")
    raise HTTPException(404, "CODIR report not generated yet")


@router.put("/tasks/{task_id}")
def update_task_endpoint(task_id: str, body: TaskUpdate):
    try:
        return update_task(task_id, body)
    except DependencyBlockedError as e:
        raise HTTPException(409, str(e))
    except KeyError:
        raise HTTPException(404, "Task not found")


@router.put("/tasks/{task_id}/archive")
def archive_task_endpoint(task_id: str):
    try:
        return archive_task(task_id)
    except KeyError:
        raise HTTPException(404, "Task not found")


@router.put("/tasks/{task_id}/restore")
def restore_task_endpoint(task_id: str):
    try:
        return restore_task(task_id)
    except KeyError:
        raise HTTPException(404, "Task not found")


@router.post("/tasks/{task_id}/comments")
def add_comment_endpoint(task_id: str, body: CommentCreate):
    try:
        return add_comment(task_id, body)
    except KeyError:
        raise HTTPException(404, "Task not found")


@router.delete("/tasks/{task_id}/comments/{comment_id}")
def delete_comment_endpoint(task_id: str, comment_id: str):
    try:
        delete_comment(task_id, comment_id)
    except KeyError as e:
        msg = str(e)
        if "Task not found" in msg:
            raise HTTPException(404, "Task not found")
        raise HTTPException(404, "Comment not found")
    return {"ok": True}


@router.post("/tasks/{task_id}/dependencies")
def add_dependencies_endpoint(task_id: str, body: DependenciesUpdate):
    try:
        deps = add_dependencies(task_id, body)
    except KeyError:
        raise HTTPException(404, "Task not found")
    return {"dependencies": deps}


@router.delete("/tasks/{task_id}/dependencies/{dependency_id}")
def delete_dependency_endpoint(task_id: str, dependency_id: str):
    try:
        deps = delete_dependency(task_id, dependency_id)
    except KeyError as e:
        msg = str(e)
        if "Task not found" in msg:
            raise HTTPException(404, "Task not found")
        raise HTTPException(404, "Dependency not found")
    return {"dependencies": deps}


@router.post("/tasks/{task_id}/split")
def split_task_endpoint(task_id: str, body: SplitTaskRequest):
    try:
        return split_task(task_id, body)
    except KeyError:
        raise HTTPException(404, "Task not found")


@router.put("/meta")
def update_meta_endpoint(body: MetaUpdate):
    return update_meta(body)


@router.post("/sync")
def sync_endpoint():
    """Trigger full parser rebuild from .md sources (requires kanban_parser on path)."""
    import sys
    codir_parent = str(CODIR_FILE.parent)
    if codir_parent not in sys.path:
        sys.path.insert(0, codir_parent)
    try:
        from kanban_parser.parser import KanbanParser
        parser = KanbanParser()
        output = parser.run()
        return {
            "ok": True,
            "tasks": output.stats.total_tasks,
            "completion_rate": output.stats.completion_rate,
        }
    except Exception as e:
        raise HTTPException(500, f"Sync failed: {e}")
