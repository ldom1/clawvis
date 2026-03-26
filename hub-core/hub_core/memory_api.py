"""Hub Memory API: Brain (memory + Quartz) endpoints.

This is intentionally separate from the Kanban API surface.
"""

import mimetypes
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse

from kanban_api.core import (  # reuse implementation; separate service boundary
    _CLAWVIS_ROOT,
    active_brain_memory_root,
    get_hub_settings,
    list_instances,
    list_memory_project_files,
    list_memory_quartz_pages,
    read_memory_project_file,
    rebuild_brain_static,
    save_memory_project_file,
    update_hub_settings,
    link_instance,
    unlink_instance,
    read_memory_quartz_page,
)
from kanban_api.models import HubSettingsUpdate, InstanceLinkRequest, MemoryFileSave


app = FastAPI(title="Hub Memory API")


@app.get("/settings")
def settings_endpoint():
    data = dict(get_hub_settings())
    data["active_brain_memory"] = str(active_brain_memory_root(data))
    return data


@app.put("/settings")
def update_settings_endpoint(body: HubSettingsUpdate):
    # Only supports instances_external_root today (same as kanban_api.core)
    return update_hub_settings(body)


@app.get("/instances")
def instances_endpoint():
    return list_instances()


@app.post("/instances/link")
def link_instance_endpoint(body: InstanceLinkRequest):
    try:
        return link_instance(body.path)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/instances/unlink")
def unlink_instance_endpoint(body: InstanceLinkRequest):
    try:
        return unlink_instance(body.path)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/brain/rebuild-static")
def rebuild_static_endpoint():
    return rebuild_brain_static()


@app.get("/projects")
def list_projects_endpoint():
    return list_memory_project_files()


@app.get("/projects/{filename}")
def read_project_endpoint(filename: str):
    try:
        return read_memory_project_file(filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError:
        raise HTTPException(404, "Memory file not found")


@app.put("/projects")
def save_project_endpoint(body: MemoryFileSave):
    try:
        return save_memory_project_file(body.filename, body.content)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/quartz")
def list_quartz_endpoint():
    return list_memory_quartz_pages()


@app.get("/quartz/{filename}")
def read_quartz_page_endpoint(filename: str):
    try:
        return read_memory_quartz_page(filename)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except KeyError:
        raise HTTPException(404, "Quartz page not found")


@app.get("/quartz-static/{path:path}")
def quartz_static_endpoint(path: str):
    # Serve Quartz build output as real files (CSS/JS/assets) so the Hub iframe can render properly.
    if not path or path.endswith("/"):
        path = "index.html"
    if not Path(path).suffix:
        path = f"{path}.html"
    safe = Path(path)
    if safe.is_absolute() or ".." in safe.parts:
        raise HTTPException(400, "Invalid path")

    # Same root as kanban_api (works in Docker + editable installs; not Path(__file__).parents).
    quartz_public = _CLAWVIS_ROOT / "quartz" / "public"
    target = (quartz_public / safe).resolve()
    qroot = quartz_public.resolve()
    if not str(target).startswith(str(qroot)):
        raise HTTPException(400, "Invalid path")
    if not target.exists() or not target.is_file():
        # Quartz often has README.html as home but no root index.html; clients still request index.html.
        if safe.parent == Path(".") and safe.name == "index.html":
            for alt in ("README.html", "home.html", "clawvis.html"):
                cand = (quartz_public / alt).resolve()
                if cand.is_file() and str(cand).startswith(str(qroot)):
                    target = cand
                    safe = Path(alt)
                    break
    if not target.exists() or not target.is_file():
        raise HTTPException(404, "Not found")

    media, _ = mimetypes.guess_type(str(target))
    if target.suffix.lower() == ".html":
        html = target.read_text(encoding="utf-8", errors="ignore")
        prefix = "/api/hub/memory/quartz-static/"
        # Quartz uses relative assets (e.g. ../index.css under projects/). A single base
        # of prefix/ makes "../" escape to /api/hub/memory/ — broken CSS. Base must be
        # the HTML file's directory under quartz-static/.
        parent = safe.parent.as_posix()
        base_dir = prefix if parent == "." else f"{prefix}{parent}/"
        base_tag = f'<base href="{base_dir}" />'
        html = re.sub(r"<base\s[^>]*\/?>", "", html, flags=re.IGNORECASE)
        if re.search(r"<head[^>]*>", html, flags=re.IGNORECASE):
            html = re.sub(
                r"(<head[^>]*>)",
                rf"\1{base_tag}",
                html,
                count=1,
                flags=re.IGNORECASE,
            )
        html = html.replace(' href="/', f' href="{prefix}')
        html = html.replace(" href='/", f" href='{prefix}")
        html = html.replace(' src="/', f' src="{prefix}')
        html = html.replace(" src='/", f" src='{prefix}")
        return HTMLResponse(content=html, media_type="text/html")

    return FileResponse(target, media_type=media or "application/octet-stream")

