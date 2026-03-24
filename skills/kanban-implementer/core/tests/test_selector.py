"""Tests for task selector."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from kanban_implementer.selector import Task, load_tasks, select_task


SAMPLE_TASKS = {
    "tasks": [
        {
            "id": "task-aaa",
            "title": "High priority task",
            "project": "hub",
            "status": "To Start",
            "priority": "High",
            "effort_hours": 1.0,
            "assignee": "DomBot",
            "source_file": "",
            "description": "",
            "tags": [],
            "notes": "",
        },
        {
            "id": "task-bbb",
            "title": "Medium priority task",
            "project": "other",
            "status": "Backlog",
            "priority": "Medium",
            "effort_hours": 0.5,
            "assignee": "DomBot",
            "source_file": "",
            "description": "",
            "tags": [],
            "notes": "",
        },
        {
            "id": "task-ccc",
            "title": "Human-assigned task",
            "project": "hub",
            "status": "To Start",
            "priority": "High",
            "effort_hours": 0.5,
            "assignee": "Ldom",
            "source_file": "",
            "description": "",
            "tags": [],
            "notes": "",
        },
        {
            "id": "task-ddd",
            "title": "Done task",
            "project": "hub",
            "status": "Done",
            "priority": "High",
            "effort_hours": 0.5,
            "assignee": "DomBot",
            "source_file": "",
            "description": "",
            "tags": [],
            "notes": "",
        },
        {
            "id": "task-eee",
            "title": "Too big task",
            "project": "hub",
            "status": "Backlog",
            "priority": "High",
            "effort_hours": 10.0,
            "assignee": "DomBot",
            "source_file": "",
            "description": "",
            "tags": [],
            "notes": "",
        },
    ]
}


@pytest.fixture
def tasks_json(tmp_path: Path) -> Path:
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps(SAMPLE_TASKS))
    return p


def test_load_tasks_returns_all(tasks_json: Path) -> None:
    with patch("kanban_implementer.selector.TASKS_JSON", tasks_json):
        tasks = load_tasks()
    assert len(tasks) == 5


def test_eligible_filters_correctly(tasks_json: Path) -> None:
    with patch("kanban_implementer.selector.TASKS_JSON", tasks_json):
        tasks = load_tasks()
    eligible = [t for t in tasks if t.is_eligible]
    ids = {t.id for t in eligible}
    assert "task-aaa" in ids  # High, DomBot, To Start, 1h <= 2h
    assert "task-bbb" in ids  # Medium, DomBot, Backlog, 0.5h
    assert "task-ccc" not in ids  # Ldom (not DomBot)
    assert "task-ddd" not in ids  # Done
    assert "task-eee" not in ids  # 10h > 2h


def test_select_task_picks_high_priority(tasks_json: Path) -> None:
    with (
        patch("kanban_implementer.selector.TASKS_JSON", tasks_json),
        patch("kanban_implementer.selector.PRIORITY_PROJECT", None),
        patch("kanban_implementer.selector.MAX_EFFORT", 2.0),
    ):
        task = select_task()
    assert task is not None
    assert task.id == "task-aaa"  # High priority


def test_select_task_respects_priority_project(tasks_json: Path) -> None:
    with (
        patch("kanban_implementer.selector.TASKS_JSON", tasks_json),
        patch("kanban_implementer.selector.PRIORITY_PROJECT", None),
        patch("kanban_implementer.selector.MAX_EFFORT", 2.0),
    ):
        task = select_task(priority_project="other")
    assert task is not None
    assert task.id == "task-bbb"  # "other" project prioritized


def test_select_task_no_eligible(tmp_path: Path) -> None:
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps({"tasks": []}))
    with patch("kanban_implementer.selector.TASKS_JSON", p):
        task = select_task()
    assert task is None


def test_task_with_low_confidence_not_eligible():
    """Task with confidence below threshold is not eligible."""
    from kanban_implementer.selector import Task
    t = Task(
        id="t1", title="Test", project="hub", status="To Start",
        priority="Medium", effort_hours=1.0, assignee="DomBot",
        source_file="", confidence=0.2,
    )
    assert not t.is_eligible


def test_task_with_null_confidence_uses_default():
    """Null confidence treated as 0.5 → eligible if threshold ≤ 0.5."""
    from kanban_implementer.selector import Task
    t = Task(
        id="t2", title="Test", project="hub", status="To Start",
        priority="Medium", effort_hours=1.0, assignee="DomBot",
        source_file="", confidence=None,
    )
    assert t.is_eligible  # 0.5 >= 0.4 (default threshold)


def test_human_assignee_confidence_effective_is_one():
    """Human assignee → confidence_effective = 1.0 (never blocked by confidence filter)."""
    from kanban_implementer.selector import Task
    t = Task(
        id="t3", title="Test", project="hub", status="To Start",
        priority="Medium", effort_hours=1.0, assignee="lgiron",
        source_file="", confidence=0.0,
    )
    assert t.confidence_effective == 1.0


def test_is_ambiguous_vague_word():
    t = Task(
        id="a1", title="Cleanup old routes", project="hub", status="To Start",
        priority="High", effort_hours=1.0, assignee="DomBot", source_file="",
    )
    assert t.is_ambiguous


def test_is_ambiguous_french():
    t = Task(
        id="a2", title="Refonte module X", project="hub", status="To Start",
        priority="High", effort_hours=1.0, assignee="DomBot", source_file="",
    )
    assert t.is_ambiguous


def test_is_ambiguous_clear_title():
    t = Task(
        id="a3", title="Add retry to POST /tasks", project="hub", status="To Start",
        priority="High", effort_hours=1.0, assignee="DomBot", source_file="",
        description="Implement exponential backoff in kanban_api.",
    )
    assert not t.is_ambiguous
