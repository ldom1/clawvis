"""Memory API: FastAPI surface (delegates to kanban_api in strategy B)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hub_core import memory_api


@pytest.fixture
def client() -> TestClient:
    return TestClient(memory_api.app)


def test_app_metadata(client: TestClient):
    assert memory_api.app.title == "Hub Memory API"
    assert client.get("/openapi.json").status_code == 200


def test_settings_get_monkeypatched(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    def fake_settings():
        return {
            "projects_root": "/tmp/projects",
            "instances_external_root": "/tmp/inst",
            "linked_instances": [],
        }

    monkeypatch.setattr(memory_api, "get_hub_settings", fake_settings)
    monkeypatch.setattr(
        memory_api,
        "active_brain_memory_root",
        lambda _data: Path("/tmp/brain-mem"),
    )
    r = client.get("/settings")
    assert r.status_code == 200
    body = r.json()
    assert body["projects_root"] == "/tmp/projects"
    assert body["active_brain_memory"] == "/tmp/brain-mem"


def test_instances_get_monkeypatched(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(memory_api, "list_instances", lambda: [{"path": "/a"}])
    r = client.get("/instances")
    assert r.status_code == 200
    assert r.json() == [{"path": "/a"}]


def test_projects_list_monkeypatched(client: TestClient, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(memory_api, "list_memory_project_files", lambda: ["x.md"])
    r = client.get("/projects")
    assert r.status_code == 200
    assert r.json() == ["x.md"]


def test_quartz_static_serves_memory_projects_when_no_quartz_build(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Brain iframe uses /quartz-static/; without quartz/public, files must come from memory/projects/."""
    mem = tmp_path / "m"
    proj = mem / "projects"
    proj.mkdir(parents=True)
    (proj / "index.html").write_text(
        "<!DOCTYPE html><html><head><title>t</title></head><body>ok</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setattr(memory_api, "_CLAWVIS_ROOT", tmp_path)
    monkeypatch.setattr(memory_api, "active_brain_memory_root", lambda _data=None: mem)
    monkeypatch.setattr(
        memory_api,
        "get_hub_settings",
        lambda: {"linked_instances": [], "projects_root": "", "instances_external_root": ""},
    )
    r = client.get("/quartz-static/index.html")
    assert r.status_code == 200
    assert "ok" in r.text
