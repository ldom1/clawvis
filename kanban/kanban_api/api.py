"""Kanban REST routes."""

import mimetypes
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from .core import (
    DependencyBlockedError,
    active_brain_memory_root,
    add_comment,
    add_dependencies,
    archive_project,
    archive_task,
    create_project,
    create_task,
    delete_task,
    delete_comment,
    delete_dependency,
    delete_project,
    delete_project_logo,
    get_hub_settings,
    get_project_logo_path,
    link_instance,
    list_instances,
    get_meta,
    get_project,
    get_stats,
    list_active_tasks,
    list_archive_tasks,
    list_memory_project_files,
    list_memory_quartz_pages,
    list_projects,
    read_memory_project_file,
    read_memory_quartz_page,
    rebuild_brain_static,
    restore_task,
    save_memory_project_file,
    save_project_logo,
    update_project_memory_major,
    split_task,
    unlink_instance,
    update_hub_settings,
    update_meta,
    update_task,
)
from .models import (
    CommentCreate,
    DependenciesUpdate,
    HubSettingsUpdate,
    InstanceLinkRequest,
    MemoryFileSave,
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


@router.get("/hub/settings")
def get_hub_settings_endpoint():
    data = dict(get_hub_settings())
    data["active_brain_memory"] = str(active_brain_memory_root(data))
    return data


@router.put("/hub/settings")
def update_hub_settings_endpoint(body: HubSettingsUpdate):
    return update_hub_settings(body)


@router.get("/hub/instances")
def list_instances_endpoint():
    return list_instances()


@router.post("/hub/instances/link")
def link_instance_endpoint(body: InstanceLinkRequest):
    try:
        return link_instance(body.path)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/hub/instances/unlink")
def unlink_instance_endpoint(body: InstanceLinkRequest):
    try:
        return unlink_instance(body.path)
    except ValueError as e:
        raise HTTPException(400, str(e))


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


@router.get("/memory/projects")
def list_memory_projects_endpoint():
    return list_memory_project_files()


@router.get("/memory/quartz")
def list_memory_quartz_endpoint():
    return list_memory_quartz_pages()


@router.get("/memory/quartz/{filename}")
def read_memory_quartz_endpoint(filename: str):
    try:
        return read_memory_quartz_page(filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError:
        raise HTTPException(404, "Quartz page not found")


@router.get("/memory/quartz-static/{path:path}")
def quartz_static_endpoint(path: str):
    # Serve Quartz build output as real files (CSS/JS/assets) so the Hub iframe can render properly.
    if not path or path.endswith("/"):
        path = "index.html"
    if not Path(path).suffix:
        path = f"{path}.html"
    safe = Path(path)
    if safe.is_absolute() or ".." in safe.parts:
        raise HTTPException(400, "Invalid path")
    root = Path(__file__).resolve().parents[2]  # .../kanban/kanban_api/ -> repo root
    quartz_public = root / "quartz" / "public"
    target = (quartz_public / safe).resolve()
    if not str(target).startswith(str(quartz_public.resolve())):
        raise HTTPException(400, "Invalid path")
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "Not found")
    media, _ = mimetypes.guess_type(str(target))
    # For HTML, inject a base href so internal links (Home, Explorer) work under our mount path.
    if target.suffix.lower() == ".html":
        html = target.read_text(encoding="utf-8", errors="ignore")
        prefix = "/api/hub/kanban/memory/quartz-static/"
        base = f'<base href="{prefix}" />'
        if "<base" not in html.lower():
            html = html.replace("<head>", f"<head>{base}", 1)
        # Quartz emits some absolute links (href="/...", src="/...") which bypass <base>.
        # Rewrite them to stay under our mount prefix so clicks don't hit unknown API routes.
        html = html.replace(' href="/', f' href="{prefix}')
        html = html.replace(" href='/", f" href='{prefix}")
        html = html.replace(' src="/', f' src="{prefix}')
        html = html.replace(" src='/", f" src='{prefix}")
        return HTMLResponse(content=html, media_type="text/html")
    # Don't set "filename": would force download instead of inline render in iframe.
    return FileResponse(target, media_type=media or "application/octet-stream")


@router.get("/memory/projects/{filename}")
def read_memory_project_endpoint(filename: str):
    try:
        return read_memory_project_file(filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError:
        raise HTTPException(404, "Memory file not found")


@router.put("/memory/projects")
def save_memory_project_endpoint(body: MemoryFileSave):
    try:
        return save_memory_project_file(body.filename, body.content)
    except ValueError as e:
        raise HTTPException(400, str(e))


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
