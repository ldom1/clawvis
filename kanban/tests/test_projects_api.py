"""API tests for project archive/delete endpoints."""

from __future__ import annotations

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
