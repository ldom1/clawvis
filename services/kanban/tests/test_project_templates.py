import json
from unittest.mock import patch

from kanban_api.core import archive_project, create_project, delete_project
from kanban_api.models import ProjectCreate


def test_create_project_uses_cookiecutter_when_available(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    memory_root = tmp_path / "memory"
    monkeypatch.setattr("kanban_api.core._memory_root_path", memory_root)
    monkeypatch.setattr("kanban_api.core.TASKS_FILE", memory_root / "kanban" / "tasks.json")
    monkeypatch.setattr(
        "kanban_api.core.get_hub_settings",
        lambda: {"projects_root": str(projects_root)},
    )
    monkeypatch.setattr(
        "kanban_api.core._seed_project_tasks", lambda *_args, **_kwargs: None
    )

    def fake_run(cmd, check, stdout, stderr):
        # Simulate cookiecutter generated output folder.
        out_dir = projects_root / "my-api"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "README.md").write_text("# generated", encoding="utf-8")
        return None

    with patch("kanban_api.core.subprocess.run", side_effect=fake_run) as run_mock:
        result = create_project(
            ProjectCreate(
                name="My API",
                description="Demo",
                template="python-fastapi",
                stage="PoC",
                tags=[],
                init_git=False,
            )
        )

    assert result["slug"] == "my-api"
    assert (projects_root / "my-api" / "README.md").exists()
    assert run_mock.called
    called_cmd = run_mock.call_args.args[0]
    assert called_cmd[:5] == ["uv", "run", "--with", "cookiecutter", "cookiecutter"]
    assert "project_name=My API" in called_cmd
    assert "project_slug=my-api" in called_cmd


def test_create_project_fallback_copy_template(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    memory_root = tmp_path / "memory"
    monkeypatch.setattr("kanban_api.core._memory_root_path", memory_root)
    monkeypatch.setattr("kanban_api.core.TASKS_FILE", memory_root / "kanban" / "tasks.json")
    monkeypatch.setattr(
        "kanban_api.core.get_hub_settings",
        lambda: {"projects_root": str(projects_root)},
    )
    monkeypatch.setattr(
        "kanban_api.core._seed_project_tasks", lambda *_args, **_kwargs: None
    )

    result = create_project(
        ProjectCreate(
            name="Node Demo",
            description="Demo",
            template="node-api",
            stage="PoC",
            tags=[],
            init_git=False,
        )
    )

    readme = (projects_root / result["slug"] / "README.md").read_text(encoding="utf-8")
    assert "# Node Demo" in readme


def test_archive_project_moves_repo_memory_and_archives_tasks(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    memory_root = tmp_path / "memory"
    monkeypatch.setattr("kanban_api.core._memory_root_path", memory_root)
    monkeypatch.setattr("kanban_api.core.TASKS_FILE", memory_root / "kanban" / "tasks.json")
    monkeypatch.setattr(
        "kanban_api.core.get_hub_settings",
        lambda: {"projects_root": str(projects_root)},
    )
    monkeypatch.setattr(
        "kanban_api.core._seed_project_tasks", lambda *_args, **_kwargs: None
    )

    created = create_project(
        ProjectCreate(
            name="Archive Me",
            description="Demo",
            template="node-api",
            stage="PoC",
            tags=[],
            init_git=False,
        )
    )
    slug = created["slug"]

    tasks_path = memory_root / "kanban" / "tasks.json"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "t-1",
                        "title": "x",
                        "project": slug,
                        "status": "To Start",
                        "dependencies": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    out = archive_project(slug)
    assert out["ok"] is True
    assert not (projects_root / slug).exists()
    assert (projects_root / "archived").exists()
    assert not (memory_root / "projects" / f"{slug}.md").exists()

    payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    archived = payload["tasks"][0]
    assert archived["status"] == "Archived"


def test_delete_project_removes_repo_memory_and_tasks(tmp_path, monkeypatch):
    projects_root = tmp_path / "projects"
    memory_root = tmp_path / "memory"
    monkeypatch.setattr("kanban_api.core._memory_root_path", memory_root)
    monkeypatch.setattr("kanban_api.core.TASKS_FILE", memory_root / "kanban" / "tasks.json")
    monkeypatch.setattr(
        "kanban_api.core.get_hub_settings",
        lambda: {"projects_root": str(projects_root)},
    )
    monkeypatch.setattr(
        "kanban_api.core._seed_project_tasks", lambda *_args, **_kwargs: None
    )

    created = create_project(
        ProjectCreate(
            name="Delete Me",
            description="Demo",
            template="node-api",
            stage="PoC",
            tags=[],
            init_git=False,
        )
    )
    slug = created["slug"]

    tasks_path = memory_root / "kanban" / "tasks.json"
    tasks_path.parent.mkdir(parents=True, exist_ok=True)
    tasks_path.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "p-1",
                        "title": "x",
                        "project": slug,
                        "status": "To Start",
                        "dependencies": [],
                    },
                    {
                        "id": "p-2",
                        "title": "y",
                        "project": "other",
                        "status": "To Start",
                        "dependencies": ["p-1"],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    out = delete_project(slug)
    assert out["ok"] is True
    assert not (projects_root / slug).exists()
    assert not (memory_root / "projects" / f"{slug}.md").exists()

    payload = json.loads(tasks_path.read_text(encoding="utf-8"))
    assert len(payload["tasks"]) == 1
    assert payload["tasks"][0]["project"] == "other"
    assert payload["tasks"][0]["dependencies"] == []
