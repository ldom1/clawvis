"""Permanent task delete (JSON + dependency cleanup)."""

from __future__ import annotations

import json
from pathlib import Path

from kanban_api import core


def test_delete_task_removes_and_cleans_deps(monkeypatch, tmp_path: Path) -> None:
    tasks_file = tmp_path / "kanban" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        json.dumps(
            {
                "tasks": [
                    {
                        "id": "a",
                        "title": "A",
                        "status": "Backlog",
                        "dependencies": [],
                    },
                    {
                        "id": "b",
                        "title": "B",
                        "status": "Backlog",
                        "dependencies": ["a", "c"],
                    },
                    {
                        "id": "c",
                        "title": "C",
                        "status": "Backlog",
                        "dependencies": [],
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
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)

    out = core.delete_task("a")
    assert out["ok"] is True
    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert {t["id"] for t in data["tasks"]} == {"b", "c"}
    b = next(t for t in data["tasks"] if t["id"] == "b")
    assert b["dependencies"] == ["c"]


def test_delete_task_missing_raises(monkeypatch, tmp_path: Path) -> None:
    tasks_file = tmp_path / "kanban" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        json.dumps(
            {
                "tasks": [{"id": "x", "title": "X", "status": "Backlog"}],
                "generated": "",
                "meta": {},
                "stats": {},
                "kanban": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)
    try:
        core.delete_task("missing-id")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def _write_tasks(tmp_path: Path, tasks: list[dict]) -> Path:
    tasks_file = tmp_path / "kanban" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    tasks_file.write_text(
        json.dumps(
            {
                "tasks": tasks,
                "generated": "",
                "meta": {},
                "stats": {},
                "kanban": {},
            }
        ),
        encoding="utf-8",
    )
    return tasks_file


def test_delete_tasks_bulk_all_active(monkeypatch, tmp_path: Path) -> None:
    tasks_file = _write_tasks(
        tmp_path,
        [
            {
                "id": "a",
                "title": "A",
                "status": "Backlog",
                "project": "p1",
                "dependencies": [],
            },
            {
                "id": "b",
                "title": "B",
                "status": "In Progress",
                "project": "p2",
                "dependencies": ["a"],
            },
        ],
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)

    out = core.delete_tasks_bulk(project=None)
    assert out == {"ok": True, "deleted": 2}
    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert data["tasks"] == []


def test_delete_tasks_bulk_skips_archived(monkeypatch, tmp_path: Path) -> None:
    tasks_file = _write_tasks(
        tmp_path,
        [
            {
                "id": "keep",
                "title": "Old",
                "status": "Archived",
                "project": "p1",
                "dependencies": [],
            },
            {
                "id": "gone",
                "title": "Active",
                "status": "To Start",
                "project": "p1",
                "dependencies": [],
            },
        ],
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)

    out = core.delete_tasks_bulk(project=None)
    assert out == {"ok": True, "deleted": 1}
    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["id"] == "keep"


def test_delete_tasks_bulk_scoped_by_project(monkeypatch, tmp_path: Path) -> None:
    tasks_file = _write_tasks(
        tmp_path,
        [
            {
                "id": "x",
                "title": "X",
                "status": "Backlog",
                "project": "alpha",
                "dependencies": [],
            },
            {
                "id": "y",
                "title": "Y",
                "status": "Backlog",
                "project": "beta",
                "dependencies": ["x"],
            },
        ],
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)

    out = core.delete_tasks_bulk(project="alpha")
    assert out == {"ok": True, "deleted": 1}
    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    ids = {t["id"] for t in data["tasks"]}
    assert ids == {"y"}
    y = next(t for t in data["tasks"] if t["id"] == "y")
    assert y["dependencies"] == []


def test_delete_tasks_bulk_cleans_deps(monkeypatch, tmp_path: Path) -> None:
    tasks_file = _write_tasks(
        tmp_path,
        [
            {
                "id": "a",
                "title": "A",
                "status": "Backlog",
                "project": "p1",
                "dependencies": [],
            },
            {
                "id": "b",
                "title": "B",
                "status": "Backlog",
                "project": "p1",
                "dependencies": ["a", "c"],
            },
            {
                "id": "c",
                "title": "C",
                "status": "Backlog",
                "project": "p2",
                "dependencies": [],
            },
        ],
    )
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)

    core.delete_tasks_bulk(project="p1")
    data = json.loads(tasks_file.read_text(encoding="utf-8"))
    assert [t["id"] for t in data["tasks"]] == ["c"]


def test_delete_tasks_bulk_no_match_returns_zero(
    monkeypatch, tmp_path: Path
) -> None:
    tasks_file = _write_tasks(
        tmp_path,
        [
            {
                "id": "z",
                "title": "Z",
                "status": "Archived",
                "project": "p1",
                "dependencies": [],
            },
        ],
    )
    raw = tasks_file.read_text(encoding="utf-8")
    monkeypatch.setattr(core, "TASKS_FILE", tasks_file)
    monkeypatch.setattr(core, "_MD_SYNC", False)

    assert core.delete_tasks_bulk(project=None) == {"ok": True, "deleted": 0}
    assert tasks_file.read_text(encoding="utf-8") == raw

    assert core.delete_tasks_bulk(project="unknown") == {"ok": True, "deleted": 0}
    assert tasks_file.read_text(encoding="utf-8") == raw
