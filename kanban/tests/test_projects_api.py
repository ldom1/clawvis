"""API tests for project archive/delete endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from kanban_api.server import app


def test_archive_project_endpoint_ok(monkeypatch):
    monkeypatch.setattr(
        "kanban_api.api.archive_project",
        lambda slug: {"ok": True, "slug": slug, "tasks_archived": 3},
    )
    client = TestClient(app)
    res = client.post("/hub/projects/demo/archive")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["slug"] == "demo"
    assert data["tasks_archived"] == 3


def test_archive_project_endpoint_not_found(monkeypatch):
    def _raise(_slug: str):
        raise KeyError("Project not found")

    monkeypatch.setattr("kanban_api.api.archive_project", _raise)
    client = TestClient(app)
    res = client.post("/hub/projects/missing/archive")
    assert res.status_code == 404
    assert res.json()["detail"] == "Project not found"


def test_delete_project_endpoint_ok(monkeypatch):
    monkeypatch.setattr(
        "kanban_api.api.delete_project",
        lambda slug: {"ok": True, "slug": slug, "tasks_deleted": 2},
    )
    client = TestClient(app)
    res = client.delete("/hub/projects/demo")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["slug"] == "demo"
    assert data["tasks_deleted"] == 2


def test_set_brain_status_endpoint_ok(monkeypatch):
    monkeypatch.setattr(
        "kanban_api.api.set_project_brain_status",
        lambda slug, st: {"ok": True, "slug": slug, "brain_status": st},
    )
    client = TestClient(app)
    res = client.post(
        "/hub/projects/demo/brain-status",
        json={"status": "active"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data["slug"] == "demo"
    assert data["brain_status"] == "active"


def test_set_brain_status_endpoint_not_found(monkeypatch):
    def _raise(_slug: str, _st: str):
        raise KeyError("Project not found")

    monkeypatch.setattr("kanban_api.api.set_project_brain_status", _raise)
    client = TestClient(app)
    res = client.post(
        "/hub/projects/missing/brain-status",
        json={"status": "active"},
    )
    assert res.status_code == 404


def test_delete_project_endpoint_not_found(monkeypatch):
    def _raise(_slug: str):
        raise KeyError("Project not found")

    monkeypatch.setattr("kanban_api.api.delete_project", _raise)
    client = TestClient(app)
    res = client.delete("/hub/projects/missing")
    assert res.status_code == 404
    assert res.json()["detail"] == "Project not found"


def test_put_project_logo_ok(monkeypatch):
    def _save(slug: str, data: bytes, name: str):
        assert slug == "x"
        assert data == b"abc"
        assert name == "pic.png"
        return {"ok": True, "filename": "logo.png"}

    monkeypatch.setattr("kanban_api.api.save_project_logo", _save)
    client = TestClient(app)
    res = client.put(
        "/hub/projects/x/logo",
        files={"file": ("pic.png", b"abc", "image/png")},
    )
    assert res.status_code == 200
    assert res.json()["ok"] is True


def test_get_project_logo_not_found(monkeypatch):
    def _raise(_slug: str):
        raise KeyError("Logo not found")

    monkeypatch.setattr("kanban_api.api.get_project_logo_path", _raise)
    client = TestClient(app)
    res = client.get("/hub/projects/x/logo")
    assert res.status_code == 404


def test_delete_task_endpoint_ok(monkeypatch):
    monkeypatch.setattr(
        "kanban_api.api.delete_task",
        lambda tid: {"ok": True, "id": tid},
    )
    client = TestClient(app)
    res = client.delete("/tasks/task-abc")
    assert res.status_code == 200
    assert res.json() == {"ok": True, "id": "task-abc"}


def test_delete_task_endpoint_not_found(monkeypatch):
    def _raise(_tid: str):
        raise KeyError("Task not found")

    monkeypatch.setattr("kanban_api.api.delete_task", _raise)
    client = TestClient(app)
    res = client.delete("/tasks/missing")
    assert res.status_code == 404


def test_delete_tasks_bulk_endpoint(monkeypatch):
    monkeypatch.setattr(
        "kanban_api.api.delete_tasks_bulk",
        lambda project=None: {"ok": True, "deleted": 5 if project else 12},
    )
    client = TestClient(app)
    assert client.delete("/tasks/bulk").json() == {"ok": True, "deleted": 12}
    assert client.delete("/tasks/bulk?project=demo").json() == {
        "ok": True,
        "deleted": 5,
    }


def test_delete_tasks_bulk_endpoint_uses_core(monkeypatch, tmp_path: Path) -> None:
    tasks_file = tmp_path / "kanban" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "u",
                        "title": "U",
                        "status": "To Start",
                        "project": "demo",
                    },
                    {
                        "id": "v",
                        "title": "V",
                        "status": "Backlog",
                        "project": "other",
                    },
                ],
                "generated": "",
                "meta": {},
                "stats": {},
                "kanban": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("kanban_api.core.TASKS_FILE", tasks_file)

    client = TestClient(app)
    res = client.delete("/tasks/bulk?project=demo")
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": 1}

    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["id"] == "v"
