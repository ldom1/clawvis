"""Tests for PilotView weekly stats endpoint."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from kanban_api.weekly_stats import compute_weekly_stats, parse_git_log


def _iso(days_ago: int = 0) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat() + "Z"


SAMPLE_TASKS = [
    {
        "id": "t1",
        "title": "A",
        "project": "hub",
        "status": "Done",
        "assignee": "DomBot",
        "effort_hours": 1.0,
        "created": _iso(3),
        "updated": _iso(3),
    },
    {
        "id": "t2",
        "title": "B",
        "project": "hub",
        "status": "In Progress",
        "assignee": "DomBot",
        "effort_hours": 2.0,
        "created": _iso(2),
        "updated": _iso(2),
    },
    {
        "id": "t3",
        "title": "C",
        "project": "ruflo",
        "status": "To Start",
        "assignee": "ldom1",
        "effort_hours": 0.5,
        "created": _iso(10),
        "updated": _iso(10),
    },
]


def test_compute_weekly_stats_projects():
    result = compute_weekly_stats(SAMPLE_TASKS, recent_commits=[], pending_review=[])
    projects = {p["name"]: p for p in result["projects"]}
    assert "hub" in projects
    assert (
        projects["hub"]["active_count"] == 1
    )  # only In Progress (Done excluded from active)
    assert projects["hub"]["majority_assignee"] == "DomBot"


def test_compute_weekly_stats_weeks():
    result = compute_weekly_stats(SAMPLE_TASKS, recent_commits=[], pending_review=[])
    assert "this_week" in result["weeks"]
    assert "last_week" in result["weeks"]
    # t1 created 3 days ago → this_week done=1
    assert result["weeks"]["this_week"]["done"] >= 1


def test_parse_git_log_valid():
    raw = (
        "2026-03-19|feat: add blocked status|ldom1\n2026-03-18|fix: gantt bars|ldom1\n"
    )
    commits = parse_git_log(raw, repo="hub")
    assert len(commits) == 2
    assert commits[0]["repo"] == "hub"
    assert commits[0]["message"] == "feat: add blocked status"
    assert commits[0]["author"] == "ldom1"
    assert commits[0]["date"] == "2026-03-19"


def test_parse_git_log_empty():
    assert parse_git_log("", repo="hub") == []


def test_majority_assignee_tie_alphabetical():
    tasks = [
        {
            "project": "p",
            "status": "In Progress",
            "assignee": "zara",
            "effort_hours": 1,
        },
        {"project": "p", "status": "To Start", "assignee": "alice", "effort_hours": 1},
    ]
    result = compute_weekly_stats(tasks, recent_commits=[], pending_review=[])
    p = next(x for x in result["projects"] if x["name"] == "p")
    assert p["majority_assignee"] == "alice"  # alphabetical tiebreak
