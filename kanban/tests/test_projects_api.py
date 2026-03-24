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
