"""Compute weekly stats for PilotView dashboard."""
from __future__ import annotations

import asyncio
import logging
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

LAB_REPOS_ENV_VAR = "LAB_REPOS"


def _parse_iso(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Normalise: strip trailing Z only when no timezone offset already present
        normalized = s
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        # Handle double timezone suffix (e.g. "+00:00Z") produced by some generators
        if "+00:00+00:00" in normalized:
            normalized = normalized.replace("+00:00+00:00", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def _in_window(iso: str | None, days_start: int, days_end: int) -> bool:
    """True if the ISO date is between days_start and days_end days ago."""
    dt = _parse_iso(iso)
    if not dt:
        return False
    now = datetime.now(timezone.utc)
    return (now - timedelta(days=days_start)) >= dt >= (now - timedelta(days=days_end))


def compute_weekly_stats(
    tasks: list[dict],
    recent_commits: list[dict],
    pending_review: list[dict],
) -> dict:
    """Pure computation — no I/O."""
    active_statuses = {"Backlog", "To Start", "In Progress", "Blocked", "Review"}
    done_status = "Done"

    def week_stats(days_start: int, days_end: int) -> dict:
        created = sum(1 for t in tasks if _in_window(t.get("created"), days_start, days_end))
        done    = sum(1 for t in tasks if t.get("status") == done_status and _in_window(t.get("updated"), days_start, days_end))
        commits = sum(1 for c in recent_commits if _in_window(c.get("date") + "T00:00:00+00:00", days_start, days_end))
        return {"created": created, "done": done, "commits": commits}

    active_tasks = [t for t in tasks if t.get("status") in active_statuses]
    proj_names = sorted(set(t.get("project", "") for t in active_tasks if t.get("project")))

    projects = []
    for name in proj_names:
        proj_tasks = [t for t in active_tasks if t.get("project") == name]
        assignees = [t.get("assignee", "") for t in proj_tasks if t.get("assignee")]
        if assignees:
            count = Counter(assignees)
            max_count = max(count.values())
            majority = sorted(k for k, v in count.items() if v == max_count)[0]
        else:
            majority = ""
        projects.append({
            "name": name,
            "active_count": len(proj_tasks),
            "remaining_effort_hours": sum(t.get("effort_hours") or 0 for t in proj_tasks),
            "majority_assignee": majority,
        })

    return {
        "weeks": {
            "this_week": week_stats(0, 7),
            "last_week": week_stats(7, 14),
        },
        "projects": projects,
        "recent_commits": recent_commits[:5],
        "pending_review": pending_review,
    }


def parse_git_log(raw: str, repo: str) -> list[dict]:
    """Parse `git log --format='%as|%s|%an'` output."""
    commits = []
    for line in raw.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) >= 3:
            date, message, author = parts[0], parts[1], parts[2]
            commits.append({
                "date": date,
                "repo": repo,
                "message": message[:50],
                "author": author,
            })
    return commits


async def _git_log_async(repo_path: Path) -> list[dict]:
    """Run git log in subprocess with 3s timeout. Returns [] on error."""
    try:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                "git", "-C", str(repo_path), "log",
                "--since=14 days ago", "--format=%as|%s|%an",
                "--no-merges", "-20",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            ),
            timeout=3.0,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3.0)
        return parse_git_log(stdout.decode("utf-8", errors="replace"), repo=repo_path.name)
    except (asyncio.TimeoutError, FileNotFoundError, OSError) as e:
        logger.warning("git log failed for %s: %s", repo_path, e)
        return []


async def get_weekly_stats_data(tasks: list[dict], lab_repos_env: str) -> dict:
    """Async entry point: fetch git logs + compute stats."""
    repo_paths = []
    for p in (lab_repos_env or "").split(":"):
        p = p.strip()
        if p:
            path = Path(p)
            if path.exists() and (path / ".git").exists():
                repo_paths.append(path)
            else:
                logger.warning("LAB_REPOS path invalid or not a git repo: %s", p)

    all_commits: list[dict] = []
    if repo_paths:
        results = await asyncio.gather(*(_git_log_async(p) for p in repo_paths))
        for commits in results:
            all_commits.extend(commits)
    all_commits.sort(key=lambda c: c.get("date", ""), reverse=True)

    now = datetime.now(timezone.utc)
    pending_review = []
    for t in tasks:
        if t.get("status") in ("Review", "Blocked"):
            updated = _parse_iso(t.get("updated"))
            days_waiting = (now - updated).days if updated else 0
            pending_review.append({
                "id": t["id"],
                "title": t.get("title", ""),
                "status": t.get("status"),
                "project": t.get("project", ""),
                "updated": t.get("updated", ""),
                "days_waiting": days_waiting,
            })
    pending_review.sort(key=lambda x: x["days_waiting"], reverse=True)

    return compute_weekly_stats(tasks, all_commits, pending_review)
