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
