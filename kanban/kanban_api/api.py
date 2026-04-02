"""Kanban REST routes."""

import mimetypes
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse

from .core import (
    DependencyBlockedError,
    add_comment,
    add_dependencies,
    archive_project,
    archive_task,
    create_project,
    create_task,
    delete_task,
    delete_tasks_bulk,
    delete_comment,
    delete_dependency,
    delete_project,
    delete_project_logo,
    get_project_logo_path,
    get_meta,
    get_project,
    get_stats,
    list_active_tasks,
    list_archive_tasks,
    list_projects,
    rebuild_brain_static,
    restore_task,
    save_project_logo,
    update_project_memory_major,
    split_task,
    update_meta,
    update_task,
)
from .models import (
    CommentCreate,
    DependenciesUpdate,
    MetaUpdate,
    ProjectCreate,
    ProjectMemoryMajorUpdate,
    SplitTaskRequest,
    TaskCreate,
    TaskUpdate,
)
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


@router.get("/hub/projects")
def list_projects_endpoint():
    return list_projects()


@router.post("/hub/projects")
def create_project_endpoint(body: ProjectCreate):
    try:
        return create_project(body)
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.get("/hub/projects/{project_slug}")
def get_project_endpoint(project_slug: str):
    try:
        return get_project(project_slug)
    except KeyError:
        raise HTTPException(404, "Project not found")


@router.put("/hub/projects/{project_slug}/memory-major")
def update_project_memory_major_endpoint(
    project_slug: str, body: ProjectMemoryMajorUpdate
):
    try:
        payload = body.model_dump(exclude_unset=True)
        return update_project_memory_major(project_slug, payload)
    except KeyError:
        raise HTTPException(404, "Project not found")


@router.get("/hub/projects/{project_slug}/logo")
def get_project_logo_endpoint(project_slug: str):
    try:
        path = get_project_logo_path(project_slug)
    except KeyError:
        raise HTTPException(404, "Logo not found")
    media, _ = mimetypes.guess_type(str(path))
    return FileResponse(
        path, media_type=media or "application/octet-stream", filename=path.name
    )


@router.put("/hub/projects/{project_slug}/logo")
async def put_project_logo_endpoint(project_slug: str, file: UploadFile = File(...)):
    try:
        data = await file.read()
        return save_project_logo(project_slug, data, file.filename or "logo.png")
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError:
        raise HTTPException(404, "Project not found")


@router.delete("/hub/projects/{project_slug}/logo")
def delete_project_logo_endpoint(project_slug: str):
    try:
        return delete_project_logo(project_slug)
    except KeyError:
        raise HTTPException(404, "Project not found")


@router.post("/hub/brain/rebuild-static")
def rebuild_brain_static_endpoint():
    return rebuild_brain_static()


@router.post("/hub/projects/{project_slug}/archive")
def archive_project_endpoint(project_slug: str):
    try:
        return archive_project(project_slug)
    except KeyError:
        raise HTTPException(404, "Project not found")


@router.delete("/hub/projects/{project_slug}")
def delete_project_endpoint(project_slug: str):
    try:
        return delete_project(project_slug)
    except KeyError:
        raise HTTPException(404, "Project not found")


@router.get("/codir")
def get_codir():
    if CODIR_FILE.exists():
        return PlainTextResponse(
            CODIR_FILE.read_text(encoding="utf-8"), media_type="text/markdown"
        )
    raise HTTPException(404, "CODIR report not generated yet")


@router.put("/tasks/{task_id}")
def update_task_endpoint(task_id: str, body: TaskUpdate):
    try:
        return update_task(task_id, body)
    except DependencyBlockedError as e:
        raise HTTPException(409, str(e))
    except KeyError:
        raise HTTPException(404, "Task not found")


@router.delete("/tasks/bulk")
def delete_tasks_bulk_endpoint(project: str | None = None):
    return delete_tasks_bulk(project=project)


@router.delete("/tasks/{task_id}")
def delete_task_endpoint(task_id: str):
    try:
        return delete_task(task_id)
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
