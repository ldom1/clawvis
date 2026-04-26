"""Regression tests for Kanban -> memory markdown status sync."""

from __future__ import annotations

import json
from pathlib import Path

from kanban_api import core
from kanban_api.models import SplitTaskRequest, TaskUpdate


def _seed_tasks_file(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "tasks": [
            {
                "id": "task-1",
                "title": "Sync task",
                "project": "demo",
                "status": "To Start",
                "priority": "Medium",
                "source_file": "/tmp/demo-project.md",
                "created": "2026-03-24T00:00:00Z",
                "updated": "2026-03-24T00:00:00Z",
            }
        ],
        "generated": "2026-03-24T00:00:00Z",
        "meta": {},
        "stats": {},
        "kanban": {},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_update_task_syncs_status_to_markdown(monkeypatch, tmp_path):
    tasks_file = tmp_path / "kanban" / "tasks.json"
    _seed_tasks_file(tasks_file)
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", True)

    calls: list[tuple[str, str, dict]] = []

    def _writer(source_file: str, title: str, updates: dict):
        calls.append((source_file, title, updates))

    monkeypatch.setattr(core, "write_task_to_md", _writer, raising=False)

    updated = core.update_task("task-1", TaskUpdate(status="In Progress"))

    assert updated["status"] == "In Progress"
    assert len(calls) == 1
    assert calls[0][0] == "/tmp/demo-project.md"
    assert calls[0][1] == "Sync task"
    assert calls[0][2] == {"status": "In Progress"}


def test_update_task_without_source_file_does_not_sync_markdown(monkeypatch, tmp_path):
    tasks_file = tmp_path / "kanban" / "tasks.json"
    _seed_tasks_file(tasks_file)
    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    data["tasks"][0]["source_file"] = ""
    tasks_file.write_text(json.dumps(data), encoding="utf-8")

    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", True)

    called = {"value": False}

    def _writer(_source_file: str, _title: str, _updates: dict):
        called["value"] = True

    monkeypatch.setattr(core, "write_task_to_md", _writer, raising=False)

    updated = core.update_task("task-1", TaskUpdate(status="In Progress"))

    assert updated["status"] == "In Progress"
    assert called["value"] is False


def test_split_task_creates_markdown_entry_per_child(monkeypatch, tmp_path):
    tasks_file = tmp_path / "kanban" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "parent-1",
                        "title": "Parent",
                        "project": "myproj",
                        "status": "In Progress",
                        "priority": "High",
                        "source_file": "",
                    }
                ],
                "generated": "",
                "meta": {},
                "stats": {},
                "kanban": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", True)
    created: list[tuple[str, str]] = []

    def _create(project: str, td: dict):
        created.append((project, td["title"]))
        return str(tmp_path / f"t-{len(created)}.md")

    monkeypatch.setattr(core, "create_task_in_md", _create, raising=False)

    out = core.split_task("parent-1", SplitTaskRequest(count=2, base_title="Slice"))

    assert len(out["children"]) == 2
    assert created == [("myproj", "Slice #1"), ("myproj", "Slice #2")]
    for c in out["children"]:
        assert c.get("source_file"), "child should link to memory md"


def test_split_task_skips_md_when_no_project(monkeypatch, tmp_path):
    tasks_file = tmp_path / "kanban" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "p2",
                        "title": "Orphan",
                        "project": "",
                        "status": "Backlog",
                        "priority": "Medium",
                    }
                ],
                "generated": "",
                "meta": {},
                "stats": {},
                "kanban": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", True)
    monkeypatch.setattr(
        core,
        "create_task_in_md",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no md")),
        raising=False,
    )
    out = core.split_task("p2", SplitTaskRequest(count=1, base_title="Only"))
    assert len(out["children"]) == 1
    assert not out["children"][0].get("source_file")


def test_create_task_in_md_creates_roadmap_section(monkeypatch, tmp_path):
    projects_dir = tmp_path / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    md = projects_dir / "demo.md"
    md.write_text("# Demo\n\n## Notes\nHello\n", encoding="utf-8")
    monkeypatch.setattr(core, "_memory_file_for", lambda _slug: md)

    source = core.create_task_in_md(
        "demo",
        {
            "title": "First task",
            "priority": "High",
            "start_date": "2026-04-01",
            "end_date": None,
            "effort_hours": 1.5,
            "status": "To Start",
        },
    )

    assert source == str(md)
    content = md.read_text(encoding="utf-8")
    assert "## Roadmap" in content
    assert "| Task | Priority | Start | End | Effort | Status | Deps |" in content
    assert "| First task | High | 2026-04-01 | - | 1.5 | to start | - |" in content


def test_write_task_to_md_updates_existing_roadmap_row(tmp_path):
    md = tmp_path / "demo.md"
    md.write_text(
        "# Demo\n\n## Roadmap\n\n"
        "| Task | Priority | Start | End | Effort | Status | Deps |\n"
        "|------|----------|-------|-----|--------|--------|------|\n"
        "| First task | P1 | 2026-04-01 | - | 1.0 | backlog | - |\n",
        encoding="utf-8",
    )

    core.write_task_to_md(
        str(md),
        "First task",
        {
            "status": "In Progress",
            "priority": "Critical",
            "end_date": "2026-04-09",
            "effort_hours": 2.0,
        },
    )

    content = md.read_text(encoding="utf-8")
    assert "| First task | Critical | 2026-04-01 | 2026-04-09 | 2.0 | in progress | - |" in content
