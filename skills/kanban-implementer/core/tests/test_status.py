"""Tests for task status updates."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kanban_implementer.status import update_task_status


SAMPLE = {
    "tasks": [
        {"id": "task-abc", "title": "Test", "status": "Backlog", "updated": "2026-01-01T00:00:00Z"}
    ]
}


@pytest.fixture
def tasks_json(tmp_path: Path) -> Path:
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps(SAMPLE))
    return p


def test_update_status_valid(tasks_json: Path) -> None:
    with patch("kanban_implementer.status.TASKS_JSON", tasks_json):
        ok = update_task_status("task-abc", "In Progress")
    assert ok is True
    data = json.loads(tasks_json.read_text())
    assert data["tasks"][0]["status"] == "In Progress"


def test_update_status_invalid_status(tasks_json: Path) -> None:
    with patch("kanban_implementer.status.TASKS_JSON", tasks_json):
        ok = update_task_status("task-abc", "InvalidStatus")
    assert ok is False


def test_update_status_unknown_task(tasks_json: Path) -> None:
    with patch("kanban_implementer.status.TASKS_JSON", tasks_json):
        ok = update_task_status("task-unknown", "Done")
    assert ok is False


def test_update_status_blocked(tasks_json: Path) -> None:
    with patch("kanban_implementer.status.TASKS_JSON", tasks_json):
        ok = update_task_status("task-abc", "Blocked")
    assert ok is True
    data = json.loads(tasks_json.read_text())
    assert data["tasks"][0]["status"] == "Blocked"
